"""Validation checks (Section 5). Each returns a :class:`CheckResult`. Tests assert ``passed``, and the
mutation runner (validation/mutations.py) runs the same checks with bugs injected.

Tolerance policy (docs/MATH.md section 8):
* Deterministic comparisons: tol = 10 x (measured numerical error of BOTH methods) + a float64 floor.
  The numerical error is measured, not assumed: node doubling for quadrature, grid refinement and
  widening for grids. The floor (1e-11 relative unless stated) is about 100x the rounding accumulated
  by pairwise summation over <= 1e4 terms (~ 1e-13).
* Statistical comparisons: z x SE, with SE from the Monte Carlo design and z from a Bonferroni split
  of a family-wise alpha = 1e-3 per check. Seeds are fixed, so results are deterministic. Alpha is
  the probability that a correct implementation would have failed at design time.

Every check reaches the references through module attributes (``ar1.``, ``harness.``, ``matched_refs.``),
so the monkeypatched mutations take effect.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np
from scipy import integrate, special, stats

from dynaicl.baselines.family import build_context_only_family
from dynaicl.evaluation import harness
from dynaicl.metrics import calibration, scoring
from dynaicl.references import matched as matched_refs
from dynaicl.references.conjugate import (
    ConjugateGaussianAr1Predictor,
    GaussianCoefficientPosterior,
    NormalInverseGammaAr1Predictor,
    conjugate_gaussian_sequential_update,
    gaussian_coefficient_horizon_predictive,
    nig_posterior,
    nig_sequential_update,
)
from dynaicl.references.known import KnownSystemPredictor
from dynaicl.references.library import FiniteLibraryPredictor
from dynaicl.references.predictive import GaussianPredictive, StudentTPredictive
from dynaicl.references.quadrature import (
    CoefficientPosteriorQuadrature,
    QuadratureSettings,
    StablePriorQuadraturePredictor,
    gaussian_coefficient_quadrature,
    horizon_mixture,
)
from dynaicl.rng import NamedStreams
from dynaicl.systems import ar1
from dynaicl.systems.conditions import ContinuousPriorCondition, InitialStateSpec, LibraryCondition
from dynaicl.systems.context import ContextWindow
from dynaicl.systems.library import SystemLibrary, build_library_from_prior
from dynaicl.systems.priors import GaussianCoefficientPrior, NormalInverseGammaPrior, StableCoefficientPrior  # noqa: F401
from dynaicl.systems.splits import (
    DataSplit,
    SplitRole,
    assert_no_unintended_overlap,
    assert_parameters_disjoint,
    assert_parameters_within_library,
    generate_library_training_split,
    generate_split,
)
from dynaicl.validation import oracles

FLOAT = np.float64
FAMILY_ALPHA = 1e-3
FLOOR_REL = 1e-11

# ------------------------------------------------------------------------------------- test regimes

P_GAUSS = GaussianCoefficientPrior(mu0=0.2, tau0=0.3, sigma=1.0)
P_GAUSS_SMALL_SIGMA = GaussianCoefficientPrior(mu0=-0.3, tau0=0.25, sigma=0.2)
P_NIG = NormalInverseGammaPrior(mu0=0.2, lambda0=10.0, alpha0=3.0, beta0=2.0)
P_STABLE_TN = StableCoefficientPrior(rho=0.95, sigma=1.0, shape="truncated_normal", mu0=0.4, tau0=0.3)
P_STABLE_U = StableCoefficientPrior(rho=0.95, sigma=1.0, shape="uniform")
X0 = InitialStateSpec(mean=0.0, sd=1.0)


@dataclass
class CheckResult:
    name: str
    passed: bool
    details: dict = field(default_factory=dict)
    message: str = ""

    def __bool__(self) -> bool:
        return self.passed


def _simulate_context(a: float, sigma: float, n: int, rng: np.random.Generator, x0: float | None = None) -> np.ndarray:
    x = np.empty(n + 1)
    x[0] = rng.standard_normal() if x0 is None else x0
    for t in range(1, n + 1):
        x[t] = a * x[t - 1] + sigma * rng.standard_normal()
    return x


def _close(value: float, reference: float, numerical_error: float, floor_rel: float = FLOOR_REL) -> tuple[bool, float, float]:
    tol = 10.0 * numerical_error + floor_rel * max(1.0, abs(reference))
    err = abs(value - reference)
    return err <= tol, err, tol


def _refines(value: float, fine: float, coarse: float, floor_rel: float = FLOOR_REL) -> bool:
    """Grid-refinement convergence: the fine grid is no farther from the reference than the coarse grid
    (up to the float64 floor, since both may already sit at rounding level)."""
    return abs(value - fine) <= abs(value - coarse) + floor_rel * max(1.0, abs(value))


def _z_bonferroni(n_tests: int, family_alpha: float = FAMILY_ALPHA, two_sided: bool = True) -> float:
    level = family_alpha / n_tests
    return float(stats.norm.isf(level / 2 if two_sided else level))


def _quadrature_error(build, ys, settings: QuadratureSettings) -> float:
    """Node-doubling error estimate of logpdf and cdf at ``ys`` (max over both)."""
    p1, p2 = build(settings), build(settings.refined(2))
    return float(max(np.max(np.abs(p1.logpdf(ys) - p2.logpdf(ys))), np.max(np.abs(p1.cdf(ys) - p2.cdf(ys)))))


def _y_points(pred, ks=(-3.0, -1.0, 0.0, 1.0, 3.0)) -> np.ndarray:
    sd = math.sqrt(pred.variance())
    return np.array([pred.mean() + k * sd for k in ks])


# ================================================================== A. algebra vs independent check


def check_gaussian_reference_vs_grid(seed: int = 101) -> CheckResult:
    """P-GAUSS closed-form posterior and predictive (h = 1 exact, h > 1 quadrature) vs the raw-likelihood grid.

    Grids: uniform on mu0 +/- 12 tau0, 4001 (coarse) and 8001 (fine) points. Excluded prior mass
    beyond 12 sd is 2e-33. Error of the grid = |coarse - fine| (refinement). The check also asserts
    grid-refinement convergence: the fine grid is no farther from the reference than the coarse one
    (up to the float floor).
    """
    rng = np.random.default_rng(seed)
    rows, ok_all = [], True
    for prior in (P_GAUSS, P_GAUSS_SMALL_SIGMA):
        pred = ConjugateGaussianAr1Predictor(prior)
        lo, hi = prior.mu0 - 12 * prior.tau0, prior.mu0 + 12 * prior.tau0
        for n in (0, 1, 2, 5, 20, 100):
            a_true = float(prior.sample_systems(rng, 1)[0][0])
            x = _simulate_context(a_true, prior.sigma, n, rng)
            ctx = ContextWindow(x)
            prior_lp = oracles.scipy_prior_logpdf(prior)
            g_c = oracles.BruteForceGridPosterior(prior_lp, np.linspace(lo, hi, 4001), x, prior.sigma)
            g_f = oracles.BruteForceGridPosterior(prior_lp, np.linspace(lo, hi, 8001), x, prior.sigma)
            post = pred.posterior(ctx)
            for label, val, fine, coarse in (("post_mean", post.mean, g_f.mean(), g_c.mean()),
                                             ("post_var", post.variance, g_f.variance(), g_c.variance())):
                ok, err, tol = _close(val, fine, abs(fine - coarse))
                ok = ok and _refines(val, fine, coarse)
                ok_all &= ok
                rows.append((prior.family, prior.sigma, n, label, err, tol, ok))
            for h in (1, 3, 10):
                p_ref = pred.predict(ctx, h)
                ys = _y_points(p_ref)
                q_err = 0.0 if h == 1 else _quadrature_error(
                    lambda s: pred.with_settings(s).predict(ctx, h), ys, pred.settings)
                for label, f_ref, f_grid_f, f_grid_c in (
                        ("logpdf", p_ref.logpdf(ys), g_f.predictive_logpdf(ys, h), g_c.predictive_logpdf(ys, h)),
                        ("cdf", p_ref.cdf(ys), g_f.predictive_cdf(ys, h), g_c.predictive_cdf(ys, h))):
                    for v, gf, gc in zip(f_ref, f_grid_f, f_grid_c):
                        ok, err, tol = _close(float(v), float(gf), abs(gf - gc) + q_err)
                        ok = ok and _refines(float(v), float(gf), float(gc), FLOOR_REL + q_err)
                        ok_all &= ok
                        rows.append((prior.family, prior.sigma, n, f"{label}_h{h}", err, tol, ok))
    worst = max(rows, key=lambda r: r[4] / r[5])
    return CheckResult("A1_gaussian_reference_vs_grid", ok_all,
                       {"n_comparisons": len(rows), "worst_err_over_tol": worst[4] / worst[5], "worst": worst,
                        "failures": [r for r in rows if not r[6]][:10]})


#: Accuracy floor of the scipy.stats.truncnorm oracle (relative). Measured: scipy's truncnorm variance was off
#: by 6.1e-11 for a posterior truncated far in a Gaussian tail (standardised bounds -2.68, -2.63), while the
#: quadrature agreed with a 2e6-point Simpson rule to ~1e-16 (see docs/DECISIONS.md D-07). 1e-9 is ~15x
#: the worst observed oracle error. The independent grid comparison keeps the 1e-11 floor.
TRUNCNORM_ORACLE_FLOOR = 1e-9


def check_stable_reference_vs_closed_form_and_grid(seed: int = 102) -> CheckResult:
    """P-STABLE quadrature vs (i) the truncated-normal closed forms (scipy.stats.truncnorm; h = 1 predictive
    density, MATH.md 4.3) and (ii) the raw-likelihood grid on [-rho, rho] for h > 1.

    For the uniform prior the posterior density does not vanish at +/-rho, so trapezoid error is
    O(d^2). The measured coarse-vs-fine difference enters the tolerance, as for every grid comparison.
    """
    rng = np.random.default_rng(seed)
    rows, ok_all = [], True
    for prior in (P_STABLE_TN, P_STABLE_U):
        pred = StablePriorQuadraturePredictor(prior)
        g_lo, g_hi = -prior.rho, prior.rho
        for n in (0, 1, 2, 5, 20, 100):
            a_true = float(prior.sample_systems(rng, 1)[0][0])
            x = _simulate_context(a_true, prior.sigma, n, rng)
            ctx = ContextWindow(x)
            tn = oracles.stable_posterior_truncnorm(prior, x)
            prior_lp = oracles.scipy_prior_logpdf(prior)
            g_c = oracles.BruteForceGridPosterior(prior_lp, np.linspace(g_lo, g_hi, 8001), x, prior.sigma)
            g_f = oracles.BruteForceGridPosterior(prior_lp, np.linspace(g_lo, g_hi, 32001), x, prior.sigma)
            post, post2 = pred.posterior(ctx), pred.with_settings(pred.settings.refined()).posterior(ctx)
            for label, val, val2, ref, gf, gc in (
                    ("post_mean", post.mean(), post2.mean(), float(tn.mean()), g_f.mean(), g_c.mean()),
                    ("post_var", post.variance(), post2.variance(), float(tn.var()), g_f.variance(), g_c.variance())):
                ok, err, tol = _close(val, ref, abs(val - val2), floor_rel=TRUNCNORM_ORACLE_FLOOR)
                ok_all &= ok
                rows.append((prior.shape, n, label + "_vs_truncnorm", err, tol, ok))
                ok, err, tol = _close(val, gf, abs(val - val2) + abs(gf - gc))
                ok = ok and _refines(val, gf, gc, FLOOR_REL + abs(val - val2))
                ok_all &= ok
                rows.append((prior.shape, n, label + "_vs_grid", err, tol, ok))
            p1 = pred.predict(ctx, 1)
            ys = _y_points(p1)
            q_err = _quadrature_error(lambda s: pred.with_settings(s).predict(ctx, 1), ys, pred.settings)
            closed = oracles.stable_h1_predictive_logpdf(prior, x, ys)
            for v, c in zip(p1.logpdf(ys), closed):
                ok, err, tol = _close(float(v), float(c), q_err)
                ok_all &= ok
                rows.append((prior.shape, n, "logpdf_h1_closed_form", err, tol, ok))
            for h in (3, 10):
                ph = pred.predict(ctx, h)
                ys = _y_points(ph)
                q_err = _quadrature_error(lambda s: pred.with_settings(s).predict(ctx, h), ys, pred.settings)
                for label, f_ref, gf_v, gc_v in (("logpdf", ph.logpdf(ys), g_f.predictive_logpdf(ys, h),
                                                  g_c.predictive_logpdf(ys, h)),
                                                 ("cdf", ph.cdf(ys), g_f.predictive_cdf(ys, h), g_c.predictive_cdf(ys, h))):
                    for v, gf, gc in zip(f_ref, gf_v, gc_v):
                        ok, err, tol = _close(float(v), float(gf), abs(gf - gc) + q_err)
                        ok = ok and _refines(float(v), float(gf), float(gc), FLOOR_REL + q_err)
                        ok_all &= ok
                        rows.append((prior.shape, n, f"{label}_h{h}_grid", err, tol, ok))
    worst = max(rows, key=lambda r: r[3] / r[4])
    return CheckResult("A2_stable_reference_vs_closed_form_and_grid", ok_all,
                       {"n_comparisons": len(rows), "worst_err_over_tol": worst[3] / worst[4], "worst": worst,
                        "failures": [r for r in rows if not r[5]][:10]})


#: Accuracy target for quadrature log densities: 1e-6 nats, four orders of magnitude below the smallest
#: score gap considered practically relevant (0.02 nats, docs/PREREG_separability.md). Quadrature error
#: therefore cannot change any conclusion.
QUADRATURE_LOGPDF_TARGET = 1e-6


def quadrature_convergence_table(settings: QuadratureSettings = QuadratureSettings()) -> list[dict]:
    """Node-doubling convergence in hard regimes (h up to 50, abs(a) near 1, large x_n, explosive data)."""
    rng = np.random.default_rng(103)
    regimes = []
    x = _simulate_context(0.99, 1.0, 5, rng); x[-1] = 10.0
    regimes.append(("P-GAUSS a~0.99 n=5 x_n=10", ConjugateGaussianAr1Predictor(P_GAUSS, settings), x))
    regimes.append(("P-GAUSS explosive a=1.05 n=20", ConjugateGaussianAr1Predictor(P_GAUSS, settings),
                    _simulate_context(1.05, 1.0, 20, rng, x0=1.0)))
    regimes.append(("P-STABLE-U a=0.94 n=200", StablePriorQuadraturePredictor(P_STABLE_U, settings),
                    _simulate_context(0.94, 1.0, 200, rng)))
    regimes.append(("P-STABLE-TN n=0 x0=3", StablePriorQuadraturePredictor(P_STABLE_TN, settings), np.array([3.0])))
    regimes.append(("P-STABLE-TN a=-0.9 n=5", StablePriorQuadraturePredictor(P_STABLE_TN, settings),
                    _simulate_context(-0.9, 1.0, 5, rng)))
    # wide posteriors with large x_0/sigma: the integrand is sharp near abs(a) = rho (independent audit finding)
    regimes.append(("P-STABLE-U n=0 x0=50", StablePriorQuadraturePredictor(P_STABLE_U, settings), np.array([50.0])))
    tn_small = StableCoefficientPrior(rho=0.95, sigma=0.25, shape="truncated_normal", mu0=0.4, tau0=0.3)
    regimes.append(("P-STABLE-TN sigma=0.25 n=0 x0=10", StablePriorQuadraturePredictor(tn_small, settings),
                    np.array([10.0])))
    regimes.append(("P-STABLE-TN sigma=0.25 n=2 x0=100", StablePriorQuadraturePredictor(tn_small, settings),
                    _simulate_context(0.9, 0.25, 2, rng, x0=100.0)))
    out = []
    for label, pred, x in regimes:
        ctx = ContextWindow(x)
        for h in (2, 5, 20, 50):
            p0 = pred.predict(ctx, h)
            p1 = pred.with_settings(settings.refined(2)).predict(ctx, h)
            p2 = pred.with_settings(settings.refined(4)).predict(ctx, h)
            ys = p2.quantile(np.array([1e-3, 0.1, 0.5, 0.9, 1 - 1e-3]))
            out.append({"regime": label, "h": h,
                        "nodes_used": [p.info["quadrature"]["n_nodes"] for p in (p0, p1, p2)],
                        "resolution_cells": p0.info["quadrature"]["resolution_cells"],
                        "capped": bool(p0.info["quadrature"]["capped"]),
                        "logpdf_err_N_vs_4N": float(np.max(np.abs(p0.logpdf(ys) - p2.logpdf(ys)))),
                        "logpdf_err_2N_vs_4N": float(np.max(np.abs(p1.logpdf(ys) - p2.logpdf(ys)))),
                        "cdf_err_N_vs_4N": float(np.max(np.abs(p0.cdf(ys) - p2.cdf(ys)))),
                        "mean_err_N_vs_4N": abs(p0.mean() - p2.mean())})
    return out


def check_quadrature_convergence(settings: QuadratureSettings = QuadratureSettings()) -> CheckResult:
    """Default resolution reaches QUADRATURE_LOGPDF_TARGET without hitting the panel cap, and doubling does not
    increase the error. The monotonicity check allows 1e-13 of rounding noise.
    """
    table = quadrature_convergence_table(settings)
    ok = all(r["logpdf_err_N_vs_4N"] <= QUADRATURE_LOGPDF_TARGET and r["cdf_err_N_vs_4N"] <= QUADRATURE_LOGPDF_TARGET
             and r["logpdf_err_2N_vs_4N"] <= r["logpdf_err_N_vs_4N"] + 1e-13 and not r["capped"] for r in table)
    worst = max(table, key=lambda r: r["logpdf_err_N_vs_4N"])
    return CheckResult("A3_quadrature_convergence", ok, {"table": table, "worst": worst})


def check_closed_form_vs_quadrature_h1(seed: int = 104) -> CheckResult:
    """P-GAUSS h = 1: exact Gaussian predictive vs the quadrature mixture over N(m_n, v_n) forced at h = 1."""
    rng = np.random.default_rng(seed)
    pred = ConjugateGaussianAr1Predictor(P_GAUSS)
    rows, ok_all = [], True
    for n in (0, 2, 10, 50):
        x = _simulate_context(float(P_GAUSS.sample_systems(rng, 1)[0][0]), 1.0, n, rng)
        ctx = ContextWindow(x)
        post = pred.posterior(ctx)
        exact = pred.predict(ctx, 1)

        def build(s, post=post, x=x):
            return horizon_mixture(gaussian_coefficient_quadrature(post.mean, post.variance, s), float(x[-1]), 1.0, 1)

        ys = _y_points(exact)
        q_err = _quadrature_error(build, ys, QuadratureSettings())
        quad = build(QuadratureSettings())
        for v, c in list(zip(quad.logpdf(ys), exact.logpdf(ys))) + list(zip(quad.cdf(ys), exact.cdf(ys))):
            ok, err, tol = _close(float(v), float(c), q_err)
            ok_all &= ok
            rows.append((n, err, tol, ok))
    return CheckResult("A4_closed_form_vs_quadrature_h1", ok_all,
                       {"max_err": max(r[1] for r in rows), "n_comparisons": len(rows)})


def check_nig_vs_2d_grid(seed: int = 105) -> CheckResult:
    """P-NIG closed form vs a 2-D grid over (a, log sigma^2) with the raw likelihood and scipy.stats prior.

    The comparison is against the WIDE grid. Oracle error estimate = |coarse - fine| (refinement) +
    |fine - wide| (range doubling), and the tolerance is 10x that plus the float floor. Adequacy: the
    estimate must be <= 1e-6, or the check is not informative. An algebra error in the NIG update
    (e.g. alpha_n off by 1/2, a dropped lambda0 term) changes these quantities by >= 1e-3 relative at
    n <= 20 (ASSUMED from the size of the terms; not derived). The measured oracle error is about
    1e-8 at n = 2, where posterior tails are heavy, and below 1e-11 at n >= 5.
    """
    rng = np.random.default_rng(seed)
    pr = P_NIG
    rows, ok_all, adequacy = [], True, []
    for n in (2, 5, 20):
        a_true, s_true = (float(v[0]) for v in pr.sample_systems(rng, 1))
        x = _simulate_context(a_true, s_true, n, rng)
        ctx = ContextWindow(x)
        post = nig_posterior(pr, x)
        pred = NormalInverseGammaAr1Predictor(pr).predict(ctx, 1)

        def grid(na, nu, a_half, u_lo, u_hi):
            return oracles.BruteForceNigGrid(pr.mu0, pr.lambda0, pr.alpha0, pr.beta0,
                                             np.linspace(pr.mu0 - a_half, pr.mu0 + a_half, na),
                                             np.linspace(u_lo, u_hi, nu), x)

        g_c = grid(501, 401, 12.0, math.log(1e-6), math.log(1e6))
        g_f = grid(1001, 801, 12.0, math.log(1e-6), math.log(1e6))
        g_w = grid(2001, 1201, 24.0, math.log(1e-9), math.log(1e9))
        ys = _y_points(pred)
        dof, loc, s2 = post.coefficient_marginal()
        comps = [("a_mean", post.mu, g_f.coefficient_mean(), g_c.coefficient_mean(), g_w.coefficient_mean()),
                 ("a_var", s2 * dof / (dof - 2), g_f.coefficient_variance(), g_c.coefficient_variance(),
                  g_w.coefficient_variance()),
                 ("sigma2_mean", post.beta / (post.alpha - 1), g_f.noise_variance_mean(), g_c.noise_variance_mean(),
                  g_w.noise_variance_mean())]
        lp_f, lp_c, lp_w = g_f.predictive_logpdf(ys), g_c.predictive_logpdf(ys), g_w.predictive_logpdf(ys)
        comps += [(f"logpdf_y{i}", float(v), float(lp_f[i]), float(lp_c[i]), float(lp_w[i]))
                  for i, v in enumerate(pred.logpdf(ys))]
        for label, val, gf, gc, gw in comps:
            oracle_err = abs(gf - gc) + abs(gf - gw)
            adequacy.append(oracle_err)
            ok, err, tol = _close(val, gw, oracle_err)
            ok_all &= ok
            rows.append((n, label, err, tol, ok))
    grid_ok = max(adequacy) <= 1e-6
    return CheckResult("A5_nig_vs_2d_grid", ok_all and grid_ok,
                       {"max_err_vs_wide_grid": max(r[2] for r in rows), "max_oracle_error_estimate": max(adequacy),
                        "failures": [r for r in rows if not r[4]][:10]})


def check_library_vs_raw_likelihood(seed: int = 106) -> CheckResult:
    """Finite-library posterior weights vs an explicit per-atom loop with scipy.stats (abs 1e-10 in log weights).

    Tolerance: each log weight is a sum of <= 200 terms of magnitude <= ~1e3, so rounding is
    <= 200 * 1e3 * 2.2e-16, about 4e-11.
    """
    rng = np.random.default_rng(seed)
    lib = SystemLibrary(np.array([-0.8, -0.2, 0.1, 0.5, 0.9]), np.array([1.0, 0.5, 1.0, 2.0, 1.0]),
                        np.array([0.1, 0.2, 0.3, 0.25, 0.15]))
    pred = FiniteLibraryPredictor(lib)
    worst = 0.0
    for n in (0, 1, 3, 30, 200):
        x = _simulate_context(0.5, 2.0, n, rng)
        lw = pred.posterior_log_weights(ContextWindow(x))
        raw = np.log(lib.weights) + np.array([oracles.raw_log_likelihood(np.array(a), x, s)
                                              for a, s in zip(lib.coefficients, lib.noise_scales)])
        raw = raw - special.logsumexp(raw)
        worst = max(worst, float(np.max(np.abs(lw - raw))))
    return CheckResult("A6_library_vs_raw_likelihood", worst <= 1e-10, {"max_abs_logweight_err": worst})


# ======================================================================= B. independent Monte Carlo


def check_predictive_monte_carlo(seed: int = 201, n_draws: int = 400_000) -> CheckResult:
    """Importance sampling from the prior with raw-likelihood weights, then forward simulation of x_{n+h}.

    Compares predictive mean, variance and quantiles (0.05, 0.25, 0.5, 0.75, 0.95). SEs use the
    self-normalised-IS delta method: SE(mean) = sqrt(sum w_i^2 (y_i - mu)^2), and similarly for the
    variance. A quantile's SE is the indicator SE divided by the reference density at the quantile.
    z: Bonferroni over every comparison in the check (family alpha 1e-3).
    """
    rng = np.random.default_rng(seed)
    cases = [("P-GAUSS", P_GAUSS, ConjugateGaussianAr1Predictor(P_GAUSS), 1),
             ("P-GAUSS", P_GAUSS, ConjugateGaussianAr1Predictor(P_GAUSS), 3),
             ("P-STABLE-TN", P_STABLE_TN, StablePriorQuadraturePredictor(P_STABLE_TN), 1),
             ("P-STABLE-TN", P_STABLE_TN, StablePriorQuadraturePredictor(P_STABLE_TN), 5),
             ("P-STABLE-U", P_STABLE_U, StablePriorQuadraturePredictor(P_STABLE_U), 2),
             ("P-NIG", P_NIG, NormalInverseGammaAr1Predictor(P_NIG), 1)]
    probs = (0.05, 0.25, 0.5, 0.75, 0.95)
    n_tests = len(cases) * (2 + len(probs))
    z = _z_bonferroni(n_tests)
    rows, ok_all = [], True
    for label, prior, pred, h in cases:
        a_true, s_true = (float(v[0]) for v in prior.sample_systems(rng, 1))
        x = _simulate_context(a_true, s_true, 5, rng)
        ref = pred.predict(ContextWindow(x), h)
        y, w = oracles.importance_sample_predictive(prior.sample_systems, x, h, n_draws, rng)
        ess = 1.0 / float(np.sum(w * w))
        mu = float(w @ y)
        dev2 = (y - mu) ** 2
        var = float(w @ dev2)
        comps = [("mean", mu, ref.mean(), math.sqrt(float(np.sum(w * w * dev2)))),
                 ("variance", var, ref.variance(), math.sqrt(float(np.sum(w * w * (dev2 - var) ** 2))))]
        for p in probs:
            q_ref = float(ref.quantile(p))
            ind_se = math.sqrt(float(np.sum(w * w * ((y <= q_ref) - p) ** 2)))
            comps.append((f"q{p}", oracles.weighted_quantile(y, w, p), q_ref, ind_se / math.exp(float(ref.logpdf(q_ref)))))
        for name, est, refv, se in comps:
            ok = abs(est - refv) <= z * se
            ok_all &= ok
            rows.append({"case": f"{label} h={h}", "stat": name, "mc": est, "reference": refv, "se": se,
                         "z": (est - refv) / se, "ess": ess, "ok": ok})
    return CheckResult("B1_predictive_monte_carlo", ok_all,
                       {"z_crit": z, "max_abs_z": max(abs(r["z"]) for r in rows),
                        "min_ess": min(r["ess"] for r in rows), "rows": rows})


def check_library_importance_sampling(seed: int = 202, n_draws: int = 200_000) -> CheckResult:
    """Atoms drawn from pi with raw-likelihood weights estimate the posterior probabilities; compared at z x SE."""
    rng = np.random.default_rng(seed)
    lib = SystemLibrary(np.linspace(-0.9, 0.9, 8), np.full(8, 1.0), np.arange(1, 9) / 36.0)
    x = _simulate_context(float(lib.coefficients[5]), 1.0, 10, rng)
    exact = np.exp(FiniteLibraryPredictor(lib).posterior_log_weights(ContextWindow(x)))
    k = rng.choice(lib.size, size=n_draws, p=lib.weights)
    logw = oracles.raw_log_likelihood(lib.coefficients[k], x, lib.noise_scales[k])
    w = np.exp(logw - special.logsumexp(logw))
    z = _z_bonferroni(lib.size)
    rows, ok_all = [], True
    for j in range(lib.size):
        ind = (k == j).astype(float)
        est = float(w @ ind)
        se = math.sqrt(float(np.sum(w * w * (ind - est) ** 2)))
        ok = abs(est - exact[j]) <= z * se
        ok_all &= ok
        rows.append((j, est, float(exact[j]), se, ok))
    return CheckResult("B2_library_importance_sampling", ok_all, {"z_crit": z, "rows": rows})


# ======================================================================= C. structural identities


def check_sequential_equals_batch(seed: int = 301) -> CheckResult:
    """Sequential and batch updating agree. Sequential updates take (x_prev, x_next) explicitly, while batch
    updates go through ar1.transition_pairs, so an indexing bug in either one breaks the identity.

    Tolerance 1e-10 relative: 40 updates, each with O(10) float operations at about 1.1e-16, give
    about 1e-13. 1e-10 leaves room for conditioning, while an indexing error changes results at O(1).
    """
    rng = np.random.default_rng(seed)
    x = _simulate_context(0.6, 1.0, 40, rng)
    errs = {}
    # P-GAUSS
    post = GaussianCoefficientPosterior(P_GAUSS.mu0, P_GAUSS.tau0**2)
    for t in range(1, len(x)):
        post = conjugate_gaussian_sequential_update(post, x[t - 1], x[t], P_GAUSS.sigma)
    batch = ConjugateGaussianAr1Predictor(P_GAUSS).posterior(ContextWindow(x))
    errs["gauss"] = max(abs(post.mean - batch.mean) / max(1, abs(batch.mean)), abs(post.variance / batch.variance - 1))
    # P-NIG
    from dynaicl.references.conjugate import NormalInverseGammaPosterior
    p = NormalInverseGammaPosterior(P_NIG.mu0, P_NIG.lambda0, P_NIG.alpha0, P_NIG.beta0)
    for t in range(1, len(x)):
        p = nig_sequential_update(p, x[t - 1], x[t])
    b = nig_posterior(P_NIG, x)
    errs["nig"] = max(abs(p.mu - b.mu) / max(1, abs(b.mu)), abs(p.lam / b.lam - 1), abs(p.alpha / b.alpha - 1),
                      abs(p.beta / b.beta - 1))
    # finite library: multiply in one transition at a time
    lib = SystemLibrary(np.linspace(-0.9, 0.9, 7), np.full(7, 1.0), np.full(7, 1 / 7))
    lw = np.log(lib.weights)
    for t in range(1, len(x)):
        lw = lw + stats.norm.logpdf(x[t], lib.coefficients * x[t - 1], lib.noise_scales)
        lw = lw - special.logsumexp(lw)
    errs["library"] = float(np.max(np.abs(lw - FiniteLibraryPredictor(lib).posterior_log_weights(ContextWindow(x)))))
    # quadrature posterior: fixed nodes, sequential multiplication of transition likelihoods
    qpred = StablePriorQuadraturePredictor(P_STABLE_TN)
    qpost = qpred.posterior(ContextWindow(x))
    _, gl_w = __import__("dynaicl.references.quadrature", fromlist=["x"]).composite_gauss_legendre(
        qpost.window[0], qpost.window[1], qpost.settings.panels, qpost.settings.nodes_per_panel)
    seq = np.log(gl_w) + P_STABLE_TN.coefficient_logpdf(qpost.nodes)
    seq -= special.logsumexp(seq)
    for t in range(1, len(x)):
        seq = seq + stats.norm.logpdf(x[t], qpost.nodes * x[t - 1], P_STABLE_TN.sigma)
        seq -= special.logsumexp(seq)
    errs["quadrature"] = float(np.max(np.abs(seq - qpost.log_masses)))
    ok = errs["gauss"] <= 1e-10 and errs["nig"] <= 1e-10 and errs["library"] <= 1e-10 and errs["quadrature"] <= 1e-10
    return CheckResult("C1_sequential_equals_batch", ok, errs)


def check_n0_prior_predictive() -> CheckResult:
    """With n = 0 (context x_0 only), every reference reduces to its prior predictive."""
    errs = {}
    x0 = 1.7
    ctx = ContextWindow(np.array([x0]))
    p = ConjugateGaussianAr1Predictor(P_GAUSS).predict(ctx, 1)
    errs["gauss_h1"] = max(abs(p.mean() - P_GAUSS.mu0 * x0),
                           abs(p.variance() - (P_GAUSS.sigma**2 + P_GAUSS.tau0**2 * x0**2)))
    t = NormalInverseGammaAr1Predictor(P_NIG).predict(ctx, 1)
    ref_t = StudentTPredictive(P_NIG.mu0 * x0, (P_NIG.beta0 / P_NIG.alpha0) * (1 + x0**2 / P_NIG.lambda0),
                               2 * P_NIG.alpha0)
    ys = np.linspace(-4, 4, 9)
    errs["nig_h1"] = float(np.max(np.abs(t.logpdf(ys) - ref_t.logpdf(ys))))
    lib = SystemLibrary(np.array([-0.5, 0.3, 0.8]), np.array([1.0, 1.0, 0.5]), np.array([0.2, 0.5, 0.3]))
    errs["library_weights"] = float(np.max(np.abs(np.exp(FiniteLibraryPredictor(lib).posterior_log_weights(ctx))
                                                  - lib.weights)))
    q_tn = StablePriorQuadraturePredictor(P_STABLE_TN).posterior(ctx)
    tn = oracles.stable_posterior_truncnorm(P_STABLE_TN, np.array([x0]))
    errs["stable_tn_moments"] = max(abs(q_tn.mean() - tn.mean()), abs(q_tn.variance() - tn.var()))
    q_u = StablePriorQuadraturePredictor(P_STABLE_U).posterior(ctx)
    errs["stable_u_moments"] = max(abs(q_u.mean()), abs(q_u.variance() - P_STABLE_U.rho**2 / 3))
    g = oracles.BruteForceGridPosterior(oracles.scipy_prior_logpdf(P_GAUSS), np.linspace(-3.4, 3.8, 8001),
                                        np.array([x0]), P_GAUSS.sigma)
    p3 = ConjugateGaussianAr1Predictor(P_GAUSS).predict(ctx, 3)
    ys = _y_points(p3)
    errs["gauss_h3_vs_prior_grid"] = float(np.max(np.abs(p3.logpdf(ys) - g.predictive_logpdf(ys, 3))))
    tol = {"gauss_h1": 1e-14, "nig_h1": 1e-12, "library_weights": 1e-15, "stable_tn_moments": 1e-10,
           "stable_u_moments": 1e-12, "gauss_h3_vs_prior_grid": 1e-9}
    ok = all(errs[k] <= tol[k] for k in errs)
    return CheckResult("C2_n0_prior_predictive", ok, {"errors": errs, "tolerances": tol})


def check_single_atom_library_equals_known_system() -> CheckResult:
    """K = 1 library is the known-system predictor (identical arithmetic; 1e-14 relative)."""
    rng = np.random.default_rng(303)
    lib = SystemLibrary(np.array([0.73]), np.array([0.6]), np.array([1.0]))
    known = KnownSystemPredictor(0.73, 0.6)
    worst = 0.0
    for n in (0, 3, 50):
        ctx = ContextWindow(_simulate_context(0.73, 0.6, n, rng))
        for h in (1, 4, 30):
            p, k = FiniteLibraryPredictor(lib).predict(ctx, h), known.predict(ctx, h)
            ys = _y_points(k)
            worst = max(worst, float(np.max(np.abs(p.logpdf(ys) - k.logpdf(ys)))),
                        abs(p.mean() - k.mean()) / max(1, abs(k.mean())), abs(p.variance() / k.variance() - 1))
    return CheckResult("C3_single_atom_library_equals_known_system", worst <= 1e-14, {"max_err": worst})


def check_chain_rule_h2(seed: int = 304) -> CheckResult:
    """p(x_{n+2} = z | D) = integral of p(x_{n+1} = w | D) p(x_{n+2} = z | D, w) dw, by adaptive 1-D quadrature
    over w, using each predictor's own one-step predictive on the augmented context.

    Tolerance: 10 x (quad's abserr + node-doubling error of the h = 2 mixture) + 1e-9 relative. The floor
    covers the inner quadrature error of the one-step predictives (<= 1e-10 by check A3) and the
    tolerance of the outer adaptive rule.
    """
    rng = np.random.default_rng(seed)
    lib = build_library_from_prior(P_STABLE_U, 8, NamedStreams(304))
    cases = [("P-GAUSS", ConjugateGaussianAr1Predictor(P_GAUSS)),
             ("P-STABLE-TN", StablePriorQuadraturePredictor(P_STABLE_TN)),
             ("library", FiniteLibraryPredictor(lib))]
    rows, ok_all = [], True
    for label, pred in cases:
        x = _simulate_context(0.5, 1.0, 5, rng)
        ctx = ContextWindow(x)
        p2 = pred.predict(ctx, 2)
        p1 = pred.predict(ctx, 1)
        zs = p2.quantile(np.array([0.05, 0.5, 0.95]))
        q_err = 0.0
        if hasattr(pred, "with_settings"):
            q_err = _quadrature_error(lambda s: pred.with_settings(s).predict(ctx, 2), zs, pred.settings)
        for z in zs:
            def integrand(w, z=z):
                nxt = pred.predict(ContextWindow(np.append(x, w)), 1)
                return math.exp(float(p1.logpdf(w)) + float(nxt.logpdf(z)))
            lo, hi = p1.quantile(1e-12), p1.quantile(1 - 1e-12)
            val, abserr = integrate.quad(integrand, lo, hi, epsabs=1e-13, epsrel=1e-11, limit=400)
            ref = math.exp(float(p2.logpdf(z)))
            tol = 10 * (abserr + q_err * ref) + 1e-9 * ref
            ok = abs(val - ref) <= tol
            ok_all &= ok
            rows.append((label, float(z), val, ref, abs(val - ref) / ref, ok))
    return CheckResult("C4_chain_rule_h2", ok_all, {"rows": rows, "max_rel_err": max(r[4] for r in rows)})


# ===================================================================== D. known-parameter behaviour


def check_known_parameter_predictive(seed: int = 401, n_sims: int = 400_000) -> CheckResult:
    """Known (a, sigma): N(a^h x_n, sigma^2 sum a^{2j}) agrees with (i) the geometric closed form
    sigma^2 (1 - a^{2h}) / (1 - a^2) where abs(a) is not 1 (relative 1e-12; the closed form loses about
    h eps / abs(1 - a^2)), and (ii) forward simulation (mean and variance within z x SE, Bonferroni).
    """
    rng = np.random.default_rng(seed)
    rows, ok_all = [], True
    cases = [(0.7, 1.0, 1.3), (-0.95, 0.5, -2.0), (1.0, 1.0, 0.5), (1.05, 0.3, 1.0)]
    hs = (1, 2, 10, 50)
    z = _z_bonferroni(len(cases) * len(hs) * 2)
    for a, s, xn in cases:
        k = KnownSystemPredictor(a, s)
        for h in hs:
            p = k.predict(ContextWindow(np.array([0.0, xn])), h)
            if abs(a) != 1.0:
                cf = s**2 * (1 - a ** (2 * h)) / (1 - a**2)
                ok = abs(p.variance() / cf - 1) <= 1e-12 + 4 * h * np.finfo(float).eps / abs(1 - a**2)
                ok_all &= ok
                rows.append((a, h, "closed_form_var", abs(p.variance() / cf - 1), ok))
            else:
                ok = abs(p.variance() - s**2 * h) <= 1e-12 * s**2 * h
                ok_all &= ok
                rows.append((a, h, "unit_root_var", abs(p.variance() - s**2 * h), ok))
            state = np.full(n_sims, xn)
            for _ in range(h):
                state = a * state + s * rng.standard_normal(n_sims)
            m_se = state.std() / math.sqrt(n_sims)
            v_se = math.sqrt(np.var((state - state.mean()) ** 2) / n_sims)
            ok_m = abs(state.mean() - p.mean()) <= z * m_se
            ok_v = abs(state.var() - p.variance()) <= z * v_se
            ok_all &= ok_m and ok_v
            rows.append((a, h, "mc_mean_z", (state.mean() - p.mean()) / m_se, ok_m))
            rows.append((a, h, "mc_var_z", (state.var() - p.variance()) / v_se, ok_v))
    return CheckResult("D1_known_parameter_predictive", ok_all, {"rows": rows, "z_crit": z})


def posterior_concentration_table(seed: int = 402, a_true: float = 0.6, reps: int = 400,
                                  ns: tuple[int, ...] = (100, 400, 1600, 6400)) -> dict:
    """Mean posterior variance and posterior-mean RMSE vs n for a fixed true a (P-GAUSS reference)."""
    rng = np.random.default_rng(seed)
    nmax = max(ns)
    x = np.empty((reps, nmax + 1))
    x[:, 0] = rng.standard_normal(reps)
    eps = rng.standard_normal((reps, nmax))
    for t in range(1, nmax + 1):
        x[:, t] = a_true * x[:, t - 1] + eps[:, t - 1]
    pred = ConjugateGaussianAr1Predictor(P_GAUSS)
    var = np.empty((len(ns), reps))
    err = np.empty((len(ns), reps))
    for i, n in enumerate(ns):
        for r in range(reps):
            post = pred.posterior(ContextWindow(x[r, : n + 1]))
            var[i, r] = post.variance
            err[i, r] = post.mean - a_true
    return {"ns": np.array(ns), "var": var, "err": err, "a_true": a_true}


def _loglog_slope(ns: np.ndarray, vals: np.ndarray) -> float:
    return float(np.polyfit(np.log(ns), np.log(vals), 1)[0])


def check_posterior_concentration(seed: int = 402) -> CheckResult:
    """Posterior variance ~ 1/n (slope -1) and posterior-mean RMSE ~ n^{-1/2} (slope -1/2), log-log over n.

    SE of each slope: bootstrap over replications (200 resamples). Tolerance 4 SE + 0.02. The 0.02
    allows for finite-n transients: E[S_xx] = n sigma^2/(1-a^2) + O(1), so the relative deviation from
    the asymptotic rate is O(1/n). That is <= 0.01 at n >= 100 for a = 0.6, giving a slope bias of at
    most about 0.01. 0.02 is twice that.
    """
    tab = posterior_concentration_table(seed)
    ns, var, err = tab["ns"], tab["var"], tab["err"]
    s_var = _loglog_slope(ns, var.mean(axis=1))
    s_rmse = _loglog_slope(ns, np.sqrt((err**2).mean(axis=1)))
    rng = np.random.default_rng(seed + 1)
    bv, br = [], []
    for _ in range(200):
        idx = rng.integers(0, var.shape[1], var.shape[1])
        bv.append(_loglog_slope(ns, var[:, idx].mean(axis=1)))
        br.append(_loglog_slope(ns, np.sqrt((err[:, idx] ** 2).mean(axis=1))))
    se_v, se_r = float(np.std(bv)), float(np.std(br))
    ok = abs(s_var + 1.0) <= 4 * se_v + 0.02 and abs(s_rmse + 0.5) <= 4 * se_r + 0.02
    asym = float((var.mean(axis=1) * ns)[-1])
    return CheckResult("D2_posterior_concentration", ok,
                       {"slope_var": s_var, "se_var": se_v, "slope_rmse": s_rmse, "se_rmse": se_r,
                        "n_times_var_at_max_n": asym, "theory_1_minus_a2": 1 - tab["a_true"] ** 2})


# =========================================================== E. calibration of the matched reference


def _calibration_library() -> SystemLibrary:
    lib = build_library_from_prior(P_STABLE_U, 8, NamedStreams(555))
    w = np.arange(1, 9, dtype=float)
    return SystemLibrary(lib.coefficients, lib.noise_scales, w / w.sum(), provenance=lib.provenance)


def calibration_conditions():
    return [ContinuousPriorCondition(P_GAUSS, X0), ContinuousPriorCondition(P_NIG, X0),
            ContinuousPriorCondition(P_STABLE_TN, X0), ContinuousPriorCondition(P_STABLE_U, X0),
            LibraryCondition(_calibration_library(), X0)]


def _condition_label(cond) -> str:
    return cond.name + ("" if cond.name == "E-LIB" else f"[{cond.prior.family}{'-' + cond.prior.shape if hasattr(cond.prior, 'shape') else ''}]")


def _posterior_ranks(predictor, contexts, true_a, true_s2, n_draws, rng):
    """SBC ranks of the true parameter among ``n_draws`` posterior draws (MATH.md section 8.4).

    Quadrature posteriors: with inverse-CDF sampling, #{draws < a_true} = #{U_l < F(a_true)} exactly,
    so the rank is drawn as Binomial(L, F(a_true)). This is equal in distribution to drawing the L
    samples, at a fraction of the cost.
    """
    ranks_a, ranks_s2 = [], []
    for ctx, a, s2 in zip(contexts, true_a, true_s2):
        if isinstance(predictor, FiniteLibraryPredictor):
            w = np.exp(predictor.posterior_log_weights(ctx))
            k = rng.choice(w.size, size=n_draws, p=w / w.sum())
            ranks_a.append(calibration.sbc_ranks(np.array([a]), predictor.library.coefficients[k][None, :], rng)[0])
        elif isinstance(predictor, StablePriorQuadraturePredictor):
            u = float(predictor.posterior(ctx).cdf(a))
            ranks_a.append(int(rng.binomial(n_draws, u)))
        elif isinstance(predictor, NormalInverseGammaAr1Predictor):
            da, ds2 = predictor.posterior(ctx).sample(rng, n_draws)
            ranks_a.append(calibration.sbc_ranks(np.array([a]), da[None, :], rng)[0])
            ranks_s2.append(calibration.sbc_ranks(np.array([s2]), ds2[None, :], rng)[0])
        else:
            d = predictor.posterior(ctx).sample(rng, n_draws)
            ranks_a.append(calibration.sbc_ranks(np.array([a]), d[None, :], rng)[0])
    return np.array(ranks_a), (np.array(ranks_s2) if ranks_s2 else None)


def check_matched_reference_calibration(n_items: int = 2000, ns=(2, 10, 40), hs=(1, 3), n_draws: int = 99,
                                        conditions=None, root_seed: int = 501) -> CheckResult:
    """Simulation-based calibration, PIT uniformity and 50/80/95% coverage of the MATCHED reference,
    for each evaluation condition and several (n, h). Uses the harness path (generate_split ->
    build_evaluation_set -> matched_reference_for -> score_predictor).

    Tests: SBC chi-square (10 rank bins) per (condition, n) (plus sigma^2 for P-NIG); KS of the PIT and
    exact binomial coverage tests per (condition, n, h). Bonferroni over all tests, family alpha 1e-3.
    """
    conditions = conditions or calibration_conditions()
    streams = NamedStreams(root_seed)
    plan = []
    for cond in conditions:
        h_list = (1,) if (cond.name == "E-CONT" and cond.prior.family == "P-NIG") else hs
        for n in ns:
            plan.append((cond, n, h_list))
    n_tests = sum(1 + (1 if (c.name == "E-CONT" and c.prior.family == "P-NIG") else 0) + 4 * len(hl)
                  for c, _, hl in plan)
    level = calibration.bonferroni_level(FAMILY_ALPHA, n_tests)
    rows, ok_all = [], True
    for cond, n, h_list in plan:
        split = generate_split(cond, SplitRole.EVALUATION, streams, n_items, max(ns) + max(hs) + 1)
        ref = matched_refs.matched_reference_for(cond)
        label = _condition_label(cond)
        es0 = harness.build_evaluation_set(cond, split, n, h_list[0])
        true_a, true_s, _ = harness.ground_truth_for_validation(es0)
        rng = streams.stream("monte_carlo", cond.stream_code, n)
        ranks_a, ranks_s2 = _posterior_ranks(ref.predictor, es0.contexts, true_a, true_s**2, n_draws, rng)
        p = calibration.rank_uniformity_pvalue(ranks_a, n_draws)
        rows.append((label, n, "-", "SBC_a", p, p >= level))
        ok_all &= p >= level
        if ranks_s2 is not None:
            p = calibration.rank_uniformity_pvalue(ranks_s2, n_draws)
            rows.append((label, n, "-", "SBC_sigma2", p, p >= level))
            ok_all &= p >= level
        for h in h_list:
            es = harness.build_evaluation_set(cond, split, n, h)
            tab = harness.score_predictor(ref.predictor, es)
            p = calibration.ks_uniform_pvalue(tab.pit)
            rows.append((label, n, h, "PIT_KS", p, p >= level))
            ok_all &= p >= level
            for lev in (0.5, 0.8, 0.95):
                k = int(scoring.covered_from_pit(tab.pit, lev).sum())
                p = calibration.coverage_pvalue(k, n_items, lev)
                rows.append((label, n, h, f"coverage_{int(lev * 100)}={k / n_items:.3f}", p, p >= level))
                ok_all &= p >= level
    return CheckResult("E_matched_reference_calibration", ok_all,
                       {"n_tests": n_tests, "per_test_level": level, "min_p": min(r[4] for r in rows),
                        "failures": [r for r in rows if not r[5]], "rows": rows})


# ================================================================ F. optimality of the matched reference


def check_matched_reference_optimality(n_items: int = 2000, ns=(3, 10), hs=(1, 3), root_seed: int = 601,
                                       conditions=None) -> CheckResult:
    """T1: under each condition the matched reference's mean log score >= every competitor's, within paired SE.

    A competitor 'beats' the reference only if mean(log p_ref - log q) < -z SE (one-sided). z comes from
    a Bonferroni split of family alpha 1e-3 over all comparisons. Competitors: continuous-prior Bayes
    under other priors, the finite library (K = 8), and the full context-only family.
    """
    conditions = conditions or calibration_conditions()
    streams = NamedStreams(root_seed)
    lib8 = _calibration_library()
    plan = []
    for cond in conditions:
        h_list = (1,) if (cond.name == "E-CONT" and cond.prior.family == "P-NIG") else hs
        for n in ns:
            for h in h_list:
                plan.append((cond, n, h))

    def competitors(cond, h):
        comps = {}
        for name, pr in (("cont[P-GAUSS]", P_GAUSS), ("cont[P-STABLE-TN]", P_STABLE_TN),
                         ("cont[P-STABLE-U]", P_STABLE_U), ("cont[P-NIG]", P_NIG)):
            if pr.family == "P-NIG" and h != 1:
                continue
            comps[name] = matched_refs.continuous_prior_predictor(pr)
        comps["library_K8"] = FiniteLibraryPredictor(lib8)
        sigma = cond.prior.sigma if (cond.name == "E-CONT" and hasattr(cond.prior, "sigma")) else 1.0
        comps.update(build_context_only_family(sigma))
        return comps

    def n_scored(cond, h):
        ref_fp = cond.system_distribution_fingerprint()
        return sum(p.description.assumed_system_distribution != ref_fp for p in competitors(cond, h).values())

    n_comp = sum(n_scored(c, h) for c, _, h in plan)
    z = _z_bonferroni(n_comp, two_sided=False)
    rows, ok_all = [], True
    for cond, n, h in plan:
        split = generate_split(cond, SplitRole.EVALUATION, streams, n_items, max(ns) + max(hs) + 1)
        es = harness.build_evaluation_set(cond, split, n, h)
        ref = matched_refs.matched_reference_for(cond)
        ref_tab = harness.score_predictor(ref.predictor, es)
        comp_tabs = {}
        for name, pred in competitors(cond, h).items():
            if pred.description.assumed_system_distribution == ref.predictor.description.assumed_system_distribution:
                continue  # identical to the reference
            comp_tabs[name] = harness.score_predictor(pred, es)
        for r in harness.optimality_diagnostics(ref, es, ref_tab, comp_tabs, z):
            ok_all &= not r.violates
            rows.append((_condition_label(cond), n, h, r.competitor, r.difference.mean, r.difference.se,
                         r.difference.z, not r.violates))
    return CheckResult("F_matched_reference_optimality", ok_all,
                       {"z_crit": z, "n_comparisons": len(rows), "min_z": min(r[6] for r in rows),
                        "failures": [r for r in rows if not r[7]], "rows": rows})


# ============================================================================== J. leakage controls


def _perturb_future(split: DataSplit, n: int, rng: np.random.Generator) -> DataSplit:
    traj = np.array(split.trajectories, copy=True)
    traj[:, n + 1:] += rng.standard_normal(traj[:, n + 1:].shape) * 10.0
    return DataSplit(split.role, split.condition_name, split.coefficients, split.noise_scales, split.system_ids,
                     split.innovations, traj, split.initial_state)


def check_future_perturbation_invariance(n: int = 10, h: int = 3, n_items: int = 50) -> CheckResult:
    """Perturbing the target and all future values leaves every prediction bitwise unchanged (harness path)."""
    streams = NamedStreams(701)
    lib = build_library_from_prior(P_STABLE_TN, 16, streams)
    rows, ok_all = [], True
    for cond in (ContinuousPriorCondition(P_STABLE_TN, X0), LibraryCondition(lib, X0)):
        split = generate_split(cond, SplitRole.EVALUATION, streams, n_items, n + h + 5)
        pert = _perturb_future(split, n, np.random.default_rng(9))
        es_a = harness.build_evaluation_set(cond, split, n, h)
        es_b = harness.build_evaluation_set(cond, pert, n, h)
        preds = {"matched": matched_refs.matched_reference_for(cond).predictor,
                 "continuous": matched_refs.continuous_prior_predictor(P_STABLE_TN),
                 "library": FiniteLibraryPredictor(lib), **build_context_only_family(1.0)}
        ys = np.linspace(-5, 5, 11)
        for name, pred in preds.items():
            same = True
            for ca, cb in zip(es_a.contexts, es_b.contexts):
                pa, pb = pred.predict(ca, h), pred.predict(cb, h)
                same &= bool(np.array_equal(pa.logpdf(ys), pb.logpdf(ys)) and pa.mean() == pb.mean()
                             and pa.variance() == pb.variance())
            targets_changed = not np.array_equal(harness.ground_truth_for_validation(es_a)[2],
                                                 harness.ground_truth_for_validation(es_b)[2])
            ok_all &= same and targets_changed
            rows.append((cond.name, name, same, targets_changed))
    return CheckResult("J1_future_perturbation_invariance", ok_all, {"rows": rows})


def check_stream_independence() -> CheckResult:
    """The library depends only on the library stream: changing the evaluation streams' seeds or item
    counts leaves the library bitwise identical. Changing the library stream changes it."""
    base = NamedStreams(702)
    alt_eval = NamedStreams(702, (("eval_systems", 99), ("eval_noise", 98)))
    alt_lib = NamedStreams(702, (("library_systems", 97),))
    l0 = build_library_from_prior(P_STABLE_TN, 32, base)
    l1 = build_library_from_prior(P_STABLE_TN, 32, alt_eval)
    l2 = build_library_from_prior(P_STABLE_TN, 32, alt_lib)
    cond = ContinuousPriorCondition(P_STABLE_TN, X0)
    _ = generate_split(cond, SplitRole.EVALUATION, base, 500, 20)  # drawing eval items must not affect the library
    l3 = build_library_from_prior(P_STABLE_TN, 32, base)
    ok = (np.array_equal(l0.coefficients, l1.coefficients) and np.array_equal(l0.coefficients, l3.coefficients)
          and not np.array_equal(l0.coefficients, l2.coefficients))
    return CheckResult("J2_stream_independence", ok, {"library_fp": l0.fingerprint()[:12]})


def check_split_disjointness() -> CheckResult:
    """E-CONT: evaluation systems disjoint from library atoms. E-LIB: evaluation systems are atoms (intentional).
    Both: no shared trajectories, noise sequences, noise values or state/target values between the
    library training data, the selection split and the evaluation split."""
    streams = NamedStreams(703)
    lib = build_library_from_prior(P_STABLE_TN, 64, streams)
    train = generate_library_training_split(lib, streams, 30, X0)
    details = {}
    for cond in (ContinuousPriorCondition(P_STABLE_TN, X0), LibraryCondition(lib, X0)):
        ev = generate_split(cond, SplitRole.EVALUATION, streams, 1000, 30)
        sel = generate_split(cond, SplitRole.SELECTION, streams, 1000, 30)
        if cond.name == "E-CONT":
            details["E-CONT_min_param_distance"] = assert_parameters_disjoint(ev, lib)
            assert_parameters_disjoint(sel, lib)
        else:
            assert_parameters_within_library(ev, lib)
            assert_parameters_within_library(sel, lib)
            details["E-LIB_distinct_atoms_used"] = len(set(ev.system_ids))
        for a, b in ((ev, train), (sel, train), (ev, sel)):
            assert_no_unintended_overlap(a, b)
    return CheckResult("J3_split_disjointness", True, details)


def check_kernel_validation_causality(seed: int = 704) -> CheckResult:
    """Rolling origin: the validation prediction for pair j reads only x_0..x_j. Blocked: a fold's validation
    predictions read nothing inside its gaps. Checked by perturbing exactly those observations and
    requiring bitwise-identical predictions. Positive control: perturbing data a row *may* read must
    change that row's prediction, which shows the perturbation has power.
    """
    from dynaicl.baselines.kernel import KernelSettings, analog_pairs, validation_mask, validation_predictions
    rng = np.random.default_rng(seed)
    settings = KernelSettings()
    x = _simulate_context(0.7, 1.0, 40, rng)
    ok, n_checked, controls_ok = True, 0, True
    for h in (1, 3):
        preds, rows, _ = validation_predictions(x, h, "rolling_origin", settings)
        for j in np.flatnonzero(rows):
            xp = x.copy()
            xp[j + 1:] += 5.0 + rng.standard_normal(xp[j + 1:].size)   # everything after forecast origin j
            pp, _, _ = validation_predictions(xp, h, "rolling_origin", settings)
            ok &= bool(np.array_equal(pp[:, j], preds[:, j]))
            xc = x.copy()
            xc[j] += 1.0                                                # the origin itself may be read
            pc, _, _ = validation_predictions(xc, h, "rolling_origin", settings)
            controls_ok &= not np.array_equal(pc[:, j], preds[:, j])
            n_checked += 1
        u, _ = analog_pairs(x, h)
        m = u.size
        g = max(h, settings.gap)
        preds_b, _, _ = validation_predictions(x, h, "blocked", settings)
        for block in np.array_split(np.arange(m), min(settings.n_blocks, m)):
            s0, e0 = int(block[0]), int(block[-1])
            gap_idx = [t for t in list(range(s0 - g, s0)) + list(range(e0 + h + 1, e0 + h + 1 + g)) if 0 <= t < x.size]
            xp = x.copy()
            xp[gap_idx] += 7.0
            pb, _, _ = validation_predictions(xp, h, "blocked", settings)
            ok &= bool(np.array_equal(pb[:, block], preds_b[:, block], equal_nan=True))
            n_checked += 1
    return CheckResult("J4_kernel_validation_causality", ok and controls_ok,
                       {"n_checked": n_checked, "positive_controls_detected": controls_ok})


# ======================================================================================= registry

ALL_CHECKS = {
    "A1": check_gaussian_reference_vs_grid,
    "A2": check_stable_reference_vs_closed_form_and_grid,
    "A3": check_quadrature_convergence,
    "A4": check_closed_form_vs_quadrature_h1,
    "A5": check_nig_vs_2d_grid,
    "A6": check_library_vs_raw_likelihood,
    "B1": check_predictive_monte_carlo,
    "B2": check_library_importance_sampling,
    "C1": check_sequential_equals_batch,
    "C2": check_n0_prior_predictive,
    "C3": check_single_atom_library_equals_known_system,
    "C4": check_chain_rule_h2,
    "D1": check_known_parameter_predictive,
    "D2": check_posterior_concentration,
    "E": check_matched_reference_calibration,
    "F": check_matched_reference_optimality,
    "J1": check_future_perturbation_invariance,
    "J2": check_stream_independence,
    "J3": check_split_disjointness,
    "J4": check_kernel_validation_causality,
}
