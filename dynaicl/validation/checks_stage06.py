"""Stage 0.6 validation checks (Phase B). Each returns a CheckResult carrying pass/fail plus NUMERICAL diagnostics only.
Checks that compute gains (Tier-1 regression, optimality) report errors and violation counts, never effect sizes.

Seeds: the dedicated validation streams 61001-61099 (see config/stage06_seed_manifest.yaml). They are disjoint from the
pilot (62xxx), selection (63xxx), Stage 0.5 and confirmatory (64xxx) streams. The exception is check V4, which
regenerates the stored Stage 0.5 items from the Stage 0.5 seeds, as the Tier-1 regression requires.

The reference and the harness are reached through module attributes (``kq.``, ``nh.``), so the mutations take effect.
"""

from __future__ import annotations

import csv
import math
from pathlib import Path

import numpy as np
from scipy import integrate, stats

from dynaicl.baselines.family import build_context_only_family
from dynaicl.evaluation import noisy_harness as nh
from dynaicl.metrics import calibration, scoring
from dynaicl.references import kalman_quadrature as kq
from dynaicl.references.matched import assert_matched
from dynaicl.references.quadrature import StablePriorQuadraturePredictor
from dynaicl.rng import NamedStreams
from dynaicl.systems.context import ContextWindow, GroundTruth
from dynaicl.systems.noisy import NoisyObservationCondition, NoisyObservationModel, generate_noisy_split
from dynaicl.systems.priors import StableCoefficientPrior
from dynaicl.systems.splits import DataSplit, SplitRole, generate_split
from dynaicl.validation import noisy_oracles as O
from dynaicl.validation.checks import CheckResult

FLOAT = np.float64
EPS = np.finfo(float).eps
POP_PRIOR = StableCoefficientPrior(rho=0.95, sigma=1.0, shape="truncated_normal", mu0=0.4, tau0=0.3)
STAB_PRIOR = StableCoefficientPrior(rho=0.999, sigma=1.0, shape="uniform")
QS = (0.0, 0.755, 2.56, 6.5)
RS = (0.25, 1.0, 4.0)
SETTINGS = kq.KalmanQuadratureSettings()
ERROR_BUDGET = 2e-4          # max numerical error in a per-forecast paired gain (delta/100; MATH_STAGE06 section 6)
FAMILY_ALPHA = 1e-3
ROOT = Path(__file__).resolve().parents[2]


def model_for(q: float, r: float) -> NoisyObservationModel:
    return NoisyObservationModel(1.0, math.sqrt(q), r)


def simulate(a: float, model: NoisyObservationModel, length: int, rng: np.random.Generator):
    x = np.empty(length + 1)
    x[0] = model.x0_sd * rng.standard_normal()
    for t in range(1, length + 1):
        x[t] = a * x[t - 1] + model.sigma_w * rng.standard_normal()
    return x, x + model.sigma_v * rng.standard_normal(length + 1)


def primary_pair(model, settings=SETTINGS):
    return kq.noisy_population_reference(POP_PRIOR, model, settings), kq.noise_aware_stability_predictor(model, 0.999, settings)


# ============================================================= V1-V2: Kalman vs joint-Gaussian; target variance


def check_kalman_vs_cholesky(seed: int = 61001) -> CheckResult:
    """Fixed a: Kalman log-likelihood and h-step predictive moments (observed AND latent target) vs Cholesky
    conditioning on the explicitly built joint covariance. Tolerance per quantity: 50 eps kappa(Sigma) x max(1, |value|),
    the standard first-order perturbation bound for an SPD solve with condition number kappa."""
    rng = np.random.default_rng(seed)
    worst, n_cmp, ok = 0.0, 0, True
    for q in QS:
        for r in RS:
            model = model_for(q, r)
            for n in (0, 1, 2, 5, 20, 40):
                for a in (-0.9, 0.0, 0.4, 0.94, 0.998):
                    _, y = simulate(a, model, n, rng)
                    f = kq.kalman_filter_on_nodes(y[None, :], np.array([a]), model, (n,))
                    kappa = np.linalg.cond(O.joint_covariance(a, list(range(n + 6)), 1.0, model.sigma_v, r))
                    tol_rel = max(1e-12, 50 * EPS * kappa)
                    ll_c = O.cholesky_loglik(y, a, 1.0, model.sigma_v, r)
                    cmp = [(float(f["loglik"][n][0, 0]), ll_c)]
                    for h in (1, 5):
                        mo, vo = kq.observation_predictive_moments(np.array([a]), f["m"][n][0], f["P"][n], model, h)
                        ml, vl = kq.latent_predictive_moments(np.array([a]), f["m"][n][0], f["P"][n], model, h)
                        _, mc, vc = O.cholesky_predictive(y, a, h, 1.0, model.sigma_v, r, target_observed=True)
                        _, mcl, vcl = O.cholesky_predictive(y, a, h, 1.0, model.sigma_v, r, target_observed=False)
                        cmp += [(float(mo[0]), mc), (float(vo[0]), vc), (float(ml[0]), mcl), (float(vl[0]), vcl)]
                    for v, c in cmp:
                        err = abs(v - c) / max(1.0, abs(c))
                        worst = max(worst, err / tol_rel)
                        ok &= err <= tol_rel
                        n_cmp += 1
    return CheckResult("V1_kalman_vs_cholesky", ok, {"n_comparisons": n_cmp, "worst_err_over_tol": worst})


def check_target_noise_variance(seed: int = 61002) -> CheckResult:
    """The observed-target predictive variance exceeds the latent-target variance by exactly sigma_v^2 (rounding
    tolerance 8 eps x variance), in the production function and in the Cholesky oracle."""
    rng = np.random.default_rng(seed)
    ok, worst = True, 0.0
    for q in QS[1:]:
        model = model_for(q, 1.0)
        a = rng.uniform(-0.99, 0.99, 50)
        m, P = rng.normal(size=50), rng.uniform(0.1, 3, 50)
        for h in (1, 5):
            _, vo = kq.observation_predictive_moments(a, m, P, model, h)
            _, vl = kq.latent_predictive_moments(a, m, P, model, h)
            d = np.abs((vo - vl) - model.sigma_v ** 2) / (8 * EPS * vo)
            worst = max(worst, float(d.max()))
            ok &= bool(np.all(d <= 1.0))
        _, y = simulate(0.5, model, 10, rng)
        _, _, vc = O.cholesky_predictive(y, 0.5, 1, 1.0, model.sigma_v, 1.0, True)
        _, _, vcl = O.cholesky_predictive(y, 0.5, 1, 1.0, model.sigma_v, 1.0, False)
        ok &= abs((vc - vcl) - model.sigma_v ** 2) <= 1e-10 * vc
    return CheckResult("V2_target_noise_variance", ok, {"worst_err_over_tol": worst})


# ======================================================== V3-V5: zero-noise recovery (path, Tier-1, continuity)


def _quad_err(build, ctx, h, ys):
    p1, p2 = build(SETTINGS).predict(ctx, h), build(SETTINGS.refined(2)).predict(ctx, h)
    return float(max(np.max(np.abs(p1.logpdf(ys) - p2.logpdf(ys))), np.max(np.abs(p1.cdf(ys) - p2.cdf(ys)))))


def check_zero_noise_matches_stage05_path(seed: int = 61003) -> CheckResult:
    """q = 0: the Kalman reference and comparator vs the validated Stage 0.5 code path (StablePriorQuadraturePredictor,
    conditioning on x_0) on the same contexts. Tolerance: 10 x (node-doubling error of the Kalman path) + 1e-11 x max(1, |value|)."""
    rng = np.random.default_rng(seed)
    ok, worst, n_cmp = True, 0.0, 0
    for r in RS:
        model = model_for(0.0, r)
        for prior, s05 in ((POP_PRIOR, StablePriorQuadraturePredictor(POP_PRIOR)),
                           (STAB_PRIOR, StablePriorQuadraturePredictor(STAB_PRIOR))):
            def build(s, prior=prior, model=model):
                return kq.NoisyObservationBayesPredictor(prior, model, s, kq.noise_aware_stability_predictor(model).description)
            for n in (1, 2, 5, 10, 20, 40):
                a = float(prior.sample_systems(rng, 1)[0][0])
                x, _ = simulate(a, model, n, rng)
                ctx = ContextWindow(x)
                for h in (1, 5):
                    ref = s05.predict(ctx, h)
                    ys = ref.quantile(np.array([0.01, 0.25, 0.5, 0.75, 0.99]))
                    kal = build(SETTINGS).predict(ctx, h)
                    qerr = _quad_err(build, ctx, h, ys)
                    for v, c in list(zip(kal.logpdf(ys), ref.logpdf(ys))) + list(zip(kal.cdf(ys), ref.cdf(ys))):
                        tol = 10 * qerr + 1e-11 * max(1.0, abs(c))
                        worst = max(worst, abs(v - c) / tol)
                        ok &= abs(v - c) <= tol
                        n_cmp += 1
    return CheckResult("V3_zero_noise_matches_stage05_path", ok, {"n_comparisons": n_cmp, "worst_err_over_tol": worst})


STAGE05_RUN = ROOT / "runs" / "20261010T053729455237Z_stage05_population_advantage_51c7621b7a"
TIER1_TOL = 1e-9   # per item, nats; << ERROR_BUDGET. Fixed before running (validation report).


def check_tier1_regression_stage05(run_dir: Path = STAGE05_RUN, n_items: int = 3378) -> CheckResult:
    """Tier-1: the Kalman path at sigma_v = 0, on the Stage 0.5 seeds (evaluation roots 52101, 52102; E-CONT; r, n, h as
    in Stage 0.5), reproduces the STORED Stage 0.5 per-item primary contrast (matched - frontier_ctx; the frontier was
    stability-only in all cells, VERIFIED). Contexts and targets go through the Stage 0.6 harness. Reports only
    the maximum absolute difference and the item count (no effect sizes)."""
    arr = np.load(run_dir / "results" / "item_contrasts.npy")
    if not 1 <= n_items <= arr.shape[1]:
        raise ValueError(f"n_items must be in 1..{arr.shape[1]}")
    with open(run_dir / "results" / "item_contrasts_index.csv", encoding="utf-8") as fh:
        idx = list(csv.DictReader(fh))
    stored = {(r["key"].split("|")[0], float(r["r"]), int(r["n"]), int(r["h"])): arr[int(r["row"])]
              for r in idx if r["condition"] == "E-CONT" and r["key"].endswith("matched_minus_frontier_ctx")}
    ns, hs = (1, 2, 3, 5, 10, 20), (1, 5)
    max_diff, count, ok = 0.0, 0, True
    for rep, seed in (("R1", 52101), ("R2", 52102)):
        for r in RS:
            model = model_for(0.0, r)
            cond = NoisyObservationCondition(POP_PRIOR, model)
            split = generate_noisy_split(cond, SplitRole.EVALUATION, NamedStreams(seed), n_items, 25)
            latent05 = generate_split(cond, SplitRole.EVALUATION, NamedStreams(seed), n_items, 25)
            ok &= bool(np.array_equal(split.observations, latent05.trajectories))   # sigma_v = 0: y is the Stage 0.5 path
            eset = nh.build_noisy_evaluation(split, ns, hs)
            pop, stab = primary_pair(model)
            sp, ss = nh.score_noisy_batch(pop, eset), nh.score_noisy_batch(stab, eset)
            for n in ns:
                for h in hs:
                    d = (sp[(n, h)][0] - ss[(n, h)][0]) - stored[(rep, r, n, h)][:n_items]   # items: prefix (V19)
                    max_diff = max(max_diff, float(np.max(np.abs(d))))
                    count += d.size
    ok &= max_diff <= TIER1_TOL
    return CheckResult("V4_tier1_regression_stage05", ok, {"items_compared": count, "max_abs_diff": max_diff,
                                                            "tolerance": TIER1_TOL})


def check_continuity_sigma_v_to_zero(seed: int = 61005, n: int = 10, h: int = 1) -> CheckResult:
    """Kalman path at small sigma_v vs the Stage 0.5 path at sigma_v = 0 (context y_0..y_n, target index n + h).
    (a) Fixed data: y = x, target x_{n+h}; only the model's sigma_v -> 0. Expected rate O(sigma_v^2) (DERIVED: for
    fixed data the log-density is smooth in sigma_v^2). (b) Consistent data: y = x + sigma_v nu, target
    x_{n+h} + sigma_v nu_{n+h}. Expected O(sigma_v) (DERIVED: the data move by O(sigma_v)). Pass: monotone decrease over
    sigma_v in {1e-1, 1e-2, 1e-3, 1e-4}, and a log-log slope within 0.3 of the expected rate."""
    svs = (1e-1, 1e-2, 1e-3, 1e-4)
    res = {}
    for mode in ("fixed_data", "consistent_data"):
        errs = []
        for sv in svs:
            e = 0.0
            for j, r in enumerate(RS):
                g = np.random.default_rng(seed + j)            # identical latent path and noise across sv levels
                x, _ = simulate(0.6, model_for(0.0, r), n + h, g)
                nu = g.standard_normal(n + h + 1)
                model = NoisyObservationModel(1.0, sv, r)
                if mode == "fixed_data":
                    y, target = x, x[n + h]
                else:
                    y, target = x + sv * nu, x[n + h] + sv * nu[n + h]
                for prior in (POP_PRIOR, STAB_PRIOR):
                    ref = StablePriorQuadraturePredictor(prior).predict(ContextWindow(x[: n + 1]), h)
                    kal = kq.NoisyObservationBayesPredictor(prior, model, SETTINGS,
                                                            kq.noise_aware_stability_predictor(model).description)
                    p = kal.predict(ContextWindow(y[: n + 1]), h)
                    e = max(e, abs(float(p.logpdf(target)) - float(ref.logpdf(x[n + h]))))
            errs.append(e)
        slope = float(np.polyfit(np.log(svs), np.log(errs), 1)[0])
        res[mode] = {"errors": errs, "slope": slope}
    ok = (all(a > b for a, b in zip(res["fixed_data"]["errors"], res["fixed_data"]["errors"][1:]))
          and all(a > b for a, b in zip(res["consistent_data"]["errors"], res["consistent_data"]["errors"][1:]))
          and abs(res["fixed_data"]["slope"] - 2.0) <= 0.3 and abs(res["consistent_data"]["slope"] - 1.0) <= 0.3)
    return CheckResult("V5_continuity_sigma_v_to_zero", ok, res)


# ===================================================================== V6-V8: integration over a


def quadrature_convergence_table() -> list[dict]:
    rng = np.random.default_rng(61006)
    cases = [("broad: q=6.5 n=2 r=0.25", 6.5, 0.25, 2, 0.4), ("broad: q=6.5 n=40 r=1", 6.5, 1.0, 40, 0.4),
             ("concentrated: q=0 n=40 r=4 a=0.5", 0.0, 4.0, 40, 0.5), ("concentrated: q=0.755 n=40 r=4", 0.755, 4.0, 40, 0.5),
             ("boundary: q=0 n=40 r=4 a=0.949", 0.0, 4.0, 40, 0.949), ("boundary: q=0 n=40 r=4 a=0.998", 0.0, 4.0, 40, 0.998),
             ("boundary: q=0.755 n=40 r=1 a=-0.949", 0.755, 1.0, 40, -0.949), ("large state h=5: q=0.755 n=10 r=4", 0.755, 4.0, 10, 0.9)]
    out = []
    for label, q, r, n, a in cases:
        model = model_for(q, r)
        _, y = simulate(a, model, n, rng)
        ctx = ContextWindow(y)
        for h in (1, 5):
            preds = {s: primary_pair(model, s) for s in (SETTINGS, SETTINGS.refined(2), SETTINGS.refined(4))}
            ys = preds[SETTINGS.refined(4)][0].predict(ctx, h).quantile(np.array([1e-3, 0.1, 0.5, 0.9, 1 - 1e-3]))
            lp = {s: (np.asarray(p.predict(ctx, h).logpdf(ys)), np.asarray(st.predict(ctx, h).logpdf(ys)))
                  for s, (p, st) in preds.items()}
            fine = lp[SETTINGS.refined(4)]
            row = {"case": label, "h": h, "nodes": [int(preds[s][0].nodes.size) for s in preds]}
            for tag, s in (("N", SETTINGS), ("2N", SETTINGS.refined(2))):
                row[f"logpdf_err_{tag}"] = float(max(np.max(np.abs(lp[s][0] - fine[0])), np.max(np.abs(lp[s][1] - fine[1]))))
                row[f"gain_err_{tag}"] = float(np.max(np.abs((lp[s][0] - lp[s][1]) - (fine[0] - fine[1]))))
            out.append(row)
    return out


def check_quadrature_convergence_noisy() -> CheckResult:
    """Error budget: <= 2e-4 nats per-forecast paired gain (delta/100). Required at the default resolution: <= 2e-5 for
    both logpdf and gain error vs 4x nodes (a 10x margin), with no increase from N to 2N (1e-13 slack)."""
    t = quadrature_convergence_table()
    ok = all(r["logpdf_err_N"] <= ERROR_BUDGET / 10 and r["gain_err_N"] <= ERROR_BUDGET / 10
             and r["gain_err_2N"] <= r["gain_err_N"] + 1e-13 for r in t)
    worst = max(t, key=lambda r: r["gain_err_N"])
    return CheckResult("V6_quadrature_convergence", ok, {"table": t, "worst_gain_err": worst["gain_err_N"],
                                                         "worst_case": worst["case"], "budget": ERROR_BUDGET})


def check_independent_integration(seed: int = 61007) -> CheckResult:
    """Production (Kalman + shared GL nodes) vs the independent oracle (Cholesky likelihood + scipy.quad adaptive
    integration over a) for the reference AND the comparator: the posterior mean/var of a and the predictive logpdf/cdf
    at 3 points. Tolerance: 10 x (quad's relative error estimate + production node-doubling error) + 1e-9 relative."""
    rng = np.random.default_rng(seed)
    ok, worst, n_cmp = True, 0.0, 0
    for q, r, n in ((0.755, 0.25, 2), (0.755, 4.0, 40), (6.5, 1.0, 10), (2.56, 1.0, 40), (6.5, 4.0, 2)):
        model = model_for(q, r)
        a = float(POP_PRIOR.sample_systems(rng, 1)[0][0])
        _, y = simulate(a, model, n + 5, rng)
        ctx = ContextWindow(y[: n + 1])
        pop, stab = primary_pair(model)
        for pred, prior in ((pop, POP_PRIOR), (stab, STAB_PRIOR)):
            for h in (1, 5):
                p = pred.predict(ctx, h)
                ys = p.quantile(np.array([0.05, 0.5, 0.95]))
                oracle = O.adaptive_reference(y[: n + 1], h, prior, 1.0, model.sigma_v, r, ys)
                pairs = [(float(v), c, e) for v, c, e in zip(p.logpdf(ys), oracle["logpdf"], oracle["abserr_rel"])]
                qerr = 0.0
                if isinstance(pred, kq.NoisyObservationBayesPredictor):
                    lw, _, _ = pred.posterior(ctx)
                    w = np.exp(lw)
                    pm = float(w @ pred.nodes)
                    pv = float(w @ (pred.nodes - pm) ** 2)
                    qerr = _quad_err(lambda s, pred=pred: pred.with_settings(s), ctx, h, ys)
                    pairs += [(pm, oracle["post_mean"], oracle["Z_abserr_rel"]), (pv, oracle["post_var"], oracle["Z_abserr_rel"])]
                pairs += [(float(v), c, e) for v, c, e in zip(p.cdf(ys), oracle["cdf"], oracle["abserr_rel"])]
                for v, c, e in pairs:
                    tol = 10 * (e * max(1.0, abs(c)) + qerr) + 1e-9 * max(1.0, abs(c))
                    worst = max(worst, abs(v - c) / tol)
                    ok &= abs(v - c) <= tol
                    n_cmp += 1
    return CheckResult("V7_independent_integration_oracle", ok, {"n_comparisons": n_cmp, "worst_err_over_tol": worst})


def check_monte_carlo_noisy(seed: int = 61008, n_draws: int = 20000) -> CheckResult:
    """Importance sampling (a from the prior, Cholesky weights, exact conditional draws of y_{n+h}) vs the production
    predictive mean, variance and quantiles (0.1, 0.5, 0.9). SE from self-normalised IS (as in Stage 0 check B1); z is
    Bonferroni over all comparisons (family alpha 1e-3)."""
    rng = np.random.default_rng(seed)
    cases = [(0.755, 1.0, 5, 1), (2.56, 0.25, 10, 5), (6.5, 4.0, 3, 1)]
    probs = (0.1, 0.5, 0.9)
    z = float(stats.norm.isf(FAMILY_ALPHA / (2 * len(cases) * (2 + len(probs)))))
    ok, max_z = True, 0.0
    for q, r, n, h in cases:
        model = model_for(q, r)
        a = float(POP_PRIOR.sample_systems(rng, 1)[0][0])
        _, y = simulate(a, model, n, rng)
        ref = kq.noisy_population_reference(POP_PRIOR, model).predict(ContextWindow(y), h)
        s, w = O.monte_carlo_predictive(y, h, POP_PRIOR.sample_systems, 1.0, model.sigma_v, r, n_draws, rng)
        mu = float(w @ s)
        dev2 = (s - mu) ** 2
        var = float(w @ dev2)
        comps = [(mu, ref.mean(), math.sqrt(float(np.sum(w * w * dev2)))),
                 (var, ref.variance(), math.sqrt(float(np.sum(w * w * (dev2 - var) ** 2))))]
        for pq in probs:
            qr = float(ref.quantile(pq))
            order = np.argsort(s)
            cw = np.cumsum(w[order])
            est = float(s[order][np.searchsorted(cw, pq * cw[-1])])
            se = math.sqrt(float(np.sum(w * w * ((s <= qr) - pq) ** 2))) / math.exp(float(ref.logpdf(qr)))
            comps.append((est, qr, se))
        for est, rv, se in comps:
            zz = abs(est - rv) / se
            max_z = max(max_z, zz)
            ok &= zz <= z
    return CheckResult("V8_monte_carlo_noisy", ok, {"z_crit": z, "max_abs_z": max_z})


# ============================================================== V9-V10: calibration and optimality


def check_noisy_calibration(seed: int = 61009, n_items: int = 1000, ns=(2, 10, 40), hs=(1, 5), qs=QS[1:], rs=RS,
                            n_draws: int = 99) -> CheckResult:
    """Population-aware reference under data generated from the model: SBC ranks of a (Binomial(L, F(a*)), with F from
    the reference's posterior CDF; MATH.md 8.4), PIT (KS) and 50/80/95% coverage of y_{n+h}. Bonferroni over all tests
    (family alpha 1e-3). Reports p-values only."""
    streams = NamedStreams(seed)
    n_tests = len(qs) * len(rs) * (len(ns) + len(ns) * len(hs) * 4)
    level = calibration.bonferroni_level(FAMILY_ALPHA, n_tests)
    ok, min_p, fails, rows = True, 1.0, [], []
    for qi, q in enumerate(qs):
        for ri, r in enumerate(rs):
            model = model_for(q, r)
            cond = NoisyObservationCondition(POP_PRIOR, model)
            split = generate_noisy_split(cond, SplitRole.EVALUATION, streams, n_items, max(ns) + max(hs))
            eset = nh.build_noisy_evaluation(split, ns, hs)
            pop = kq.noisy_population_reference(POP_PRIOR, model)
            assert_matched(pop, cond)
            sc = nh.score_noisy_batch(pop, eset)
            g = streams.stream("monte_carlo", qi, ri)
            for n in ns:
                ranks = [int(g.binomial(n_draws, pop.posterior_cdf(eset.context(i, n), float(eset._true_a[i]))))
                         for i in range(eset.size)]
                p = calibration.rank_uniformity_pvalue(np.array(ranks), n_draws)
                tests = [("SBC", p)]
                for h in hs:
                    u = sc[(n, h)][1]
                    tests.append((f"PIT h={h}", calibration.ks_uniform_pvalue(u)))
                    for lev in (0.5, 0.8, 0.95):
                        tests.append((f"cov{lev} h={h}", calibration.coverage_pvalue(int(scoring.covered_from_pit(u, lev).sum()), u.size, lev)))
                for name, p in tests:
                    min_p = min(min_p, p)
                    rows.append({"q": q, "r": r, "n": n, "test": name, "p": p})
                    if p < level:
                        ok = False
                        fails.append((q, r, n, name, p))
    return CheckResult("V9_noisy_calibration", ok, {"n_tests": n_tests, "per_test_level": level, "min_p": min_p,
                                                    "failures": fails, "rows": rows})


def check_noisy_optimality(seed: int = 61010, n_items: int = 2000, ns=(2, 5, 10, 20, 40), hs=(1, 5),
                           naive_items: int = 300, naive_ns=(2, 10, 40)) -> CheckResult:
    """Bayes optimality: with systems drawn from the population prior, the reference's paired mean log score must not
    be significantly below ANY other predictor's (noise-aware stability, arcsine and MLE plug-in; noise-naive Stage 0.5
    members on a subset). One-sided z, Bonferroni, family alpha 1e-3. Reports violation COUNTS only (no effect sizes;
    Stage 0.6 standing rule)."""
    streams = NamedStreams(seed)
    comps = []
    for q in QS[1:]:
        model = model_for(q, 1.0)
        cond = NoisyObservationCondition(POP_PRIOR, model)
        split = generate_noisy_split(cond, SplitRole.EVALUATION, streams, n_items, max(ns) + max(hs))
        eset = nh.build_noisy_evaluation(split, ns, hs)
        pop = kq.noisy_population_reference(POP_PRIOR, model)
        ref = nh.score_noisy_batch(pop, eset)
        others = {"stability": nh.score_noisy_batch(kq.noise_aware_stability_predictor(model), eset),
                  "arcsine": nh.score_noisy_batch(kq.noise_aware_arcsine_predictor(model), eset)}
        mle = nh.score_noisy_per_context(kq.NoiseAwareMlePlugInPredictor(model), eset, items=range(naive_items))
        for name, sc in others.items():
            for k in ref:
                comps.append(ref[k][0] - sc[k][0])
        for k in mle:
            comps.append(ref[k][0][:naive_items] - mle[k][0])
        for name, pred in build_context_only_family(1.0, stability_bound=0.999).items():
            if name.startswith("kernel_") and name != "kernel_rolling_origin":
                continue
            sc = nh.score_noisy_per_context(pred, eset, ns=naive_ns, items=range(naive_items))
            for k in sc:
                comps.append(ref[k][0][:naive_items] - sc[k][0])
    z = float(stats.norm.isf(FAMILY_ALPHA / len(comps)))
    violations = sum(1 for d in comps if d.mean() < -z * d.std(ddof=1) / math.sqrt(d.size))
    return CheckResult("V10_noisy_optimality", violations == 0, {"n_comparisons": len(comps), "n_violations": violations,
                                                                 "z_crit": z})


# ============================================================== V11-V16: parity, access, batch, seeds, specials


def check_parity_null(seed: int = 61011) -> CheckResult:
    """The population-aware class built with the STABILITY prior reproduces the noise-aware stability predictor bitwise,
    for every n in 2..40, h in {1, 5}, all q and r (per-context and batch paths). The primary pair shares the model,
    settings, nodes and observation-model declaration, and differs only in the prior."""
    rng = np.random.default_rng(seed)
    ok, n_cmp = True, 0
    for q in QS:
        for r in RS:
            model = model_for(q, r)
            stab_prior = StableCoefficientPrior(rho=0.999, sigma=1.0, shape="uniform")
            pop_with_stab = kq.noisy_population_reference(stab_prior, model)
            stab = kq.noise_aware_stability_predictor(model)
            pop = kq.noisy_population_reference(POP_PRIOR, model)
            _, y = simulate(float(rng.uniform(-0.9, 0.9)), model, 45, rng)
            for n in range(2, 41):
                ctx = ContextWindow(y[: n + 1])
                for h in (1, 5):
                    a_, b_ = pop_with_stab.predict(ctx, h), stab.predict(ctx, h)
                    ys = np.array([y[n + h], 0.0, 2.0])
                    ok &= bool(np.array_equal(a_.logpdf(ys), b_.logpdf(ys)) and np.array_equal(a_.cdf(ys), b_.cdf(ys))
                               and a_.mean() == b_.mean() and a_.variance() == b_.variance())
                    n_cmp += 1
            ok &= (getattr(stab, "model", None) == pop.model and getattr(stab, "settings", None) == pop.settings
                   and np.array_equal(getattr(stab, "nodes", np.empty(0)), pop.nodes)
                   and pop.description.observation_model == stab.description.observation_model
                   and pop.description.uses_true_noise_scale == stab.description.uses_true_noise_scale)
            if hasattr(stab, "batch_scores"):
                tg = {(n, h): np.array([y[n + h]]) for n in range(2, 41) for h in (1, 5)}
                ba = pop_with_stab.batch_scores(y[None, :41], tg, tuple(range(2, 41)), (1, 5))
                bb = stab.batch_scores(y[None, :41], tg, tuple(range(2, 41)), (1, 5))
                ok &= all(np.array_equal(ba[k][0], bb[k][0]) and np.array_equal(ba[k][1], bb[k][1]) for k in ba)
            else:
                ok = False      # the declared noise-aware comparator lacks the shared batch API
    return CheckResult("V11_parity_null", ok, {"n_comparisons": n_cmp})


def _rebuild_split(split, latent_traj=None, obs_noise=None):
    lat = split.latent
    new_lat = DataSplit(lat.role, lat.condition_name, lat.coefficients, lat.noise_scales, lat.system_ids,
                        lat.innovations, lat.trajectories if latent_traj is None else latent_traj, lat.initial_state)
    nu = split.obs_noise if obs_noise is None else obs_noise
    from dynaicl.systems.noisy import NoisySplit
    return NoisySplit(new_lat, nu, new_lat.trajectories + split.sigma_v * nu, split.sigma_v)


def check_information_access_noisy(seed: int = 61012) -> CheckResult:
    """(d) Off-by-one FIRST, from the canonical cutters: the context has n + 1 values (y_0..y_n) and the target index is
    n + h; shifting the context by one changes the prediction (positive control). (a) Perturbing the LATENT path
    while holding the observations fixed leaves every prediction bitwise unchanged. (b) Perturbing observations after
    y_n leaves predictions for n unchanged (per-context and batch). (c) Predictors reject raw arrays and GroundTruth.
    If the harness's own consistency guard trips, that is recorded as a failed sub-check, not as an exception."""
    streams = NamedStreams(seed)
    model = model_for(2.56, 1.0)
    cond = NoisyObservationCondition(POP_PRIOR, model)
    split = generate_noisy_split(cond, SplitRole.EVALUATION, streams, 20, 50)
    ns, hs = (2, 10, 40), (1, 5)
    pop, stab = primary_pair(model)
    naive = build_context_only_family(1.0, stability_bound=0.999)["flat_prior_bayes"]
    details = {}
    # (d) indexing, via the canonical cutters directly
    row = split.observations[0]
    ctx = nh.make_noisy_context(row, 10)
    d_ok = len(ctx) == 11 and bool(np.array_equal(ctx.values, row[:11])) and nh.target_index(10, 5) == 15
    pc = pop.predict(ctx, 1)
    shifted = pop.predict(ContextWindow(np.array(row[:12])), 1)
    d_ok &= not np.array_equal(pc.logpdf(np.array([0.3])), shifted.logpdf(np.array([0.3])))   # positive control
    details["indexing"] = bool(d_ok)
    try:
        base = nh.build_noisy_evaluation(split, ns, hs)
        details["harness_guard_ok"] = True
    except (AssertionError, ValueError) as exc:
        details["harness_guard_ok"] = False
        details["harness_guard_message"] = str(exc)[:120]
        return CheckResult("V12_information_access", False, details)
    details["targets_at_n_plus_h"] = float(base._targets[(10, 5)][0]) == float(split.observations[0, 15])
    # (a) latent perturbation with y held fixed: x' = x + d, nu' = nu - d / sigma_v
    dlt = np.random.default_rng(seed).normal(size=split.latent.trajectories.shape) * 3.0
    alt = _rebuild_split(split, latent_traj=split.latent.trajectories + dlt, obs_noise=split.obs_noise - dlt / model.sigma_v)
    alt_set = nh.build_noisy_evaluation(alt, ns, hs)
    same_y = bool(np.allclose(alt.observations, split.observations, rtol=0, atol=1e-12))
    a_ok = True
    for pred in (pop, stab, naive):
        s1 = nh.score_noisy_per_context(pred, base, items=range(5))
        s2 = nh.score_noisy_per_context(pred, alt_set, items=range(5))
        a_ok &= all(np.allclose(s1[k][0], s2[k][0], rtol=0, atol=1e-12) for k in s1)
    details["latent_invariance"] = bool(a_ok and same_y)
    # (b) future perturbation
    b_ok = True
    for n in ns:
        y = np.array(base.context_matrix[0], copy=True)
        yp = y.copy()
        yp[n + 1:] += 5.0
        for pred in (pop, stab):
            p1, p2 = pred.predict(ContextWindow(y[: n + 1]), 1), pred.predict(ContextWindow(yp[: n + 1]), 1)
            b_ok &= bool(np.array_equal(p1.logpdf(np.array([0.3])), p2.logpdf(np.array([0.3]))))
            if hasattr(pred, "batch_posterior"):
                b_ok &= bool(np.array_equal(pred.batch_posterior(y[None, :], (n,))[n][0],
                                            pred.batch_posterior(yp[None, :], (n,))[n][0]))
            else:
                b_ok = False
    details["future_invariance"] = bool(b_ok)
    # (c) interface
    c_ok = True
    for bad in (np.array([0.1, 0.2]), GroundTruth(0, 0.5, 1.0, "x", 0.1, 1, "h")):
        try:
            pop.predict(bad, 1)
            c_ok = False
        except TypeError:
            pass
    details["interface"] = c_ok
    return CheckResult("V12_information_access", all(v for k, v in details.items() if isinstance(v, bool)), details)


def check_batch_equals_per_context(seed: int = 61013) -> CheckResult:
    """The shared-prefix batch path equals the canonical per-context predict for every n in 2..40, h in {1, 5}, all q
    and r. Tolerance 1e-12 absolute (same arithmetic, different vectorisation)."""
    streams = NamedStreams(seed)
    worst, ok = 0.0, True
    ns, hs = tuple(range(2, 41)), (1, 5)
    for q in QS:
        for r in RS:
            model = model_for(q, r)
            split = generate_noisy_split(NoisyObservationCondition(POP_PRIOR, model), SplitRole.EVALUATION, streams, 3, 45)
            eset = nh.build_noisy_evaluation(split, ns, hs)
            for pred in primary_pair(model):
                b = nh.score_noisy_batch(pred, eset)
                p = nh.score_noisy_per_context(pred, eset)
                for k in b:
                    e = float(max(np.max(np.abs(b[k][0] - p[k][0])), np.max(np.abs(b[k][1] - p[k][1]))))
                    worst = max(worst, e)
                    ok &= e <= 1e-12
    return CheckResult("V13_batch_equals_per_context", ok, {"max_abs_diff": worst})


def check_seed_isolation_noisy() -> CheckResult:
    """The latent path is identical across q for the same seeds; observation noise is never shared between roles or
    replicates; and the Stage 0.6 seed manifest is disjoint from every seed literal used elsewhere in the repository."""
    from dynaicl.systems.noisy import assert_no_obs_noise_overlap
    import re
    import yaml
    s = NamedStreams(61014)
    splits = {q: generate_noisy_split(NoisyObservationCondition(POP_PRIOR, model_for(q, 1.0)), SplitRole.EVALUATION, s, 50, 20)
              for q in QS}
    ok = all(np.array_equal(splits[q].latent.trajectories, splits[0.0].latent.trajectories) for q in QS)
    sel = generate_noisy_split(NoisyObservationCondition(POP_PRIOR, model_for(1.0, 1.0)), SplitRole.SELECTION, s, 50, 20)
    other = generate_noisy_split(NoisyObservationCondition(POP_PRIOR, model_for(1.0, 1.0)), SplitRole.EVALUATION, NamedStreams(61015), 50, 20)
    try:
        assert_no_obs_noise_overlap(splits[0.755], sel)
        assert_no_obs_noise_overlap(splits[0.755], other)
    except AssertionError:
        ok = False
    with open(ROOT / "config" / "stage06_seed_manifest.yaml", encoding="utf-8") as fh:
        manifest = yaml.safe_load(fh)
    s06 = [v for role in manifest["roles"].values() for v in role["seeds"]]
    used = set()
    for path in list((ROOT / "dynaicl").rglob("*.py")) + list((ROOT / "tests").rglob("*.py")) + list((ROOT / "config").glob("*.yaml")):
        if "stage06" in path.name or "checks_stage06" in path.name or path.name.startswith("test_stage06"):
            continue
        used |= {int(m) for m in re.findall(r"\b\d{2,8}\b", path.read_text(encoding="utf-8"))}
    collide = sorted(set(s06) & used)
    ok &= len(s06) == len(set(s06)) and not collide
    return CheckResult("V14_seed_isolation", ok, {"stage06_seeds": len(s06), "collisions_with_repo_literals": collide})


def check_analytic_special_cases(seed: int = 61016) -> CheckResult:
    """(a) A narrow uniform prior [a0 +/- 1e-4] reproduces the plain Kalman predictive at a0 (from Cholesky): |dlogpdf|
    <= 1e-6. (b) As q -> infinity the predictive approaches the prior predictive N(0, V_{n+h}(a) + sigma_v^2) mixed over
    the prior; the error must shrink monotonically over q in {1e2, 1e4, 1e6}. (c) Riccati: P_{t|t} at t = 300 equals the
    steady-state fixed point (closed form) to 1e-12 relative. (d) Chain rule h = 2: integral of p(y_{n+1}) p(y_{n+2} | y_{0:n+1})
    dy_{n+1} equals the h = 2 predictive (relative 1e-8 + quad error)."""
    rng = np.random.default_rng(seed)
    det = {}

    class NarrowUniform:
        def __init__(self, lo, hi):
            self.support = (lo, hi)
        def coefficient_logpdf(self, a):
            a = np.asarray(a, dtype=FLOAT)
            lo, hi = self.support
            return np.where((a >= lo) & (a <= hi), -math.log(hi - lo), -np.inf)

    a0, eps = 0.6, 1e-4
    model = model_for(0.755, 1.0)
    st = kq.KalmanQuadratureSettings(breakpoints=(-0.95, a0 - eps, a0 + eps, 0.95))
    pred = kq.NoisyObservationBayesPredictor(NarrowUniform(a0 - eps, a0 + eps), model, st,
                                             kq.noise_aware_stability_predictor(model).description)
    _, y = simulate(a0, model, 12, rng)
    errs = []
    for h in (1, 5):
        _, mu, v = O.cholesky_predictive(y, a0, h, 1.0, model.sigma_v, 1.0)
        p = pred.predict(ContextWindow(y), h)
        for yv in (mu - 2 * math.sqrt(v), mu, mu + 1.5 * math.sqrt(v)):
            errs.append(abs(float(p.logpdf(yv)) - float(stats.norm.logpdf(yv, mu, math.sqrt(v)))))
    det["narrow_prior_max_err"] = max(errs)
    # (b) high-noise limit
    hn = []
    for q in (1e2, 1e4, 1e6):
        m = model_for(q, 1.0)
        _, yy = simulate(0.5, m, 8, rng)
        pop = kq.noisy_population_reference(POP_PRIOR, m)
        a_n, w_n = O.truncnorm_prior_nodes(0.4, 0.3, 0.95, 200)
        yv = float(yy[-1])
        prior_pred = math.log(sum(wi * stats.norm.pdf(yv, 0.0, math.sqrt(O.latent_variances(ai, 9, 1.0, 1.0)[9] + q))
                                  for ai, wi in zip(a_n, w_n)))
        hn.append(abs(float(pop.predict(ContextWindow(yy), 1).logpdf(yv)) - prior_pred))
    det["high_noise_errors"] = hn
    # (c) Riccati steady state
    rc = []
    for a in (0.3, 0.9):
        m = model_for(2.56, 1.0)
        f = kq.kalman_filter_on_nodes(np.zeros((1, 301)), np.array([a]), m, (300,))
        sw2, sv2 = 1.0, m.sigma_v ** 2
        # fixed point of P_f = (a^2 P_f + sw2) sv2 / (a^2 P_f + sw2 + sv2): a^2 P^2 + (sw2 + sv2 - a^2 sv2) P - sw2 sv2 = 0
        A, B, C = a * a, sw2 + sv2 - a * a * sv2, -sw2 * sv2
        Pstar = (-B + math.sqrt(B * B - 4 * A * C)) / (2 * A)
        rc.append(abs(float(f["P"][300][0]) - Pstar) / Pstar)
    det["riccati_rel_err"] = max(rc)
    # (d) chain rule h = 2
    m = model_for(0.755, 1.0)
    pop = kq.noisy_population_reference(POP_PRIOR, m)
    _, yy = simulate(0.5, m, 6, rng)
    ctx = ContextWindow(yy)
    p1, p2 = pop.predict(ctx, 1), pop.predict(ctx, 2)
    z = float(p2.quantile(0.5))
    val, abserr = integrate.quad(lambda w: math.exp(float(p1.logpdf(w)) + float(pop.predict(ContextWindow(np.append(yy, w)), 1).logpdf(z))),
                                 p1.quantile(1e-12), p1.quantile(1 - 1e-12), epsabs=1e-13, epsrel=1e-11, limit=400)
    ref = math.exp(float(p2.logpdf(z)))
    det["chain_rule_rel_err"] = abs(val - ref) / ref
    ok = (det["narrow_prior_max_err"] <= 1e-6 and hn[0] > hn[1] > hn[2] and det["riccati_rel_err"] <= 1e-12
          and det["chain_rule_rel_err"] <= 1e-8 + 10 * abserr / ref)
    return CheckResult("V15_analytic_special_cases", ok, det)


def check_failure_surfacing() -> CheckResult:
    """Non-finite inputs and impossible configurations raise; they are never silently dropped. (Failed cells in the
    confirmatory runner are recorded by the Phase D runner; tested there.)"""
    det = {}
    model = model_for(0.755, 1.0)
    pop = kq.noisy_population_reference(POP_PRIOR, model)
    try:
        ContextWindow(np.array([0.1, np.nan]))
        det["nan_context_rejected"] = False
    except ValueError:
        det["nan_context_rejected"] = True
    try:
        kq.kalman_filter_on_nodes(np.array([[0.1, np.inf]]), pop.nodes, model, (1,))
        det["inf_observation_raises"] = False
    except FloatingPointError:
        det["inf_observation_raises"] = True
    try:
        kq.NoisyObservationBayesPredictor(StableCoefficientPrior(0.9, 1.0), model, SETTINGS, pop.description)
        det["support_not_on_cut_points_raises"] = False
    except ValueError:
        det["support_not_on_cut_points_raises"] = True
    try:
        pop.batch_scores(np.array([[0.1, 0.2, 0.3]]), {(2, 1): np.array([np.nan])}, (2,), (1,))
        det["nan_target_raises"] = False
    except FloatingPointError:
        det["nan_target_raises"] = True
    try:
        NoisyObservationModel(1.0, 0.0, 0.0)
        det["singular_model_rejected"] = False
    except ValueError:
        det["singular_model_rejected"] = True
    return CheckResult("V16_failure_surfacing", all(det.values()), det)


def check_noise_naive_definitions(seed: int = 61017) -> CheckResult:
    """The noise-naive baselines are the Stage 0.5 predictors applied to y: at q = 0 they reproduce Stage 0.5 exactly
    (same class, same context), and at q > 0 the flat-prior posterior mean equals S_xy/S_xx computed from y."""
    rng = np.random.default_rng(seed)
    fam = build_context_only_family(1.0, stability_bound=0.999)
    model = model_for(2.56, 1.0)
    _, y = simulate(0.6, model, 15, rng)
    m, v, _ = fam["flat_prior_bayes"].coefficient_posterior(ContextWindow(y))
    ok = abs(m - float(y[:-1] @ y[1:] / (y[:-1] @ y[:-1]))) <= 1e-14 * max(1, abs(m))
    ok &= all(p.description.observation_model == "noise-free" for p in fam.values())
    return CheckResult("V17_noise_naive_definitions", bool(ok), {"flat_prior_mean_matches_definition": bool(ok)})


def log_shifted_oracle_logpdf(y_ctx: np.ndarray, h: int, prior, model: NoisyObservationModel, y_eval: float) -> float:
    """High-precision (relative) oracle for the predictive log density at a possibly far-tail point. Independent code:
    the Cholesky likelihood and conditional moments, with integration over a by scipy.quad AFTER shifting the log
    integrand by its maximum on a 4001-point grid. So the integrand is O(1) at its peak whatever the tail depth, and
    quad's relative tolerance applies to the tail density itself."""
    lo, hi = prior.support

    def f_num(a):
        ll, mu, v = O.cholesky_predictive(y_ctx, a, h, model.sigma_w, model.sigma_v, model.x0_sd)
        return ll + float(prior.coefficient_logpdf(np.array(a))) - 0.5 * math.log(2 * math.pi * v) - 0.5 * (y_eval - mu) ** 2 / v

    def f_den(a):
        return O.cholesky_loglik(y_ctx, a, model.sigma_w, model.sigma_v, model.x0_sd) + float(prior.coefficient_logpdf(np.array(a)))

    def log_integral(f):
        grid = np.linspace(lo, hi, 4001)[1:-1]
        vals = np.array([f(a) for a in grid])
        c, a_star = float(vals.max()), float(grid[int(vals.argmax())])
        pts = [a_star] if lo < a_star < hi else None
        val, _ = integrate.quad(lambda a: math.exp(f(a) - c), lo, hi, points=pts, limit=500, epsabs=0, epsrel=1e-12)
        return c + math.log(val)

    return log_integral(f_num) - log_integral(f_den)


FAR_TAIL_TOL = 1e-6   # nats, absolute (<< ERROR_BUDGET); fixed before running


def check_far_tail_logdensity(seed: int = 61018) -> CheckResult:
    """Far tails: (a) production predictive log density at y = mean +/- k sd, k in {6, 10, 15}, vs the log-shifted
    high-precision oracle, for both primary predictors, broad and concentrated posteriors, h in {1, 5}.
    (b) Analytic reference: with a narrow uniform prior [a0 +/- eps], eps = 1e-7, the predictive tends to the Gaussian at
    a0. Writing l(a) = log N(y; mu(a), v(a)), the mixture differs from it by (eps^2/6)(l'^2 + l'') + O(eps^4) (DERIVED:
    second-order expansion of E_a[exp(l)] with Var(a) = eps^2/3). The tolerance is FAR_TAIL_TOL + 2 (eps^2/6)(l'^2 + |l''|),
    with l', l'' from central differences of the independent Cholesky density. (Correction, disclosure entry 10: the first
    version used eps = 1e-4 and an underived k^2-scaled tolerance. That failed, because the mixing term is real; the code
    matched the oracle for the same prior to 2e-13.)"""
    rng = np.random.default_rng(seed)
    worst_a, worst_b, n_cmp = 0.0, 0.0, 0
    for q, r, n in ((0.755, 1.0, 2), (6.5, 0.25, 40), (0.755, 4.0, 40), (2.56, 1.0, 10)):
        model = model_for(q, r)
        a = float(POP_PRIOR.sample_systems(rng, 1)[0][0])
        _, y = simulate(a, model, n, rng)
        ctx = ContextWindow(y)
        for pred, prior in zip(primary_pair(model), (POP_PRIOR, STAB_PRIOR)):
            for h in (1, 5):
                p = pred.predict(ctx, h)
                m, sd = p.mean(), math.sqrt(p.variance())
                for k in (-15, -10, -6, 6, 10, 15):
                    yv = m + k * sd
                    err = abs(float(p.logpdf(yv)) - log_shifted_oracle_logpdf(y, h, prior, model, yv))
                    worst_a = max(worst_a, err)
                    n_cmp += 1

    class NarrowUniform:
        def __init__(self, lo, hi):
            self.support = (lo, hi)

        def coefficient_logpdf(self, a):
            a = np.asarray(a, dtype=FLOAT)
            lo, hi = self.support
            return np.where((a >= lo) & (a <= hi), -math.log(hi - lo), -np.inf)

    a0, eps = 0.6, 1e-7
    model = model_for(0.755, 1.0)
    st = kq.KalmanQuadratureSettings(breakpoints=(-0.95, a0 - eps, a0 + eps, 0.95))
    pred = kq.NoisyObservationBayesPredictor(NarrowUniform(a0 - eps, a0 + eps), model, st,
                                             kq.noise_aware_stability_predictor(model).description)
    _, y = simulate(a0, model, 12, rng)

    def ell(a, h, yv):
        _, m_, v_ = O.cholesky_predictive(y, a, h, 1.0, model.sigma_v, 1.0)
        return -0.5 * math.log(2 * math.pi * v_) - 0.5 * (yv - m_) ** 2 / v_

    for h in (1, 5):
        _, mu, v = O.cholesky_predictive(y, a0, h, 1.0, model.sigma_v, 1.0)
        p = pred.predict(ContextWindow(y), h)
        for k in (-40, -20, -10, 10, 20, 40):
            yv = mu + k * math.sqrt(v)
            d = 1e-4
            l1 = (ell(a0 + d, h, yv) - ell(a0 - d, h, yv)) / (2 * d)
            l2 = (ell(a0 + d, h, yv) - 2 * ell(a0, h, yv) + ell(a0 - d, h, yv)) / (d * d)
            tol_b = FAR_TAIL_TOL + 2 * (eps * eps / 6) * (l1 * l1 + abs(l2))
            err = abs(float(p.logpdf(yv)) - float(stats.norm.logpdf(yv, mu, math.sqrt(v))))
            worst_b = max(worst_b, err / tol_b)
            n_cmp += 1
    ok = worst_a <= FAR_TAIL_TOL and worst_b <= 1.0
    return CheckResult("V18_far_tail_logdensity", ok, {"n_comparisons": n_cmp, "max_abs_err_vs_oracle": worst_a,
                                                       "narrow_prior_worst_err_over_tol": worst_b, "tolerance": FAR_TAIL_TOL})


def check_design_common_random_numbers(seed: int = 61019, n_items: int = 30) -> CheckResult:
    """Design audit: every (q, r) condition of a replicate shares the SAME held-out systems and draws. Same a, same
    standardised initial-state draw (x_0 / r), same process-noise innovations, same standardised observation-noise draws
    (scaled by sigma_v). Systems are drawn from exactly the prior the population reference assumes (fingerprint
    match), and items are independent system-level units (item i does not depend on the number of items)."""
    streams = NamedStreams(seed)
    base = None
    det = {"same_a": True, "same_z0": True, "same_process_noise": True, "same_obs_noise": True,
           "reference_matched": True, "item_independent_of_count": True}
    for q in QS:
        for r in RS:
            model = model_for(q, r)
            cond = NoisyObservationCondition(POP_PRIOR, model)
            sp = generate_noisy_split(cond, SplitRole.EVALUATION, streams, n_items, 45)
            try:
                assert_matched(kq.noisy_population_reference(POP_PRIOR, model), cond)
            except Exception:
                det["reference_matched"] = False
            cur = (sp.latent.coefficients, sp.latent.trajectories[:, 0] / r, sp.latent.innovations, sp.obs_noise)
            if base is None:
                base = cur
            else:
                det["same_a"] &= bool(np.array_equal(cur[0], base[0]))
                det["same_z0"] &= bool(np.allclose(cur[1], base[1], rtol=1e-15, atol=0))
                det["same_process_noise"] &= bool(np.array_equal(cur[2], base[2]))
                det["same_obs_noise"] &= bool(np.array_equal(cur[3], base[3]))
    small = generate_noisy_split(NoisyObservationCondition(POP_PRIOR, model_for(2.56, 1.0)), SplitRole.EVALUATION, streams, 5, 45)
    large = generate_noisy_split(NoisyObservationCondition(POP_PRIOR, model_for(2.56, 1.0)), SplitRole.EVALUATION, streams, 12, 45)
    det["item_independent_of_count"] = bool(np.array_equal(small.observations, large.observations[:5]))
    return CheckResult("V19_design_common_random_numbers", all(det.values()), det)


ALL_CHECKS_STAGE06 = {
    "V1": check_kalman_vs_cholesky, "V2": check_target_noise_variance, "V3": check_zero_noise_matches_stage05_path,
    "V4": check_tier1_regression_stage05, "V5": check_continuity_sigma_v_to_zero, "V6": check_quadrature_convergence_noisy,
    "V7": check_independent_integration, "V8": check_monte_carlo_noisy, "V9": check_noisy_calibration,
    "V10": check_noisy_optimality, "V11": check_parity_null, "V12": check_information_access_noisy,
    "V13": check_batch_equals_per_context, "V14": check_seed_isolation_noisy, "V15": check_analytic_special_cases,
    "V16": check_failure_surfacing, "V17": check_noise_naive_definitions, "V18": check_far_tail_logdensity,
    "V19": check_design_common_random_numbers,
}
