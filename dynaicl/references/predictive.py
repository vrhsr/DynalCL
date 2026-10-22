"""Predictive distributions (Section 2.6).

Every probabilistic predictor returns a :class:`Predictive` exposing mean, variance, logpdf, cdf,
quantile and sample. Point-only predictors return a :class:`PointForecast`. Scoring functions refuse
to compute log score or CRPS on a PointForecast.

Implementation note: these use scipy.special and numpy directly rather than scipy.stats frozen
distributions, which cost about 50 us per call and dominate experiment run time.
"""

from __future__ import annotations

import math
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

import numpy as np
from scipy import optimize, special

FLOAT = np.float64
_LOG_2PI = math.log(2.0 * math.pi)


def _as_float_array(y) -> np.ndarray:
    return np.asarray(y, dtype=FLOAT)


def _maybe_scalar(arr: np.ndarray, like) -> np.ndarray | float:
    return float(arr) if np.ndim(like) == 0 else arr


class Predictive(ABC):
    """Predictive distribution of a scalar target."""

    kind: str = "abstract"

    def __init__(self, info: dict | None = None):
        self.info = dict(info or {})

    @abstractmethod
    def mean(self) -> float: ...

    @abstractmethod
    def variance(self) -> float: ...

    @abstractmethod
    def logpdf(self, y): ...

    @abstractmethod
    def cdf(self, y): ...

    @abstractmethod
    def quantile(self, p): ...

    @abstractmethod
    def sample(self, rng: np.random.Generator, size: int) -> np.ndarray: ...


class GaussianPredictive(Predictive):
    kind = "gaussian"

    def __init__(self, mean: float, variance: float, info: dict | None = None):
        super().__init__(info)
        if not (math.isfinite(mean) and math.isfinite(variance) and variance > 0):
            raise ValueError(f"Gaussian predictive needs finite mean and variance > 0, got {mean}, {variance}")
        self._mean = float(mean)
        self._var = float(variance)
        self._sd = math.sqrt(self._var)

    def mean(self) -> float:
        return self._mean

    def variance(self) -> float:
        return self._var

    def logpdf(self, y):
        y_arr = _as_float_array(y)
        z = (y_arr - self._mean) / self._sd
        return _maybe_scalar(-0.5 * _LOG_2PI - math.log(self._sd) - 0.5 * z * z, y)

    def cdf(self, y):
        y_arr = _as_float_array(y)
        return _maybe_scalar(special.ndtr((y_arr - self._mean) / self._sd), y)

    def quantile(self, p):
        p_arr = _as_float_array(p)
        return _maybe_scalar(self._mean + self._sd * special.ndtri(p_arr), p)

    def sample(self, rng, size):
        return self._mean + self._sd * rng.standard_normal(size)


class StudentTPredictive(Predictive):
    """Location-scale Student-t: y = loc + sqrt(scale2) * T_dof."""

    kind = "student_t"

    def __init__(self, loc: float, scale2: float, dof: float, info: dict | None = None):
        super().__init__(info)
        if not (math.isfinite(loc) and math.isfinite(scale2) and scale2 > 0 and math.isfinite(dof) and dof > 0):
            raise ValueError(f"invalid Student-t parameters loc={loc}, scale2={scale2}, dof={dof}")
        self.loc = float(loc)
        self.scale2 = float(scale2)
        self.scale = math.sqrt(self.scale2)
        self.dof = float(dof)
        self._log_norm = (special.gammaln(0.5 * (self.dof + 1.0)) - special.gammaln(0.5 * self.dof)
                          - 0.5 * math.log(self.dof * math.pi) - math.log(self.scale))

    def mean(self) -> float:
        if self.dof <= 1.0:
            raise ValueError("Student-t mean is undefined for dof <= 1")
        return self.loc

    def variance(self) -> float:
        """scale2 * dof / (dof - 2); mathematically infinite for 1 < dof <= 2 (returned as inf)."""
        if self.dof <= 1.0:
            raise ValueError("Student-t variance is undefined for dof <= 1")
        if self.dof <= 2.0:
            return math.inf
        return self.scale2 * self.dof / (self.dof - 2.0)

    def logpdf(self, y):
        z = (_as_float_array(y) - self.loc) / self.scale
        return _maybe_scalar(self._log_norm - 0.5 * (self.dof + 1.0) * np.log1p(z * z / self.dof), y)

    def cdf(self, y):
        z = (_as_float_array(y) - self.loc) / self.scale
        return _maybe_scalar(special.stdtr(self.dof, z), y)

    def quantile(self, p):
        return _maybe_scalar(self.loc + self.scale * special.stdtrit(self.dof, _as_float_array(p)), p)

    def sample(self, rng, size):
        return self.loc + self.scale * rng.standard_t(self.dof, size)


class GaussianMixturePredictive(Predictive):
    """sum_k w_k N(mu_k, v_k), weights supplied as (possibly unnormalised) log weights."""

    kind = "gaussian_mixture"

    def __init__(self, log_weights: np.ndarray, means: np.ndarray, variances: np.ndarray,
                 info: dict | None = None):
        super().__init__(info)
        lw = _as_float_array(log_weights).ravel()
        mu = _as_float_array(means).ravel()
        var = _as_float_array(variances).ravel()
        if not (lw.shape == mu.shape == var.shape and lw.size >= 1):
            raise ValueError("mixture arrays must have equal length >= 1")
        if not (np.all(np.isfinite(mu)) and np.all(np.isfinite(var)) and np.all(var > 0)):
            raise ValueError("mixture components need finite means and finite positive variances")
        if np.any(np.isnan(lw)) or np.any(lw == np.inf) or not np.any(np.isfinite(lw)):
            raise ValueError("mixture log weights must be < inf with at least one finite entry")
        self.log_weights = lw - special.logsumexp(lw)
        self.weights = np.exp(self.log_weights)
        self.means = mu
        self.variances = var
        self.sds = np.sqrt(var)
        self._log_sds = np.log(self.sds)

    @property
    def n_components(self) -> int:
        return int(self.means.size)

    def mean(self) -> float:
        return float(self.weights @ self.means)

    def variance(self) -> float:
        m = self.mean()
        return float(self.weights @ (self.variances + (self.means - m) ** 2))

    def logpdf(self, y):
        y_arr = np.atleast_1d(_as_float_array(y))
        z = (y_arr[:, None] - self.means[None, :]) / self.sds[None, :]
        comp = self.log_weights[None, :] - 0.5 * _LOG_2PI - self._log_sds[None, :] - 0.5 * z * z
        out = special.logsumexp(comp, axis=1)
        return float(out[0]) if np.ndim(y) == 0 else out.reshape(np.shape(y))

    def cdf(self, y):
        y_arr = np.atleast_1d(_as_float_array(y))
        z = (y_arr[:, None] - self.means[None, :]) / self.sds[None, :]
        out = np.clip(special.ndtr(z) @ self.weights, 0.0, 1.0)
        return float(out[0]) if np.ndim(y) == 0 else out.reshape(np.shape(y))

    def quantile(self, p):
        """Root of F(x) = p, bracketed by the extreme component quantiles (exact bracket, see MATH.md)."""
        p_arr = np.atleast_1d(_as_float_array(p))
        out = np.empty_like(p_arr)
        live = self.weights > 0
        for i, pi in enumerate(p_arr):
            if not (0.0 < pi < 1.0):
                raise ValueError("quantile level must be in (0, 1)")
            comp_q = self.means[live] + self.sds[live] * special.ndtri(pi)
            lo, hi = float(comp_q.min()), float(comp_q.max())
            f_lo, f_hi = self.cdf(lo) - pi, self.cdf(hi) - pi
            # Mathematically F(lo) <= p <= F(hi). If rounding puts an endpoint on the wrong side, that
            # endpoint is the root to within rounding.
            if f_lo >= 0.0:
                out[i] = lo
            elif f_hi <= 0.0:
                out[i] = hi
            else:
                out[i] = optimize.brentq(lambda t: self.cdf(t) - pi, lo, hi, xtol=1e-14,
                                         rtol=4 * np.finfo(FLOAT).eps, maxiter=500)
        return float(out[0]) if np.ndim(p) == 0 else out.reshape(np.shape(p))

    def sample(self, rng, size):
        k = rng.choice(self.n_components, size=size, p=self.weights)
        return self.means[k] + self.sds[k] * rng.standard_normal(size)


class QuadratureMixturePredictive(GaussianMixturePredictive):
    """Gaussian mixture whose weights are quadrature masses over a 1-D coefficient posterior.

    NUMERICALLY APPROXIMATED: the continuous mixture over ``a`` is replaced by a finite node
    set. ``info['quadrature']`` records the node count and window.
    """

    kind = "quadrature_mixture"


class EmpiricalPredictive(GaussianMixturePredictive):
    """Sample-based predictive smoothed by a Gaussian kernel (an equal-weight mixture).

    The bandwidth defaults to Silverman's rule 1.06 * sd * N^(-1/5). This is an approximation,
    intended for future sample-based models. No Stage 0 reference uses it.
    """

    kind = "empirical"

    def __init__(self, samples: np.ndarray, bandwidth: float | None = None, info: dict | None = None):
        s = _as_float_array(samples).ravel()
        if s.size < 2 or not np.all(np.isfinite(s)):
            raise ValueError("need at least two finite samples")
        if bandwidth is None:
            sd = float(np.std(s, ddof=1))
            bandwidth = 1.06 * (sd if sd > 0 else 1.0) * s.size ** (-0.2)
        super().__init__(np.zeros(s.size), s, np.full(s.size, bandwidth**2), info)
        self.bandwidth = float(bandwidth)


@dataclass(frozen=True)
class PointForecast:
    """Point-only forecast. Scored only with point metrics, never with log score or CRPS."""

    point: float
    info: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not math.isfinite(self.point):
            raise ValueError("point forecast must be finite")
