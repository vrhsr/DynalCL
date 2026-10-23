"""F1 (AR(1), unknown noise scale) reference validation: docs/MATH_F1.md section 6, checks F1-V1..F1-V8.

Tolerances: closed forms against scipy.integrate.quad 1e-8 relative (quad's own accuracy, epsrel 1e-12, is the limit);
quadrature over a against the 2-D grid oracle and node doubling 1e-6 nats (four orders below delta = 0.02, as MATH 5.3);
statistical checks at the levels stated per test.
"""

from __future__ import annotations

import math

import numpy as np
import pytest
from scipy import integrate, stats

from dynaicl.rng import NamedStreams
from dynaicl_families.ar1_known_sigma import ContextStats, population_prior
from dynaicl_families.ar1_unknown_sigma import (CoefficientPrior, F1Stats, InverseGammaScale, LogUniformScale,
                                                ScaleLibrary, UnknownScaleReference, context_only_f1, population_f1,
                                                student_t_mixture_cdf)
from dynaicl_families.sampling import F1PopulationCondition, contexts_and_targets, simulate
from dynaicl.systems.conditions import InitialStateSpec


def _contexts(n, r, n_items, seed):
    split = simulate(F1PopulationCondition(initial_state=InitialStateSpec(0.0, r)), NamedStreams(seed), n_items, n + 2)
    ctx, y = contexts_and_targets(split, n)
    return F1Stats.from_contexts(ctx), y, ctx


@pytest.mark.parametrize("scale", [InverseGammaScale(3.0, 2.0), LogUniformScale(0.01, 100.0)])
def test_v1_sigma_marginal_closed_form_matches_quad(scale):
    """F1-V1: log M_n(R) against direct numerical integration over sigma^2 (up to the log-uniform constant)."""
    for n in (2, 3, 5, 20):
        for r in (0.05, 1.0, 7.3, 60.0):
            if isinstance(scale, InverseGammaScale):
                a, b = scale.alpha0, scale.beta0

                def f(s2):
                    return s2 ** (-n / 2) * math.exp(-r / (2 * s2)) * stats.invgamma.pdf(s2, a, scale=b)
            else:
                def f(s2):
                    return s2 ** (-n / 2) * math.exp(-r / (2 * s2)) / s2
            # integrate in log sigma^2 for robustness
            val, _ = integrate.quad(lambda t: f(math.exp(t)) * math.exp(t), math.log(1e-4) if isinstance(
                scale, LogUniformScale) else -30, math.log(1e4) if isinstance(scale, LogUniformScale) else 30,
                epsabs=0, epsrel=1e-12, limit=500)
            got = float(scale.log_marginal(n, np.array([r]))[0])
            assert abs(got - math.log(val)) <= 1e-8, (n, r, got, math.log(val))


def test_v2_inverse_gamma_predictive_given_a_is_student_t():
    st, y, _ = _contexts(5, 1.0, 20, 101)
    scale = InverseGammaScale(3.0, 2.0)
    a = np.linspace(-0.9, 0.9, 7)[None, :].repeat(st.size, 0)
    r = st.rss(a)
    resid = y[:, None] - a * st.last[:, None]
    got = scale.log_marginal(st.n + 1, r + resid**2) - scale.log_marginal(st.n, r) - 0.5 * math.log(2 * math.pi)
    alpha_n = 3.0 + st.n / 2
    beta_n = 2.0 + r / 2
    want = stats.t.logpdf(y[:, None], df=2 * alpha_n, loc=a * st.last[:, None], scale=np.sqrt(beta_n / alpha_n))
    assert np.max(np.abs(got - want)) <= 1e-10


def _grid_oracle(ref: UnknownScaleReference, ctx: np.ndarray, y: np.ndarray, na: int, ns: int) -> np.ndarray:
    """Brute-force p(y | D) on a dense (a, log sigma) grid with Simpson weights; prior densities from scipy."""
    rho = ref.coef.rho
    a = np.linspace(-rho, rho, na)
    if isinstance(ref.scale, InverseGammaScale):
        ls = np.linspace(math.log(0.05), math.log(20.0), ns)            # IG(3, 2) mass outside < 1e-12 (checked below)
        log_ps = stats.invgamma.logpdf(np.exp(2 * ls), ref.scale.alpha0, scale=ref.scale.beta0) + math.log(2) + 2 * ls
    else:
        ls = np.linspace(math.log(ref.scale.s_lo), math.log(ref.scale.s_hi), ns)
        log_ps = np.zeros(ns)                                            # uniform in log sigma
    if ref.coef.tau0 is None:
        log_pa = np.zeros(na)
    else:
        log_pa = stats.truncnorm.logpdf(a, (-rho - ref.coef.mu0) / ref.coef.tau0, (rho - ref.coef.mu0) / ref.coef.tau0,
                                        loc=ref.coef.mu0, scale=ref.coef.tau0)
    wa = integrate.simpson(np.eye(na), x=a)      # Simpson weights
    ws = integrate.simpson(np.eye(ns), x=ls)
    prev, curr = ctx[:-1], ctx[1:]
    rss = ((curr[None, :] - a[:, None] * prev[None, :]) ** 2).sum(axis=1)       # (na,)
    sig = np.exp(ls)
    n = prev.size
    loglik = -n * ls[None, :] - rss[:, None] / (2 * sig[None, :] ** 2)           # (na, ns), constants dropped
    logpost = loglik + log_pa[:, None] + log_ps[None, :] + np.log(wa)[:, None] + np.log(ws)[None, :]
    logpost -= np.logaddexp.reduce(logpost.ravel())
    out = []
    for yy in y:
        z = (yy - a[:, None] * ctx[-1]) / sig[None, :]
        out.append(np.logaddexp.reduce((logpost - 0.5 * z * z - ls[None, :] - 0.5 * math.log(2 * math.pi)).ravel()))
    return np.array(out)


@pytest.mark.parametrize("which", ["pop", "ctx"])
@pytest.mark.parametrize("n,r", [(2, 1.0), (3, 4.0), (20, 0.25)])
def test_v3_grid_oracle(which, n, r):
    ref = population_f1() if which == "pop" else context_only_f1()
    st, y_true, ctx = _contexts(n, r, 3, 202 + n)
    worst = 0.0
    for i in range(st.size):
        sub = F1Stats(st.n, st.sxx[i:i + 1], st.a_hat[i:i + 1], st.r_min[i:i + 1], st.last[i:i + 1])
        ys = y_true[i] + np.array([-2.0, -0.5, 0.0, 0.7, 2.5])
        got = ref.logpdf(sub, ys[None, :])[0]
        g1 = _grid_oracle(ref, ctx[i], ys, 4001, 1201)
        g2 = _grid_oracle(ref, ctx[i], ys, 8001, 2401)
        assert np.max(np.abs(g1 - g2)) <= 1e-6        # the oracle itself has converged
        worst = max(worst, float(np.max(np.abs(got - g2))))
    assert worst <= 1e-6, worst


@pytest.mark.parametrize("which", ["pop", "ctx"])
def test_v4_node_doubling_and_normalisation(which):
    """Node doubling on 40 contexts per (n, r) at five y values; normalisation by Simpson over
    the whole real line (substitution y = y_i + tan u, 3999 interior points), 4 contexts per (n, r).

    History: a first version integrated over y_i +/- 60 and found a mass deficit of 2.6e-4 for the context-only
    reference; integrating over the whole line showed the deficit was the window (heavy tails), not the density."""
    ref = population_f1() if which == "pop" else context_only_f1()
    fine = UnknownScaleReference(ref.coef, ref.scale, refine=2)
    worst, worst_mass = 0.0, 0.0
    for n, r in ((2, 4.0), (3, 1.0), (5, 0.25), (20, 1.0), (40, 4.0)):
        st, y, _ = _contexts(n, r, 40, 303 + n)
        ys = y[:, None] + np.array([-3.0, -1.0, 0.0, 1.0, 3.0])[None, :]
        worst = max(worst, float(np.max(np.abs(ref.logpdf(st, ys) - fine.logpdf(st, ys)))))
        sub = F1Stats(st.n, st.sxx[:4], st.a_hat[:4], st.r_min[:4], st.last[:4])
        # whole real line via y = y_i + tan(u): the context-only predictive has polynomial tails at small n
        # (scale-invariant sigma prior up to 100), so a finite window would miss mass of order 1e-4 (measured)
        u = np.linspace(-np.pi / 2, np.pi / 2, 4001)[1:-1]
        grid = y[:4, None] + np.tan(u)[None, :]
        mass = integrate.simpson(np.exp(ref.logpdf(sub, grid)) / np.cos(u)[None, :] ** 2, x=u, axis=1)
        worst_mass = max(worst_mass, float(np.max(np.abs(mass - 1.0))))
    assert worst <= 1e-6, worst
    assert worst_mass <= 1e-6, worst_mass


def test_v8_library_matches_brute_force():
    rng = np.random.default_rng(5)
    lib = ScaleLibrary(rng.uniform(-0.9, 0.9, 7), rng.uniform(0.5, 2.0, 7))
    st, y, ctx = _contexts(4, 1.0, 10, 404)
    got = lib.logpdf(st, y)
    for i in range(ctx.shape[0]):
        prev, curr = ctx[i, :-1], ctx[i, 1:]
        lw = np.array([stats.norm.logpdf(curr, a * prev, s).sum() for a, s in zip(lib.a, lib.sigma)])
        lw -= np.logaddexp.reduce(lw)
        want = np.logaddexp.reduce(lw + stats.norm.logpdf(y[i], lib.a * ctx[i, -1], lib.sigma))
        assert abs(got[i] - want) <= 1e-12


def test_v6_population_reference_is_optimal_on_population_systems():
    """F1-V6: E[LS(pop) - LS(other)] >= 0 on P_F1 systems (DERIVED: pop is Bayes there). One-sided z > -3.5 each
    (Bonferroni over 4 comparisons at about 1e-3). Fixed seed."""
    pop, ctx_only = population_f1(), context_only_f1()
    rng = np.random.default_rng(6)
    lib = ScaleLibrary(rng.uniform(0.0, 0.8, 4), rng.uniform(0.7, 1.4, 4))
    for n in (2, 10):
        st, y, _ = _contexts(n, 1.0, 4000, 505 + n)
        lp = pop.logpdf(st, y)
        for other in (ctx_only, lib):
            d = lp - other.logpdf(st, y)
            z = d.mean() / (d.std(ddof=1) / math.sqrt(d.size))
            assert z > -3.5, (n, type(other).__name__, z)


def test_v5_calibration_pit_of_population_reference():
    """F1-V5: PIT of the matched population reference is uniform on P_F1 systems (KS p >= 1e-3 per test; 4 tests).
    PIT from the closed-form Student-t mixture CDF; the CDF is checked against numerical integration of the density."""
    pop = population_f1()
    st, y, _ = _contexts(3, 1.0, 5, 600)
    grid = np.linspace(-60, 0, 6001)[None, :] + y[:, None]
    numeric = integrate.simpson(np.exp(pop.logpdf(st, grid)), x=grid, axis=1)
    assert np.max(np.abs(numeric - student_t_mixture_cdf(pop, st, y))) <= 1e-6
    for n, r in ((2, 1.0), (5, 4.0), (10, 0.25), (20, 1.0)):
        st, y, _ = _contexts(n, r, 3000, 606 + n)
        p = stats.kstest(student_t_mixture_cdf(pop, st, y), "uniform").pvalue
        assert p >= 1e-3, (n, r, p)


def test_v7_known_sigma_limit():
    """F1-V7: as alpha0 grows with beta0 = alpha0 (prior mean of sigma^2 near 1, sd -> 0), the F1 population
    reference converges to the known-sigma (sigma = 1) Stage 1A population reference."""
    st, y, ctx = _contexts(5, 1.0, 200, 707)
    known = population_prior(sigma=1.0).logpdf(ContextStats.from_contexts(ctx), y)
    errs = []
    for a0 in (1e3, 1e5, 1e7):
        ref = UnknownScaleReference(CoefficientPrior(0.95, 0.4, 0.3), InverseGammaScale(a0, a0 + 1.0))
        errs.append(float(np.max(np.abs(ref.logpdf(st, y) - known))))
    assert errs[0] > errs[1] > errs[2], errs
    assert errs[2] <= 1e-4, errs


def test_n1_is_refused():
    with pytest.raises(ValueError):
        F1Stats.from_contexts(np.array([[0.3, 0.5]]))


def test_log_gammaincc_asymptotic_branch_matches_direct():
    from scipy import special
    from dynaicl_families import ar1_unknown_sigma as m
    for s in (0.5, 1.0, 2.5, 10.5, 20.5):
        u = np.array([150.0, 300.0, 600.0])
        direct = np.log(special.gammaincc(s, u))
        term, total = np.ones_like(u), np.ones_like(u)
        for k in range(1, m.ASYMPTOTIC_TERMS + 1):
            term = term * (s - k) / u
            total = total + term
        asym = (s - 1.0) * np.log(u) - u - special.gammaln(s) + np.log(total)
        assert np.max(np.abs(asym - direct)) <= 1e-12 * np.max(np.abs(direct)), (s, asym - direct)
    # far tail is finite and decreasing (direct value underflows there)
    far = m.log_gammaincc(3.0, np.array([800.0, 1e4, 1e8]))
    assert np.all(np.isfinite(far)) and far[0] > far[1] > far[2]
