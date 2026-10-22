"""Stage 0.6 Phase C: the user's pre-specified diagnostic protocol for the low V9 calibration p-value.

    python scripts/stage06_calibration_diagnostic.py   -> docs/STAGE06_CALIBRATION_DIAGNOSTIC.md

Steps (user decision 11):
1. Rerun V9 exactly (seed 61009, 1000 items) and list every test with its p-value, and the expected number below thresholds.
2. Identify the minimum-p test and regime, and show the shape of the deviation (PIT or SBC-rank histogram).
3. Rerun that SAME test with the ORIGINAL per-test threshold, a larger sample (5000 items) and a fresh validation seed (61020).
4. Quantify the possible effect on the paired gain: the expected log-score improvement available by recalibrating a
   predictive equals KL(PIT density || uniform) (DERIVED: E[log g(PIT)] with g the PIT density). It is estimated from a
   10-bin histogram, minus the plug-in bias (bins - 1)/(2N).
5. Classify the deviation: replicated (a theorem-level failure, fix and re-validate) or not replicated (chance, with the arithmetic).
5b. (Added after step 1 showed many small SBC p-values; not part of the user's protocol, reported as an extra.) Dependence
   between tests: every V9 cell shares the SAME held-out a-values (common random numbers, V19). At small n the posterior is
   close to the prior, so each SBC test largely tests whether those shared a-values are uniform under the prior CDF.
   Test that directly (chi-square on 10 bins and KS of F_prior(a_i)) for the V9 sample and for the fresh sample.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dynaicl.evaluation import noisy_harness as nh  # noqa: E402
from scipy import stats  # noqa: E402

from dynaicl.metrics import calibration, scoring  # noqa: E402
from dynaicl.references import kalman_quadrature as kq  # noqa: E402
from dynaicl.rng import NamedStreams  # noqa: E402
from dynaicl.systems.noisy import NoisyObservationCondition, generate_noisy_split  # noqa: E402
from dynaicl.systems.splits import SplitRole  # noqa: E402
from dynaicl.validation import checks_stage06 as C  # noqa: E402


def regime_values(seed, n_items, q, r, n, test, qs_order, rs_order):
    """The PIT values (or SBC ranks) underlying one V9 test, regenerated with V9's own code path."""
    streams = NamedStreams(seed)
    model = C.model_for(q, r)
    split = generate_noisy_split(NoisyObservationCondition(C.POP_PRIOR, model), SplitRole.EVALUATION, streams, n_items, 45)
    eset = nh.build_noisy_evaluation(split, (2, 10, 40), (1, 5))
    pop = kq.noisy_population_reference(C.POP_PRIOR, model)
    if test == "SBC":
        g = streams.stream("monte_carlo", qs_order.index(q), rs_order.index(r))
        return np.array([int(g.binomial(99, pop.posterior_cdf(eset.context(i, n), float(eset._true_a[i]))))
                         for i in range(eset.size)])
    h = int(test.split("h=")[1])
    return nh.score_noisy_batch(pop, eset)[(n, h)][1]


def test_p(values, test):
    if test == "SBC":
        return calibration.rank_uniformity_pvalue(values, 99)
    if test.startswith("PIT"):
        return calibration.ks_uniform_pvalue(values)
    lev = float(test.split()[0][3:])
    return calibration.coverage_pvalue(int(scoring.covered_from_pit(values, lev).sum()), values.size, lev)


def histogram(values, test):
    return (np.bincount(values // 10, minlength=10) if test == "SBC"
            else np.histogram(values, bins=10, range=(0, 1))[0])


def main() -> None:
    res = C.check_noisy_calibration()                     # step 1: exact rerun of V9
    rows, level, n_tests = res.details["rows"], res.details["per_test_level"], res.details["n_tests"]
    ps = np.array([r["p"] for r in rows])
    worst = min(rows, key=lambda r: r["p"])
    L = ["# Stage 0.6 calibration diagnostic (user decision 11, pre-specified protocol)", "",
         f"## Step 1: every V9 test (seed 61009, 1000 items; {n_tests} tests; Bonferroni per-test level {level:.2e})", "",
         "Expected number of p-values below t under correct calibration = n_tests x t:", ""]
    for t in (1e-3, 1e-2, 0.05):
        L.append(f"- t = {t:g}: expected {n_tests * t:.2f}, observed {int((ps < t).sum())}")
    L += [f"- V9 passed: {res.passed}; min p = {ps.min():.2e}", "", "| q | r | n | test | p |", "|---|---|---|---|---|"]
    for r in sorted(rows, key=lambda r: r["p"]):
        L.append(f"| {r['q']} | {r['r']} | {r['n']} | {r['test']} | {r['p']:.3e} |")
    qs_order, rs_order = list(C.QS[1:]), list(C.RS)
    vals = regime_values(61009, 1000, worst["q"], worst["r"], worst["n"], worst["test"], qs_order, rs_order)   # step 2
    L += ["", f"## Step 2: the minimum-p test: q = {worst['q']}, r = {worst['r']}, n = {worst['n']}, test = {worst['test']}", "",
          f"Regenerated p = {test_p(vals, worst['test']):.3e} (must equal the V9 value {worst['p']:.3e}).", "",
          f"10-bin histogram (expected {len(vals) / 10:.0f} per bin): {histogram(vals, worst['test']).tolist()}"]
    fresh = regime_values(61020, 5000, worst["q"], worst["r"], worst["n"], worst["test"], qs_order, rs_order)  # step 3
    p_fresh = test_p(fresh, worst["test"])
    replicated = p_fresh < level
    L += ["", "## Step 3: the same test, fresh seed 61020, 5000 items, original threshold", "",
          f"p = {p_fresh:.3e} vs per-test level {level:.2e} -> **{'REPLICATED' if replicated else 'NOT replicated'}**", "",
          f"10-bin histogram (expected {len(fresh) / 10:.0f} per bin): {histogram(fresh, worst['test']).tolist()}"]
    pit = fresh / 99.0 if worst["test"] == "SBC" else fresh                                                     # step 4
    cnt = np.histogram(pit, bins=10, range=(0, 1))[0]
    pj = cnt / cnt.sum()
    kl = float(np.sum(np.where(pj > 0, pj * np.log(np.where(pj > 0, pj, 1.0) / 0.1), 0.0)))
    kl_corr = max(0.0, kl - 9 / (2 * cnt.sum()))
    L += ["", "## Step 4: possible effect on the paired gain", "",
          f"KL(histogram || uniform) on the fresh sample = {kl:.2e}; bias-corrected = {kl_corr:.2e} nats/forecast. "
          "This bounds the expected log-score change available from recalibrating the reference in this regime. Compare "
          "delta = 0.02 and the numerical error budget 2e-4.", ""]
    p_any = 1 - (1 - worst["p"]) ** n_tests                                                                       # step 5
    L += ["## Step 5: classification", "",
          ("**Replicated deviation: a theorem-level failure.** Fix the cause and repeat the full validation." if replicated else
           f"**Not replicated; recorded as chance.** Under correct calibration, the probability that the minimum of {n_tests} "
           f"independent p-values is <= {worst['p']:.2e} is 1 - (1 - p)^{n_tests} = {p_any:.3f}.")]
    sbc = [r for r in rows if r["test"] == "SBC"]
    lo, hi = C.POP_PRIOR._tn_bounds()
    L += ["", "## Step 5b (extra): dependence between the SBC tests through the shared a-values", "",
          f"SBC tests with p <= 0.05: {sum(r['p'] <= 0.05 for r in sbc)} of {len(sbc)}; with p <= 0.01: "
          f"{sum(r['p'] <= 0.01 for r in sbc)}. Independent tests would give about {0.05 * len(sbc):.1f} and {0.01 * len(sbc):.2f}. "
          "The tests are not independent: every (q, r) cell uses the same held-out a-values (V19), and the posterior at "
          "small n is close to the prior. The direct test of the shared sample, u_i = F_prior(a_i):", "",
          "| sample | items | chi-square p (10 bins) | KS p | 10-bin histogram of u |", "|---|---|---|---|---|"]
    for seed, n_items in ((61009, 1000), (61020, 5000)):
        sp = generate_noisy_split(NoisyObservationCondition(C.POP_PRIOR, C.model_for(worst["q"], worst["r"])),
                                  SplitRole.EVALUATION, NamedStreams(seed), n_items, 45)
        u = stats.truncnorm.cdf(sp.latent.coefficients, lo, hi, loc=C.POP_PRIOR.mu0, scale=C.POP_PRIOR.tau0)
        cnt = np.histogram(u, bins=10, range=(0, 1))[0]
        L.append(f"| seed {seed} ({'V9' if seed == 61009 else 'fresh'}) | {n_items} | {stats.chisquare(cnt).pvalue:.3e} | "
                 f"{calibration.ks_uniform_pvalue(u):.3e} | {cnt.tolist()} |")
    L += ["", "Reading: the V9 a-sample itself is mildly unusual under the prior (its lowest deciles are under-filled, the "
          "same shape as the step-2 histogram). Every SBC test inherits this, so the small SBC p-values form one "
          "correlated cluster rather than many independent signals. The fresh sample is uniform, and step 3 did not "
          "replicate. Under positive dependence the step-5 arithmetic 1 - (1 - p)^n_tests is an upper bound for the chance "
          "probability of the minimum (Sidak inequality). The cluster as a whole corresponds to ONE chance event in the shared "
          "a-sample, with its own uniformity p-values in the table: unusual (about 1 in 100 to 200), but a property of the "
          "drawn a-values, not of the predictor."]
    out = ROOT / "docs" / "STAGE06_CALIBRATION_DIAGNOSTIC.md"
    out.write_text("\n".join(L) + "\n", encoding="utf-8", newline="\n")
    print(f"wrote {out}: worst {worst['test']} q={worst['q']} r={worst['r']} n={worst['n']} p={worst['p']:.2e}; "
          f"fresh p={p_fresh:.2e}; replicated={replicated}; KL_corr={kl_corr:.2e}")


if __name__ == "__main__":
    main()
