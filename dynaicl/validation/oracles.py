"""Independent test oracles. They never import the reference implementations' formulas.

* :class:`BruteForceGridPosterior`: posterior over ``a`` on a uniform grid from the RAW likelihood.
  An explicit loop over x[t], x[t-1] with scipy.stats.norm.logpdf, a prior log density supplied by
  the caller (the checks pass :func:`scipy_prior_logpdf`, which is independent of the reference's
  ``coefficient_logpdf``), and the trapezoid rule. No sufficient statistics, no conjugacy, no
  ``transition_pairs``.
* :class:`BruteForceNigGrid`: 2-D grid over (a, log sigma^2) for P-NIG.
* Truncated-normal closed forms for P-STABLE (posterior via scipy.stats.truncnorm; the h = 1
  predictive density in closed form, MATH.md section 4.3).
* Importance sampling from the prior with raw-likelihood weights, followed by forward simulation.

NUMERICALLY APPROXIMATED (grids, Monte Carlo). Used only in tests.
"""

from __future__ import annotations

import math

import numpy as np
from scipy import special, stats

FLOAT = np.float64


def scipy_prior_logpdf(prior):
    """Prior log density of ``a`` built from scipy.stats, independent of ``prior.coefficient_logpdf``."""
    fam = prior.family
    if fam == "P-GAUSS":
        dist = stats.norm(loc=prior.mu0, scale=prior.tau0)
    elif fam == "P-STABLE" and prior.shape == "uniform":
        dist = stats.uniform(loc=-prior.rho, scale=2 * prior.rho)
    elif fam == "P-STABLE":
        dist = stats.truncnorm((-prior.rho - prior.mu0) / prior.tau0, (prior.rho - prior.mu0) / prior.tau0,
                               loc=prior.mu0, scale=prior.tau0)
    else:
        raise ValueError(f"no scipy prior for {fam}")
    return dist.logpdf


def raw_log_likelihood(a_values: np.ndarray, x: np.ndarray, sigma) -> np.ndarray:
    """sum_{t=1..n} log N(x[t]; a x[t-1], sigma^2), explicit loop over t. ``sigma`` may broadcast with a_values."""
    a_values = np.asarray(a_values, dtype=FLOAT)
    total = np.zeros(np.broadcast(a_values, np.asarray(sigma)).shape, dtype=FLOAT)
    for t in range(1, len(x)):
        total = total + stats.norm.logpdf(x[t], loc=a_values * x[t - 1], scale=sigma)
    return total


def trapezoid_log_weights(grid: np.ndarray) -> np.ndarray:
    d = np.diff(grid)
    w = np.zeros_like(grid)
    w[:-1] += 0.5 * d
    w[1:] += 0.5 * d
    return np.log(w)


def forward_moments(a: np.ndarray, x_n: float, sigma, h: int) -> tuple[np.ndarray, np.ndarray]:
    """Mean and variance of x_{n+h} | a by explicit recursion (independent of the Horner sum)."""
    m = np.full(np.shape(a), x_n, dtype=FLOAT)
    v = np.zeros(np.shape(a), dtype=FLOAT)
    for _ in range(h):
        m = a * m
        v = a * a * v + np.square(sigma)
    return m, v


class BruteForceGridPosterior:
    """Posterior over ``a`` on a grid (known sigma) from the raw likelihood and an explicit prior log density."""

    def __init__(self, prior_logpdf, grid: np.ndarray, x: np.ndarray, sigma: float):
        self.grid = np.asarray(grid, dtype=FLOAT)
        self.x = np.asarray(x, dtype=FLOAT)
        self.sigma = float(sigma)
        logpost = prior_logpdf(self.grid) + raw_log_likelihood(self.grid, self.x, self.sigma)
        lw = trapezoid_log_weights(self.grid) + logpost
        self.log_masses = lw - special.logsumexp(lw)
        self.masses = np.exp(self.log_masses)

    def mean(self) -> float:
        return float(self.masses @ self.grid)

    def variance(self) -> float:
        m = self.mean()
        return float(self.masses @ (self.grid - m) ** 2)

    def predictive_logpdf(self, y: np.ndarray, h: int) -> np.ndarray:
        mh, vh = forward_moments(self.grid, self.x[-1], self.sigma, h)
        y = np.atleast_1d(np.asarray(y, dtype=FLOAT))
        comp = self.log_masses[None, :] + stats.norm.logpdf(y[:, None], loc=mh[None, :], scale=np.sqrt(vh)[None, :])
        return special.logsumexp(comp, axis=1)

    def predictive_cdf(self, y: np.ndarray, h: int) -> np.ndarray:
        mh, vh = forward_moments(self.grid, self.x[-1], self.sigma, h)
        y = np.atleast_1d(np.asarray(y, dtype=FLOAT))
        return stats.norm.cdf(y[:, None], loc=mh[None, :], scale=np.sqrt(vh)[None, :]) @ self.masses


class BruteForceNigGrid:
    """2-D trapezoid grid over (a, u = log sigma^2) for P-NIG, with the raw likelihood and a scipy.stats prior."""

    def __init__(self, mu0, lambda0, alpha0, beta0, a_grid: np.ndarray, u_grid: np.ndarray, x: np.ndarray):
        self.a = np.asarray(a_grid, dtype=FLOAT)
        self.u = np.asarray(u_grid, dtype=FLOAT)
        self.x = np.asarray(x, dtype=FLOAT)
        A, U = np.meshgrid(self.a, self.u, indexing="ij")
        S2 = np.exp(U)
        log_prior = (stats.invgamma.logpdf(S2, alpha0, scale=beta0) + U  # Jacobian d sigma^2 / du = sigma^2
                     + stats.norm.logpdf(A, loc=mu0, scale=np.sqrt(S2 / lambda0)))
        logpost = log_prior + raw_log_likelihood(A, self.x, np.sqrt(S2))
        lw = trapezoid_log_weights(self.a)[:, None] + trapezoid_log_weights(self.u)[None, :] + logpost
        self.log_masses = lw - special.logsumexp(lw)
        self.masses = np.exp(self.log_masses)
        self.A, self.S2 = A, S2

    def coefficient_mean(self) -> float:
        return float(np.sum(self.masses * self.A))

    def coefficient_variance(self) -> float:
        m = self.coefficient_mean()
        return float(np.sum(self.masses * (self.A - m) ** 2))

    def noise_variance_mean(self) -> float:
        return float(np.sum(self.masses * self.S2))

    def predictive_logpdf(self, y: np.ndarray) -> np.ndarray:
        x_n = self.x[-1]
        y = np.atleast_1d(np.asarray(y, dtype=FLOAT))
        out = []
        for yi in y:
            comp = self.log_masses + stats.norm.logpdf(yi, loc=self.A * x_n, scale=np.sqrt(self.S2))
            out.append(special.logsumexp(comp))
        return np.array(out)


# --------------------------------------------------------------------------- P-STABLE closed-form oracle


def _raw_quadratic(x: np.ndarray, sigma: float) -> tuple[float, float]:
    """(sum x[t-1]^2 / sigma^2, sum x[t-1] x[t] / sigma^2) by an explicit loop (independent of ar1.py)."""
    p = 0.0
    c = 0.0
    for t in range(1, len(x)):
        p += x[t - 1] * x[t - 1]
        c += x[t - 1] * x[t]
    return p / sigma**2, c / sigma**2


def stable_posterior_parameters(prior, x: np.ndarray) -> tuple[float, float]:
    """(m, s) of the untruncated Gaussian factor of the P-STABLE posterior; s = inf for a flat posterior."""
    p, c = _raw_quadratic(x, prior.sigma)
    if prior.shape == "truncated_normal":
        p += 1.0 / prior.tau0**2
        c += prior.mu0 / prior.tau0**2
    if p == 0.0:
        return 0.0, math.inf
    return c / p, math.sqrt(1.0 / p)


def stable_posterior_truncnorm(prior, x: np.ndarray):
    """scipy.stats frozen truncated normal (or uniform) posterior of a under P-STABLE."""
    m, s = stable_posterior_parameters(prior, x)
    if not math.isfinite(s):
        return stats.uniform(loc=-prior.rho, scale=2 * prior.rho)
    return stats.truncnorm((-prior.rho - m) / s, (prior.rho - m) / s, loc=m, scale=s)


def _log_ndtr_diff(lo: np.ndarray, hi: np.ndarray) -> np.ndarray:
    """log(Phi(hi) - Phi(lo)) for hi > lo, using the tail that avoids cancellation."""
    lo = np.asarray(lo, dtype=FLOAT)
    hi = np.asarray(hi, dtype=FLOAT)
    upper = lo > 0
    a = np.where(upper, -hi, lo)
    b = np.where(upper, -lo, hi)
    la, lb = special.log_ndtr(a), special.log_ndtr(b)
    return lb + np.log1p(-np.exp(la - lb))


def stable_h1_predictive_logpdf(prior, x: np.ndarray, y: np.ndarray) -> np.ndarray:
    """Closed-form log p(x_{n+1} = y | D) under P-STABLE (MATH.md section 4.3)."""
    y = np.atleast_1d(np.asarray(y, dtype=FLOAT))
    sigma, rho, x_n = prior.sigma, prior.rho, float(x[-1])
    m, s = stable_posterior_parameters(prior, x)
    if not math.isfinite(s):
        if x_n == 0.0:
            return stats.norm.logpdf(y, 0.0, sigma)
        c = abs(x_n)
        sgn_y = y * np.sign(x_n)
        return _log_ndtr_diff((sgn_y - rho * c) / sigma, (sgn_y + rho * c) / sigma) - math.log(2 * rho * c)
    base = stats.norm.logpdf(y, loc=m * x_n, scale=math.sqrt(sigma**2 + s**2 * x_n**2))
    s2p = 1.0 / (1.0 / s**2 + x_n**2 / sigma**2)
    mp = s2p * (m / s**2 + y * x_n / sigma**2)
    sp = math.sqrt(s2p)
    num = _log_ndtr_diff((-rho - mp) / sp, (rho - mp) / sp)
    den = _log_ndtr_diff(np.array((-rho - m) / s), np.array((rho - m) / s))
    return base + num - den


# --------------------------------------------------------------------------- importance-sampling oracle


def importance_sample_predictive(prior_sampler, x: np.ndarray, h: int, n_draws: int,
                                 rng: np.random.Generator) -> tuple[np.ndarray, np.ndarray]:
    """Draw (a, sigma) from the prior, weight by the raw likelihood, simulate x_{n+h} forward with fresh noise.

    Returns (samples of x_{n+h}, normalised importance weights). No conjugacy formulas are used.
    """
    a, sig = prior_sampler(rng, n_draws)
    logw = raw_log_likelihood(a, x, sig)
    w = np.exp(logw - special.logsumexp(logw))
    state = np.full(n_draws, x[-1], dtype=FLOAT)
    for _ in range(h):
        state = a * state + sig * rng.standard_normal(n_draws)
    return state, w


def weighted_quantile(values: np.ndarray, weights: np.ndarray, p: float) -> float:
    order = np.argsort(values)
    cw = np.cumsum(weights[order])
    return float(values[order][np.searchsorted(cw, p * cw[-1])])
