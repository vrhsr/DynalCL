"""1-D quadrature over the AR coefficient (docs/MATH.md section 5).

NUMERICALLY APPROXIMATED with verified convergence. The posterior over ``a`` is represented by
composite Gauss-Legendre nodes on a window that holds all but a negligible fraction of the
posterior mass. The window is derived from the exact quadratic form of the log posterior. The node
masses come from the prior log density plus the conditional log-likelihood evaluated at each node,
so they are not taken from conjugacy formulas.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, replace
from functools import lru_cache

import numpy as np
from scipy import special

from dynaicl.references.base import Predictor, PredictorDescription
from dynaicl.references.predictive import QuadratureMixturePredictive
from dynaicl.systems import ar1
from dynaicl.systems.context import ContextWindow
from dynaicl.systems.priors import StableCoefficientPrior

FLOAT = np.float64


@dataclass(frozen=True)
class QuadratureSettings:
    """Composite Gauss-Legendre settings.

    ``log_drop``: the window is {a : log p(a|D) >= max - log_drop}, intersected with the prior support.
    For a Gaussian-shaped posterior the excluded mass is 2 * (1 - Phi(sqrt(2 * log_drop))). At 40 that
    is about 4e-19, below float64 resolution of a unit mass. (DERIVED, MATH.md section 4.2.)
    """

    panels: int = 16
    nodes_per_panel: int = 8
    log_drop: float = 40.0
    #: h-step predictives: at least this many panels per "resolution cell" of the integrand in a
    #: (see :func:`integrand_resolution_cells`), capped at ``max_panels``.
    panels_per_cell: float = 2.0
    max_panels: int = 8192

    def __post_init__(self) -> None:
        if (self.panels < 1 or self.nodes_per_panel < 1 or not self.log_drop > 0 or not self.panels_per_cell > 0
                or self.max_panels < self.panels):
            raise ValueError("invalid quadrature settings")

    @property
    def n_nodes(self) -> int:
        return self.panels * self.nodes_per_panel

    def refined(self, factor: int = 2) -> "QuadratureSettings":
        """Every resolution parameter multiplied by ``factor`` (used for node-doubling error estimates)."""
        return replace(self, panels=self.panels * factor, panels_per_cell=self.panels_per_cell * factor,
                       max_panels=self.max_panels * factor)


@lru_cache(maxsize=64)
def _legendre(q: int) -> tuple[np.ndarray, np.ndarray]:
    x, w = np.polynomial.legendre.leggauss(q)
    x.setflags(write=False)
    w.setflags(write=False)
    return x, w


def composite_gauss_legendre(lo: np.ndarray | float, hi: np.ndarray | float, panels: int,
                             q: int) -> tuple[np.ndarray, np.ndarray]:
    """Nodes and weights of a composite rule on [lo, hi] (vectorised over leading dims of lo/hi)."""
    lo = np.asarray(lo, dtype=FLOAT)
    hi = np.asarray(hi, dtype=FLOAT)
    x, w = _legendre(q)
    edges = lo[..., None] + (hi - lo)[..., None] * (np.arange(panels + 1) / panels)
    a, b = edges[..., :-1], edges[..., 1:]
    half = 0.5 * (b - a)
    mid = 0.5 * (b + a)
    nodes = (mid[..., None] + half[..., None] * x).reshape(*lo.shape, panels * q)
    weights = (half[..., None] * w).reshape(*lo.shape, panels * q)
    return nodes, weights


def gauss_legendre_on_edges(edges: np.ndarray, q: int) -> tuple[np.ndarray, np.ndarray]:
    """Composite Gauss-Legendre nodes and weights on arbitrary (sorted) panel edges."""
    x, w = _legendre(q)
    a, b = edges[:-1], edges[1:]
    half = 0.5 * (b - a)
    mid = 0.5 * (b + a)
    return (mid[:, None] + half[:, None] * x).ravel(), (half[:, None] * w).ravel()


def quadratic_window(precision: float, linear: float, support: tuple[float, float],
                     log_drop: float) -> tuple[float, float]:
    """Window for a log density -0.5 P a^2 + c a on ``support`` (log-concave, exactly quadratic).

    With m = c / P and mode a* = clip(m, support), the set {log p >= log p(a*) - log_drop} is
    abs(a - m) <= sqrt((a* - m)^2 + 2 log_drop / P), intersected with the support. If P = 0 the
    density is flat and the window is the whole (necessarily bounded) support.
    """
    lo_s, hi_s = support
    if precision <= 0.0:
        if not (math.isfinite(lo_s) and math.isfinite(hi_s)):
            raise ValueError("improper flat posterior on an unbounded support")
        return float(lo_s), float(hi_s)
    m = linear / precision
    mode = min(max(m, lo_s), hi_s)
    r = math.sqrt((mode - m) ** 2 + 2.0 * log_drop / precision)
    return float(max(lo_s, m - r)), float(min(hi_s, m + r))


@dataclass(frozen=True, eq=False)
class CoefficientPosteriorQuadrature:
    """Discretised posterior over ``a``: nodes, normalised log masses, and the window used."""

    nodes: np.ndarray
    log_masses: np.ndarray
    window: tuple[float, float]
    settings: QuadratureSettings
    log_density: object            # callable a -> unnormalised log posterior (kept for cdf / refinement)
    log_normaliser: float

    @classmethod
    def from_log_density(cls, log_density, window: tuple[float, float],
                         settings: QuadratureSettings) -> "CoefficientPosteriorQuadrature":
        if not window[1] > window[0]:
            # Posterior narrower than float64 resolution: a point mass at the window location.
            node = np.array([window[0]], dtype=FLOAT)
            return cls(node, np.zeros(1), (window[0], window[0]), settings, log_density, float(log_density(node)[0]))
        nodes, gl_w = composite_gauss_legendre(window[0], window[1], settings.panels, settings.nodes_per_panel)
        with np.errstate(divide="ignore"):
            log_w = np.log(gl_w)
        logf = log_density(nodes)
        unnorm = log_w + logf
        log_z = float(special.logsumexp(unnorm))
        if not math.isfinite(log_z):
            raise FloatingPointError("posterior quadrature normaliser is not finite")
        return cls(nodes, unnorm - log_z, window, settings, log_density, log_z)

    @classmethod
    def from_log_density_on_edges(cls, log_density, edges: np.ndarray,
                                  settings: QuadratureSettings) -> "CoefficientPosteriorQuadrature":
        """As :meth:`from_log_density`, with explicit (non-uniform) panel edges spanning the window."""
        nodes, gl_w = gauss_legendre_on_edges(edges, settings.nodes_per_panel)
        with np.errstate(divide="ignore"):
            unnorm = np.log(gl_w) + log_density(nodes)
        log_z = float(special.logsumexp(unnorm))
        if not math.isfinite(log_z):
            raise FloatingPointError("posterior quadrature normaliser is not finite")
        return cls(nodes, unnorm - log_z, (float(edges[0]), float(edges[-1])),
                   replace(settings, panels=int(edges.size - 1)), log_density, log_z)

    @property
    def masses(self) -> np.ndarray:
        return np.exp(self.log_masses)

    def mean(self) -> float:
        return float(self.masses @ self.nodes)

    def variance(self) -> float:
        m = self.mean()
        return float(self.masses @ (self.nodes - m) ** 2)

    def cdf(self, a) -> np.ndarray:
        """P(A <= a | D) by composite Gauss-Legendre on [window_lo, clip(a)] (vectorised)."""
        a_arr = np.atleast_1d(np.asarray(a, dtype=FLOAT))
        lo, hi = self.window
        if not hi > lo:   # point mass at lo
            out = (a_arr >= lo).astype(FLOAT)
            return float(out[0]) if np.ndim(a) == 0 else out
        upper = np.clip(a_arr, lo, hi)
        nodes, w = composite_gauss_legendre(np.full(upper.shape, lo), upper, self.settings.panels,
                                            self.settings.nodes_per_panel)
        with np.errstate(divide="ignore"):
            log_terms = np.log(w) + self.log_density(nodes) - self.log_normaliser
        out = np.where(upper > lo, np.exp(special.logsumexp(log_terms, axis=-1)), 0.0)
        out = np.clip(out, 0.0, 1.0)
        return float(out[0]) if np.ndim(a) == 0 else out

    def sample(self, rng: np.random.Generator, size: int) -> np.ndarray:
        """Inverse-CDF sampling by vectorised bisection (60 halvings: below float64 resolution of the window)."""
        u = rng.uniform(size=size)
        lo = np.full(size, self.window[0])
        hi = np.full(size, self.window[1])
        for _ in range(60):
            mid = 0.5 * (lo + hi)
            below = self.cdf(mid) < u
            lo = np.where(below, mid, lo)
            hi = np.where(below, hi, mid)
        return 0.5 * (lo + hi)


#: Quadrature nodes whose h-step mean or variance overflows float64 are dropped only if their total posterior
#: mass is at most this (a relative change below float64 resolution of a unit mass). Otherwise the predictive
#: is reported as not representable (FloatingPointError), never returned silently as inf/NaN.
MAX_DROPPED_MASS = 1e-15


def integrand_cell_increments(window: tuple[float, float], x_n: float, sigma: float, h: int,
                              n_probe: int = 1025) -> tuple[np.ndarray, np.ndarray]:
    """Probe grid on the window and per-interval 'resolution cell' increments of the h-step integrand
    N(y; mu(a), s(a)^2), with mu(a) = a^h x_n and s(a) = sigma sqrt(c_h(a)):

        dC = |d mu| / s + |d log s|.

    Within one cell the component mean moves by at most about one component sd and the log sd by at
    most about 1, so the integrand is smooth on that scale for every y. Non-finite increments (overflow)
    are returned as +inf. A heuristic, verified by node doubling (check A3).
    """
    lo, hi = window
    a = np.linspace(lo, hi, n_probe)
    with np.errstate(over="ignore", invalid="ignore"):
        mu = np.power(a, h) * x_n
        log_s = np.log(sigma) + 0.5 * np.log(ar1.horizon_variance_factor(a, h))
        s_mid = np.exp(0.5 * (log_s[1:] + log_s[:-1]))
        inc = np.abs(np.diff(mu)) / s_mid + np.abs(np.diff(log_s))
    inc = np.where(np.isfinite(inc), inc, np.inf)
    return a, inc


def resolution_panel_edges(window: tuple[float, float], x_n: float, sigma: float, h: int,
                           settings: QuadratureSettings) -> tuple[np.ndarray, float, bool]:
    """Panel edges at equal quantiles of the resolution density

        g(a) = panels / width  (uniform part: resolves the posterior, as for h = 1)
             + panels_per_cell * dC/da  (integrand part: panels where the integrand is sharp).

    The number of panels is ceil(integral of g), capped at max_panels. Placing edges by quantile
    (rather than uniformly) matters: the cells concentrate where a^h x_n changes fastest (near
    abs(a) = rho for wide posteriors), and uniform panels under-resolved that region (audit finding,
    docs/DECISIONS.md D-08). Returns (edges, total cells, capped).
    """
    a, inc = integrand_cell_increments(window, x_n, sigma, h)
    cells = float(np.sum(inc))
    if not math.isfinite(cells):
        return np.linspace(window[0], window[1], settings.max_panels + 1), math.inf, True
    g = settings.panels / (a.size - 1) + settings.panels_per_cell * inc
    cum = np.concatenate([[0.0], np.cumsum(g)])
    wanted = int(math.ceil(cum[-1]))
    capped = wanted > settings.max_panels
    n_panels = min(max(settings.panels, wanted), settings.max_panels)
    edges = np.interp(np.linspace(0.0, cum[-1], n_panels + 1), cum, a)
    edges[0], edges[-1] = window
    return edges, cells, capped


def horizon_mixture(posterior: CoefficientPosteriorQuadrature, x_n: float, sigma: float, h: int,
                    info: dict | None = None) -> QuadratureMixturePredictive:
    """x_{n+h} | D  ~=  sum_i m_i N(a_i^h x_n, sigma^2 c_h(a_i)) over quadrature nodes a_i.

    The posterior is re-discretised on panel edges placed by :func:`resolution_panel_edges` (more
    panels where the h-step integrand is sharp; a cap hit is recorded in ``info['quadrature']['capped']``).
    """
    settings = posterior.settings
    cells, capped = 0.0, False
    if posterior.window[1] > posterior.window[0]:
        edges, cells, capped = resolution_panel_edges(posterior.window, x_n, sigma, h, settings)
        posterior = CoefficientPosteriorQuadrature.from_log_density_on_edges(posterior.log_density, edges, settings)
    a = posterior.nodes
    log_masses = posterior.log_masses
    with np.errstate(over="ignore", invalid="ignore"):
        means = np.power(a, h) * x_n
        variances = sigma**2 * ar1.horizon_variance_factor(a, h)
    finite = np.isfinite(means) & np.isfinite(variances)
    dropped_mass = float(np.exp(special.logsumexp(log_masses[~finite]))) if (~finite).any() else 0.0
    if dropped_mass > MAX_DROPPED_MASS:
        raise FloatingPointError(
            f"h={h} predictive is not representable in float64: nodes holding posterior mass {dropped_mass:.3e} "
            f"have overflowing mean/variance (window {posterior.window}, x_n={x_n})")
    if dropped_mass > 0.0:
        a, log_masses, means, variances = a[finite], log_masses[finite], means[finite], variances[finite]
    meta = {"quadrature": {"n_nodes": int(a.size), "panels": posterior.settings.panels,
                           "nodes_per_panel": posterior.settings.nodes_per_panel,
                           "window": [float(posterior.window[0]), float(posterior.window[1])],
                           "log_drop": posterior.settings.log_drop, "resolution_cells": cells,
                           "capped": capped, "dropped_overflow_mass": dropped_mass},
            "quadrature_capped": float(capped)}
    meta.update(info or {})
    return QuadratureMixturePredictive(log_masses, means, variances, info=meta)


def gaussian_coefficient_quadrature(mean: float, variance: float,
                                    settings: QuadratureSettings) -> CoefficientPosteriorQuadrature:
    """Quadrature representation of a Gaussian coefficient posterior N(mean, variance)."""
    window = quadratic_window(1.0 / variance, mean / variance, (-math.inf, math.inf), settings.log_drop)

    def log_density(a):
        return -0.5 * (a - mean) ** 2 / variance

    return CoefficientPosteriorQuadrature.from_log_density(log_density, window, settings)


def stable_log_likelihood_terms(x: np.ndarray, sigma: float) -> tuple[float, float]:
    """(S_xx / sigma^2, S_xy / sigma^2): the conditional log-likelihood is -0.5 P a^2 + c a + const."""
    s_xx, s_xy, _, _ = ar1.sufficient_statistics(x)
    return s_xx / sigma**2, s_xy / sigma**2


class StablePriorQuadraturePredictor(Predictor):
    """Continuous-prior Bayes predictor under P-STABLE (any h). NUMERICALLY APPROXIMATED, verified convergence."""

    def __init__(self, prior: StableCoefficientPrior, settings: QuadratureSettings = QuadratureSettings()):
        if not isinstance(prior, StableCoefficientPrior):
            raise TypeError("StablePriorQuadraturePredictor requires a StableCoefficientPrior")
        self.prior = prior
        self.settings = settings
        self.description = PredictorDescription(
            name="continuous_prior_bayes",
            category="continuous-prior-bayes",
            assumed_system_distribution=prior.fingerprint(),
            may_access=("context", "continuous prior P-STABLE", "known sigma"),
            must_not_access=("true a", "future values", "library"),
            uses_true_noise_scale=True,
            assumptions="a ~ P-STABLE prior; sigma known; likelihood conditional on x_0 with x_0 independent of a",
        )

    def with_settings(self, settings: QuadratureSettings) -> "StablePriorQuadraturePredictor":
        return StablePriorQuadraturePredictor(self.prior, settings)

    def posterior(self, context: ContextWindow) -> CoefficientPosteriorQuadrature:
        x = context.values
        sigma = self.prior.sigma
        p_lik, c_lik = stable_log_likelihood_terms(x, sigma)
        p_pri, c_pri = self.prior.gaussian_prior_terms()
        window = quadratic_window(p_lik + p_pri, c_lik + c_pri, self.prior.support, self.settings.log_drop)
        s_xx = p_lik * sigma**2
        a_hat = (c_lik / p_lik) if p_lik > 0 else 0.0
        prior = self.prior

        def log_density(a):
            # prior log density + conditional log-likelihood (completed square; constants dropped)
            loglik = -0.5 * (s_xx / sigma**2) * (a - a_hat) ** 2 if s_xx > 0 else np.zeros_like(a)
            return prior.coefficient_logpdf(a) + loglik

        return CoefficientPosteriorQuadrature.from_log_density(log_density, window, self.settings)

    def _predict(self, context: ContextWindow, horizon: int) -> QuadratureMixturePredictive:
        post = self.posterior(context)
        return horizon_mixture(post, context.last, self.prior.sigma, horizon)
