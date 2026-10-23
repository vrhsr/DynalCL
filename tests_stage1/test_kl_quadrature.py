"""KL quadrature: closed-form Gaussian oracle, node doubling, mass, and the Rao-Blackwell identity (held-out)."""

from __future__ import annotations

import numpy as np

from dynaicl.rng import NamedStreams
from dynaicl.systems.conditions import ContinuousPriorCondition, InitialStateSpec
from dynaicl.systems.priors import StableCoefficientPrior
from dynaicl_families.ar1_known_sigma import ContextStats, FiniteLibrary, population_prior, stability_prior
from dynaicl_families.kl import gaussian_kl, kl_quadrature
from dynaicl_families.sampling import contexts_and_targets, simulate
from dynaicl_families.separability import reference_window

POP_FROZEN = StableCoefficientPrior(rho=0.95, sigma=1.0, shape="truncated_normal", mu0=0.4, tau0=0.3)


def _gauss_logpdf(m, s):
    def f(idx, y):
        mm, ss = m[idx][:, None], s[idx][:, None]
        return -0.5 * ((y - mm) / ss) ** 2 - np.log(ss) - 0.5 * np.log(2 * np.pi)
    return f


def test_gaussian_closed_form():
    rng = np.random.default_rng(3)
    m1, m2 = rng.normal(0, 3, 200), rng.normal(0, 3, 200)
    s1, s2 = rng.uniform(1, 4, 200), rng.uniform(1, 4, 200)
    kl, mass = kl_quadrature(_gauss_logpdf(m1, s1), _gauss_logpdf(m2, s2), m1 - 12 * s1, m1 + 12 * s1, panel_width=0.5)
    assert np.max(np.abs(kl - gaussian_kl(m1, s1, m2, s2))) <= 1e-10
    assert np.max(np.abs(mass - 1.0)) <= 1e-12


def _heldout_stats(n, r, n_items, seed):
    cond = ContinuousPriorCondition(POP_FROZEN, InitialStateSpec(0.0, r))
    split = simulate(cond, NamedStreams(seed), n_items, n + 2)
    ctx, y = contexts_and_targets(split, n)
    return ContextStats.from_contexts(ctx), y


def _logfn(ref, st):
    def f(idx, yy):
        sub = ContextStats(st.sxx[idx], st.sxy[idx], st.last[idx])
        return ref.logpdf(sub, yy)
    return f


def test_node_doubling_and_mass_for_reference_pairs():
    lib = FiniteLibrary(np.array([0.1, 0.45, 0.8]))
    worst_doubling, worst_mass = 0.0, 0.0
    for n, r in ((1, 4.0), (2, 1.0), (10, 0.25)):
        st, _ = _heldout_stats(n, r, 400, 4242 + n)
        for p, q in ((population_prior(), stability_prior()), (population_prior(), lib), (lib, population_prior()),
                     (stability_prior(), lib)):
            lo, hi = reference_window(p, st)
            k1, m1 = kl_quadrature(_logfn(p, st), _logfn(q, st), lo, hi, panel_width=0.5)
            k2, m2 = kl_quadrature(_logfn(p, st), _logfn(q, st), lo, hi, panel_width=0.25)
            worst_doubling = max(worst_doubling, float(np.max(np.abs(k1 - k2))))
            worst_mass = max(worst_mass, float(np.max(np.abs(m1 - 1.0))), float(np.max(np.abs(m2 - 1.0))))
            assert np.all(k1 >= -1e-12)
    assert worst_doubling <= 1e-8, worst_doubling
    assert worst_mass <= 1e-9, worst_mass


def test_window_holds_mass_when_posterior_is_pinned_at_the_support_edge():
    """Mildly explosive contexts (a = 1.05, n = 40) put the population posterior kernel more than 10 sd beyond
    rho = 0.95 for 8 of these 50 seeded contexts, which exercises the pinned window branch.

    History: a first version asserted that ALL contexts were pinned (false: wrong precondition). A second used
    a = 1.2, where |x_n| reaches about 6000 and float64 cancellation in the density itself limits the mass check to
    about 1.5e-9 (finer panels and a wider window did not change it, and the frozen quadrature reference differs from
    the closed form by 2e-9 there). That regime is outside the map (|a| <= 0.999 there; mass error about 2e-14)."""
    rng = np.random.default_rng(11)
    ctx = []
    for _ in range(50):
        x = np.empty(41)
        x[0] = rng.normal()
        for t in range(1, 41):
            x[t] = 1.05 * x[t - 1] + rng.normal()
        ctx.append(x)
    st = ContextStats.from_contexts(np.stack(ctx))
    pop, stab = population_prior(), stability_prior()
    m, s = pop.posterior(st)
    assert int(np.sum(m - 10 * s > pop.rho)) >= 5    # the pinned branch is exercised
    lo, hi = reference_window(pop, st)
    k1, m1 = kl_quadrature(_logfn(pop, st), _logfn(stab, st), lo, hi, panel_width=0.5)
    k2, m2 = kl_quadrature(_logfn(pop, st), _logfn(stab, st), lo, hi, panel_width=0.25)
    assert np.max(np.abs(m1 - 1.0)) <= 1e-9 and np.max(np.abs(m2 - 1.0)) <= 1e-9
    assert np.max(np.abs(k1 - k2)) <= 1e-8


def test_rao_blackwell_equals_realized_score_gap_in_expectation():
    """On held-out systems y | context ~ pop exactly, so E[KL(pop || stab)] = E[log pop(y) - log stab(y)] (DERIVED).
    Fixed seed; 4-SE tolerance (two-sided p about 6e-5 under correct code)."""
    pop, stab = population_prior(), stability_prior()
    for n, r in ((1, 1.0), (3, 0.25)):
        st, y = _heldout_stats(n, r, 20000, 5150 + n)
        lo, hi = reference_window(pop, st)
        kl, _ = kl_quadrature(_logfn(pop, st), _logfn(stab, st), lo, hi, panel_width=0.5)
        d = pop.logpdf(st, y) - stab.logpdf(st, y)
        diff = d - kl                       # paired: removes most context-level variance
        z = diff.mean() / (diff.std(ddof=1) / np.sqrt(diff.size))
        assert abs(z) <= 4.0, (n, r, z, kl.mean(), d.mean())


def test_window_mode_just_outside_support_audit_a5():
    """Audit finding A5: stab with context (0.1, 10.0899) has its kernel mode 9.99 sd above 0.999 (neither interior nor
    pinned); the window previously held 0.838 of the mass. It must now hold all of it (the run-time check enforces 1e-8)."""
    st = ContextStats.from_contexts(np.array([[0.1, 10.0899]]))
    stab = stability_prior()
    m, s = stab.posterior(st)
    assert 9.9 < float((m[0] - stab.rho) / s[0]) < 10.0
    lo, hi = reference_window(stab, st)
    _, mass = kl_quadrature(_logfn(stab, st), _logfn(population_prior(), st), lo, hi, panel_width=0.25)
    assert abs(float(mass[0]) - 1.0) <= 1e-9
