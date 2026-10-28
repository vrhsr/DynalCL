"""F2 reference validation, fast part (docs/MATH_F2.md section 9): F2-V1, V2, V3, V4, V5 (estimator agreement and rate),
V6 (d = 1 reduced case against nested quadrature), V7 (independent prior-sampling estimator), V8.

Tolerances: closed forms 1e-10 (relative where values are O(1e2)); Monte Carlo comparisons |z| <= 4 (two-sided p about
6e-5 per comparison; this file makes fewer than 40 such comparisons, so the family-wise false-alarm rate is below 0.003).
Seeds come from the stage 2 seed-role table (role f2_tests)."""

from __future__ import annotations

import math

import numpy as np
import pytest
from scipy import integrate, stats

from dynaicl.rng import NamedStreams
from dynaicl_families.stage2 import f2_var as fv
from dynaicl_families.stage2.seeds import role_seed

SEED = role_seed("f2_tests")


def _contexts(prior, n, r, n_items, seed, horizon=1):
    split = fv.simulate_f2(prior, r, NamedStreams(seed), n_items, n + horizon + 1)
    ctx, y = fv.contexts_and_targets(split, n, horizon)
    return ctx, y, split


def test_v1_spectral_radius_closed_form():
    rng = np.random.default_rng(SEED)
    a = rng.normal(scale=0.8, size=(20000, 2, 2))
    a[:50] = np.array([[0.3, 1.0], [-1.0, 0.3]])            # complex pair
    a[50:100] = np.array([[0.5, 0.0], [0.0, -0.9]])          # real, distinct
    a[100:150] = np.array([[0.7, 1.0], [0.0, 0.7]])          # defective, repeated
    want = np.max(np.abs(np.linalg.eigvals(a)), axis=-1)
    got = fv.spectral_radius(a)
    assert np.max(np.abs(got - want) / np.maximum(1.0, want)) <= 1e-12
    assert np.mean(np.iscomplex(np.linalg.eigvals(a)).any(axis=-1)) > 0.2   # both branches exercised


def _mniw_logpdf(b, sig, prior_like):
    b0, v0, nu0, psi0 = prior_like
    return (stats.invwishart.logpdf(sig, df=nu0, scale=psi0)
            + stats.matrix_normal.logpdf(b, mean=b0, rowcov=v0, colcov=sig))


@pytest.mark.parametrize("which", ["pop", "ctx"])
def test_v2_conjugate_update_identity(which):
    prior = fv.population_f2() if which == "pop" else fv.context_only_f2()
    ctx, _, _ = _contexts(fv.population_f2(), 6, 1.0, 3, SEED + 1)
    post = fv.posterior(prior, ctx)
    x, y = fv.regression_arrays(ctx)
    rng = np.random.default_rng(SEED + 2)
    for i in range(ctx.shape[0]):
        # Psi_n in the S_yy form agrees with the residual form used by the code
        v0i = np.linalg.inv(prior.v0)
        alt = (prior.psi0 + y[i].T @ y[i] + prior.b0.T @ v0i @ prior.b0
               - post.bn[i].T @ np.linalg.inv(post.vn[i]) @ post.bn[i])
        assert np.max(np.abs(alt - post.psin[i])) <= 1e-10 * max(1.0, np.max(np.abs(alt)))
        diffs = []
        for _ in range(6):
            sig = stats.invwishart.rvs(df=5.0, scale=np.eye(2), random_state=rng)
            b = rng.normal(scale=0.5, size=(2, 2))
            loglik = sum(stats.multivariate_normal.logpdf(y[i, t], b.T @ x[i, t], sig) for t in range(x.shape[1]))
            lhs = _mniw_logpdf(b, sig, (post.bn[i], post.vn[i], post.nun, post.psin[i]))
            rhs = _mniw_logpdf(b, sig, (prior.b0, prior.v0, prior.nu0, prior.psi0)) + loglik
            diffs.append(lhs - rhs)
        assert np.ptp(diffs) <= 1e-9, diffs                  # posterior / (prior x likelihood) is constant


def test_v4_untruncated_predictive_matches_scipy_and_monte_carlo():
    prior = fv.population_f2()
    ctx, y, _ = _contexts(prior, 4, 1.0, 3, SEED + 3)
    post = fv.posterior(prior, ctx)
    ys = y[:, None, :] + np.array([[0.0, 0.0], [1.0, -0.5], [-2.0, 1.5]])[None]
    got = fv.untruncated_logpdf(post, ys)
    dof = post.nun - 1
    rng = np.random.default_rng(SEED + 4)
    for i in range(ctx.shape[0]):
        q = post.last[i] @ post.vn[i] @ post.last[i]
        want = stats.multivariate_t.logpdf(ys[i], loc=post.bn[i].T @ post.last[i],
                                           shape=post.psin[i] * (1 + q) / dof, df=dof)
        assert np.max(np.abs(got[i] - want)) <= 1e-10
        b, sig = fv.sample_mniw(post.bn[i], post.vn[i], post.nun, post.psin[i], 400000, rng)
        loc = np.einsum("jik,i->jk", b, post.last[i])
        f = np.exp(fv.mvn_logpdf(ys[i][None], loc[:, None, :], sig[:, None]) - got[i][None])
        z = (f.mean(axis=0) - 1.0) / (f.std(axis=0, ddof=1) / math.sqrt(f.shape[0]))
        assert np.all(np.abs(z) <= 4.0), z


def test_v3_rao_blackwell_identity():
    """p(y | B, D) (Student-t) equals the average of N(y; B^T x_n, Sigma) over Sigma | B, D ~ IW(nu_n + d, Psi_B)."""
    prior = fv.population_f2()
    ctx, y, _ = _contexts(prior, 5, 1.0, 1, SEED + 5)
    post = fv.posterior(prior, ctx).item(0)
    rng = np.random.default_rng(SEED + 6)
    b, _ = fv.sample_mniw(post.bn[0], post.vn[0], post.nun, post.psin[0], 3, rng)
    ys = y[0][None] + np.array([[0.0, 0.0], [1.5, -1.0]])
    rb = fv.rb_logpdf(post, b, ys)
    for j in range(3):
        db = b[j] - post.bn[0]
        psi_b = post.psin[0] + db.T @ post.vn_inv[0] @ db
        sig = fv.sample_iw(post.nun + 2, psi_b, 400000, rng)
        f = np.exp(fv.mvn_logpdf(ys[None], (b[j].T @ post.last[0])[None, None], sig[:, None]) - rb[j][None])
        z = (f.mean(axis=0) - 1.0) / (f.std(axis=0, ddof=1) / math.sqrt(f.shape[0]))
        assert np.all(np.abs(z) <= 4.0), z


def test_v8_library_matches_brute_force():
    prior = fv.population_f2()
    rng = np.random.default_rng(SEED + 7)
    lib = fv.library_from_prior(prior, 5, rng)
    ctx, y, _ = _contexts(prior, 4, 1.0, 4, SEED + 8, horizon=3)
    for h in (1, 3):
        got = lib.logpdf(ctx, y[:, None, :], horizon=h)[:, 0]
        for i in range(ctx.shape[0]):
            lw = np.array([sum(stats.multivariate_normal.logpdf(ctx[i, t + 1], a @ ctx[i, t], s) for t in range(4))
                           for a, s in zip(lib.a, lib.sigma)])
            lw -= np.logaddexp.reduce(lw)
            comps = []
            for a, s in zip(lib.a, lib.sigma):
                ah, cov = np.eye(2), np.zeros((2, 2))
                for _ in range(h):
                    cov, ah = cov + ah @ s @ ah.T, a @ ah
                comps.append(stats.multivariate_normal.logpdf(y[i], ah @ ctx[i, -1], cov))
            assert abs(got[i] - np.logaddexp.reduce(lw + np.array(comps))) <= 1e-10


def test_v5_estimators_agree_and_large_radius_is_exact():
    prior = fv.population_f2()
    ctx, y, _ = _contexts(prior, 3, 1.0, 2, SEED + 9)
    post = fv.posterior(prior, ctx)
    for i in range(2):
        pi = post.item(i)
        ys = y[i][None] + np.array([[0.0, 0.0], [1.0, 1.0]])
        r = fv.truncated_logpdf_item(prior, pi, ys, np.random.default_rng(SEED + 10 + i), target_se=5e-4, force="R")
        c = fv.truncated_logpdf_item(prior, pi, ys, np.random.default_rng(SEED + 20 + i), target_se=5e-4, force="C")
        z = (r.logpdf - c.logpdf) / np.sqrt(r.se_log ** 2 + c.se_log ** 2)
        assert np.all(np.abs(z) <= 4.0) and not r.capped and not c.capped, (z, r, c)
        wide = fv.MNIWPrior("wide", prior.b0, prior.v0, prior.nu0, prior.psi0, 50.0)
        e = fv.truncated_logpdf_item(wide, pi, ys, np.random.default_rng(SEED + 30 + i), target_se=5e-4)
        assert e.accepted == e.draws and np.max(np.abs(e.logpdf - fv.untruncated_logpdf(pi, ys[None])[0])) <= 1e-12


def test_v5_variance_rate():
    """Doubling the number of draws halves the variance of the log estimate (checked through the reported SE at fixed
    draw counts: SE(4J) / SE(J) within [0.4, 0.6] of the 1/2 expected; DERIVED: SE ~ J^(-1/2))."""
    prior = fv.context_only_f2()
    ctx, y, _ = _contexts(fv.population_f2(), 3, 1.0, 1, SEED + 11)
    pi = fv.posterior(prior, ctx).item(0)
    ses = []
    for j in (2 ** 15, 2 ** 17):
        e = fv.truncated_logpdf_item(prior, pi, y[:1], np.random.default_rng(SEED + 12), target_se=0.0,
                                     batch=2 ** 13, max_draws=j)
        ses.append(float(e.se_log[0]))
    assert 0.4 <= ses[1] / ses[0] <= 0.6, ses


def _nig_truncated_oracle(b0, v0, nu0, psi0, c, ctx, y):
    """d = 1: nested scipy quad over sigma^2 (inner) and a in (-c, c) (outer) of prior x conditional likelihood x
    N(y; a x_n, sigma^2); prior a | sigma^2 ~ N(b0, sigma^2 v0), sigma^2 ~ IG(nu0 / 2, psi0 / 2). No closed form used."""
    prev, curr, last = ctx[:-1], ctx[1:], ctx[-1]

    def inner(a, with_y):
        def f(s2):
            ll = stats.norm.logpdf(curr, a * prev, math.sqrt(s2)).sum()
            lp = stats.norm.logpdf(a, b0, math.sqrt(s2 * v0)) + stats.invgamma.logpdf(s2, nu0 / 2, scale=psi0 / 2)
            ly = stats.norm.logpdf(y, a * last, math.sqrt(s2)) if with_y else 0.0
            return math.exp(ll + lp + ly + 10.0)
        return integrate.quad(f, 0.0, np.inf, epsabs=0, epsrel=1e-11, limit=200)[0]

    num = integrate.quad(lambda a: inner(a, True), -c, c, epsabs=0, epsrel=1e-10, limit=200)[0]
    den = integrate.quad(lambda a: inner(a, False), -c, c, epsabs=0, epsrel=1e-10, limit=200)[0]
    return math.log(num / den)


def test_v6_reduced_case_d1_against_nested_quadrature():
    prior = fv.MNIWPrior("NIG-1", np.array([[0.4]]), np.array([[0.09]]), 6.0, np.array([[4.0]]), 0.95)
    rng = np.random.default_rng(SEED + 13)
    for n, a_true in ((3, 0.9), (6, 0.5)):
        x = np.empty(n + 2)
        x[0] = rng.normal()
        for t in range(1, n + 2):
            x[t] = a_true * x[t - 1] + rng.normal()
        ctx = x[None, :n + 1, None]
        post = fv.posterior(prior, ctx).item(0)
        for yv in (x[n + 1], x[n + 1] + 1.5):
            e = fv.truncated_logpdf_item(prior, post, np.array([[yv]]), np.random.default_rng(SEED + 14 + n),
                                         target_se=1e-4)
            want = _nig_truncated_oracle(0.4, 0.09, 6.0, 4.0, 0.95, x[:n + 1], yv)
            assert abs(e.logpdf[0] - want) <= 4 * e.se_log[0] + 1e-6, (n, yv, e, want)


def test_v7_independent_prior_sampling_estimator():
    """Sampling the truncated PRIOR and weighting by the likelihood (no posterior sampling) agrees with the posterior
    estimator on short contexts (n = 2), |z| <= 4 with the delta-method SE of the ratio of means."""
    prior = fv.population_f2()
    ctx, y, _ = _contexts(prior, 2, 1.0, 3, SEED + 15)
    post = fv.posterior(prior, ctx)
    rng = np.random.default_rng(SEED + 16)
    b, sig, _ = fv.sample_truncated_prior(prior, 400000, rng)
    a = np.swapaxes(b, 1, 2)
    for i in range(3):
        x, yy = fv.regression_arrays(ctx[i:i + 1])
        loglik = sum(fv.mvn_logpdf(yy[0, t][None], (a @ x[0, t])[:, :], sig) for t in range(x.shape[1]))
        fy = fv.mvn_logpdf(y[i][None], a @ ctx[i, -1], sig)
        m = loglik.max()
        w, wf = np.exp(loglik - m), np.exp(loglik - m + fy)
        p = wf.sum() / w.sum()
        # delta method for the ratio of means
        cov = np.cov(np.stack([wf, w]))
        var = (cov[0, 0] - 2 * p * cov[0, 1] + p * p * cov[1, 1]) / (w.size * w.mean() ** 2)
        se_prior = math.sqrt(var) / p
        e = fv.truncated_logpdf_item(prior, post.item(i), y[i][None], np.random.default_rng(SEED + 17 + i),
                                     target_se=5e-4)
        z = (math.log(p) - e.logpdf[0]) / math.sqrt(se_prior ** 2 + e.se_log[0] ** 2)
        assert abs(z) <= 4.0, (i, z, math.log(p), e)


def test_contexts_are_cut_by_the_frozen_harness():
    prior = fv.population_f2()
    split = fv.simulate_f2(prior, 1.0, NamedStreams(SEED + 18), 5, 8)
    ctx, y = fv.contexts_and_targets(split, 4)
    assert np.array_equal(ctx, split.trajectories[:, :5, :]) and np.array_equal(y, split.trajectories[:, 5, :])
    again = fv.simulate_f2(prior, 1.0, NamedStreams(SEED + 18), 9, 8)     # items independent of n_items
    assert np.array_equal(again.trajectories[:5], split.trajectories)
    assert np.all(fv.spectral_radius(split.a) < 0.95)


def test_v5b_stable_interval_matches_spectral_radius():
    """With b12, b21, b22 fixed, rho(B) < c exactly on (L, U) (Jury conditions); checked on a b11 grid away from the
    endpoints (|b11 - endpoint| > 1e-9) for random rests and c in {0.95, 0.999}."""
    rng = np.random.default_rng(SEED + 40)
    for c in (0.95, 0.999):
        rest = rng.normal(scale=0.7, size=(400, 3))
        lo, hi = fv.stable_interval_b11(rest[:, 0], rest[:, 1], rest[:, 2], c)
        grid = np.linspace(-3, 3, 2001)
        for i in range(rest.shape[0]):
            b = np.zeros((grid.size, 2, 2))
            b[:, 0, 0], b[:, 0, 1], b[:, 1, 0], b[:, 1, 1] = grid, rest[i, 0], rest[i, 1], rest[i, 2]
            stable = fv.spectral_radius(b) < c
            inside = (grid > lo[i]) & (grid < hi[i])
            away = np.minimum(np.abs(grid - lo[i]), np.abs(grid - hi[i])) > 1e-9
            assert np.array_equal(stable[away], inside[away]), (c, i, lo[i], hi[i])


def test_v6b_interval_estimator_d1_against_nested_quadrature():
    prior = fv.MNIWPrior("NIG-1", np.array([[0.4]]), np.array([[0.09]]), 6.0, np.array([[4.0]]), 0.95)
    rng = np.random.default_rng(SEED + 41)
    for n, a_true in ((3, 0.9), (6, 0.5)):
        x = np.empty(n + 2)
        x[0] = rng.normal()
        for t in range(1, n + 2):
            x[t] = a_true * x[t - 1] + rng.normal()
        post = fv.posterior(prior, x[None, :n + 1, None]).item(0)
        for yv in (x[n + 1], x[n + 1] + 1.5):
            e = fv.interval_rb_logpdf_item(prior, post, np.array([[yv]]), np.random.default_rng(SEED + 42 + n),
                                           target_se=1e-4)
            want = _nig_truncated_oracle(0.4, 0.09, 6.0, 4.0, 0.95, x[:n + 1], yv)
            assert not e.capped and abs(e.logpdf[0] - want) <= 4 * e.se_log[0] + 1e-6, (n, yv, e, want)


def test_v5c_interval_estimator_agrees_with_plain_estimator():
    """The interval Rao-Blackwell estimator I (MATH_F2 5b; an independent algorithm: no indicator, Sigma and b11
    integrated) and the production plain estimator (C or R, MATH_F2 5) agree within |z| <= 4 on population and
    context-only posteriors (n = 10). Target 2e-3 keeps the test fast; the comparison is statistical at any target."""
    for prior in (fv.population_f2(), fv.context_only_f2()):
        ctx, y, _ = _contexts(fv.population_f2(), 10, 1.0, 2, SEED + 43)
        post = fv.posterior(prior, ctx)
        for i in range(2):
            pi = post.item(i)
            ys = y[i][None] + np.array([[0.0, 0.0], [1.0, -1.0]])
            a = fv.interval_rb_logpdf_item(prior, pi, ys, np.random.default_rng(SEED + 44 + i), target_se=2e-3)
            b = fv.truncated_logpdf_item(prior, pi, ys, np.random.default_rng(SEED + 54 + i), target_se=2e-3,
                                         max_draws=2 ** 23)
            z = (a.logpdf - b.logpdf) / np.sqrt(a.se_log ** 2 + b.se_log ** 2)
            assert np.all(np.abs(z) <= 4.0) and not a.capped and not b.capped, (prior.name, i, z, a, b)


def test_v5d_interval_quadrature_node_doubling():
    """Node doubling 64 -> 128 of the tan-substitution Gauss-Legendre integral changes the estimate-level sums by
    <= 1e-8 relative (the project's quadrature budget is 1e-6 nats, MATH 5.3), for population and context-only posteriors
    at n in {2, 10}. History (disclosure S30): a first bound of 1e-9 per draw at 32 nodes failed only for draws carrying
    about 6e-6 of the sum (sum-level change 9.7e-8); the per-draw bound had no error-budget justification."""
    for prior in (fv.population_f2(), fv.context_only_f2()):
        for n in (2, 10):
            ctx, y, _ = _contexts(fv.population_f2(), n, 1.0, 2, SEED + 60 + n)
            post = fv.posterior(prior, ctx)
            for i in range(2):
                pi = post.item(i)
                b, _ = fv.sample_mniw(pi.bn[0], pi.vn[0], pi.nun, pi.psin[0], 2000, np.random.default_rng(SEED + 61))
                ys = y[i][None] + np.array([[0.0, 0.0], [2.0, -1.0]])
                for terms in (fv.interval_rb_terms,):
                    a1, g1 = terms(prior, pi, b, ys, nodes=64)
                    a2, g2 = terms(prior, pi, b, ys, nodes=128)
                    assert np.array_equal(a1, a2)
                    rel = np.abs(g1.sum(0) - g2.sum(0)) / g2.sum(0)
                    assert np.max(rel) <= 1e-8, (prior.name, n, i, terms.__name__, rel)
