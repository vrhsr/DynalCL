"""Vectorised one-step (h = 1) Bayes predictives for scalar AR(1) with known sigma (Stage 1A separability map).

The frozen references (``dynaicl.references``) evaluate one context at a time. The separability map needs about
10^6-10^7 contexts, so this module evaluates the SAME predictives in batch, from per-context sufficient statistics:

* truncated-Gaussian coefficient priors on (-rho, rho), covering P-STABLE truncated normal (the population prior) and
  P-STABLE uniform (the generic-stability, context-only prior): posterior TN(m, s^2; -rho, rho) and the closed-form
  one-step predictive density of docs/MATH.md section 4.3 (DERIVED there; ANALYTICALLY EXACT);
* finite libraries: posterior weights from the Gaussian-in-a quadratic form, predictive sum_k w_k N(a_k x_n, sigma^2)
  (docs/MATH.md section 6; ANALYTICALLY EXACT given the library).

Equality with the frozen references is TESTED (tests_stage1/test_ar1_batch_references.py) to <= 1e-9 nats, the frozen
Tier-1 tolerance, on random contexts and on the stored Stage 0.5 per-item contrasts.

Only h = 1 is implemented: Stage 1 is a next-step study (the h = 5 gap is negligible, Stage 0.5).

Domain of accuracy (TESTED / measured): for stationary contexts (|a| <= 0.999, |x_n| up to about 50) the batch and
frozen log densities agree to about 1e-13 or better. For explosive data with |x_n| of order 10^3-10^4 (a = 1.2, n = 40)
float64 cancellation between terms of size 10^3-10^5 limits agreement to about 2e-9. Stage 1A never evaluates there.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from scipy import special

FLOAT = np.float64
LOG_SQRT_2PI = 0.5 * math.log(2.0 * math.pi)


@dataclass(frozen=True)
class ContextStats:
    """Per-context sufficient statistics of x_0..x_n: S_xx = sum x_{t-1}^2, S_xy = sum x_{t-1} x_t, last = x_n."""

    sxx: np.ndarray
    sxy: np.ndarray
    last: np.ndarray

    @staticmethod
    def from_contexts(values: np.ndarray) -> "ContextStats":
        """``values``: (N, n + 1) array of contexts x_0..x_n (all of equal length), each cut by harness.make_context."""
        v = np.asarray(values, dtype=FLOAT)
        if v.ndim != 2 or v.shape[1] < 2:
            raise ValueError("contexts must be (N, n + 1) with n >= 1")
        prev, curr = v[:, :-1], v[:, 1:]
        return ContextStats(np.einsum("ij,ij->i", prev, prev), np.einsum("ij,ij->i", prev, curr), v[:, -1].copy())

    @property
    def size(self) -> int:
        return int(self.sxx.shape[0])


def log_ndtr_diff(lo: np.ndarray, hi: np.ndarray) -> np.ndarray:
    """log(Phi(hi) - Phi(lo)) for lo < hi, accurate in both tails (reflect so the pair sits in the lower tail)."""
    lo = np.asarray(lo, dtype=FLOAT)
    hi = np.asarray(hi, dtype=FLOAT)
    if np.any(hi <= lo):
        raise ValueError("log_ndtr_diff requires lo < hi")
    flip = lo > 0
    a = np.where(flip, -hi, lo)
    b = np.where(flip, -lo, hi)
    la, lb = special.log_ndtr(a), special.log_ndtr(b)
    # log(e^lb - e^la) = lb + log1p(-e^(la - lb)); la < lb strictly
    return lb + np.log1p(-np.exp(la - lb))


@dataclass(frozen=True)
class TruncatedGaussianPrior:
    """a ~ N(mu0, tau0^2) truncated to (-rho, rho); ``tau0 = None`` means uniform on (-rho, rho). sigma known."""

    rho: float
    sigma: float = 1.0
    mu0: float | None = None
    tau0: float | None = None

    def __post_init__(self) -> None:
        if not (0.0 < self.rho < 1.0) or not self.sigma > 0:
            raise ValueError("need 0 < rho < 1 and sigma > 0")
        if (self.mu0 is None) != (self.tau0 is None):
            raise ValueError("give both mu0 and tau0, or neither (uniform)")
        if self.tau0 is not None and not self.tau0 > 0:
            raise ValueError("tau0 must be > 0")

    @property
    def precision_terms(self) -> tuple[float, float]:
        if self.tau0 is None:
            return 0.0, 0.0
        return 1.0 / self.tau0**2, self.mu0 / self.tau0**2

    def posterior(self, st: ContextStats) -> tuple[np.ndarray, np.ndarray]:
        """(m, s) of the untruncated Gaussian kernel of the posterior (MATH 4.1). Raises if improper."""
        p0, h0 = self.precision_terms
        s2inv = st.sxx / self.sigma**2 + p0
        if np.any(s2inv <= 0):
            raise ValueError("improper posterior (S_xx = 0 under a uniform prior)")
        s2 = 1.0 / s2inv
        m = s2 * (st.sxy / self.sigma**2 + h0)
        return m, np.sqrt(s2)

    def logpdf(self, st: ContextStats, y: np.ndarray) -> np.ndarray:
        """log p(y | context) for h = 1 (MATH 4.3). ``y`` broadcasts against the batch: (N,) or (N, G)."""
        m, s = self.posterior(st)
        c, sig2 = st.last, self.sigma**2
        y = np.asarray(y, dtype=FLOAT)
        extra = y.ndim - 1
        shp = (-1,) + (1,) * extra
        m_, s_, c_ = m.reshape(shp), s.reshape(shp), c.reshape(shp)
        var_y = sig2 + s_**2 * c_**2
        log_gauss = -0.5 * (y - m_ * c_) ** 2 / var_y - 0.5 * np.log(var_y) - LOG_SQRT_2PI
        sp2 = 1.0 / (1.0 / s_**2 + c_**2 / sig2)
        mp = sp2 * (m_ / s_**2 + y * c_ / sig2)
        sp = np.sqrt(sp2)
        num = log_ndtr_diff((-self.rho - mp) / sp, (self.rho - mp) / sp)
        den = log_ndtr_diff((-self.rho - m_) / s_, (self.rho - m_) / s_)
        return log_gauss + num - den

    def predictive_moments(self, st: ContextStats) -> tuple[np.ndarray, np.ndarray]:
        """Mean m c and sd sqrt(sigma^2 + s^2 c^2) of the untruncated Gaussian part (diagnostic only)."""
        m, s = self.posterior(st)
        return m * st.last, np.sqrt(self.sigma**2 + s**2 * st.last**2)


@dataclass(frozen=True)
class FiniteLibrary:
    """Uniform-weight (or given-weight) library of K atoms a_k with a shared known sigma."""

    atoms: np.ndarray
    sigma: float = 1.0
    weights: np.ndarray | None = None

    def __post_init__(self) -> None:
        a = np.asarray(self.atoms, dtype=FLOAT)
        if a.ndim != 1 or a.size < 1 or not np.all(np.isfinite(a)):
            raise ValueError("atoms must be a finite 1-D array")
        w = np.full(a.size, 1.0 / a.size) if self.weights is None else np.asarray(self.weights, dtype=FLOAT)
        if w.shape != a.shape or np.any(w <= 0) or abs(w.sum() - 1.0) > 1e-12:
            raise ValueError("weights must be positive, same length as atoms, and sum to 1")
        object.__setattr__(self, "atoms", a)
        object.__setattr__(self, "weights", w)

    @property
    def size(self) -> int:
        return int(self.atoms.size)

    def posterior_log_weights(self, st: ContextStats) -> np.ndarray:
        """(N, K) normalised log weights. S_yy cancels in the normalisation, so only a^2 S_xx - 2 a S_xy
        enters (no cancellation)."""
        a = self.atoms[None, :]
        quad = a * a * st.sxx[:, None] - 2.0 * a * st.sxy[:, None]
        lw = np.log(self.weights)[None, :] - quad / (2.0 * self.sigma**2)
        return lw - special.logsumexp(lw, axis=1, keepdims=True)

    def logpdf(self, st: ContextStats, y: np.ndarray, max_elements: int = 4_000_000) -> np.ndarray:
        """log p(y | context), h = 1. ``y``: (N,) or (N, G). Contexts are processed in chunks so that one
        (chunk, G, K) temporary holds at most ``max_elements`` float64 values (memory bound, not accuracy)."""
        y = np.asarray(y, dtype=FLOAT)
        squeeze = y.ndim == 1
        yy = y[:, None] if squeeze else y
        out = np.empty(yy.shape, dtype=FLOAT)
        lw_all = self.posterior_log_weights(st)
        chunk = max(1, max_elements // (yy.shape[1] * self.size))
        for i0 in range(0, st.size, chunk):
            i1 = min(st.size, i0 + chunk)
            lw = lw_all[i0:i1]                                   # (n, K)
            mu = self.atoms[None, :] * st.last[i0:i1, None]       # (n, K)
            z = (yy[i0:i1, :, None] - mu[:, None, :]) / self.sigma  # (n, G, K)
            comp = -0.5 * z * z - math.log(self.sigma) - LOG_SQRT_2PI + lw[:, None, :]
            out[i0:i1] = special.logsumexp(comp, axis=2)
        return out[:, 0] if squeeze else out

    def predictive_moments(self, st: ContextStats) -> tuple[np.ndarray, np.ndarray]:
        w = np.exp(self.posterior_log_weights(st))
        mu = self.atoms[None, :] * st.last[:, None]
        mean = (w * mu).sum(axis=1)
        var = self.sigma**2 + (w * (mu - mean[:, None]) ** 2).sum(axis=1)
        return mean, np.sqrt(var)


def population_prior(sigma: float = 1.0) -> TruncatedGaussianPrior:
    """The Stage 0.5 / 1A population prior P (config/stage05.yaml: truncated normal mu0 0.4, tau0 0.3, rho 0.95)."""
    return TruncatedGaussianPrior(rho=0.95, sigma=sigma, mu0=0.4, tau0=0.3)


def stability_prior(sigma: float = 1.0, bound: float = 0.999) -> TruncatedGaussianPrior:
    """The locked context-only comparator: uniform on (-0.999, 0.999) (Stage 0.5 generic-stability Bayes)."""
    return TruncatedGaussianPrior(rho=bound, sigma=sigma)
