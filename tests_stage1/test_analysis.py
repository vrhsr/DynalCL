"""Stage 1A analysis: two-level SE, simultaneous bands (bootstrap and Gaussian), classification rules."""

from __future__ import annotations

import numpy as np
import pytest

from dynaicl_neural.analysis import (Band, Statistic, band, classify_behavioural, classify_q1_held,
                                     covariance_of_estimates, critical_value_bootstrap, critical_value_gaussian,
                                     estimates, two_level)


def _crossed(rng, m, n, mu, s_u, s_e, s_eta, e=None):
    e = rng.normal(0, s_e, n) if e is None else e
    return mu + rng.normal(0, s_u, (m, 1)) + e[None, :] + rng.normal(0, s_eta, (m, n))


def test_two_level_se_is_conservative_and_close():
    """E[se^2] = s_u^2/M + s_e^2/N + 2 s_eta^2/(MN) (DERIVED); the true variance has 1 s_eta^2/(MN).
    500 simulated studies; tolerance 15% on variances (Monte Carlo relative sd about sqrt(2/500) = 6%)."""
    rng = np.random.default_rng(1)
    m, n, s_u, s_e, s_eta = 16, 400, 0.01, 0.2, 0.3
    th, se2 = [], []
    for _ in range(500):
        t, s = two_level(_crossed(rng, m, n, 0.0, s_u, s_e, s_eta))
        th.append(t)
        se2.append(s * s)
    true_var = s_u**2 / m + s_e**2 / n + s_eta**2 / (m * n)
    expected_se2 = s_u**2 / m + s_e**2 / n + 2 * s_eta**2 / (m * n)
    assert abs(np.var(th, ddof=1) / true_var - 1) < 0.15
    assert abs(np.mean(se2) / expected_se2 - 1) < 0.05
    assert np.mean(se2) >= true_var


def _family(rng, m, n, mus, s_u=0.01, s_e=0.15, s_eta=0.2):
    """Four statistics on one item set with shared system effects (correlated), plus one on a second set."""
    e = rng.normal(0, s_e, n)
    stats = [Statistic(f"s{k}", _crossed(rng, m, n, mu, s_u, s_e, s_eta, e=e * (1 + 0.3 * k)), "HELD")
             for k, mu in enumerate(mus[:4])]
    stats.append(Statistic("probe", _crossed(rng, m, n // 2, mus[4], s_u, s_e, s_eta), "PROBE"))
    return stats


def test_simultaneous_coverage_bootstrap_and_gaussian():
    """Familywise coverage at alpha = 0.05 over 150 studies, both critical values. Lower acceptance 0.88 (binomial:
    P(X <= 132 | n = 150, p = 0.95) is about 0.002); the band is mildly conservative by construction."""
    rng = np.random.default_rng(7)
    mus = [0.05, 0.02, -0.01, 0.0, 0.1]
    cover_b = cover_g = 0
    agree = []
    sims = 150
    for _ in range(sims):
        st = _family(rng, 12, 200, mus)
        est = estimates(st)
        cb, _ = critical_value_bootstrap(st, 0.05, 400, rng)
        cg = critical_value_gaussian(covariance_of_estimates(st), 0.05, rng, 5000)
        agree.append(cb / cg)
        cover_b += all(abs(est[s.name][0] - mu) <= cb * est[s.name][1] for s, mu in zip(st, mus))
        cover_g += all(abs(est[s.name][0] - mu) <= cg * est[s.name][1] for s, mu in zip(st, mus))
    assert cover_b / sims >= 0.88, cover_b / sims
    assert cover_g / sims >= 0.88, cover_g / sims
    assert 0.85 <= float(np.median(agree)) <= 1.25, np.median(agree)


def test_bootstrap_refuses_degenerate_statistic():
    st = [Statistic("const", np.ones((5, 10)), "HELD"), Statistic("x", np.random.default_rng(0).normal(size=(5, 10)),
                                                                   "HELD")]
    with pytest.raises(FloatingPointError):
        critical_value_bootstrap(st, 0.05, 20, np.random.default_rng(1))


def test_statistic_validation():
    with pytest.raises(ValueError):
        Statistic("bad", np.array([[1.0, np.nan], [0.0, 1.0]]), "HELD")
    with pytest.raises(ValueError):
        Statistic("bad", np.ones(5), "HELD")


@pytest.mark.parametrize("r_pop,g,expected", [
    ((0.000, -0.004, 0.004), (0.044, 0.035, 0.053), "POP-LIKE"),
    ((0.044, 0.035, 0.053), (0.000, -0.009, 0.009), "STAB-LIKE"),
    ((0.090, 0.075, 0.105), (-0.04, -0.05, -0.03), "WORSE-THAN-STAB"),
    ((0.020, 0.010, 0.030), (0.024, 0.014, 0.034), "INCONCLUSIVE"),
    ((0.000, -0.004, 0.0219), (0.044, 0.035, 0.053), "POP-LIKE"),      # hi just below Delta/2 = 0.022
    ((0.000, -0.004, 0.0221), (0.044, 0.035, 0.053), "INCONCLUSIVE"),  # hi just above
])
def test_classify_q1_held(r_pop, g, expected):
    assert classify_q1_held(Band(*r_pop), Band(*g), gap=0.044, epsilon=0.01) == expected


def test_classify_behavioural_three_references():
    sep = {("lib", "pop"): 0.10, ("lib", "stab"): 0.20, ("pop", "stab"): 0.08}
    near_lib = {"lib": Band(0.005, 0.0, 0.01), "pop": Band(0.09, 0.08, 0.10), "stab": Band(0.2, 0.18, 0.22)}
    con = {}
    for x in near_lib:
        for y in near_lib:
            if x != y:
                d = near_lib[y].estimate - near_lib[x].estimate
                con[(y, x)] = Band(d, d - 0.01, d + 0.01)
    assert classify_behavioural(near_lib, con, sep) == "LIB-LIKE"
    far = {k: Band(1.0, 0.9, 1.1) for k in near_lib}
    con_far = {(y, x): Band(0.0, -0.05, 0.05) for x in far for y in far if x != y}
    assert classify_behavioural(far, con_far, sep) == "NEITHER"
    mid = {"lib": Band(0.04, 0.03, 0.06), "pop": Band(0.04, 0.03, 0.06), "stab": Band(0.2, 0.18, 0.22)}
    con_mid = {(y, x): Band(mid[y].estimate - mid[x].estimate, mid[y].estimate - mid[x].estimate - 0.02,
                            mid[y].estimate - mid[x].estimate + 0.02) for x in mid for y in mid if x != y}
    assert classify_behavioural(mid, con_mid, sep) == "INCONCLUSIVE"


def test_classify_memorisation_two_way():
    from dynaicl_neural.analysis import classify_memorisation
    sep = {("lib", "pop"): 0.185, ("lib", "stab"): 0.274, ("pop", "stab"): 0.022}

    def con(d):
        return {(y, x): Band(d[y].estimate - d[x].estimate, d[y].estimate - d[x].estimate - 0.01,
                             d[y].estimate - d[x].estimate + 0.01) for x in d for y in d if x != y}
    pop_like = {"lib": Band(0.19, 0.18, 0.20), "pop": Band(0.01, 0.0, 0.02), "stab": Band(0.03, 0.02, 0.04)}
    assert classify_memorisation(pop_like, con(pop_like), sep) == "GENERALISING"
    lib_like = {"lib": Band(0.01, 0.0, 0.02), "pop": Band(0.18, 0.17, 0.19), "stab": Band(0.27, 0.26, 0.28)}
    assert classify_memorisation(lib_like, con(lib_like), sep) == "LIB-LIKE"
    between = {"lib": Band(0.09, 0.08, 0.10), "pop": Band(0.09, 0.08, 0.10), "stab": Band(0.15, 0.14, 0.16)}
    assert classify_memorisation(between, con(between), sep) == "INCONCLUSIVE"
    far = {"lib": Band(0.5, 0.4, 0.6), "pop": Band(0.5, 0.4, 0.6), "stab": Band(0.6, 0.5, 0.7)}
    assert classify_memorisation(far, con(far), sep) == "NEITHER"


def test_band():
    b = band(0.03, 0.002, 2.5)
    assert (b.lo, b.hi) == pytest.approx((0.025, 0.035))


def test_bootstrap_coverage_in_the_seed_dominated_small_m_regime_audit_a1():
    """Audit finding A1: with seed variation dominating, the SE has about M - 1 df. The hierarchical bootstrap (the
    analysis's procedure) must keep familywise coverage at M = 16 (measured 0.95-0.98 in 200-study runs); the Gaussian
    value undercovers there (measured 0.85-0.91). 80 studies, B = 300; acceptance >= 0.88 for the bootstrap
    (binomial: P(X <= 70 | 80, 0.95) is about 0.004)."""
    rng = np.random.default_rng(11)
    m, n, cover = 16, 40, 0
    for _ in range(80):
        stats = []
        for k in range(10):
            stats.append(Statistic(f"s{k}", rng.normal(0, 0.01, (m, 1)) + rng.normal(0, 0.002, (m, n)), "HELD"))
        est = estimates(stats)
        c, _ = critical_value_bootstrap(stats, 0.05, 300, rng)
        cover += all(abs(est[s.name][0]) <= c * est[s.name][1] for s in stats)
    assert cover / 80 >= 0.88, cover / 80
