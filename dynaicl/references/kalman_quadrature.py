"""Stage 0.6 reference: Kalman likelihood given a (ANALYTICALLY EXACT given a, in float64) and composite Gauss-Legendre
integration over a on a SHARED, full-support node set (NUMERICALLY APPROXIMATED with verified convergence).
See docs/MATH_STAGE06.md sections 3-6.

Information parity by construction:
* the population-aware reference and the noise-aware stability-only comparator are both
  :class:`NoisyObservationBayesPredictor`. They share the Kalman code, the noise model, the x_0 prior and the node set,
  and differ **only** in ``prior``;
* the node set covers (-outer_bound, outer_bound) with every prior-support endpoint as a panel edge, so a prior that is
  zero outside its support (P-STABLE truncated at +/-0.95) is integrated exactly over its own support.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, replace
from functools import lru_cache

import numpy as np
from scipy import special

from dynaicl.baselines.common import CONTEXT_ONLY_MUST_NOT_ACCESS
from dynaicl.references.base import Predictor, PredictorDescription
from dynaicl.references.predictive import QuadratureMixturePredictive
from dynaicl.systems import ar1
from dynaicl.systems.context import ContextWindow
from dynaicl.systems.noisy import NoisyObservationCondition, NoisyObservationModel
from dynaicl.systems.priors import StableCoefficientPrior

FLOAT = np.float64
_LOG_2PI = math.log(2.0 * math.pi)


# ------------------------------------------------------------------------------------------- node set


@dataclass(frozen=True)
class KalmanQuadratureSettings:
    outer_bound: float = 0.999
    breakpoints: tuple[float, ...] = (-0.95, 0.95)
    panels_per_unit: int = 64
    nodes_per_panel: int = 8

    def __post_init__(self) -> None:
        if not 0 < self.outer_bound < 1 or self.panels_per_unit < 1 or self.nodes_per_panel < 1:
            raise ValueError("invalid KalmanQuadratureSettings")
        if any(abs(b) >= self.outer_bound for b in self.breakpoints):
            raise ValueError("breakpoints must lie strictly inside the outer bound")

    def refined(self, factor: int = 2) -> "KalmanQuadratureSettings":
        return replace(self, panels_per_unit=self.panels_per_unit * factor)

    def cut_points(self) -> tuple[float, ...]:
        return tuple(sorted({-self.outer_bound, self.outer_bound, *self.breakpoints}))


@lru_cache(maxsize=32)
def shared_node_set(settings: KalmanQuadratureSettings) -> tuple[np.ndarray, np.ndarray]:
    """(nodes, log GL weights) of the composite rule. Every cut point is a panel edge."""
    x, w = np.polynomial.legendre.leggauss(settings.nodes_per_panel)
    cuts = settings.cut_points()
    nodes, weights = [], []
    for lo, hi in zip(cuts[:-1], cuts[1:]):
        p = max(1, math.ceil((hi - lo) * settings.panels_per_unit))
        edges = np.linspace(lo, hi, p + 1)
        for a, b in zip(edges[:-1], edges[1:]):
            nodes.append(0.5 * (a + b) + 0.5 * (b - a) * x)
            weights.append(0.5 * (b - a) * w)
    n, lw = np.concatenate(nodes), np.log(np.concatenate(weights))
    n.setflags(write=False)
    lw.setflags(write=False)
    return n, lw


# ------------------------------------------------------------------------------------- Kalman filter


def kalman_filter_on_nodes(Y: np.ndarray, a: np.ndarray, model: NoisyObservationModel,
                           keep: tuple[int, ...]) -> dict:
    """Kalman filter for B observation sequences (rows of Y, columns y_0..y_T) and every a in ``a`` at once.

    Returns {"loglik": {n: (B, M)}, "m": {n: (B, M)}, "P": {n: (M,)}} for each context length n in ``keep``.
    loglik[n] = log p(y_{0:n} | a); m[n], P[n] = mean and variance of x_n | y_{0:n}, a.
    Causal: the values for n depend only on columns 0..n of Y. (TESTED: perturbing later columns changes nothing.)
    """
    Y = np.asarray(Y, dtype=FLOAT)
    if Y.ndim != 2:
        raise ValueError("Y must be (B, T + 1)")
    a = np.asarray(a, dtype=FLOAT)
    sw2, sv2 = model.sigma_w ** 2, model.sigma_v ** 2
    B, T1 = Y.shape
    if max(keep) >= T1:
        raise ValueError("requested context length exceeds the observations supplied")
    keep_set = set(keep)
    out = {"loglik": {}, "m": {}, "P": {}}
    m = np.zeros((B, a.size))
    P = np.full(a.size, model.x0_sd ** 2)                       # P_{0|-1}
    ll = np.zeros((B, a.size))
    for t in range(max(keep) + 1):
        if t > 0:
            m = a[None, :] * m                                  # m_{t|t-1}
            P = a * a * P + sw2                                 # P_{t|t-1}
        S = P + sv2
        e = Y[:, t:t + 1] - m
        ll = ll - 0.5 * (_LOG_2PI + np.log(S))[None, :] - 0.5 * e * e / S[None, :]
        K = P / S
        m = m + K[None, :] * e
        P = P * sv2 / S                                         # = (1 - K) P_{t|t-1}, cancellation-free
        if t in keep_set:
            out["loglik"][t], out["m"][t], out["P"][t] = ll.copy(), m.copy(), P.copy()
    if not all(np.all(np.isfinite(v)) for d in out.values() for v in d.values()):
        raise FloatingPointError("non-finite Kalman quantities")
    return out


def observation_predictive_moments(a: np.ndarray, m: np.ndarray, P: np.ndarray, model: NoisyObservationModel,
                                   h: int) -> tuple[np.ndarray, np.ndarray]:
    """Moments of y_{n+h} | y_{0:n}, a: mean a^h m, variance a^{2h} P + sigma_w^2 c_h(a) + sigma_v^2 (MATH_STAGE06 section 5).
    The target observation's own noise variance sigma_v^2 is added exactly once."""
    ah = np.power(a, h)
    mean = ah * m
    var = ah * ah * P + model.sigma_w ** 2 * ar1.horizon_variance_factor(a, h) + model.sigma_v ** 2
    return mean, var


def latent_predictive_moments(a, m, P, model, h):
    """Moments of the latent x_{n+h} | y_{0:n}, a (exploratory target only)."""
    ah = np.power(a, h)
    return ah * m, ah * ah * P + model.sigma_w ** 2 * ar1.horizon_variance_factor(a, h)


def mixture_logpdf_cdf(log_w: np.ndarray, means: np.ndarray, variances: np.ndarray,
                       y: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Row-wise mixture log density and CDF at y. log_w, means: (B, M); variances: (B, M) or (M,); y: (B,)."""
    var = np.broadcast_to(variances, means.shape)
    z = (y[:, None] - means) / np.sqrt(var)
    comp = log_w - 0.5 * (_LOG_2PI + np.log(var)) - 0.5 * z * z
    lp = special.logsumexp(comp, axis=1)
    cdf = np.clip(np.sum(np.exp(log_w) * special.ndtr(z), axis=1), 0.0, 1.0)
    return lp, cdf


# ------------------------------------------------------------------------------------------- priors


@dataclass(frozen=True)
class ArcsineCoefficientPrior:
    """Generic context-only alternative prior (secondary only): density ∝ (1 - a^2)^(-1/2) on (-b, b).
    It encodes stability, with more mass near +/-1 than the uniform prior. It uses no population information."""

    bound: float = 0.999
    family: str = "ARCSINE"

    @property
    def support(self) -> tuple[float, float]:
        return (-self.bound, self.bound)

    def spec(self) -> dict:
        return {"family": self.family, "bound": float(self.bound)}

    def coefficient_logpdf(self, a) -> np.ndarray:
        a = np.asarray(a, dtype=FLOAT)
        inside = np.abs(a) <= self.bound
        with np.errstate(divide="ignore", invalid="ignore"):
            val = -0.5 * np.log1p(-a * a) - math.log(2.0 * math.asin(self.bound))
        return np.where(inside, val, -np.inf)


# ---------------------------------------------------------------------------------------- predictors


class NoisyObservationBayesPredictor(Predictor):
    """Posterior-predictive over a for the noisy-observation model, for a given prior. Both primary predictors are
    instances of this class (they differ only in ``prior``)."""

    def __init__(self, prior, model: NoisyObservationModel, settings: KalmanQuadratureSettings,
                 description: PredictorDescription):
        self.prior = prior
        self.model = model
        self.settings = settings
        self.description = description
        self.nodes, self.log_gl = shared_node_set(settings)
        cuts = settings.cut_points()
        lo, hi = prior.support
        if not (any(abs(lo - c) <= 1e-15 for c in cuts) and any(abs(hi - c) <= 1e-15 for c in cuts)):
            raise ValueError(f"prior support {prior.support} endpoints must be node-set cut points {cuts}")
        with np.errstate(divide="ignore"):
            lp = np.asarray(prior.coefficient_logpdf(self.nodes), dtype=FLOAT)
        self.log_prior = lp
        self._log_base = self.log_gl + lp           # -inf where the prior is zero

    def with_settings(self, settings: KalmanQuadratureSettings) -> "NoisyObservationBayesPredictor":
        return NoisyObservationBayesPredictor(self.prior, self.model, settings, self.description)

    # ---- posterior on the node set
    def batch_posterior(self, Y_context: np.ndarray, ns: tuple[int, ...]) -> dict:
        """For B observation rows and each n in ns: (log masses (B, M), m (B, M), P (M,)). Uses only columns 0..n."""
        f = kalman_filter_on_nodes(Y_context, self.nodes, self.model, ns)
        out = {}
        for n in ns:
            lw = self._log_base[None, :] + f["loglik"][n]
            norm = special.logsumexp(lw, axis=1, keepdims=True)
            if not np.all(np.isfinite(norm)):
                raise FloatingPointError("posterior normaliser is not finite")
            out[n] = (lw - norm, f["m"][n], f["P"][n])
        return out

    def batch_scores(self, Y_context: np.ndarray, targets: dict, ns: tuple[int, ...], hs: tuple[int, ...]) -> dict:
        """Log scores and PIT of y_{n+h} for every (n, h). ``targets[(n, h)]`` is a (B,) array held by the EVALUATOR.
        The predictor never receives the target columns themselves. TESTED equal to per-context ``predict``."""
        post = self.batch_posterior(Y_context, ns)
        out = {}
        for n in ns:
            lw, m, P = post[n]
            for h in hs:
                mean, var = observation_predictive_moments(self.nodes[None, :], m, P[None, :], self.model, h)
                lp, cdf = mixture_logpdf_cdf(lw, mean, var, targets[(n, h)])
                if not (np.all(np.isfinite(lp)) and np.all(np.isfinite(cdf))):
                    raise FloatingPointError(f"non-finite score at n={n}, h={h}")
                out[(n, h)] = (lp, cdf)
        return out

    def posterior(self, context: ContextWindow) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        n = context.n_transitions
        lw, m, P = self.batch_posterior(context.values[None, :], (n,))[n]
        return lw[0], m[0], P

    def posterior_cdf(self, context: ContextWindow, a_star: float) -> float:
        """P(a <= a_star | y_{0:n}). Node masses below the panel containing a_star, plus an 8-point GL integral
        over [panel start, a_star] with the Kalman likelihood at those points. Used for SBC."""
        n = context.n_transitions
        lw, _, _ = self.posterior(context)
        y = context.values[None, :]
        full = kalman_filter_on_nodes(y, self.nodes, self.model, (n,))
        log_norm = special.logsumexp(self._log_base + full["loglik"][n][0])
        k = self.settings.nodes_per_panel
        # panel edges from node layout: panel j spans [edge_j, edge_{j+1}]
        edges = _panel_edges(self.settings)
        j = int(np.clip(np.searchsorted(edges, a_star, side="right") - 1, 0, len(edges) - 2))
        below = special.logsumexp(lw[: j * k]) if j > 0 else -np.inf
        lo_e, hi_e = edges[j], min(max(a_star, edges[j]), edges[j + 1])
        if hi_e > lo_e:
            x, w = np.polynomial.legendre.leggauss(k)
            pts = 0.5 * (lo_e + hi_e) + 0.5 * (hi_e - lo_e) * x
            ll = kalman_filter_on_nodes(y, pts, self.model, (n,))["loglik"][n][0]
            with np.errstate(divide="ignore"):
                part = special.logsumexp(np.log(0.5 * (hi_e - lo_e) * w) + self.prior.coefficient_logpdf(pts) + ll) - log_norm
        else:
            part = -np.inf
        return float(min(1.0, np.exp(np.logaddexp(below, part))))

    def _predict(self, context: ContextWindow, horizon: int) -> QuadratureMixturePredictive:
        lw, m, P = self.posterior(context)
        mean, var = observation_predictive_moments(self.nodes, m, P, self.model, horizon)
        ar1.require_representable(mean[np.isfinite(lw)], var[np.isfinite(lw)], self.description.name)
        return QuadratureMixturePredictive(lw, mean, var, info={
            "quadrature": {"n_nodes": int(self.nodes.size), "panels_per_unit": self.settings.panels_per_unit,
                           "nodes_per_panel": self.settings.nodes_per_panel, "capped": False},
            "quadrature_capped": 0.0, "fallback": False})


@lru_cache(maxsize=32)
def _panel_edges(settings: KalmanQuadratureSettings) -> np.ndarray:
    cuts = settings.cut_points()
    edges = [cuts[0]]
    for lo, hi in zip(cuts[:-1], cuts[1:]):
        p = max(1, math.ceil((hi - lo) * settings.panels_per_unit))
        edges.extend(np.linspace(lo, hi, p + 1)[1:].tolist())
    e = np.array(edges)
    e.setflags(write=False)
    return e


class NoiseAwareMlePlugInPredictor(Predictor):
    """Secondary noise-aware context-only alternative: grid maximum-likelihood a_hat over the shared node set
    (flat on (-0.999, 0.999)), then the plug-in Kalman predictive at a_hat. NON-BAYESIAN; same information as the
    primary pair (same likelihood, noise levels and x_0 prior)."""

    def __init__(self, model: NoisyObservationModel, settings: KalmanQuadratureSettings = KalmanQuadratureSettings()):
        self.model = model
        self.settings = settings
        self.nodes, _ = shared_node_set(settings)
        self.description = PredictorDescription(
            name="noise_aware_mle_plugin", category="context-only", assumed_system_distribution=None,
            may_access=("context", "known sigma_w, sigma_v, x_0 prior"), must_not_access=CONTEXT_ONLY_MUST_NOT_ACCESS,
            uses_true_noise_scale=True, assumptions="grid MLE of a under the Kalman likelihood; plug-in predictive",
            observation_model=model.label)

    def _predict(self, context: ContextWindow, horizon: int):
        from dynaicl.references.predictive import GaussianPredictive
        n = context.n_transitions
        f = kalman_filter_on_nodes(context.values[None, :], self.nodes, self.model, (n,))
        i = int(np.argmax(f["loglik"][n][0]))
        a = self.nodes[i:i + 1]
        mean, var = observation_predictive_moments(a, f["m"][n][0, i:i + 1], f["P"][n][i:i + 1], self.model, horizon)
        return GaussianPredictive(float(mean[0]), float(var[0]), info={"a_hat": float(a[0]), "fallback": False})


# ------------------------------------------------------------------------------------------ factories


def noisy_population_reference(prior, model: NoisyObservationModel,
                               settings: KalmanQuadratureSettings = KalmanQuadratureSettings()) -> NoisyObservationBayesPredictor:
    """Population-aware (matched) reference for NoisyObservationCondition(prior, model)."""
    cond = NoisyObservationCondition(prior, model)
    return NoisyObservationBayesPredictor(prior, model, settings, PredictorDescription(
        name="noisy_population_bayes", category="continuous-prior-bayes",
        assumed_system_distribution=cond.system_distribution_fingerprint(),
        may_access=("context y_0..y_n", "population prior over a", "known sigma_w, sigma_v, x_0 prior"),
        must_not_access=("latent states", "true a", "future observations", "system identity"),
        uses_true_noise_scale=True, assumptions="a ~ population prior; Kalman likelihood with latent x_0",
        observation_model=model.label))


def noise_aware_stability_predictor(model: NoisyObservationModel, bound: float = 0.999,
                                    settings: KalmanQuadratureSettings = KalmanQuadratureSettings()) -> NoisyObservationBayesPredictor:
    """PRIMARY COMPARATOR: identical to the reference except prior = U(-bound, bound) (generic stability only)."""
    prior = StableCoefficientPrior(rho=bound, sigma=model.sigma_w, shape="uniform")
    return NoisyObservationBayesPredictor(prior, model, settings, PredictorDescription(
        name="noise_aware_stability_bayes", category="context-only", assumed_system_distribution=None,
        may_access=("context y_0..y_n", "generic stability bound", "known sigma_w, sigma_v, x_0 prior"),
        must_not_access=CONTEXT_ONLY_MUST_NOT_ACCESS + ("latent states",), uses_true_noise_scale=True,
        assumptions="a ~ U(-bound, bound): stability only; same Kalman likelihood as the reference",
        observation_model=model.label))


def noise_aware_arcsine_predictor(model: NoisyObservationModel, bound: float = 0.999,
                                  settings: KalmanQuadratureSettings = KalmanQuadratureSettings()) -> NoisyObservationBayesPredictor:
    """Secondary noise-aware context-only alternative (selection audit only)."""
    return NoisyObservationBayesPredictor(ArcsineCoefficientPrior(bound), model, settings, PredictorDescription(
        name="noise_aware_arcsine_bayes", category="context-only", assumed_system_distribution=None,
        may_access=("context y_0..y_n", "generic stability bound", "known sigma_w, sigma_v, x_0 prior"),
        must_not_access=CONTEXT_ONLY_MUST_NOT_ACCESS + ("latent states",), uses_true_noise_scale=True,
        assumptions="a ~ arcsine on (-bound, bound): stability only", observation_model=model.label))
