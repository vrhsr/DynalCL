"""F1 validation at Stage-0 scale (task A2) and the extra detectors of the F1-V9 mutation matrix (task A1).

Every patched name (``population_f1``, ``F1Stats.from_contexts``, ``contexts_and_targets``, ``F1PopulationCondition``,
``InverseGammaScale.log_marginal``) is looked up through its module at call time, so a mutation applied by
``f1_mutations.apply`` reaches these checks.

Checks (each returns a JSON-serialisable dict with a boolean ``pass``):
* ``matched_guard``: the population reference's prior equals the evaluation condition's (structural, like Stage 0's
  fingerprint guard);
* ``leakage``: contexts are exactly x_0..x_n of each trajectory and do not change when the future is changed;
* ``calibration_cell``: PIT (closed-form Student-t mixture CDF) KS test, central 50/80/95% coverage (binomial z), and
  continuous SBC: the posterior CDF at the true a and at the true sigma^2 must be Uniform(0, 1) (KS);
* ``optimality_cell``: E[log p_pop(y) - log p_other(y)] >= 0 on population systems (paired one-sided z);
* ``known_sigma_limit``: the F1 population reference converges to the known-sigma reference as alpha0 grows.
"""

from __future__ import annotations

import math
from dataclasses import asdict

import numpy as np
from scipy import special, stats

from dynaicl.rng import NamedStreams
from dynaicl.systems.conditions import InitialStateSpec

FLOAT = np.float64
COVERAGE_LEVELS = (0.5, 0.8, 0.95)


def _uf():
    from dynaicl_families import ar1_unknown_sigma as uf
    return uf


def _sm():
    from dynaicl_families import sampling as sm
    return sm


def population_sample(n: int, r: float, n_items: int, seed: int):
    """(stats, targets, contexts, true a, true sigma) for systems from the evaluation condition."""
    sm, uf = _sm(), _uf()
    cond = sm.F1PopulationCondition(initial_state=InitialStateSpec(0.0, r))
    split = sm.simulate(cond, NamedStreams(seed), n_items, n + 2)
    ctx, y = sm.contexts_and_targets(split, n)
    return uf.F1Stats.from_contexts(ctx), y, ctx, np.asarray(split.coefficients), np.asarray(split.noise_scales)


# ---------------------------------------------------------------------------------------------- structural checks

def matched_guard() -> dict:
    """The matched population reference must use exactly the evaluation condition's prior (rho, mu0, tau0, alpha0,
    beta0). Exact equality of the parameters is required: they are configuration constants, not computed values."""
    ref, cond = _uf().population_f1(), _sm().F1PopulationCondition()
    want = {"rho": cond.rho, "mu0": cond.mu0, "tau0": cond.tau0, "alpha0": cond.alpha0, "beta0": cond.beta0}
    got = {"rho": ref.coef.rho, "mu0": ref.coef.mu0, "tau0": ref.coef.tau0,
           "alpha0": getattr(ref.scale, "alpha0", None), "beta0": getattr(ref.scale, "beta0", None)}
    return {"check": "matched_guard", "pass": got == want, "reference": got, "condition": want}


def leakage(seed: int, n_items: int = 64) -> dict:
    """Contexts must equal x_0..x_n exactly, targets x_{n+1}, and the context must not change when every value after
    x_n is replaced (the target and beyond)."""
    sm = _sm()
    bad = []
    for n in (2, 5, 20):
        split = sm.simulate(sm.F1PopulationCondition(), NamedStreams(seed + n), n_items, n + 3)
        ctx, y = sm.contexts_and_targets(split, n)
        traj = np.asarray(split.trajectories)
        if not np.array_equal(ctx, traj[:, :n + 1]):
            bad.append(f"n={n}: context is not x_0..x_n")
        if not np.array_equal(y, traj[:, n + 1]):
            bad.append(f"n={n}: target is not x_(n+1)")
        changed = type(split)(**{**split.__dict__, "trajectories": np.concatenate(
            [traj[:, :n + 1], traj[:, n + 1:] + 1000.0], axis=1)})
        ctx2, _ = sm.contexts_and_targets(changed, n)
        if not np.array_equal(ctx, ctx2):
            bad.append(f"n={n}: context depends on values after x_n")
    return {"check": "leakage", "pass": not bad, "problems": bad}


# ---------------------------------------------------------------------------------------------- posterior CDFs

def _log_unnormalised(ref, st, a: np.ndarray) -> np.ndarray:
    return ref.coef.logpdf(a) + ref.scale.log_marginal(st.n, st.rss(a))


def _merged_gl(lo: np.ndarray, hi: np.ndarray, clo: np.ndarray, chi: np.ndarray, panels: int,
               nodes: int = 8) -> tuple[np.ndarray, np.ndarray]:
    """(N, G) Gauss-Legendre nodes and log weights on [lo_i, hi_i] over the sorted union of ``panels`` uniform panels and
    ``panels`` panels over the core window [clo_i, chi_i] (inside [lo_i, hi_i]); zero-width panels get log weight -inf."""
    x, w = np.polynomial.legendre.leggauss(nodes)
    frac = (np.arange(panels + 1) / panels)[None, :]
    edges = np.sort(np.concatenate([lo[:, None] + (hi - lo)[:, None] * frac,
                                    clo[:, None] + (chi - clo)[:, None] * frac], axis=1), axis=1)
    a0, a1 = edges[:, :-1], edges[:, 1:]
    h, mid = 0.5 * (a1 - a0), 0.5 * (a1 + a0)
    with np.errstate(divide="ignore"):
        return ((mid[:, :, None] + h[:, :, None] * x).reshape(lo.size, -1),
                np.log(h[:, :, None] * w).reshape(lo.size, -1))


def posterior_cdf_a(ref, st, a_true: np.ndarray, refine: int = 1) -> np.ndarray:
    """P(a <= a_true | D): composite Gauss-Legendre of the unnormalised posterior over [-rho, a_true] divided by the
    same over [-rho, rho]. Panels: 256 uniform plus 256 over the reference's core window a_hat +/- 40 s_core, both
    clipped to the interval, 8 nodes each (``refine`` multiplies both); NUMERICALLY APPROXIMATED, convergence checked by
    node doubling and a fine-grid oracle in tests_stage2/test_f1_checks.py."""
    rho = ref.coef.rho
    half = 40.0 * ref.scale.core_scale(st)

    def log_integral(lo: np.ndarray, hi: np.ndarray) -> np.ndarray:
        clo, chi = np.clip(st.a_hat - half, lo, hi), np.clip(st.a_hat + half, lo, hi)
        a, lw = _merged_gl(lo, hi, clo, chi, 256 * refine)
        return special.logsumexp(lw + _log_unnormalised(ref, st, a), axis=1)

    lo = np.full(st.size, -rho)
    top = log_integral(lo, np.clip(np.asarray(a_true, dtype=FLOAT), -rho, rho))
    return np.exp(top - log_integral(lo, np.full(st.size, rho)))


def posterior_cdf_sigma2(ref, st, s2_true: np.ndarray) -> np.ndarray:
    """P(sigma^2 <= s2_true | D) for the inverse-gamma scale prior: sum over the reference's a-nodes of the node mass
    times the IG(alpha_n, beta_n(a)) CDF, which is Q(alpha_n, beta_n(a) / s2) (MATH_F1 section 4)."""
    uf = _uf()
    if not isinstance(ref.scale, uf.InverseGammaScale):
        raise TypeError("closed-form sigma^2 posterior only for the inverse-gamma prior")
    a, lw, r = ref.posterior(st)
    alpha_n = ref.scale.alpha0 + st.n / 2.0
    beta_n = ref.scale.beta0 + r / 2.0
    return (np.exp(lw) * special.gammaincc(alpha_n, beta_n / np.asarray(s2_true)[:, None])).sum(axis=1)


# ---------------------------------------------------------------------------------------------- statistical checks

def calibration_cell(n: int, r: float, n_items: int, seed: int, alpha_per_test: float) -> dict:
    """PIT KS, coverage at 50/80/95% (two-sided binomial z) and continuous SBC (KS on the posterior CDF at the true a
    and at the true sigma^2) for the matched population reference. ``alpha_per_test`` is the Bonferroni level."""
    uf = _uf()
    pop = uf.population_f1()
    st, y, _, a_true, s_true = population_sample(n, r, n_items, seed)
    pit = uf.student_t_mixture_cdf(pop, st, y)
    tests = {"pit_ks": float(stats.kstest(pit, "uniform").pvalue)}
    z_crit = float(stats.norm.isf(alpha_per_test / 2))
    cover = {}
    for lev in COVERAGE_LEVELS:
        hits = int(np.sum(np.abs(pit - 0.5) <= lev / 2))
        z = (hits - n_items * lev) / math.sqrt(n_items * lev * (1 - lev))
        cover[str(lev)] = {"rate": hits / n_items, "z": z}
        tests[f"coverage_{lev}"] = float(2 * stats.norm.sf(abs(z)))
    u_a = posterior_cdf_a(pop, st, a_true)
    u_s = posterior_cdf_sigma2(pop, st, s_true ** 2)
    tests["sbc_a_ks"] = float(stats.kstest(u_a, "uniform").pvalue)
    tests["sbc_sigma2_ks"] = float(stats.kstest(u_s, "uniform").pvalue)
    return {"check": "calibration", "n": n, "r": r, "items": n_items, "seed": seed, "p_values": tests,
            "coverage": cover, "alpha_per_test": alpha_per_test, "z_crit": z_crit,
            "pass": all(p >= alpha_per_test for p in tests.values())}


def library_atoms(k: int, seed: int) -> "object":
    """K atoms (a_k, sigma_k) drawn iid from the evaluation condition's population (MATH_F1 section 5)."""
    sm, uf = _sm(), _uf()
    rng = np.random.default_rng(seed)
    cond = sm.F1PopulationCondition()
    atoms = [cond.draw_system(rng)[:2] for _ in range(k)]
    return uf.ScaleLibrary(np.array([a for a, _ in atoms]), np.array([s for _, s in atoms]))


def optimality_cell(n: int, r: float, n_items: int, seed: int, z_crit: float, lib_ks=(2, 16, 256)) -> dict:
    """E[LS(pop) - LS(other)] >= 0 on population systems (the population reference is Bayes there: DERIVED, MATH 6).
    One-sided: fail if z < -z_crit. Others: the context-only reference and libraries of K atoms from the population."""
    uf = _uf()
    pop = uf.population_f1()
    st, y, _, _, _ = population_sample(n, r, n_items, seed)
    lp = pop.logpdf(st, y)
    others = {"context_only": uf.context_only_f1()}
    others.update({f"LIB-{k}": library_atoms(k, seed + 7919 * k) for k in lib_ks})
    rows = {}
    for name, ref in others.items():
        d = lp - ref.logpdf(st, y)
        z = float(d.mean() / (d.std(ddof=1) / math.sqrt(d.size)))
        rows[name] = {"mean": float(d.mean()), "se": float(d.std(ddof=1) / math.sqrt(d.size)), "z": z}
    return {"check": "optimality", "n": n, "r": r, "items": n_items, "seed": seed, "z_crit": z_crit, "rows": rows,
            "pass": all(v["z"] >= -z_crit for v in rows.values())}


def known_sigma_limit(n: int, r: float, n_items: int, seed: int, alphas=(1e2, 1e3, 1e4, 1e5, 1e6, 1e7)) -> dict:
    """Max |log p_F1(y) - log p_known(y)| over items for IG(alpha0, alpha0 + 1) (prior mean of sigma^2 = 1 + 1/alpha0
    ... -> 1, sd -> 0). Expected (DERIVED heuristically: the Student-t with 2 alpha_n dof differs from the Gaussian by
    O(1/alpha_n), and the prior mean of sigma^2 differs from 1 by 1/alpha0): error ~ C / alpha0, so the fitted log-log
    slope should be close to -1. Pass: errors strictly decrease, the last (alpha0 = 1e7, as the frozen F1-V7) <= 1e-4
    nats, slope in [-1.2, -0.8]. History: a first grid ending at 1e6 failed the 1e-4 bound (measured C about 12.6 nats,
    error 1.26e-4 at 1e6, slope -0.99); the grid was extended to the frozen F1-V7 range, the bound unchanged."""
    from dynaicl_families.ar1_known_sigma import ContextStats, population_prior
    uf = _uf()
    st, y, ctx, _, _ = population_sample(n, r, n_items, seed)
    known = population_prior(sigma=1.0).logpdf(ContextStats.from_contexts(ctx), y)
    errs = []
    for a0 in alphas:
        ref = uf.UnknownScaleReference(uf.CoefficientPrior(0.95, 0.4, 0.3), uf.InverseGammaScale(a0, a0 + 1.0))
        errs.append(float(np.max(np.abs(ref.logpdf(st, y) - known))))
    slope = float(np.polyfit(np.log(alphas), np.log(errs), 1)[0])
    ok = all(e1 > e2 for e1, e2 in zip(errs, errs[1:])) and errs[-1] <= 1e-4 and -1.2 <= slope <= -0.8
    return {"check": "known_sigma_limit", "n": n, "r": r, "items": n_items, "alphas": list(alphas), "max_err": errs,
            "loglog_slope": slope, "pass": ok}


def as_dict(obj) -> dict:
    return asdict(obj)
