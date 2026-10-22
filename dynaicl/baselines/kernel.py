"""Kernel analog (Nadaraya-Watson) baseline, the "parroting-flavoured" predictor (Section 2.5).

Direct h-step analog regression on context pairs (u_j, y_j) = (x_j, x_{j+h}), j = 0..m-1, m = n - h + 1:

    m_b(u) = sum_j K((u - u_j)/b) y_j / sum_j K((u - u_j)/b),   Gaussian K.

Bandwidth b = c * scale. The multiplier c is selected on validation points inside the context. During
validation, each row's scale uses only the data that row may read (rolling origin: x_0..x_j; blocked:
the fold's training observations). The final forecast uses c* times sd(x_0..x_n). The predictive is N(m_b*(x_n), v), where v is
the mean squared validation residual at b*. Each residual is out-of-sample, but taking the minimum over
the candidate bandwidths biases v low (a selection effect). This is a baseline heuristic, and its calibration
is measured, not assumed.

Validation schemes (an entry allowed[j, i] means training pair i may be used to predict validation pair j):

* rolling_origin (default): pair j has forecast origin j, since x_j is known and x_{j+h} is the target.
  Only pairs whose target time i + h <= j may be used, i.e. i <= j - h. Pair j is a validation point
  only if at least ``min_train_pairs`` such pairs exist.
* blocked: contiguous validation blocks of pairs [s, e] (which use observations x_s..x_{e+h}).
  Training pairs must leave at least g = max(h, gap) unused time points between their observations and
  that span (i.e. a distance of g + 1 or more): i + h < s - g, or i > e + h + g.
* leave_one_out: all i != j. COMPARISON ONLY. Adjacent pairs share observations and are dependent.

If a scheme gives fewer than ``min_validation_points`` validation residuals, the plug-in bandwidth
b = 1.06 sd(u) m^(-1/5) (Silverman's rule) is used, with variance equal to the mean squared
h-step increment over the pairs. If m < ``min_pairs``, the predictor falls back to persistence.
Both fallbacks are flagged in ``info``.

Limitation: short contexts give few validation points, so the bandwidth and variance are noisy.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from dynaicl.baselines.common import CONTEXT_ONLY_MUST_NOT_ACCESS, FallbackSettings, variance_floor
from dynaicl.baselines.persistence import persistence_variance
from dynaicl.references.base import Predictor, PredictorDescription
from dynaicl.references.predictive import GaussianPredictive
from dynaicl.systems.context import ContextWindow

FLOAT = np.float64
SCHEMES = ("rolling_origin", "blocked", "leave_one_out")


@dataclass(frozen=True)
class KernelSettings:
    bandwidth_multipliers: tuple[float, ...] = (0.05, 0.1, 0.2, 0.4, 0.8, 1.6, 3.2, 6.4)
    min_train_pairs: int = 3
    n_blocks: int = 4
    gap: int = 1
    min_pairs: int = 3
    min_validation_points: int = 2

    def __post_init__(self) -> None:
        mult = tuple(self.bandwidth_multipliers)
        if not mult or any(not c > 0 for c in mult) or list(mult) != sorted(mult):
            raise ValueError("bandwidth multipliers must be positive and sorted ascending")
        if min(self.min_train_pairs, self.n_blocks, self.min_pairs, self.min_validation_points) < 1 or self.gap < 0:
            raise ValueError("invalid kernel settings")


def analog_pairs(x: np.ndarray, h: int) -> tuple[np.ndarray, np.ndarray]:
    """(u, y) = (x_0..x_{n-h}, x_h..x_n). Empty if n < h."""
    if x.shape[0] <= h:
        return x[:0], x[:0]
    return x[:-h], x[h:]


def validation_mask(m: int, h: int, scheme: str, settings: KernelSettings) -> tuple[np.ndarray, np.ndarray]:
    """(allowed (m, m) bool, is_validation_row (m,) bool) for the scheme. See module docstring."""
    j = np.arange(m)[:, None]
    i = np.arange(m)[None, :]
    if scheme == "rolling_origin":
        allowed = i <= j - h
        rows = allowed.sum(axis=1) >= settings.min_train_pairs
    elif scheme == "blocked":
        g = max(h, settings.gap)
        allowed = np.zeros((m, m), dtype=bool)
        for block in np.array_split(np.arange(m), min(settings.n_blocks, m)):
            if block.size == 0:
                continue
            s, e = int(block[0]), int(block[-1])
            ok = (np.arange(m) + h < s - g) | (np.arange(m) > e + h + g)
            allowed[block[:, None], np.arange(m)[None, :]] = ok[None, :]
        rows = allowed.any(axis=1)
    elif scheme == "leave_one_out":
        allowed = i != j
        rows = allowed.any(axis=1)
    else:
        raise ValueError(f"unknown scheme {scheme!r}")
    allowed = allowed & rows[:, None]
    return allowed, rows


def nadaraya_watson(u_query: np.ndarray, u_train: np.ndarray, y_train: np.ndarray, allowed: np.ndarray,
                    bandwidths: np.ndarray) -> np.ndarray:
    """Predictions of shape (B, Q). ``bandwidths`` is (B,) or (B, Q). Rows with no allowed training pair are
    NaN; callers mask them out.

    Weights are stabilised by subtracting the row maximum of the log kernel, so a query far from all
    inputs returns the target of the nearest allowed input instead of 0/0.
    """
    bw = np.asarray(bandwidths, dtype=FLOAT)
    bw = bw[:, None, None] if bw.ndim == 1 else bw[:, :, None]   # (B,) shared, or (B, Q) per query row
    d = (u_query[:, None] - u_train[None, :])[None, :, :] / bw
    logk = np.where(allowed[None, :, :], -0.5 * d * d, -np.inf)
    row_max = logk.max(axis=2, keepdims=True)
    has_any = np.isfinite(row_max)
    w = np.exp(np.where(has_any, logk - np.where(has_any, row_max, 0.0), -np.inf))
    num = w @ y_train
    den = w.sum(axis=2)
    out = np.full(den.shape, np.nan)
    np.divide(num, den, out=out, where=den > 0)
    return out


@dataclass(frozen=True)
class BandwidthSelection:
    scheme: str
    bandwidth: float
    multiplier: float | None
    validation_mse: float
    n_validation: int
    used_plugin: bool
    mse_by_multiplier: tuple[float, ...]


def context_scale(x: np.ndarray) -> float:
    sd = float(np.std(x))
    if sd > 0:
        return sd
    mx = float(np.max(np.abs(x)))
    return mx if mx > 0 else 1.0


def _robust_scale(sd: np.ndarray, absmax: np.ndarray) -> np.ndarray:
    """context_scale applied elementwise: sd, else max|x|, else 1."""
    return np.where(sd > 0, sd, np.where(absmax > 0, absmax, 1.0))


def validation_scales(x: np.ndarray, h: int, scheme: str, allowed: np.ndarray, rows: np.ndarray,
                      settings: KernelSettings) -> np.ndarray:
    """Bandwidth scale for each validation row, computed only from data that row's validation may read.

    rolling_origin: sd(x_0..x_j), the data available at forecast origin j. Vectorised by masking
    later entries to NaN, so they cannot influence the result.
    blocked: sd of the observations used by the fold's training pairs (excludes the block and its gaps).
    leave_one_out: sd of the whole context (comparison scheme; it is not time-respecting anyway).
    Non-validation rows get NaN.
    """
    m = rows.shape[0]
    scales = np.full(m, np.nan)
    idx = np.flatnonzero(rows)
    if idx.size == 0:
        return scales
    if scheme == "rolling_origin":
        visible = np.arange(x.size)[None, :] <= idx[:, None]
        xs = np.where(visible, x[None, :], np.nan)
        scales[idx] = _robust_scale(np.nanstd(xs, axis=1), np.nanmax(np.abs(xs), axis=1))
    elif scheme == "blocked":
        for block in np.array_split(np.arange(m), min(settings.n_blocks, m)):
            vb = block[rows[block]]
            if vb.size == 0:
                continue
            tr = np.flatnonzero(allowed[vb[0]])
            obs = np.concatenate([x[tr], x[tr + h]])
            scales[vb] = context_scale(obs)
    else:
        scales[idx] = context_scale(x)
    return scales


def validation_predictions(x: np.ndarray, h: int, scheme: str, settings: KernelSettings
                           ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """(predictions (B, m) with NaN off the validation rows, validation-row mask (m,), multipliers (B,)).

    Validation row j uses bandwidth c_k * scale_j (see :func:`validation_scales`), so neither the
    candidate bandwidths nor the predictions read data the scheme forbids for that row.
    """
    u, y = analog_pairs(x, h)
    m = u.shape[0]
    mult = np.asarray(settings.bandwidth_multipliers, dtype=FLOAT)
    allowed, rows = validation_mask(m, h, scheme, settings)
    preds = np.full((mult.size, m), np.nan)
    if rows.any():
        scales = validation_scales(x, h, scheme, allowed, rows, settings)
        preds[:, rows] = nadaraya_watson(u[rows], u, y, allowed[rows], mult[:, None] * scales[None, rows])
    return preds, rows, mult


def select_bandwidth(x: np.ndarray, h: int, scheme: str, settings: KernelSettings,
                     fallback: FallbackSettings) -> BandwidthSelection:
    u, y = analog_pairs(x, h)
    m = u.shape[0]
    scale = context_scale(x)
    mult = np.asarray(settings.bandwidth_multipliers, dtype=FLOAT)
    all_preds, rows, _ = validation_predictions(x, h, scheme, settings)
    n_val = int(rows.sum())
    if n_val >= settings.min_validation_points:
        preds = all_preds[:, rows]
        resid = y[rows][None, :] - preds
        mse = np.mean(resid * resid, axis=1)
        best = int(np.flatnonzero(mse == mse.min())[-1])  # exact ties -> larger (smoother) bandwidth
        # final bandwidth: selected multiplier times the scale of the full context (available at origin n)
        return BandwidthSelection(scheme, float(mult[best] * scale), float(mult[best]), float(mse[best]), n_val,
                                  False, tuple(float(v) for v in mse))
    sd_u = float(np.std(u)) if m > 1 else 0.0
    b = 1.06 * (sd_u if sd_u > 0 else scale) * max(m, 1) ** (-0.2)
    d = y - u
    v = float(np.mean(d * d)) if m > 0 else persistence_variance(x, h, fallback)[0]
    return BandwidthSelection(scheme, b, None, v, n_val, True, ())


class KernelAnalogPredictor(Predictor):
    def __init__(self, scheme: str = "rolling_origin", settings: KernelSettings = KernelSettings(),
                 fallback: FallbackSettings = FallbackSettings()):
        if scheme not in SCHEMES:
            raise ValueError(f"scheme must be one of {SCHEMES}")
        self.scheme = scheme
        self.settings = settings
        self.fallback = fallback
        self.description = PredictorDescription(
            name=f"kernel_{scheme}", category="context-only", assumed_system_distribution=None,
            may_access=("context", "config hyperparameters"), must_not_access=CONTEXT_ONLY_MUST_NOT_ACCESS,
            uses_true_noise_scale=False,
            assumptions=f"Nadaraya-Watson direct h-step analog; bandwidth by {scheme} validation within the context",
        )

    def _predict(self, context: ContextWindow, horizon: int) -> GaussianPredictive:
        x = context.values
        u, y = analog_pairs(x, horizon)
        if u.shape[0] < self.settings.min_pairs:
            v, how = persistence_variance(x, horizon, self.fallback)
            return GaussianPredictive(context.last, v, info={"fallback": True, "fallback_rule": "persistence/" + how})
        sel = select_bandwidth(x, horizon, self.scheme, self.settings, self.fallback)
        allowed = np.ones((1, u.shape[0]), dtype=bool)
        mean = float(nadaraya_watson(np.array([context.last]), u, y, allowed, np.array([sel.bandwidth]))[0, 0])
        v = max(sel.validation_mse, variance_floor(x, self.fallback.variance_relative_floor))
        return GaussianPredictive(mean, v, info={"fallback": sel.used_plugin, "bandwidth": sel.bandwidth,
                                                 "multiplier": sel.multiplier, "n_validation": sel.n_validation,
                                                 "scheme": self.scheme})
