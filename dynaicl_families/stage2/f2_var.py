"""F2 references: bivariate VAR(1) with a stability-truncated matrix-normal-inverse-Wishart prior (docs/MATH_F2.md).

* conjugate posterior and the untruncated one-step predictive (multivariate Student-t): ANALYTICALLY EXACT (MATH_F2 3-4);
* the truncated one-step predictive: Monte Carlo over B from the untruncated posterior with Sigma integrated given B
  (Rao-Blackwellised Student-t), ratio estimator R or complement control variate C (MATH_F2 section 5); NUMERICALLY
  APPROXIMATED, per-item delta-method SE of the log density reported and driven below a target;
* libraries over (A_k, Sigma_k): ANALYTICALLY EXACT given the atoms (MATH_F2 section 7).

Conventions: Y = X B + E with B = A^T (MATH_F2 section 1); arrays are float64; contexts are (N, n + 1, d) and are cut per
coordinate by the frozen ``harness.make_context``; the likelihood is conditional on x_0; randomness from NamedStreams.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np
from scipy import special

from dynaicl.evaluation import harness
from dynaicl.rng import NamedStreams

FLOAT = np.float64
D = 2
LOG_PI = math.log(math.pi)


# ------------------------------------------------------------------------------------------------ priors

@dataclass(frozen=True)
class MNIWPrior:
    """Sigma ~ IW(nu0, Psi0); vec(B) | Sigma ~ N(vec(B0), Sigma kron V0); truncated to rho(B) < c (c = inf: none)."""

    name: str
    b0: np.ndarray
    v0: np.ndarray
    nu0: float
    psi0: np.ndarray
    c: float

    def __post_init__(self) -> None:
        d = np.asarray(self.b0).shape[0]
        for k in ("b0", "v0", "psi0"):
            a = np.asarray(getattr(self, k), dtype=FLOAT)
            if a.shape != (d, d):
                raise ValueError(f"{k} must be d x d")
            object.__setattr__(self, k, a)
        if not self.nu0 > d - 1:
            raise ValueError("IW needs nu0 > d - 1")

    @property
    def d(self) -> int:
        return int(self.b0.shape[0])

    def params(self) -> dict:
        return {"name": self.name, "b0": self.b0.tolist(), "v0": self.v0.tolist(), "nu0": self.nu0,
                "psi0": self.psi0.tolist(), "c": self.c}


def population_f2() -> MNIWPrior:
    """P_F2 (MATH_F2 section 2): B0 = 0.4 I, V0 = 0.09 I, nu0 = 7, Psi0 = 4 I, truncated at rho < 0.95."""
    return MNIWPrior("P_F2", 0.4 * np.eye(D), 0.09 * np.eye(D), 7.0, 4.0 * np.eye(D), 0.95)


def context_only_f2() -> MNIWPrior:
    """C_F2 (MATH_F2 section 2): B0 = 0, V0 = 100 I, nu0 = 1.5, Psi0 = 0.01 I, truncated at rho < 0.999."""
    return MNIWPrior("C_F2", np.zeros((D, D)), 100.0 * np.eye(D), 1.5, 0.01 * np.eye(D), 0.999)


# ------------------------------------------------------------------------------------------------ 2 x 2 linear algebra

def det2(m: np.ndarray) -> np.ndarray:
    """Determinants (batch); closed form for 2 x 2, numpy otherwise."""
    if m.shape[-1] == 2:
        return m[..., 0, 0] * m[..., 1, 1] - m[..., 0, 1] * m[..., 1, 0]
    return np.linalg.det(m)


def inv2(m: np.ndarray) -> np.ndarray:
    """Inverses (batch); closed form for 2 x 2, numpy otherwise."""
    if m.shape[-1] != 2:
        return np.linalg.inv(m)
    d = det2(m)
    out = np.empty_like(m)
    out[..., 0, 0], out[..., 1, 1] = m[..., 1, 1] / d, m[..., 0, 0] / d
    out[..., 0, 1], out[..., 1, 0] = -m[..., 0, 1] / d, -m[..., 1, 0] / d
    return out


def chol2(m: np.ndarray) -> np.ndarray:
    """Lower Cholesky factors of symmetric positive-definite matrices (batch); closed form for 2 x 2."""
    if m.shape[-1] != 2:
        return np.linalg.cholesky(m)
    l11 = np.sqrt(m[..., 0, 0])
    l21 = m[..., 1, 0] / l11
    l22 = np.sqrt(m[..., 1, 1] - l21 * l21)
    out = np.zeros_like(m)
    out[..., 0, 0], out[..., 1, 0], out[..., 1, 1] = l11, l21, l22
    return out


def spectral_radius(a: np.ndarray) -> np.ndarray:
    """rho of real square matrices (batch). For 2 x 2 in closed form (MATH_F2 section 8): with tau = trace and
    delta = det, if tau^2/4 - delta < 0 the eigenvalues are complex conjugates with modulus sqrt(delta); otherwise
    rho = |tau|/2 + sqrt(disc). For d = 1, |a|; otherwise numpy eigenvalues."""
    if a.shape[-1] == 1:
        return np.abs(a[..., 0, 0])
    if a.shape[-1] != 2:
        return np.max(np.abs(np.linalg.eigvals(a)), axis=-1)
    tau = a[..., 0, 0] + a[..., 1, 1]
    delta = det2(a)
    disc = 0.25 * tau * tau - delta
    return np.where(disc < 0, np.sqrt(np.abs(delta)), 0.5 * np.abs(tau) + np.sqrt(np.maximum(disc, 0.0)))


def _quad_form(diff: np.ndarray, minv: np.ndarray) -> np.ndarray:
    """diff^T minv diff with full broadcasting of the leading axes of both arguments."""
    lead = np.broadcast_shapes(diff.shape[:-1], minv.shape[:-2])
    d = diff.shape[-1]
    return np.einsum("...i,...ij,...j->...", np.broadcast_to(diff, lead + (d,)), np.broadcast_to(minv, lead + (d, d)),
                     np.broadcast_to(diff, lead + (d,)))


def mvt_logpdf(y: np.ndarray, loc: np.ndarray, scale: np.ndarray, dof) -> np.ndarray:
    """Log density of the d-variate Student-t with location ``loc``, scale matrix ``scale`` and ``dof`` degrees of freedom;
    arguments broadcast over leading axes (y, loc: (..., d); scale: (..., d, d))."""
    d = y.shape[-1]
    diff = y - loc
    quad = _quad_form(diff, inv2(scale))
    nu = np.asarray(dof, dtype=FLOAT)
    return (special.gammaln((nu + d) / 2.0) - special.gammaln(nu / 2.0) - 0.5 * d * (np.log(nu) + LOG_PI)
            - 0.5 * np.log(det2(scale)) - 0.5 * (nu + d) * np.log1p(quad / nu))


def mvn_logpdf(y: np.ndarray, loc: np.ndarray, cov: np.ndarray) -> np.ndarray:
    d = y.shape[-1]
    diff = y - loc
    quad = _quad_form(diff, inv2(cov))
    return -d / 2.0 * math.log(2 * math.pi) - 0.5 * np.log(det2(cov)) - 0.5 * quad


# ------------------------------------------------------------------------------------------------ posterior

@dataclass(frozen=True)
class F2Posterior:
    """Untruncated MNIW posterior per context (MATH_F2 section 3); arrays have a leading item axis N."""

    n: int
    bn: np.ndarray        # (N, d, d)
    vn: np.ndarray        # (N, d, d)
    nun: float
    psin: np.ndarray      # (N, d, d)
    last: np.ndarray      # (N, d) = x_n
    vn_inv: np.ndarray = field(repr=False, default=None)

    @property
    def size(self) -> int:
        return int(self.bn.shape[0])

    def item(self, i: int) -> "F2Posterior":
        return F2Posterior(self.n, self.bn[i:i + 1], self.vn[i:i + 1], self.nun, self.psin[i:i + 1],
                           self.last[i:i + 1], self.vn_inv[i:i + 1])


def regression_arrays(ctx: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """X = [x_0 .. x_{n-1}]^T and Y = [x_1 .. x_n]^T for contexts (N, n + 1, d)."""
    c = np.asarray(ctx, dtype=FLOAT)
    if c.ndim != 3 or c.shape[1] < 2:
        raise ValueError("F2 contexts must be (N, n + 1, d) with n >= 1")
    return c[:, :-1, :], c[:, 1:, :]


def posterior(prior: MNIWPrior, ctx: np.ndarray) -> F2Posterior:
    x, y = regression_arrays(ctx)
    v0_inv = inv2(prior.v0)
    sxx = np.einsum("nti,ntj->nij", x, x)
    sxy = np.einsum("nti,ntj->nij", x, y)
    vn_inv = v0_inv[None] + sxx
    vn = inv2(vn_inv)
    bn = vn @ (v0_inv @ prior.b0 + sxy)
    resid = y - x @ bn
    db = bn - prior.b0
    psin = prior.psi0 + np.einsum("nti,ntj->nij", resid, resid) + np.swapaxes(db, 1, 2) @ v0_inv @ db
    psin = 0.5 * (psin + np.swapaxes(psin, 1, 2))
    return F2Posterior(int(x.shape[1]), bn, vn, prior.nu0 + x.shape[1], psin, np.asarray(ctx, dtype=FLOAT)[:, -1, :],
                       vn_inv)


def untruncated_logpdf(post: F2Posterior, y: np.ndarray) -> np.ndarray:
    """log p_U(y | D), y of shape (N, G, d): t_{nu_n - d + 1}(B_n^T x_n, Psi_n (1 + x_n^T V_n x_n) / (nu_n - d + 1))."""
    dof = post.nun - post.last.shape[1] + 1
    loc = np.einsum("nij,ni->nj", post.bn, post.last)
    q = np.einsum("ni,nij,nj->n", post.last, post.vn, post.last)
    scale = post.psin * ((1.0 + q) / dof)[:, None, None]
    return mvt_logpdf(y, loc[:, None, :], scale[:, None], dof)


# ------------------------------------------------------------------------------------------------ sampling

def sample_iw(nu: float, psi: np.ndarray, size: int, rng: np.random.Generator) -> np.ndarray:
    """Sigma ~ IW(nu, psi) via the Bartlett decomposition of Sigma^{-1} ~ Wishart(nu, psi^{-1}): lower-triangular A with
    A_ii = sqrt(chi2(nu - i)) (i = 0..d-1) and standard normal entries below the diagonal; valid for real nu > d - 1."""
    d = psi.shape[-1]
    l = chol2(inv2(psi))
    a = np.zeros((size, d, d))
    for i in range(d):
        a[:, i, i] = np.sqrt(rng.chisquare(nu - i, size))
        for j in range(i):
            a[:, i, j] = rng.standard_normal(size)
    la = l @ a
    return inv2(la @ np.swapaxes(la, 1, 2))


def sample_mniw(b: np.ndarray, v: np.ndarray, nu: float, psi: np.ndarray, size: int,
                rng: np.random.Generator) -> tuple[np.ndarray, np.ndarray]:
    """(B, Sigma) ~ MNIW(b, v, nu, psi): Sigma ~ IW(nu, psi), B = b + chol(v) Z chol(Sigma)^T, Z iid N(0, 1) (d x d)."""
    sig = sample_iw(nu, psi, size, rng)
    z = rng.standard_normal((size,) + b.shape[-2:])
    return b + chol2(v) @ z @ np.swapaxes(chol2(sig), 1, 2), sig


def sample_truncated_prior(prior: MNIWPrior, size: int, rng: np.random.Generator,
                           max_rounds: int = 1000) -> tuple[np.ndarray, np.ndarray, float]:
    """Exact draws from the truncated prior by rejection; returns (B, Sigma, acceptance fraction)."""
    bs, ss, tried, kept = [], [], 0, 0
    for _ in range(max_rounds):
        b, s = sample_mniw(prior.b0, prior.v0, prior.nu0, prior.psi0, max(64, 2 * (size - kept)), rng)
        ok = spectral_radius(b) < prior.c
        tried += b.shape[0]
        kept += int(ok.sum())
        bs.append(b[ok])
        ss.append(s[ok])
        if kept >= size:
            return np.concatenate(bs)[:size], np.concatenate(ss)[:size], kept / tried
    raise RuntimeError("truncated prior acceptance too low")


# ------------------------------------------------------------------------------------------------ truncated predictive

def rb_logpdf(post_i: F2Posterior, b: np.ndarray, y: np.ndarray) -> np.ndarray:
    """log p(y | B, D) with Sigma integrated (MATH_F2 section 4): t_{nu_n + 1}(B^T x_n, Psi_B / (nu_n + 1)),
    Psi_B = Psi_n + (B - B_n)^T V_n^{-1} (B - B_n). post_i holds one item; b (J, d, d); y (G, d) -> (J, G)."""
    db = b - post_i.bn[0]
    psi_b = post_i.psin[0] + np.swapaxes(db, 1, 2) @ post_i.vn_inv[0] @ db
    loc = np.einsum("jik,i->jk", b, post_i.last[0])
    dof = post_i.nun + 1.0
    return mvt_logpdf(y[None, :, :], loc[:, None, :], (psi_b / dof)[:, None], dof)


@dataclass(frozen=True)
class TruncatedEstimate:
    logpdf: np.ndarray        # (G,)
    se_log: np.ndarray        # (G,) delta-method SE of the log density
    draws: int
    accepted: int
    estimator: str            # "C" (complement control variate) or "R" (ratio)
    capped: bool


def truncated_logpdf_item(prior: MNIWPrior, post_i: F2Posterior, y: np.ndarray, rng: np.random.Generator,
                          target_se: float = 2e-4, batch: int = 8192, min_accepted: int = 1000,
                          max_draws: int = 2 ** 22, force: str | None = None) -> TruncatedEstimate:
    """Truncated one-step predictive log density at the G points y (G, d) for one context (MATH_F2 section 5).

    Densities are scaled by the closed-form untruncated predictive p_U(y) before summing (both estimators are linear in
    f / p_U), which keeps every running sum O(1). Draws are added in batches until max_g SE(log p) <= target_se with at
    least ``min_accepted`` accepted draws, or ``max_draws`` is reached (then ``capped``). Estimator choice (two-phase):
    a separate pilot batch, then discarded, estimates the rejected fraction q; C if q <= 0.5, else R. Because the pilot
    draws are not reused, the choice adds no selection bias. ``force`` = "C" or "R" overrides the rule (tests only).
    A non-positive or non-finite running estimate never counts as converged (C can go negative at moderate q)."""
    y = np.asarray(y, dtype=FLOAT)
    log_pu = untruncated_logpdf(post_i, y[None])[0]                       # (G,)
    if not math.isfinite(prior.c):
        return TruncatedEstimate(log_pu, np.zeros_like(log_pu), 0, 0, "exact", False)
    if force is None:
        pilot, _ = sample_mniw(post_i.bn[0], post_i.vn[0], post_i.nun, post_i.psin[0], batch, rng)
        force = "C" if float(np.mean(spectral_radius(pilot) >= prior.c)) <= 0.5 else "R"
    n_all = n_acc = 0
    s_f = np.zeros_like(log_pu); s_f2 = np.zeros_like(log_pu)            # sums over accepted draws (R)
    u_f = np.zeros_like(log_pu); u_f2 = np.zeros_like(log_pu)            # sums over rejected draws (C)
    while True:
        b, _ = sample_mniw(post_i.bn[0], post_i.vn[0], post_i.nun, post_i.psin[0], batch, rng)
        ok = spectral_radius(b) < prior.c
        f = np.exp(rb_logpdf(post_i, b, y) - log_pu[None, :])            # (J, G) = f / p_U
        n_all += batch
        n_acc += int(ok.sum())
        s_f += f[ok].sum(axis=0); s_f2 += (f[ok] ** 2).sum(axis=0)
        u_f += f[~ok].sum(axis=0); u_f2 += (f[~ok] ** 2).sum(axis=0)
        q = 1.0 - n_acc / n_all
        if force == "C":
            m_u, m_uf, m_uf2 = q, u_f / n_all, u_f2 / n_all
            p = (1.0 - m_uf) / (1.0 - m_u)
            e1 = m_uf - p * m_u
            var = np.maximum(m_uf2 - 2 * p * m_uf + p * p * m_u - e1 * e1, 0.0)
            se = np.sqrt(var / (n_all * (1.0 - m_u) ** 2)) / p
            est = "C"
        else:
            p = s_f / max(n_acc, 1)
            var = np.maximum(s_f2 / max(n_acc, 1) - p * p, 0.0)
            se = np.sqrt(var / max(n_acc, 1)) / np.where(p > 0, p, np.nan)
            est = "R"
        done = (n_acc >= min_accepted and bool(np.all(p > 0)) and bool(np.all(np.isfinite(se)))
                and float(np.max(se)) <= target_se)
        if done or n_all >= max_draws:
            with np.errstate(divide="ignore"):
                return TruncatedEstimate(log_pu + np.log(p), se, n_all, n_acc, est, not done)


# ------------------------------------------------------------------------------------------------ interval Rao-Blackwell

def stable_interval_b11(b12: np.ndarray, b21: np.ndarray, b22: np.ndarray, c: float) -> tuple[np.ndarray, np.ndarray]:
    """(L, U) such that, with the other three entries fixed, rho(B) < c iff L < b11 < U (MATH_F2 section 5b).
    Jury conditions for a real 2 x 2 matrix: both eigenvalues have modulus < c iff |det| < c^2 and |tr| < c + det / c;
    each is linear in b11 (det = b22 b11 - b12 b21, tr = b11 + b22), so the stable set is an intersection of half-lines,
    an interval (empty when L >= U)."""
    beta = b12 * b21
    alphas = (b22, -b22, 1.0 - b22 / c, -1.0 - b22 / c)
    gammas = (c * c + beta, c * c - beta, c - b22 - beta / c, c + b22 - beta / c)
    lo = np.full(np.shape(b22), -np.inf)
    hi = np.full(np.shape(b22), np.inf)
    for al, ga in zip(alphas, gammas):
        al = np.broadcast_to(al, lo.shape)
        ga = np.broadcast_to(ga, lo.shape)
        with np.errstate(divide="ignore", invalid="ignore"):
            bound = ga / al
        hi = np.where(al > 0, np.minimum(hi, bound), hi)
        lo = np.where(al < 0, np.maximum(lo, bound), lo)
        dead = (al == 0) & (ga <= 0)
        hi = np.where(dead, -np.inf, hi)
    return lo, hi


INTERVAL_NODES = 64           # tan-substitution Gauss-Legendre; d = 1 oracle: 16 nodes 5e-7, 32 nodes 1e-14 (S30)


def _b11_conditional_t(post_i: F2Posterior, b: np.ndarray) -> tuple[np.ndarray, np.ndarray, float]:
    """Conditional of e = b11 - B_n[0, 0] given the other entries under the matrix-t marginal posterior of B (Sigma
    integrated; MATH_F2 section 5b): p(B | D) is proportional to |Psi_n + D^T W D|^{-(nu_n + d)/2} with D = B - B_n,
    W = V_n^{-1}; the determinant is a quadratic alpha e^2 + beta e + gamma in e, so e | rest is Student-t with
    nu' = nu_n + d - 1, location -beta / (2 alpha) and scale^2 (gamma - beta^2 / (4 alpha)) / (alpha nu').
    Returns (location of b11, scale, nu') per draw. d in {1, 2}."""
    d = post_i.last.shape[1]
    w = post_i.vn_inv[0]
    psi = post_i.psin[0]
    nu_c = post_i.nun + d - 1.0
    if d == 1:
        loc = np.full(b.shape[0], post_i.bn[0, 0, 0])
        scale = np.full(b.shape[0], math.sqrt(psi[0, 0] / (w[0, 0] * nu_c)))
        return loc, scale, nu_c
    dd = b - post_i.bn[0]
    d10, d01, d11 = dd[:, 1, 0], dd[:, 0, 1], dd[:, 1, 1]
    a11 = psi[1, 1] + w[0, 0] * d01 ** 2 + 2 * w[0, 1] * d01 * d11 + w[1, 1] * d11 ** 2
    u = w[0, 0] * d01 + w[0, 1] * d11
    v = psi[0, 1] + d10 * (w[1, 0] * d01 + w[1, 1] * d11)
    alpha = a11 * w[0, 0] - u * u
    beta = 2.0 * (a11 * w[0, 1] * d10 - u * v)
    gamma = a11 * (psi[0, 0] + w[1, 1] * d10 ** 2) - v * v
    loc_e = -beta / (2.0 * alpha)
    scale = np.sqrt((gamma - beta * beta / (4.0 * alpha)) / (alpha * nu_c))
    return post_i.bn[0, 0, 0] + loc_e, scale, nu_c


def _segment_terms(post_i: F2Posterior, b: np.ndarray, y: np.ndarray, lo: np.ndarray, hi: np.ndarray,
                   nodes: int) -> tuple[np.ndarray, np.ndarray]:
    """For each draw j and the b11 segment (lo_j, hi_j) (infinite ends allowed): the conditional mass
    P(b11 in segment | rest) (Student-t CDF) and the integral over the segment of p(y | B, D) p(b11 | rest) d b11
    (MATH_F2 section 5b). Quadrature: b11 = qm + qs tan(theta), centred on the product of p(b11 | rest) and a Gaussian
    approximation of the y-likelihood in b11; ``nodes``-point Gauss-Legendre in theta; the integrand is bounded and decays
    like cos(theta)^nu' at the ends (NUMERICALLY APPROXIMATED; node doubling and the d = 1 nested-quad oracle in
    tests_stage2). History (disclosure S30): Gauss-Legendre in the conditional CDF variable converged only algebraically."""
    d = post_i.last.shape[1]
    loc, scale, nu_c = _b11_conditional_t(post_i, b)
    hi = np.maximum(hi, lo)
    sgn = np.where(lo - loc > 0, -1.0, 1.0)                  # CDF of the side that does not cancel near 1
    z1, z2 = sgn * (lo - loc) / scale, sgn * (hi - loc) / scale
    with np.errstate(invalid="ignore"):
        mass = np.maximum(special.stdtr(nu_c, np.maximum(z1, z2)) - special.stdtr(nu_c, np.minimum(z1, z2)), 0.0)
    x = post_i.last[0]
    bl = b.copy()
    bl[:, 0, 0] = loc
    db = bl - post_i.bn[0]
    sc = (post_i.psin[0] + np.swapaxes(db, 1, 2) @ post_i.vn_inv[0] @ db) / (post_i.nun + 1.0)      # (J, d, d)
    if d == 1:
        r = np.broadcast_to(y[None, :, 0], (b.shape[0], y.shape[0]))
        sy2 = sc[:, 0, 0][:, None]
    else:
        k = sc[:, 0, 1] / sc[:, 1, 1]
        mean1 = b[:, 0, 1] * x[0] + b[:, 1, 1] * x[1]
        r = y[None, :, 0] - (b[:, 1, 0] * x[1])[:, None] - k[:, None] * (y[None, :, 1] - mean1[:, None])
        sy2 = (sc[:, 0, 0] - k * sc[:, 0, 1])[:, None]
    x0 = x[0]
    prec = 1.0 / scale[:, None] ** 2 + x0 * x0 / sy2                                           # (J, G)
    qs = 1.0 / np.sqrt(prec)
    qm = (loc[:, None] / scale[:, None] ** 2 + x0 * r / sy2) / prec
    with np.errstate(invalid="ignore"):
        th_lo = np.arctan((lo[:, None] - qm) / qs)
        th_hi = np.arctan((hi[:, None] - qm) / qs)
    xg, wg = np.polynomial.legendre.leggauss(nodes)
    half, mid = 0.5 * (th_hi - th_lo), 0.5 * (th_hi + th_lo)                                   # (J, G)
    tn = np.tan(mid[..., None] + half[..., None] * xg)                                         # (J, G, K)
    b11 = qm[..., None] + qs[..., None] * tn
    nj, ng = b.shape[0], y.shape[0]
    bk = np.repeat(b[:, None, :, :], ng * nodes, axis=1).reshape(-1, d, d)
    bk[:, 0, 0] = b11.reshape(-1)
    lf = np.einsum("jgkg->jgk", rb_logpdf(post_i, bk, y).reshape(nj, ng, nodes, ng))            # f(y_g | B_jgk)
    lt = special.gammaln((nu_c + 1) / 2) - special.gammaln(nu_c / 2) - 0.5 * math.log(nu_c * math.pi)
    lp = lt - np.log(scale)[:, None, None] - (nu_c + 1) / 2 * np.log1p(((b11 - loc[:, None, None])
                                                                         / scale[:, None, None]) ** 2 / nu_c)
    ljac = np.log(qs)[..., None] + np.log1p(tn * tn)                                           # d b11 / d theta
    g = np.einsum("jgk,k->jg", np.exp(lf + lp + ljac), wg) * half
    return mass, np.where((mass[:, None] > 0) & (half > 0), g, 0.0)


def _stable_bounds(prior: MNIWPrior, b: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    d = b.shape[-1]
    if d == 1:
        return np.full(b.shape[0], -prior.c), np.full(b.shape[0], prior.c)
    if d == 2:
        lo, hi = stable_interval_b11(b[:, 0, 1], b[:, 1, 0], b[:, 1, 1], prior.c)
        return lo, np.maximum(hi, lo)
    raise ValueError("interval Rao-Blackwellisation is implemented for d in {1, 2}")


def interval_rb_terms(prior: MNIWPrior, post_i: F2Posterior, b: np.ndarray, y: np.ndarray,
                      nodes: int = INTERVAL_NODES) -> tuple[np.ndarray, np.ndarray]:
    """Stable-segment terms (a_j, g_j) of estimator I (MATH_F2 section 5b); only b12, b21, b22 of each draw are used."""
    lo, hi = _stable_bounds(prior, b)
    return _segment_terms(post_i, b, y, lo, hi, nodes)


def interval_rb_logpdf_item(prior: MNIWPrior, post_i: F2Posterior, y: np.ndarray, rng: np.random.Generator,
                            target_se: float = 2e-4, batch: int = 4096, min_draws: int = 16384,
                            max_draws: int = 2 ** 22) -> TruncatedEstimate:
    """Truncated one-step predictive by the interval Rao-Blackwell estimator p = sum_j g_j / sum_j a_j (MATH_F2 5b),
    a ratio of means of draw-wise closed forms (no 0/1 indicator). Delta-method SE of the log of the ratio. Densities
    are scaled by the untruncated predictive p_U(y) to keep sums O(1). Stops when max SE <= target_se (after at least
    min_draws) or at max_draws (``capped``); a non-positive running estimate never stops the loop."""
    y = np.asarray(y, dtype=FLOAT)
    log_pu = untruncated_logpdf(post_i, y[None])[0]
    n = 0
    s_a = s_a2 = 0.0
    s_g = np.zeros_like(log_pu); s_g2 = np.zeros_like(log_pu); s_ga = np.zeros_like(log_pu)
    while True:
        b, _ = sample_mniw(post_i.bn[0], post_i.vn[0], post_i.nun, post_i.psin[0], batch, rng)
        a, g = interval_rb_terms(prior, post_i, b, y)
        g = g / np.exp(log_pu)[None, :]
        n += batch
        s_a += a.sum(); s_a2 += (a * a).sum()
        s_g += g.sum(axis=0); s_g2 += (g * g).sum(axis=0); s_ga += (g * a[:, None]).sum(axis=0)
        ma, mg = s_a / n, s_g / n
        p = mg / ma if ma > 0 else np.full_like(mg, np.nan)
        var_a, var_g, cov = s_a2 / n - ma * ma, s_g2 / n - mg * mg, s_ga / n - mg * ma
        var = np.maximum(var_g - 2 * p * cov + p * p * var_a, 0.0) / (n * ma * ma) if ma > 0 else np.full_like(mg, np.inf)
        with np.errstate(divide="ignore", invalid="ignore"):
            se = np.sqrt(var) / p
        valid = bool(np.all(p > 0) and np.all(np.isfinite(se)))
        done = valid and n >= min_draws and float(np.max(se)) <= target_se
        if done or n >= max_draws:
            with np.errstate(divide="ignore", invalid="ignore"):
                return TruncatedEstimate(log_pu + np.log(p), se, n, int(round(s_a)), "I", not done)


# ------------------------------------------------------------------------------------------------ libraries

@dataclass(frozen=True)
class VarLibrary:
    """K atoms (A_k, Sigma_k), uniform weights; exact posterior weights and Gaussian-mixture predictive (MATH_F2 7)."""

    a: np.ndarray         # (K, d, d)
    sigma: np.ndarray     # (K, d, d)

    def log_weights(self, ctx: np.ndarray) -> np.ndarray:
        x, y = regression_arrays(ctx)
        resid = y[:, None, :, :] - np.einsum("kij,ntj->nkti", self.a, x)           # (N, K, n, d)
        scat = np.einsum("nkti,nktj->nkij", resid, resid)
        sinv = inv2(self.sigma)
        n = x.shape[1]
        ll = -0.5 * n * np.log(det2(self.sigma))[None, :] - 0.5 * np.einsum("kij,nkji->nk", sinv, scat)
        return ll - special.logsumexp(ll, axis=1, keepdims=True)

    def logpdf(self, ctx: np.ndarray, y: np.ndarray, horizon: int = 1) -> np.ndarray:
        """y (N, G, d) -> (N, G)."""
        lw = self.log_weights(ctx)
        last = np.asarray(ctx, dtype=FLOAT)[:, -1, :]
        ah = np.broadcast_to(np.eye(self.a.shape[-1]), self.a.shape).copy()
        cov = np.zeros_like(self.sigma)
        for _ in range(horizon):
            cov = cov + ah @ self.sigma @ np.swapaxes(ah, 1, 2)
            ah = self.a @ ah
        loc = np.einsum("kij,nj->nki", ah, last)                                    # (N, K, d)
        comp = mvn_logpdf(y[:, :, None, :], loc[:, None, :, :], cov[None, None])    # (N, G, K)
        return special.logsumexp(comp + lw[:, None, :], axis=2)


def library_from_prior(prior: MNIWPrior, k: int, rng: np.random.Generator) -> VarLibrary:
    b, s, _ = sample_truncated_prior(prior, k, rng)
    return VarLibrary(np.swapaxes(b, 1, 2), s)


# ------------------------------------------------------------------------------------------------ simulation

@dataclass(frozen=True)
class F2Split:
    a: np.ndarray             # (N, d, d)
    sigma: np.ndarray         # (N, d, d)
    trajectories: np.ndarray  # (N, T + 1, d)


def simulate_f2(prior: MNIWPrior, r: float, streams: NamedStreams, n_items: int, length: int,
                stream_code: int = 11, system_override: tuple[np.ndarray, np.ndarray] | None = None) -> F2Split:
    """Item i: (A, Sigma) from the truncated prior using child (selection_systems, i, code); x_0 ~ N(0, r^2 I) and the
    innovations from child (selection_noise, i, code). Items do not depend on n_items (Stage 0 stream conventions).
    ``system_override`` = (A (N, d, d), Sigma (N, d, d)) fixes the systems (used for library-member evaluation)."""
    d = prior.d
    a = np.empty((n_items, d, d)); s = np.empty((n_items, d, d))
    traj = np.empty((n_items, length + 1, d))
    for i in range(n_items):
        if system_override is None:
            b, sig, _ = sample_truncated_prior(prior, 1, streams.item("selection_systems", i, stream_code))
            a[i], s[i] = b[0].T, sig[0]
        else:
            a[i], s[i] = system_override[0][i], system_override[1][i]
        g = streams.item("selection_noise", i, stream_code)
        x = r * g.standard_normal(d)
        eps = g.standard_normal((length, d))
        l = chol2(s[i])
        traj[i, 0] = x
        for t in range(length):
            x = a[i] @ x + l @ eps[t]
            traj[i, t + 1] = x
    return F2Split(a, s, traj)


def contexts_and_targets(split: F2Split, n: int, horizon: int = 1) -> tuple[np.ndarray, np.ndarray]:
    """Contexts (N, n + 1, d) cut coordinate by coordinate with the frozen ``harness.make_context`` (the only place
    contexts are cut), and targets x_{n+h} (N, d) on the evaluator side."""
    tr = split.trajectories
    if tr.shape[1] < n + horizon + 1:
        raise ValueError("trajectories too short")
    ctx = np.stack([np.stack([harness.make_context(np.ascontiguousarray(tr[i, :, k]), n).values
                              for k in range(tr.shape[2])],
                             axis=1) for i in range(tr.shape[0])])
    return ctx, np.array(tr[:, n + horizon, :], dtype=FLOAT)
