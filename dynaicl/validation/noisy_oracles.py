"""Independent oracles for Stage 0.6 (test/design use only). Nothing here calls the Kalman filter or the Gauss-Legendre
node set, except ``kalman_score_finite_difference``, which is a deliberately *different* route for Fisher information.

* Joint-Gaussian covariance of (y_0..y_n, targets) built from first principles, with Cholesky conditioning given a.
* Integration over a by scipy.integrate.quad (adaptive Gauss-Kronrod), with breakpoints at the prior-support edges.
* Monte Carlo: a drawn from the prior, importance weights from the Cholesky likelihood, and y_{n+h} drawn from the exact
  conditional Gaussian.
* Finite-n Fisher information for a: I_n(a) = 0.5 tr(S^-1 S' S^-1 S') with an analytic S', cross-checked by a
  finite-difference S' and by the Monte Carlo variance of the score.
"""

from __future__ import annotations

import math

import numpy as np
from scipy import integrate, special, stats

FLOAT = np.float64


def latent_variances(a: float, t_max: int, sigma_w: float, x0_sd: float) -> np.ndarray:
    """V_t = Var(x_t) = a^{2t} x0_sd^2 + sigma_w^2 sum_{j<t} a^{2j}, by forward recursion V_t = a^2 V_{t-1} + sigma_w^2."""
    v = np.empty(t_max + 1)
    v[0] = x0_sd ** 2
    for t in range(1, t_max + 1):
        v[t] = a * a * v[t - 1] + sigma_w ** 2
    return v


def latent_variance_derivatives(a: float, t_max: int, sigma_w: float, x0_sd: float) -> np.ndarray:
    """dV_t/da = 2t a^{2t-1} x0_sd^2 + sigma_w^2 sum_{j=1}^{t-1} 2j a^{2j-1} (explicit sum; independent of the recursion)."""
    d = np.zeros(t_max + 1)
    for t in range(1, t_max + 1):
        d[t] = 2 * t * a ** (2 * t - 1) * x0_sd ** 2 + sigma_w ** 2 * sum(2 * j * a ** (2 * j - 1) for j in range(1, t))
    return d


def joint_covariance(a: float, times: list[int], sigma_w: float, sigma_v: float, x0_sd: float,
                     observed: bool = True) -> np.ndarray:
    """Cov of (z_t for t in times), z = y (observed=True) or x. Cov(x_i, x_j) = a^{|i-j|} V_{min(i,j)}."""
    V = latent_variances(a, max(times), sigma_w, x0_sd)
    T = np.array(times)
    C = np.power(a, np.abs(T[:, None] - T[None, :])) * V[np.minimum(T[:, None], T[None, :])]
    if observed:
        C = C + sigma_v ** 2 * np.eye(len(times))
    return C


def joint_covariance_derivative(a: float, n: int, sigma_w: float, x0_sd: float) -> np.ndarray:
    """dCov(y_{0:n})/da (the observation noise does not depend on a)."""
    V = latent_variances(a, n, sigma_w, x0_sd)
    dV = latent_variance_derivatives(a, n, sigma_w, x0_sd)
    T = np.arange(n + 1)
    lag = np.abs(T[:, None] - T[None, :])
    mn = np.minimum(T[:, None], T[None, :])
    with np.errstate(divide="ignore", invalid="ignore"):
        term1 = np.where(lag > 0, lag * np.power(a, np.maximum(lag - 1, 0)) * V[mn], 0.0)
    return term1 + np.power(a, lag) * dV[mn]


def cholesky_loglik(y: np.ndarray, a: float, sigma_w: float, sigma_v: float, x0_sd: float) -> float:
    n = len(y) - 1
    C = joint_covariance(a, list(range(n + 1)), sigma_w, sigma_v, x0_sd)
    L = np.linalg.cholesky(C)
    z = np.linalg.solve(L, y)
    return float(-0.5 * (n + 1) * math.log(2 * math.pi) - np.log(np.diag(L)).sum() - 0.5 * z @ z)


def cholesky_predictive(y: np.ndarray, a: float, h: int, sigma_w: float, sigma_v: float, x0_sd: float,
                        target_observed: bool = True) -> tuple[float, float, float]:
    """(loglik of y_{0:n}, conditional mean, conditional variance) of y_{n+h} (or x_{n+h}) given y_{0:n} and a."""
    n = len(y) - 1
    times = list(range(n + 1)) + [n + h]
    C = joint_covariance(a, times, sigma_w, sigma_v, x0_sd, observed=True)
    if not target_observed:
        C[-1, -1] -= sigma_v ** 2          # latent target: no measurement noise on the target
    Cyy, c, ctt = C[:-1, :-1], C[-1, :-1], C[-1, -1]
    L = np.linalg.cholesky(Cyy)
    z = np.linalg.solve(L, y)
    w = np.linalg.solve(L.T, np.linalg.solve(L, c))
    ll = float(-0.5 * (n + 1) * math.log(2 * math.pi) - np.log(np.diag(L)).sum() - 0.5 * z @ z)
    return ll, float(w @ y), float(ctt - c @ w)


def adaptive_reference(y: np.ndarray, h: int, prior, sigma_w: float, sigma_v: float, x0_sd: float,
                       y_eval: np.ndarray) -> dict:
    """Posterior mean/var of a and the predictive logpdf/cdf of y_{n+h} at y_eval, integrating over a with
    scipy.integrate.quad and the Cholesky likelihood. Also returns quad's error estimates."""
    lo, hi = prior.support
    grid = np.linspace(lo, hi, 401)[1:-1]
    shift = max(cholesky_loglik(y, a, sigma_w, sigma_v, x0_sd) + float(prior.coefficient_logpdf(np.array(a)))
                for a in grid)

    def post(a):
        return math.exp(cholesky_loglik(y, a, sigma_w, sigma_v, x0_sd) + float(prior.coefficient_logpdf(np.array(a))) - shift)

    kw = dict(limit=400, epsabs=1e-13, epsrel=1e-11)
    Z, eZ = integrate.quad(post, lo, hi, **kw)
    M1, _ = integrate.quad(lambda a: a * post(a), lo, hi, **kw)
    mean = M1 / Z
    M2, _ = integrate.quad(lambda a: (a - mean) ** 2 * post(a), lo, hi, **kw)
    out = {"post_mean": mean, "post_var": M2 / Z, "Z_abserr_rel": eZ / Z, "logpdf": [], "cdf": [], "abserr_rel": []}
    for yv in np.atleast_1d(y_eval):
        def dens(a, yv=yv):
            _, mu, v = cholesky_predictive(y, a, h, sigma_w, sigma_v, x0_sd)
            return post(a) * math.exp(-0.5 * (yv - mu) ** 2 / v) / math.sqrt(2 * math.pi * v)

        def cdf(a, yv=yv):
            _, mu, v = cholesky_predictive(y, a, h, sigma_w, sigma_v, x0_sd)
            return post(a) * special.ndtr((yv - mu) / math.sqrt(v))

        D, eD = integrate.quad(dens, lo, hi, **kw)
        F, _ = integrate.quad(cdf, lo, hi, **kw)
        out["logpdf"].append(math.log(D / Z))
        out["cdf"].append(F / Z)
        out["abserr_rel"].append(eD / D + eZ / Z)
    return out


def monte_carlo_predictive(y: np.ndarray, h: int, prior_sampler, sigma_w: float, sigma_v: float, x0_sd: float,
                           n_draws: int, rng: np.random.Generator) -> tuple[np.ndarray, np.ndarray]:
    """Samples of y_{n+h} and normalised importance weights: a ~ prior, w ∝ Cholesky likelihood, then y_{n+h} ~ exact
    conditional Gaussian given (y_{0:n}, a)."""
    a, _ = prior_sampler(rng, n_draws)
    ll = np.empty(n_draws)
    mu = np.empty(n_draws)
    var = np.empty(n_draws)
    for i, ai in enumerate(a):
        ll[i], mu[i], var[i] = cholesky_predictive(y, float(ai), h, sigma_w, sigma_v, x0_sd)
    w = np.exp(ll - special.logsumexp(ll))
    return mu + np.sqrt(var) * rng.standard_normal(n_draws), w


# ------------------------------------------------------------------------------------- Fisher information


def fisher_information_exact(a: float, n: int, sigma_w: float, sigma_v: float, x0_sd: float,
                             derivative: str = "analytic") -> float:
    """I_n(a) for y_{0:n} ~ N(0, S(a)): 0.5 tr(S^-1 S' S^-1 S'). ``derivative`` = "analytic" or "finite-difference"."""
    S = joint_covariance(a, list(range(n + 1)), sigma_w, sigma_v, x0_sd)
    if derivative == "analytic":
        dS = joint_covariance_derivative(a, n, sigma_w, x0_sd)
    else:
        eps = 1e-6
        dS = (joint_covariance(a + eps, list(range(n + 1)), sigma_w, sigma_v, x0_sd)
              - joint_covariance(a - eps, list(range(n + 1)), sigma_w, sigma_v, x0_sd)) / (2 * eps)
    A = np.linalg.solve(S, dS)
    return float(0.5 * np.trace(A @ A))


def fisher_information_zero_noise_closed_form(a: float, n: int, sigma_w: float, x0_sd: float) -> float:
    """At sigma_v = 0: I_n(a) = sum_{t=0}^{n-1} V_t / sigma_w^2. The x_0 factor does not depend on a, and each transition
    contributes E[x_{t-1}^2]/sigma_w^2 (DERIVED; an exact analytic anchor for the finite-n computation)."""
    V = latent_variances(a, n, sigma_w, x0_sd)
    return float(V[:n].sum() / sigma_w ** 2)


def kalman_score_finite_difference(y: np.ndarray, a: float, sigma_w: float, sigma_v: float, x0_sd: float,
                                   eps: float = 1e-5) -> float:
    """d/da log p(y | a) by central differences of a scalar Kalman log-likelihood (written separately here)."""
    def ll(av):
        m, P, tot = 0.0, x0_sd ** 2, 0.0
        for t, yt in enumerate(y):
            if t > 0:
                m, P = av * m, av * av * P + sigma_w ** 2
            S = P + sigma_v ** 2
            e = yt - m
            tot += -0.5 * math.log(2 * math.pi * S) - 0.5 * e * e / S
            m, P = m + (P / S) * e, P * sigma_v ** 2 / S
        return tot
    return (ll(a + eps) - ll(a - eps)) / (2 * eps)


def fisher_information_monte_carlo(a: float, n: int, sigma_w: float, sigma_v: float, x0_sd: float,
                                   n_draws: int, rng: np.random.Generator) -> tuple[float, float]:
    """(estimate, SE) of I_n(a) = E[score^2] by simulating y_{0:n} at a and finite-differencing the Kalman log-likelihood."""
    s = np.empty(n_draws)
    for i in range(n_draws):
        x = np.empty(n + 1)
        x[0] = x0_sd * rng.standard_normal()
        for t in range(1, n + 1):
            x[t] = a * x[t - 1] + sigma_w * rng.standard_normal()
        y = x + sigma_v * rng.standard_normal(n + 1)
        s[i] = kalman_score_finite_difference(y, a, sigma_w, sigma_v, x0_sd)
    sq = s * s
    return float(sq.mean()), float(sq.std(ddof=1) / math.sqrt(n_draws))


def truncnorm_prior_nodes(mu0: float, tau0: float, rho: float, k: int = 80) -> tuple[np.ndarray, np.ndarray]:
    """Gauss-Legendre nodes on (-rho, rho) and normalised prior weights for averaging over the population prior."""
    x, w = np.polynomial.legendre.leggauss(k)
    a = rho * x
    d = stats.truncnorm((-rho - mu0) / tau0, (rho - mu0) / tau0, loc=mu0, scale=tau0).pdf(a)
    wt = rho * w * d
    return a, wt / wt.sum()
