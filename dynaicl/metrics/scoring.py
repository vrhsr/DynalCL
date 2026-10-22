"""Scoring rules (Section 4; docs/MATH.md section 8).

* Log predictive density: primary, strictly proper.
* CRPS: closed form for the Gaussian. Numerical integration of (F - 1{. >= y})^2 for everything
  else, validated against the Gaussian closed form. A closed form for Gaussian mixtures is also
  provided and used as an independent cross-check.
* PIT and central-interval coverage (coverage is derived from the PIT).
* Point metrics (squared error) are the only metrics allowed for a PointForecast.
* Paired differences on identical items, with analytic SE = sd / sqrt(N).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from scipy import integrate, special

from dynaicl.references.predictive import GaussianMixturePredictive, GaussianPredictive, PointForecast, Predictive

FLOAT = np.float64
_INV_SQRT_PI = 1.0 / math.sqrt(math.pi)


def _require_probabilistic(pred) -> None:
    if isinstance(pred, PointForecast):
        raise TypeError("log score / CRPS / PIT are not defined for point forecasts; use point metrics")
    if not isinstance(pred, Predictive):
        raise TypeError(f"expected a Predictive, got {type(pred).__name__}")


def log_score(pred: Predictive, y: float) -> float:
    _require_probabilistic(pred)
    return float(pred.logpdf(float(y)))


def pit(pred: Predictive, y: float) -> float:
    _require_probabilistic(pred)
    return float(pred.cdf(float(y)))


def covered_from_pit(u: np.ndarray, level: float) -> np.ndarray:
    """y lies in the central ``level`` interval [q((1-level)/2), q((1+level)/2)] iff |F(y) - 1/2| <= level/2."""
    if not 0.0 < level < 1.0:
        raise ValueError("coverage level must be in (0, 1)")
    return np.abs(np.asarray(u, dtype=FLOAT) - 0.5) <= 0.5 * level


def crps_gaussian(mean: float, sd: float, y: float) -> float:
    """sd * [z (2 Phi(z) - 1) + 2 phi(z) - 1/sqrt(pi)], z = (y - mean)/sd. ANALYTICALLY EXACT."""
    z = (y - mean) / sd
    phi = math.exp(-0.5 * z * z) / math.sqrt(2.0 * math.pi)
    return float(sd * (z * (2.0 * special.ndtr(z) - 1.0) + 2.0 * phi - _INV_SQRT_PI))


def _abs_normal_mean(m: np.ndarray, v: np.ndarray) -> np.ndarray:
    """E|Z| for Z ~ N(m, v): 2 sqrt(v) phi(m/sqrt(v)) + m (2 Phi(m/sqrt(v)) - 1)."""
    s = np.sqrt(v)
    z = m / s
    return 2.0 * s * np.exp(-0.5 * z * z) / math.sqrt(2.0 * math.pi) + m * (2.0 * special.ndtr(z) - 1.0)


def crps_gaussian_mixture(pred: GaussianMixturePredictive, y: float) -> float:
    """CRPS = E|X - y| - 0.5 E|X - X'| for a Gaussian mixture, in closed form. O(K^2): use for cross-checks."""
    w, mu, v = pred.weights, pred.means, pred.variances
    term1 = float(w @ _abs_normal_mean(mu - y, v))
    term2 = float(w @ _abs_normal_mean(mu[:, None] - mu[None, :], v[:, None] + v[None, :]) @ w)
    return term1 - 0.5 * term2


def crps_numerical(pred: Predictive, y: float, epsabs: float = 1e-12, epsrel: float = 1e-10) -> float:
    """CRPS = int (F(z) - 1{z >= y})^2 dz by adaptive quadrature, split at y and at central quantiles."""
    _require_probabilistic(pred)
    y = float(y)
    cdf = pred.cdf
    pts = sorted({y, float(pred.quantile(1e-6)), float(pred.quantile(0.5)), float(pred.quantile(1.0 - 1e-6))})

    def below(z):
        return cdf(z) ** 2

    def above(z):
        return (1.0 - cdf(z)) ** 2

    kw = dict(epsabs=epsabs, epsrel=epsrel, limit=400)
    total = integrate.quad(below if pts[0] <= y else above, -np.inf, pts[0], **kw)[0]
    for lo, hi in zip(pts[:-1], pts[1:]):
        total += integrate.quad(below if hi <= y else above, lo, hi, **kw)[0]
    total += integrate.quad(above if pts[-1] >= y else below, pts[-1], np.inf, **kw)[0]
    return float(total)


def crps(pred: Predictive, y: float) -> float:
    """Closed form for Gaussians, numerical otherwise."""
    _require_probabilistic(pred)
    if isinstance(pred, GaussianPredictive):
        return crps_gaussian(pred.mean(), math.sqrt(pred.variance()), y)
    return crps_numerical(pred, y)


def squared_error(pred: Predictive | PointForecast, y: float) -> float:
    point = pred.point if isinstance(pred, PointForecast) else pred.mean()
    return float((point - y) ** 2)


@dataclass(frozen=True)
class PairedDifference:
    """mean of d_i = score_A,i - score_B,i over identical items; se = sd(d) / sqrt(N) (analytic, iid items)."""

    mean: float
    se: float
    sd: float
    n: int

    @property
    def z(self) -> float:
        return self.mean / self.se if self.se > 0 else (math.inf if self.mean > 0 else -math.inf if self.mean < 0 else 0.0)


def paired_difference(scores_a: np.ndarray, scores_b: np.ndarray) -> PairedDifference:
    a = np.asarray(scores_a, dtype=FLOAT)
    b = np.asarray(scores_b, dtype=FLOAT)
    if a.shape != b.shape or a.ndim != 1 or a.size < 2:
        raise ValueError("paired scores must be 1-D arrays of equal length >= 2")
    d = a - b
    sd = float(np.std(d, ddof=1))
    return PairedDifference(float(d.mean()), sd / math.sqrt(d.size), sd, int(d.size))
