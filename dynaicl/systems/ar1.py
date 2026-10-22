"""Scalar AR(1) data-generating process: x_t = a x_{t-1} + sigma eps_t, eps_t ~ N(0, 1) iid.

All likelihoods in this project are conditional on x_0 (docs/MATH.md section 1). Index conventions
live in exactly one place, :func:`transition_pairs`, which every predictor goes through. That gives
the off-by-one mutation test (Section 5.G) a single place to inject the bug.
"""

from __future__ import annotations

import numpy as np

FLOAT = np.float64


def transition_pairs(x: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Return (regressors, targets) = (x_0..x_{n-1}, x_1..x_n) for a context x_0..x_n."""
    return x[:-1], x[1:]


def sufficient_statistics(x: np.ndarray) -> tuple[float, float, float, int]:
    """(S_xx, S_xy, S_yy, n) with S_xx = sum_{t=1..n} x_{t-1}^2, S_xy = sum x_{t-1} x_t, S_yy = sum x_t^2."""
    prev, curr = transition_pairs(x)
    n = int(curr.shape[0])
    return float(prev @ prev), float(prev @ curr), float(curr @ curr), n


def residual_sum_of_squares(x: np.ndarray, a: np.ndarray | float) -> np.ndarray:
    """RSS(a) = sum_t (x_t - a x_{t-1})^2, computed from residuals directly (no cancellation).

    ``a`` may be an array of candidate coefficients; the result has the same shape.
    """
    prev, curr = transition_pairs(x)
    a_arr = np.asarray(a, dtype=FLOAT)
    resid = curr[None, :] - a_arr.reshape(-1, 1) * prev[None, :]
    return np.einsum("ij,ij->i", resid, resid).reshape(a_arr.shape)


def horizon_variance_factor(a: np.ndarray | float, h: int) -> np.ndarray:
    """c_h(a) = sum_{j=0}^{h-1} a^{2j}, by Horner's rule (the sum form, stable at abs(a) = 1).

    Given a, the h-step state is x_{n+h} | x_n ~ N(a^h x_n, sigma^2 c_h(a)) (docs/MATH.md section 1.4).
    """
    if h < 1:
        raise ValueError("horizon must be >= 1")
    a2 = np.square(np.asarray(a, dtype=FLOAT))
    c = np.ones_like(a2)
    with np.errstate(over="ignore"):   # overflow -> +inf; callers turn that into an explicit error
        for _ in range(h - 1):
            c = 1.0 + a2 * c
    return c


def require_representable(mean, variance, what: str) -> None:
    """Raise FloatingPointError if an h-step predictive moment overflowed float64 (never return inf/NaN)."""
    if not (np.all(np.isfinite(mean)) and np.all(np.isfinite(variance))):
        raise FloatingPointError(f"{what}: h-step predictive is not representable in float64 "
                                 f"(mean/variance overflow)")


def simulate_ar1(
    a: np.ndarray,
    sigma: np.ndarray,
    x0: np.ndarray,
    eps: np.ndarray,
) -> np.ndarray:
    """Simulate trajectories x_0..x_T for N systems.

    a, sigma, x0: shape (N,); eps: shape (N, T) of standard normals. Returns shape (N, T + 1).
    Raises if any value is non-finite (explosive draws over long horizons can overflow).
    """
    a = np.asarray(a, dtype=FLOAT)
    sigma = np.asarray(sigma, dtype=FLOAT)
    x0 = np.asarray(x0, dtype=FLOAT)
    eps = np.asarray(eps, dtype=FLOAT)
    if eps.ndim != 2 or eps.shape[0] != a.shape[0]:
        raise ValueError("eps must have shape (N, T)")
    n_sys, horizon = eps.shape
    x = np.empty((n_sys, horizon + 1), dtype=FLOAT)
    x[:, 0] = x0
    with np.errstate(over="ignore", invalid="ignore"):  # overflow is detected explicitly below
        for t in range(1, horizon + 1):
            x[:, t] = a * x[:, t - 1] + sigma * eps[:, t - 1]
    if not np.all(np.isfinite(x)):
        bad = np.where(~np.all(np.isfinite(x), axis=1))[0]
        raise FloatingPointError(
            f"non-finite trajectory values for systems {bad[:5].tolist()} "
            f"(a={a[bad[:5]].tolist()}); explosive draw over too long a horizon"
        )
    return x
