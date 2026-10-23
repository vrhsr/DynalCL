"""F1 references: scalar AR(1) with unknown noise scale, h = 1 (docs/MATH_F1.md). Batch over contexts.

* sigma^2 is integrated out in closed form (inverse-gamma or log-uniform prior; MATH_F1 section 3);
* a is integrated by composite Gauss-Legendre over its bounded support with a core refinement around a_hat
  (MATH_F1 section 4): NUMERICALLY APPROXIMATED, convergence verified by node doubling and a 2-D grid oracle
  (tests_stage1/test_f1_references.py);
* libraries over (a_k, sigma_k^2) are analytically exact given the atoms (MATH_F1 section 5).

Contexts must have n >= 2 transitions (MATH_F1 section 3: n = 1 under the scale-invariant prior has a spiked posterior).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from scipy import special

FLOAT = np.float64
LOG_2PI = math.log(2.0 * math.pi)
UNIFORM_PANELS = 64
CORE_PANELS = 64
CORE_HALF_WIDTH = 40.0
NODES_PER_PANEL = 8


@dataclass(frozen=True)
class F1Stats:
    """Per-context statistics: n, S_xx, a_hat = S_xy / S_xx, R_min (residual sum at a_hat, from residuals), x_n."""

    n: int
    sxx: np.ndarray
    a_hat: np.ndarray
    r_min: np.ndarray
    last: np.ndarray

    @staticmethod
    def from_contexts(values: np.ndarray) -> "F1Stats":
        v = np.asarray(values, dtype=FLOAT)
        if v.ndim != 2 or v.shape[1] < 3:
            raise ValueError("F1 contexts must be (N, n + 1) with n >= 2")
        prev, curr = v[:, :-1], v[:, 1:]
        sxx = np.einsum("ij,ij->i", prev, prev)
        if np.any(sxx <= 0):
            raise ValueError("S_xx = 0")
        a_hat = np.einsum("ij,ij->i", prev, curr) / sxx
        resid = curr - a_hat[:, None] * prev
        return F1Stats(int(v.shape[1] - 1), sxx, a_hat, np.einsum("ij,ij->i", resid, resid), v[:, -1].copy())

    @property
    def size(self) -> int:
        return int(self.sxx.shape[0])

    def rss(self, a: np.ndarray) -> np.ndarray:
        """R(a) = R_min + S_xx (a - a_hat)^2 for a of shape (N, G)."""
        return self.r_min[:, None] + self.sxx[:, None] * (a - self.a_hat[:, None]) ** 2


# --------------------------------------------------------------------------------------------- sigma^2 priors

LOG_Q_SWITCH = 1e-280
ASYMPTOTIC_TERMS = 12


def log_gammaincc(s: float, u: np.ndarray) -> np.ndarray:
    """log Q(s, u), the regularized upper incomplete gamma. Direct where Q > 1e-280; otherwise the asymptotic series
    Q(s, u) = u^(s-1) e^(-u) / Gamma(s) * sum_k (s-1)(s-2)...(s-k) / u^k (DLMF 8.11.2). Q < 1e-280 needs u > about 640,
    and with s <= 50 the k-th term ratio is below s/u < 0.08, so 12 terms leave a relative error below 1e-13 (DERIVED;
    TESTED against the direct value where both are representable)."""
    u = np.asarray(u, dtype=FLOAT)
    q = special.gammaincc(s, u)
    with np.errstate(divide="ignore", invalid="ignore"):
        direct = np.log(q)
        term = np.ones_like(u)
        total = np.ones_like(u)
        for k in range(1, ASYMPTOTIC_TERMS + 1):
            term = term * (s - k) / u
            total = total + term
        asym = (s - 1.0) * np.log(u) - u - special.gammaln(s) + np.log(total)
    return np.where(q > LOG_Q_SWITCH, direct, asym)


@dataclass(frozen=True)
class InverseGammaScale:
    alpha0: float
    beta0: float

    def log_marginal(self, n: float, r: np.ndarray) -> np.ndarray:
        """log M_n(R) (MATH_F1 section 3), without the (2 pi)^(-n/2) factor."""
        a, b = self.alpha0, self.beta0
        return (a * math.log(b) + special.gammaln(a + n / 2.0) - special.gammaln(a)
                - (a + n / 2.0) * np.log(b + r / 2.0))

    def core_scale(self, st: F1Stats) -> np.ndarray:
        return np.sqrt((2.0 * self.beta0 + st.r_min) / (st.sxx * max(1.0, 2.0 * self.alpha0 + st.n)))


@dataclass(frozen=True)
class LogUniformScale:
    s_lo: float
    s_hi: float

    def __post_init__(self) -> None:
        if not (0 < self.s_lo < self.s_hi):
            raise ValueError("need 0 < s_lo < s_hi")

    def log_marginal(self, n: float, r: np.ndarray) -> np.ndarray:
        """log M_n(R) up to the constant C (cancels in every ratio):
        (R/2)^(-n/2) Gamma(n/2) [P(n/2, u_hi) - P(n/2, u_lo)] with u_hi = R/(2 s_lo^2), u_lo = R/(2 s_hi^2)."""
        s = n / 2.0
        r = np.asarray(r, dtype=FLOAT)
        u_hi = r / (2.0 * self.s_lo**2)          # large
        u_lo = r / (2.0 * self.s_hi**2)          # small
        # P(s, u_hi) - P(s, u_lo) = Q(s, u_lo) - Q(s, u_hi); use whichever subtraction is better conditioned.
        # When R is so large that Q(s, u_lo) underflows (y far in the predictive's tail), work in log space.
        q_lo, q_hi = special.gammaincc(s, u_lo), special.gammaincc(s, u_hi)
        with np.errstate(divide="ignore", invalid="ignore"):
            log_diff = np.log(q_lo) + np.log1p(-(q_hi / q_lo))          # main branch: Q(s, u_lo) - Q(s, u_hi)
        small = q_hi > 0.5                                               # P(s, u_hi) < 0.5: subtract P values instead
        if np.any(small):
            p_hi, p_lo = special.gammainc(s, u_hi[small]), special.gammainc(s, u_lo[small])
            with np.errstate(divide="ignore"):
                log_diff[small] = np.log(np.maximum(p_hi - p_lo, 0.0))
        tiny = (q_lo <= LOG_Q_SWITCH) & ~small                           # Q(s, u_lo) underflows: log space
        if np.any(tiny):
            l_lo, l_hi = log_gammaincc(s, u_lo[tiny]), log_gammaincc(s, u_hi[tiny])
            log_diff[tiny] = l_lo + np.log1p(-np.exp(np.minimum(l_hi - l_lo, 0.0)))
        if not np.all(np.isfinite(log_diff)):
            raise FloatingPointError("log-uniform scale marginal not representable")
        return -s * np.log(r / 2.0) + special.gammaln(s) + log_diff

    def core_scale(self, st: F1Stats) -> np.ndarray:
        return np.sqrt((self.s_lo**2 + st.r_min) / (st.sxx * max(1.0, float(st.n))))


# --------------------------------------------------------------------------------------------- coefficient priors

@dataclass(frozen=True)
class CoefficientPrior:
    """a ~ N(mu0, tau0^2) truncated to (-rho, rho); tau0 None means uniform."""

    rho: float
    mu0: float | None = None
    tau0: float | None = None

    def logpdf(self, a: np.ndarray) -> np.ndarray:
        if self.tau0 is None:
            return np.full(a.shape, -math.log(2.0 * self.rho))
        lo, hi = (-self.rho - self.mu0) / self.tau0, (self.rho - self.mu0) / self.tau0
        log_z = math.log(special.ndtr(hi) - special.ndtr(lo))
        z = (a - self.mu0) / self.tau0
        return -0.5 * z * z - math.log(self.tau0) - 0.5 * LOG_2PI - log_z


# --------------------------------------------------------------------------------------------- the reference

@dataclass(frozen=True)
class UnknownScaleReference:
    """Bayes one-step predictive under a ~ coef, sigma^2 ~ scale (independent), x_0 independent of both."""

    coef: CoefficientPrior
    scale: InverseGammaScale | LogUniformScale
    refine: int = 1                          # multiplies both panel counts (node doubling = 2)

    def nodes(self, st: F1Stats) -> tuple[np.ndarray, np.ndarray]:
        """(N, G) a-nodes and Gauss-Legendre weights: uniform panels over (-rho, rho) merged with core panels."""
        rho = self.coef.rho
        up, cp = UNIFORM_PANELS * self.refine, CORE_PANELS * self.refine
        uni = np.broadcast_to(np.linspace(-rho, rho, up + 1), (st.size, up + 1))
        half = CORE_HALF_WIDTH * self.scale.core_scale(st)
        lo = np.clip(st.a_hat - half, -rho, rho)
        hi = np.clip(st.a_hat + half, -rho, rho)
        core = lo[:, None] + (hi - lo)[:, None] * (np.arange(cp + 1) / cp)[None, :]
        edges = np.sort(np.concatenate([uni, core], axis=1), axis=1)
        x, w = np.polynomial.legendre.leggauss(NODES_PER_PANEL)
        a0, a1 = edges[:, :-1], edges[:, 1:]
        h, mid = 0.5 * (a1 - a0), 0.5 * (a1 + a0)
        nodes = (mid[:, :, None] + h[:, :, None] * x).reshape(st.size, -1)
        weights = (h[:, :, None] * w).reshape(st.size, -1)
        return nodes, weights

    def posterior(self, st: F1Stats) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """(nodes, log normalised node masses, R at nodes). Zero-width panels get zero weight (log -inf)."""
        a, w = self.nodes(st)
        r = st.rss(a)
        with np.errstate(divide="ignore"):
            lw = np.log(w) + self.coef.logpdf(a) + self.scale.log_marginal(st.n, r)
        lw = lw - special.logsumexp(lw, axis=1, keepdims=True)
        return a, lw, r

    def logpdf(self, st: F1Stats, y: np.ndarray, max_elements: int = 4_000_000) -> np.ndarray:
        """log p(y | context); y of shape (N,) or (N, Gy)."""
        y = np.asarray(y, dtype=FLOAT)
        squeeze = y.ndim == 1
        yy = y[:, None] if squeeze else y
        a, lw, r = self.posterior(st)
        out = np.empty(yy.shape, dtype=FLOAT)
        lm_n = self.scale.log_marginal(st.n, r)                      # (N, G)
        chunk = max(1, max_elements // (yy.shape[1] * a.shape[1]))
        for i0 in range(0, st.size, chunk):
            i1 = min(st.size, i0 + chunk)
            resid = yy[i0:i1, :, None] - a[i0:i1, None, :] * st.last[i0:i1, None, None]
            r_new = r[i0:i1, None, :] + resid**2
            lm_n1 = self.scale.log_marginal(st.n + 1, r_new)
            comp = lw[i0:i1, None, :] + lm_n1 - lm_n[i0:i1, None, :] - 0.5 * LOG_2PI
            out[i0:i1] = special.logsumexp(comp, axis=2)
        return out[:, 0] if squeeze else out


def student_t_mixture_cdf(ref: "UnknownScaleReference", st: F1Stats, y: np.ndarray) -> np.ndarray:
    """CDF of the one-step predictive for an inverse-gamma scale prior: given a, y is Student-t with 2 alpha_n dof,
    location a x_n and scale^2 beta_n(a) / alpha_n (MATH_F1 section 4), so the CDF is the node-weighted
    sum of t CDFs."""
    if not isinstance(ref.scale, InverseGammaScale):
        raise TypeError("closed-form CDF only for the inverse-gamma scale prior")
    a, lw, r = ref.posterior(st)
    alpha_n = ref.scale.alpha0 + st.n / 2.0
    scale = np.sqrt((ref.scale.beta0 + r / 2.0) / alpha_n)
    z = (np.asarray(y, dtype=FLOAT)[:, None] - a * st.last[:, None]) / scale
    return (np.exp(lw) * special.stdtr(2.0 * alpha_n, z)).sum(axis=1)


@dataclass(frozen=True)
class ScaleLibrary:
    """K atoms (a_k, sigma_k), uniform weights; exact posterior and mixture predictive (MATH_F1 section 5)."""

    a: np.ndarray
    sigma: np.ndarray

    def __post_init__(self) -> None:
        a, s = np.asarray(self.a, dtype=FLOAT), np.asarray(self.sigma, dtype=FLOAT)
        if a.shape != s.shape or a.ndim != 1 or np.any(s <= 0):
            raise ValueError("atoms must be 1-D, equal length, sigma > 0")
        object.__setattr__(self, "a", a)
        object.__setattr__(self, "sigma", s)

    def posterior_log_weights(self, st: F1Stats) -> np.ndarray:
        r = st.rss(np.broadcast_to(self.a, (st.size, self.a.size)))
        lw = -st.n * np.log(self.sigma)[None, :] - r / (2.0 * self.sigma[None, :] ** 2)
        return lw - special.logsumexp(lw, axis=1, keepdims=True)

    def logpdf(self, st: F1Stats, y: np.ndarray, max_elements: int = 4_000_000) -> np.ndarray:
        y = np.asarray(y, dtype=FLOAT)
        squeeze = y.ndim == 1
        yy = y[:, None] if squeeze else y
        lw = self.posterior_log_weights(st)
        out = np.empty(yy.shape, dtype=FLOAT)
        chunk = max(1, max_elements // (yy.shape[1] * self.a.size))
        for i0 in range(0, st.size, chunk):
            i1 = min(st.size, i0 + chunk)
            z = (yy[i0:i1, :, None] - self.a[None, None, :] * st.last[i0:i1, None, None]) / self.sigma[None, None, :]
            comp = lw[i0:i1, None, :] - 0.5 * z * z - np.log(self.sigma)[None, None, :] - 0.5 * LOG_2PI
            out[i0:i1] = special.logsumexp(comp, axis=2)
        return out[:, 0] if squeeze else out


def population_f1() -> UnknownScaleReference:
    """P_F1: a ~ TN(0.4, 0.3^2; +/-0.95), sigma^2 ~ IG(3, 2) (MATH_F1 section 1)."""
    return UnknownScaleReference(CoefficientPrior(0.95, 0.4, 0.3), InverseGammaScale(3.0, 2.0))


def context_only_f1() -> UnknownScaleReference:
    """C_F1: a ~ U(-0.999, 0.999), log sigma ~ U(log 0.01, log 100)."""
    return UnknownScaleReference(CoefficientPrior(0.999), LogUniformScale(0.01, 100.0))
