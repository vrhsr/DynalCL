"""Stage 0.6 Phase C: planning calculations and the decision-rule dry run (user decision 7b). SYNTHETIC DATA ONLY.

    python scripts/stage06_decision_dry_run.py [--workers 8]  -> docs/STAGE06_DECISION_DRY_RUN.md (+ .json)

1. Planning spreads from the VERIFIED Stage 0.5 artifact (per-item matched - stability gains at q = 0; the frontier
   was stability-only in every E-CONT cell). Checksums are verified against the run's checksums.json.
   * L-proxy: per-system mean over n in {10, 20} (the Stage 0.5 context lengths inside L = 10..40), per (r, h):
     sd and the (r, h) correlation matrix. A proxy for the sd of the L-average: conservative if gains shrink with n.
   * Tier-2: per-system mean over n in {2, 3, 5, 10, 20}: sd per (r, h), and the expected combined SE at N = 4000 vs the
     pooled Stage 0.5 systems, against the precision bound.
2. Planning covariance for the 24 cells (4 q x 2 h x 3 r): sd_cell = kappa_q x sd_(r,h); corr = corr_(r,h) x rho_q,
   with kappa_0 = 1, kappa_q = kappa for q > 0 (noise inflation; planning assumption, 1 and 2), and
   rho_q = rho (planning assumption, 0.5; sensitivity 0.2) between different q levels.
3. Expected simultaneous half-widths at N = 4000 for gains and increments (full frozen bootstrap schedule).
4. Scenarios through the FROZEN analysis and decision code (dynaicl.experiments.stage06_analysis): synthetic per-item
   data at (system, cell, n) resolution, items = mu_cell + u_(system, cell) + tau e_(system, cell, n).
   B = 2000 draws per replicate in the Monte Carlo loop (documented deviation, for speed; the frozen schedule
   starts at 20000). Rates are reported with exact binomial 95% intervals.
Seeds: design_calculation root 61903 only. No confirmatory seed is used.
"""

from __future__ import annotations

import os

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):   # one BLAS thread per worker process
    os.environ.setdefault(_v, "1")

import argparse
import hashlib
import json
import math
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dynaicl.config.stage06_schema import load_stage06_config  # noqa: E402
from dynaicl.experiments import stage06_analysis as A  # noqa: E402
from dynaicl.rng import NamedStreams  # noqa: E402

SEED = 61903
CFG = load_stage06_config(ROOT / "config" / "stage06.yaml")
QS, HS, RS = CFG.model.noise_ratios, CFG.grid.horizons, CFG.model.initial_state_ratios
NS, L = CFG.grid.context_lengths, CFG.grid.long_context
N = CFG.grid.n_systems
AN = CFG.analysis
DELTA = AN.delta
CELLS = [(q, h, r) for q in QS for h in HS for r in RS]
HR = [(h, r) for h in HS for r in RS]
TAU = 0.02          # within-system per-n noise sd of the synthetic items (its L-average contributes TAU^2 / 31)
B_DRY = 2000


# ------------------------------------------------------------------------------------------ planning


def stage05_items() -> tuple[dict, dict]:
    run = ROOT / CFG.tier2.stage05_run
    sums = json.loads((run / "checksums.json").read_text(encoding="utf-8"))
    for rel in ("results/item_contrasts.npy", "results/item_contrasts_index.csv"):
        h = hashlib.sha256((run / rel).read_bytes()).hexdigest()
        if h != sums[rel]:
            raise RuntimeError(f"Stage 0.5 artifact checksum mismatch: {rel}")
    arr = np.load(run / "results" / "item_contrasts.npy")
    import csv
    with open(run / "results" / "item_contrasts_index.csv", encoding="utf-8") as fh:
        idx = list(csv.DictReader(fh))
    items = {(x["key"].split("|")[0], float(x["r"]), int(x["n"]), int(x["h"])): arr[int(x["row"])]
             for x in idx if x["condition"] == "E-CONT" and x["key"].endswith("matched_minus_frontier_ctx")}
    return items, sums


def planning_spreads(items: dict) -> dict:
    out = {"L_proxy_sd": {}, "tier2_sd": {}}
    per_rep = {}
    for rep in ("R1", "R2"):
        cols = []
        for (h, r) in HR:
            v = np.mean([items[(rep, r, n, h)] for n in (10, 20)], axis=0)
            cols.append(v)
        per_rep[rep] = np.column_stack(cols)
    pooled = np.vstack([per_rep["R1"], per_rep["R2"]])
    corr = np.mean([np.corrcoef(per_rep[k], rowvar=False) for k in per_rep], axis=0)
    for j, (h, r) in enumerate(HR):
        out["L_proxy_sd"][f"h={h}|r={r}"] = float(pooled[:, j].std(ddof=1))
    out["L_proxy_corr"] = corr.tolist()
    tier = {}
    for (h, r) in HR:
        v = np.concatenate([np.mean([items[(rep, r, n, h)] for n in CFG.tier2.context_lengths], axis=0)
                            for rep in ("R1", "R2")])
        tier[(h, r)] = v
        out["tier2_sd"][f"h={h}|r={r}"] = float(v.std(ddof=1))
    crit = A.tier2_criterion(2 * len(HR), CFG.tier2.alpha, CFG.tier2.power, DELTA)
    M = len(next(iter(tier.values())))
    out["tier2"] = {"criterion": crit, "stage05_systems_pooled": M, "stage06_systems": N,
                    "expected_combined_se": {f"h={h}|r={r}": float(tier[(h, r)].std(ddof=1) * math.sqrt(1 / N + 1 / M))
                                             for (h, r) in HR}}
    out["tier2"]["informative_expected"] = all(v <= crit["max_combined_se"]
                                               for v in out["tier2"]["expected_combined_se"].values())
    return out


def planning_cov(spreads: dict, kappa: float, rho_q: float) -> np.ndarray:
    sd_hr = np.array([spreads["L_proxy_sd"][f"h={h}|r={r}"] for (h, r) in HR])
    c_hr = np.array(spreads["L_proxy_corr"])
    K = len(CELLS)
    S = np.empty((K, K))
    for i, (q, h, r) in enumerate(CELLS):
        for j, (q2, h2, r2) in enumerate(CELLS):
            a, b = HR.index((h, r)), HR.index((h2, r2))
            ki, kj = (1.0 if q == 0 else kappa), (1.0 if q2 == 0 else kappa)
            S[i, j] = ki * kj * sd_hr[a] * sd_hr[b] * c_hr[a, b] * (1.0 if q == q2 else rho_q)
    return S


# ------------------------------------------------------------------------------------------ synthetic data


def synth_items(mu: dict, S: np.ndarray, rng: np.random.Generator, tails: str) -> dict:
    """Per-item gains (N, len(ns)) per cell. System effects u ~ N(0, S - TAU^2/|L| I) (or a scaled multivariate t5
    with the same covariance); per-n noise TAU e. The L-average then has covariance S exactly."""
    K = len(CELLS)
    Ssys = S - (TAU ** 2 / len(L)) * np.eye(K)
    C = np.linalg.cholesky(Ssys)
    Z = rng.standard_normal((N, K))
    if tails == "t5":
        Z = Z / np.sqrt(rng.chisquare(5, size=(N, 1)) / 5) * math.sqrt(3 / 5)
    U = Z @ C.T
    E = TAU * rng.standard_normal((N, K, len(NS)))
    return {cell: mu[cell] + U[:, k:k + 1] + E[:, k, :] for k, cell in enumerate(CELLS)}


def mu_for(name: str) -> dict:
    pos = lambda v, v0=0.0: {c: (v if c[0] > 0 else v0) for c in CELLS}  # noqa: E731
    if name == "null_zero":
        return pos(0.0)
    if name == "null_boundary_gain":
        return pos(DELTA)
    if name == "null_boundary_increment":
        return pos(0.04, 0.04)
    if name == "sub_threshold":
        return pos(0.01)
    if name.startswith("effect_"):
        return pos(float(name.split("_")[1]), 0.005)
    if name == "narrow_effect":
        return {c: (0.04 if (c[1] == 1 and c[2] in (1.0, 4.0) and c[0] in (2.56, 6.5)) else 0.0) for c in CELLS}
    if name == "single_cell":
        return {c: (0.06 if c == (2.56, 1, 1.0) else 0.0) for c in CELLS}
    if name == "negative_cell":
        return {c: (-0.03 if c == (6.5, 5, 4.0) else 0.0) for c in CELLS}
    if name in ("missing_cell", "nonfinite_item", "zero_variance_contrast", "critical_check_failure"):
        return mu_for("effect_0.04")
    raise KeyError(name)


def one_pair(args) -> dict:
    sc_idx, name, kappa, rho_q, tails, mc, spreads = args
    S = planning_cov(spreads, kappa, rho_q)
    mu = mu_for(name)
    streams = NamedStreams(SEED)
    reps = []
    for rep in range(2):
        items = synth_items(mu, S, streams.stream("dry_run_data", sc_idx, mc, rep), tails)
        if name == "missing_cell" and rep == 1:
            del items[(0.755, 1, 0.25)]
        if name == "nonfinite_item" and rep == 0:
            items[(2.56, 5, 1.0)][7, NS.index(20)] = np.nan
        if name == "zero_variance_contrast" and rep == 0:
            items[(6.5, 1, 0.25)][:] = 0.05
        reps.append(A.analyze_replicate(items, NS, L, QS, HS, RS, DELTA, AN.alpha, (B_DRY,), AN.bootstrap_chunk, 1.0,
                                        streams.stream("dry_run_bootstrap", sc_idx, mc, rep)))
    critical = {"tier1": True, "tier2": name != "critical_check_failure", "numerics": True, "calibration": True}
    dec = A.decide(reps, critical, QS, HS, RS, AN.min_scales)
    n_sup = sum(all(r["flags"].get(c, {}).get("SUPPORTED", False) for r in reps) for c in CELLS if c[0] > 0)
    return {"verdict": dec["verdict"], "strict": dec["strict_variant_holds"], "n_supported_both": n_sup,
            "reasons": dec["reasons"][:2], "c": [r.get("critical_value", {}).get("c") for r in reps]}


SCENARIOS = [  # (name, kappa, rho_q, tails, MC pairs)
    *[(s, k, 0.5, "normal", 100) for k in (1.0, 2.0) for s in
      ("null_zero", "null_boundary_gain", "null_boundary_increment", "sub_threshold", "effect_0.025", "effect_0.03",
       "effect_0.04", "narrow_effect", "single_cell")],
    ("null_boundary_gain", 2.0, 0.5, "t5", 100),
    *[(s, 2.0, 0.2, "normal", 100) for s in ("null_zero", "null_boundary_increment", "sub_threshold", "effect_0.04")],
    *[(s, 1.0, 0.5, "normal", 20) for s in ("negative_cell", "missing_cell", "nonfinite_item", "zero_variance_contrast",
                                                  "critical_check_failure")],
]


def clopper(k: int, n: int) -> tuple[float, float]:
    lo = 0.0 if k == 0 else float(stats.beta.ppf(0.025, k, n - k + 1))
    hi = 1.0 if k == n else float(stats.beta.ppf(0.975, k + 1, n - k))
    return lo, hi


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=8)
    args = ap.parse_args()
    t0 = time.time()
    items, _ = stage05_items()
    spreads = planning_spreads(items)

    # ---- expected simultaneous half-widths at the frozen schedule (one synthetic replicate per planning setting)
    streams = NamedStreams(SEED)
    hw = {}
    for j, (kappa, rho_q) in enumerate(((1.0, 0.5), (2.0, 0.5), (2.0, 0.2))):
        S = planning_cov(spreads, kappa, rho_q)
        it = synth_items(mu_for("null_zero"), S, streams.stream("planning_data", j), "normal")
        tb = time.time()
        res = A.analyze_replicate(it, NS, L, QS, HS, RS, DELTA, AN.alpha, AN.bootstrap_draws, AN.bootstrap_chunk,
                                  AN.critical_value_rel_mc_error, streams.stream("planning_bootstrap", j))
        secs = time.time() - tb
        assert res["ok"], res["error"]
        cv = res["critical_value"]
        sd = np.sqrt(np.diag(S))
        rows = []
        for (h, r) in HR:
            k_g = CELLS.index((QS[1], h, r))
            k_0 = CELLS.index((0.0, h, r))
            sd_g = sd[k_g]
            sd_i = math.sqrt(S[k_g, k_g] + S[k_0, k_0] - 2 * S[k_g, k_0])
            rows.append({"h": h, "r": r, "gain_halfwidth": cv["c"] * sd_g / math.sqrt(N),
                         "increment_halfwidth": cv["c"] * sd_i / math.sqrt(N)})
        hw[f"kappa={kappa}|rho_q={rho_q}"] = {"critical_value": cv, "bootstrap_seconds": round(secs, 2), "rows": rows}

    # ---- scenarios
    jobs = [(i, name, kappa, rho_q, tails, mc, spreads) for i, (name, kappa, rho_q, tails, n_mc) in enumerate(SCENARIOS)
            for mc in range(n_mc)]
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        results = list(pool.map(one_pair, jobs, chunksize=4))
    summary = []
    pos = 0
    for i, (name, kappa, rho_q, tails, n_mc) in enumerate(SCENARIOS):
        rs = results[pos:pos + n_mc]
        pos += n_mc
        counts = {v: sum(x["verdict"] == v for x in rs) for v in ("GO", "STOP", "REVISE", "BLOCKED")}
        summary.append({"scenario": name, "kappa": kappa, "rho_q": rho_q, "tails": tails, "pairs": n_mc,
                        "counts": counts, "intervals": {v: clopper(c, n_mc) for v, c in counts.items()},
                        "strict_variant": sum(x["strict"] for x in rs),
                        "median_cells_supported_both": float(np.median([x["n_supported_both"] for x in rs])),
                        "example_reasons": rs[0]["reasons"]})
    out = {"seed": SEED, "B_dry": B_DRY, "tau": TAU, "N": N, "spreads": spreads, "halfwidths": hw,
           "scenarios": summary, "seconds": round(time.time() - t0, 1)}
    (ROOT / "docs" / "STAGE06_DECISION_DRY_RUN.json").write_text(json.dumps(out, indent=2, sort_keys=True) + "\n",
                                                                 encoding="utf-8", newline="\n")
    (ROOT / "docs" / "STAGE06_DECISION_DRY_RUN.md").write_text(render(out), encoding="utf-8", newline="\n")
    print(f"done in {out['seconds']} s")
    for s in summary:
        print(f"{s['scenario']:26s} kappa={s['kappa']} rho_q={s['rho_q']} {s['tails']:6s} {s['counts']}")


def render(o: dict) -> str:
    sp = o["spreads"]
    L_ = ["# Stage 0.6 planning and decision-rule dry run (synthetic data only)", "",
          f"Generated by `scripts/stage06_decision_dry_run.py` (design seed {o['seed']}; no confirmatory seed used). "
          f"Runtime {o['seconds']} s.", "",
          "## 1. Planning spreads (VERIFIED Stage 0.5 artifact, zero noise, checksums verified)", "",
          "| h | r | sd of per-system mean over n in {10, 20} (L proxy) | sd of per-system mean over Tier-2 n | expected Tier-2 combined SE |",
          "|---|---|---|---|---|"]
    for (h, r) in HR:
        k = f"h={h}|r={r}"
        L_.append(f"| {h} | {r} | {sp['L_proxy_sd'][k]:.4f} | {sp['tier2_sd'][k]:.4f} | "
                  f"{sp['tier2']['expected_combined_se'][k]:.5f} |")
    t2 = sp["tier2"]
    L_ += ["", f"Tier-2 precision bound: combined SE <= delta / (z_crit + z_power) = {DELTA} / ({t2['criterion']['z_crit']:.3f} + "
           f"{t2['criterion']['z_power']:.3f}) = {t2['criterion']['max_combined_se']:.5f} (z_crit: two-sided Bonferroni over "
           f"{t2['criterion']['n_tests']} tests at alpha = {CFG.tier2.alpha}). Stage 0.5 pooled systems: {t2['stage05_systems_pooled']}; "
           f"Stage 0.6 per replicate: {t2['stage06_systems']}. **Expected informative: {t2['informative_expected']}**.", "",
          "The (r, h) correlation matrix of the L proxy (average over the two Stage 0.5 replicates), order "
          + ", ".join(f"(h={h}, r={r})" for (h, r) in HR) + ":", "", "```"]
    for row in sp["L_proxy_corr"]:
        L_.append("  ".join(f"{v:+.3f}" for v in row))
    L_ += ["```", "", f"## 2. Expected simultaneous half-widths at N = {o['N']} (frozen schedule, 36 contrasts, alpha = {AN.alpha})", "",
           "Planning assumptions: kappa = sd inflation of positive-noise cells relative to zero noise; rho_q = correlation "
           "between noise levels of one system. Neither is estimable from Stage 0.5 (no noisy data).", ""]
    for key, v in o["halfwidths"].items():
        cv = v["critical_value"]
        L_ += [f"### {key}: c = {cv['c']:.4f} after {cv['draws']} draws; relative MC error {cv['rel_mc_error']:.4f} "
               f"(tolerance {AN.critical_value_rel_mc_error}); 95% MC interval of c {cv['c_mc_interval'][0]:.4f} to "
               f"{cv['c_mc_interval'][1]:.4f}; bootstrap time {v['bootstrap_seconds']} s", "",
               "| h | r | gain half-width | increment half-width |", "|---|---|---|---|"]
        for x in v["rows"]:
            L_.append(f"| {x['h']} | {x['r']} | {x['gain_halfwidth']:.4f} | {x['increment_halfwidth']:.4f} |")
        L_.append("")
    L_ += ["## 3. Scenarios through the frozen analysis and decision code", "",
           f"Synthetic per-item data at (system, cell, n) resolution, N = {o['N']} per replicate, 39 context lengths, tau = "
           f"{o['tau']}. B = {o['B_dry']} draws per replicate (deviation from the frozen 20000, for speed only). 95% "
           "Clopper-Pearson intervals in brackets.", "",
           "| scenario | kappa | rho_q | tails | pairs | GO | STOP | REVISE | BLOCKED | strict variant | median cells SUPPORTED in both |",
           "|---|---|---|---|---|---|---|---|---|---|---|"]
    for s in o["scenarios"]:
        f = lambda v: f"{s['counts'][v]} [{s['intervals'][v][0]:.3f}, {s['intervals'][v][1]:.3f}]"  # noqa: E731
        L_.append(f"| {s['scenario']} | {s['kappa']} | {s['rho_q']} | {s['tails']} | {s['pairs']} | {f('GO')} | {f('STOP')} | "
                  f"{f('REVISE')} | {f('BLOCKED')} | {s['strict_variant']} | {s['median_cells_supported_both']:.0f} |")
    sc = {(s["scenario"], s["kappa"], s["rho_q"], s["tails"]): s for s in o["scenarios"]}
    nulls = [s for k, s in sc.items() if k[0].startswith("null_")]
    go_null = sum(s["counts"]["GO"] for s in nulls)
    n_null = sum(s["pairs"] for s in nulls)
    L_ += ["", "### Required quantities (user decision 7b)", "",
           f"- **False-GO rate under the nulls** (all null_* rows pooled): {go_null}/{n_null}, 95% upper bound "
           f"{clopper(go_null, n_null)[1]:.4f}. Theoretical bound for a fixed GO claim: a false SUPPORTED flag is needed "
           f"in BOTH independent replicates, each at familywise level <= alpha = {AN.alpha}, so <= alpha^2 = {AN.alpha ** 2:.4f}.",
           "- **GO probability under effects:** " + "; ".join(
               f"{k[0]} (kappa {k[1]}, rho_q {k[2]}): {s['counts']['GO']}/{s['pairs']}" for k, s in sc.items()
               if k[0].startswith("effect_") or k[0] == "narrow_effect") + ".",
           "- **STOP probability:** " + "; ".join(
               f"{k[0]} (kappa {k[1]}, rho_q {k[2]}): {s['counts']['STOP']}/{s['pairs']}" for k, s in sc.items()
               if k[0] in ("null_zero", "sub_threshold")) + ".",
           "- **BLOCKED handling:** " + "; ".join(
               f"{k[0]}: {s['counts']['BLOCKED']}/{s['pairs']}" for k, s in sc.items()
               if k[0] in ("negative_cell", "missing_cell", "nonfinite_item", "zero_variance_contrast",
                           "critical_check_failure")) + ".",
           "- **BLOCKED under exact-zero gains:** the rule 'any primary gain with adjusted upper bound < 0' tests "
           "H0: gain >= 0 for 18 cells in each replicate. At the boundary gain = 0 in every cell it fires at up to about "
           "alpha/2 per replicate (one side of the two-sided band), so about 5% per pair (rows null_zero, single_cell, "
           "narrow_effect). DERIVED: each true gain is an expected KL divergence (strict propriety of the log score; the "
           "population reference is the exact posterior predictive of the data-generating process), so gain >= 0, with "
           "equality only if the two predictives coincide. The exact-zero rows are therefore the least favourable case.",
           "- **Limitation:** with uniformly sub-threshold gains (delta/2) and noise-inflated spread (kappa = 2), STOP is "
           "rarely reached (2-3/100); the verdict is then REVISE. STOP is an intersection claim over 18 cells x 2 "
           "replicates on simultaneous bounds, which is conservative by design (an intersection-union test would allow "
           "unadjusted one-sided bounds)."]
    L_ += ["", "Scenario definitions (gain means mu; q = 0 cells are the zero-noise control):", "",
           "- null_zero: every mu = 0.",
           f"- null_boundary_gain: positive-q mu = delta = {DELTA} exactly, q = 0 mu = 0 (G+ at its null boundary; I+ true).",
           "- null_boundary_increment: every mu = 0.04, including q = 0 (I+ at its null boundary; G+ true).",
           "- sub_threshold: positive-q mu = 0.01, q = 0 mu = 0.",
           "- effect_x: positive-q mu = x, q = 0 mu = 0.005.",
           "- narrow_effect: mu = 0.04 only at h = 1, r in {1, 4}, q in {2.56, 6.5}; 0 elsewhere.",
           "- single_cell: mu = 0.06 at (q 2.56, h 1, r 1) only.",
           "- negative_cell: mu = -0.03 at (q 6.5, h 5, r 4) only.",
           "- missing_cell: effect_0.04 with cell (0.755, 1, 0.25) absent from R2.",
           "- nonfinite_item: effect_0.04 with one non-finite per-item gain in R1 (inside L).",
           "- zero_variance_contrast: effect_0.04 with a constant cell in R1 (zero standard error: the bootstrap cannot studentize).",
           "- critical_check_failure: effect_0.04 with a failed Tier-2 gate.", "",
           "Example reasons (first pair of each scenario):", ""]
    for s in o["scenarios"]:
        L_.append(f"- {s['scenario']} (kappa {s['kappa']}, rho_q {s['rho_q']}, {s['tails']}): {s['example_reasons']}")
    return "\n".join(L_) + "\n"


if __name__ == "__main__":
    main()
