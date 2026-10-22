"""Stage 0.5 results tables, generated from a confirmatory run's files (no inference beyond them).

    python scripts/summarize_stage05.py [run_dir]   -> docs/STAGE05_RESULTS_TABLES.md

Per-replicate classes are the pre-registered ones (mean +/- 2.24 SE vs delta). "Pooled" (the average of the two
replicates, SE = sqrt(se1^2 + se2^2)/2, 95% CI) is shown for effect size only; decisions never use it.
"""

from __future__ import annotations

import csv
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT = ROOT / "runs" / "20261010T053729455237Z_stage05_population_advantage_51c7621b7a"


def main() -> None:
    run = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT
    res = run / "results"
    C = list(csv.DictReader(open(res / "contrasts.csv", encoding="utf-8")))
    summ = json.loads((res / "summary.json").read_text(encoding="utf-8"))
    idx = defaultdict(dict)
    for x in C:
        idx[(x["condition"], x["r"], x["K"], x.get("library_K") or x["K"], x["n"], x["h"], x["contrast"])][x["replicate"]] = x

    def cell(cond, r, K, libK, n, h, contrast):
        d = idx[(cond, r, K, libK, n, h, contrast)]
        xs = [d[k] for k in sorted(d)]
        m = sum(float(x["mean"]) for x in xs) / len(xs)
        se = math.sqrt(sum(float(x["se"]) ** 2 for x in xs)) / len(xs)
        classes = [x["class"] for x in xs]
        conf = classes[0] if len(set(classes)) == 1 else "DISCORDANT"
        return m, se, conf, xs

    rs, ns, hs, Ks = ("0.25", "1.0", "4.0"), ("1", "2", "3", "5", "10", "20"), ("1", "5"), ("2", "4", "8")
    L = ["# Stage 0.5 results tables", "",
         f"Source: `{run.relative_to(ROOT).as_posix()}` (config hash {summ.get('config_hash', '')}; see provenance.json). "
         "All values in nats per forecast. **Confirmed** = same pre-registered class in both replicates R1 and R2. "
         "'Pooled' is the average of the replicates, with a 95% CI (reporting only).", "",
         f"Decision: **{summ['decision']['verdict']}**: {summ['decision']['reason']}.", ""]

    L += ["## 1. Primary, held-out systems (E-CONT): matched - frontier_ctx", "",
          "frontier_ctx was the generic-stability Bayes member in every E-CONT cell (see frontier_selection.json).", "",
          "| r | h | n | R1 | R2 | pooled [95% CI] | confirmed | matched - flat (pooled) | stability - flat (pooled) |",
          "|---|---|---|---|---|---|---|---|---|"]
    for r in rs:
        for h in hs:
            for n in ns:
                m, se, conf, xs = cell("E-CONT", r, "0", "0", n, h, "matched_minus_frontier_ctx")
                mf = cell("E-CONT", r, "0", "0", n, h, "matched_minus_flat")[0]
                sf = cell("E-CONT", r, "0", "0", n, h, "stability_minus_flat")[0]
                L.append(f"| {r} | {h} | {n} | {float(xs[0]['mean']):+.4f} | {float(xs[1]['mean']):+.4f} | "
                         f"{m:+.4f} [{m - 1.96 * se:+.4f}, {m + 1.96 * se:+.4f}] | {conf} | {mf:+.4f} | {sf:+.4f} |")
    L.append("")

    L += ["## 2. Primary, in-library systems (E-LIB): matched (library) - frontier_ctx", "",
          "| h | K | r | " + " | ".join(f"n={n}" for n in ns) + " |", "|---|---|---|" + "---|" * len(ns)]
    for h in hs:
        for K in Ks:
            for r in rs:
                cells = []
                for n in ns:
                    m, se, conf, _ = cell("E-LIB", r, K, K, n, h, "matched_minus_frontier_ctx")
                    cells.append(f"{m:+.3f} {conf}")
                L.append(f"| {h} | {K} | {r} | " + " | ".join(cells) + " |")
    L.append("")

    L += ["## 3. Secondary: finite library - continuous-prior Bayes", "",
          "E-CONT: library mismatched (expected <= 0). E-LIB: library matched (expected >= 0).", "",
          "| condition | h | K | r | " + " | ".join(f"n={n}" for n in ns) + " |", "|---|---|---|---|" + "---|" * len(ns)]
    counts = defaultdict(lambda: defaultdict(int))
    for cond, Kfield in (("E-CONT", lambda K: "0"), ("E-LIB", lambda K: K)):
        for h in hs:
            for K in Ks:
                for r in rs:
                    cells = []
                    for n in ns:
                        m, se, conf, _ = cell(cond, r, Kfield(K), K, n, h, "library_minus_continuous")
                        cells.append(f"{m:+.3f} {conf}")
                        counts[(cond, K)][conf] += 1
                    L.append(f"| {cond} | {h} | {K} | {r} | " + " | ".join(cells) + " |")
    L += ["", "Confirmed secondary classes by (condition, K):", ""]
    for key in sorted(counts):
        L.append(f"- {key[0]} K={key[1]}: " + ", ".join(f"{c}={v}" for c, v in sorted(counts[key].items())))
    L.append("")

    rel = summ["reliability"]
    L += ["## 4. Reference reliability (P1)", "",
          f"- T1: {rel['T1_violations']} violations / {rel['T1_comparisons']} paired comparisons (min z {rel['T1_min_z']:.2f})",
          f"- T2: {rel['T2_failures']} calibration failures / {rel['T2_cells']} cell-replicates (min p {rel['T2_min_p']:.1e}, "
          f"per-test level {rel['T2_per_test_level']:.1e})",
          f"- quadrature node-doubling error at targets: max {rel['max_quadrature_error']:.1e}; matched cap rate {rel['max_matched_capped_rate']}",
          f"- bootstrap vs analytic class agreement (primary): {summ['bootstrap_agreement']['agree']}/{summ['bootstrap_agreement']['total']}", ""]
    out = ROOT / "docs" / "STAGE05_RESULTS_TABLES.md"
    out.write_text("\n".join(L) + "\n", encoding="utf-8", newline="\n")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
