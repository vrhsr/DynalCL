"""Unit tests of the F1 checks used by task A2 and by the F1-V9 mutation matrix (dynaicl_families/stage2/f1_checks.py).

Tolerances: posterior CDFs are probabilities obtained by quadrature; node doubling and the dense-grid oracle must agree to
1e-8 and 1e-6 (absolute) respectively, far below the KS resolution at the sample sizes used (about 1 / sqrt(N) >= 0.005).
"""

from __future__ import annotations

import math

import numpy as np
from scipy import integrate, stats

from dynaicl_families.ar1_unknown_sigma import F1Stats, context_only_f1, population_f1
from dynaicl_families.stage2 import f1_checks as fc
from dynaicl_families.stage2.seeds import role_seed

SEED = role_seed("f1_tests")


def _nested_quad_cdfs(ref, ctx, a_true, s2_true):
    """Independent oracle: nested scipy.integrate.quad over a (outer) and sigma^2 (inner) of the raw conditional
    likelihood times the scipy prior densities; no closed-form marginal is used. Returns (P(a <= a_true | D),
    P(sigma^2 <= s2_true | D))."""
    rho, prev, curr = ref.coef.rho, ctx[:-1], ctx[1:]
    n = prev.size
    lo, hi = (-rho - ref.coef.mu0) / ref.coef.tau0, (rho - ref.coef.mu0) / ref.coef.tau0
    a_hat = float(prev @ curr / (prev @ prev))

    def lik(a, s2):
        rss = float(((curr - a * prev) ** 2).sum())
        return s2 ** (-n / 2) * math.exp(-rss / (2 * s2))

    def inner(a, s_hi):
        f = lambda s2: lik(a, s2) * stats.invgamma.pdf(s2, ref.scale.alpha0, scale=ref.scale.beta0)
        return integrate.quad(f, 0.0, s_hi, epsabs=0, epsrel=1e-11, limit=200)[0]

    def outer(a_hi, s_hi):
        g = lambda a: stats.truncnorm.pdf(a, lo, hi, loc=ref.coef.mu0, scale=ref.coef.tau0) * inner(a, s_hi)
        pts = [p for p in (a_hat,) if -rho < p < a_hi]
        return integrate.quad(g, -rho, a_hi, points=pts or None, epsabs=0, epsrel=1e-10, limit=200)[0]

    total = outer(rho, np.inf)
    return outer(min(max(a_true, -rho), rho), np.inf) / total, outer(rho, s2_true) / total


def test_posterior_cdfs_node_doubling_and_nested_quad_oracle():
    pop = population_f1()
    for n, r in ((2, 1.0), (5, 4.0), (20, 0.25)):
        st, y, ctx, a_true, s_true = fc.population_sample(n, r, 6, SEED + n)
        u1 = fc.posterior_cdf_a(pop, st, a_true)
        u2 = fc.posterior_cdf_a(pop, st, a_true, refine=2)
        assert np.max(np.abs(u1 - u2)) <= 1e-8
        assert np.allclose(fc.posterior_cdf_a(pop, st, np.full(st.size, 0.95)), 1.0, atol=1e-12)
        us = fc.posterior_cdf_sigma2(pop, st, s_true ** 2)
        for i in range(2):
            want_a, want_s = _nested_quad_cdfs(pop, ctx[i], a_true[i], s_true[i] ** 2)
            assert abs(u1[i] - want_a) <= 1e-6, (n, r, i, u1[i], want_a)
            assert abs(us[i] - want_s) <= 1e-6, (n, r, i, us[i], want_s)


def test_structural_checks_pass_on_the_clean_code():
    assert fc.matched_guard()["pass"]
    leak = fc.leakage(SEED + 200)
    assert leak["pass"], leak["problems"]


def test_calibration_and_optimality_pass_on_the_clean_code_small():
    """Small fixed-seed versions of the A2 checks (statistical; Bonferroni over the 6 + 4 tests at family level 0.01)."""
    cal = fc.calibration_cell(3, 1.0, 1500, SEED + 300, alpha_per_test=0.01 / 10)
    assert cal["pass"], cal["p_values"]
    opt = fc.optimality_cell(3, 1.0, 1500, SEED + 301, z_crit=float(stats.norm.isf(0.01 / 10)))
    assert opt["pass"], opt["rows"]


def test_known_sigma_limit_rate():
    res = fc.known_sigma_limit(5, 1.0, 100, SEED + 400)
    assert res["pass"], res


def test_context_only_reference_is_not_matched():
    """The guard compares the population reference only; the context-only reference has no population parameters."""
    ref = context_only_f1()
    assert ref.coef.tau0 is None and not hasattr(ref.scale, "alpha0")


def test_f1_stats_unchanged_by_the_checks_module():
    st = F1Stats.from_contexts(np.array([[0.1, 0.3, -0.2, 0.5]]))
    assert st.n == 3
