"""Stage 0.5, Step 1: tabulate the current Stage 0 separability results. Reads the run files only and
infers nothing that is not in them.

    python scripts/review_stage0_results.py [run_dir]     -> docs/STAGE0_RESULTS_REVIEW.md

The Stage 0 grid varied sigma in {0.25, 1} with x_0 ~ N(0, 1). Log-score differences are invariant to a common
rescaling of (x, sigma) (docs/MATH.md section 11), so these cells correspond to initial-state-to-noise ratios
r = sd(x_0)/sigma in {4, 1}. Both labels are shown.
"""

from __future__ import annotations

import csv
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RUN = ROOT / "runs" / "20261009T094047949167Z_separability_9123175bb3"
DELTA = 0.02


def load(run: Path, name: str) -> list[dict]:
    return list(csv.DictReader(open(run / "results" / name, encoding="utf-8")))


def f(x, nd=4):
    return f"{float(x):+.{nd}f}"


def ci(r):
    m, se = float(r["mean_diff"]), float(r["se"])
    return f"[{m - 1.96 * se:+.4f}, {m + 1.96 * se:+.4f}]"


def ratio(sigma: str) -> str:
    return f"{1.0 / float(sigma):g}"


def main() -> None:
    run = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_RUN
    pairs = load(run, "paired_differences.csv")
    g_rows = load(run, "g_metric.csv")
    pred = load(run, "predictors.csv")
    L = [f"# Stage 0 results review (Stage 0.5, Step 1)", "",
         f"Source: `{run.relative_to(ROOT).as_posix()}` (60 cells, 2337 paired evaluation items per cell). "
         f"delta = {DELTA} nats, as pre-registered in Stage 0. 95% CI = mean +/- 1.96 SE (analytic, paired). "
         "r = sd(x_0)/sigma (r = 4 is sigma = 0.25; r = 1 is sigma = 1). Classification is the Stage 0 "
         "pre-registered rule. Positive differences favour the first-named predictor.", ""]

    # (a) matched vs context-only frontier
    L += ["## (a) Matched Bayesian reference vs the context-only frontier", "",
          "`frontier_all` = best context-only member on the selection split (flat-prior Bayes in every cell; "
          "it is given the true sigma). `frontier_strict` excludes sigma-informed members (it selected OLS Student-t, "
          "or OLS Gaussian in 2 cells).", ""]
    for cond in ("E-CONT", "E-LIB"):
        L += [f"### {cond}", "", "| r | K | n | h | vs frontier_all: mean (95% CI) | class | vs frontier_strict: mean (95% CI) | class |",
              "|---|---|---|---|---|---|---|---|"]
        rows = [r for r in pairs if r["condition"] == cond and r["A"] == "matched_reference" and r["B"] == "frontier_all"]
        for r in sorted(rows, key=lambda r: (-float(r["sigma"]), int(r["K"]), int(r["n"]), int(r["h"]))):
            key = {k: r[k] for k in ("sigma", "condition", "K", "n", "h")}
            s = next(x for x in pairs if all(x[k] == v for k, v in key.items()) and x["A"] == "matched_reference"
                     and x["B"] == "frontier_strict")
            L.append(f"| {ratio(r['sigma'])} | {r['K']} | {r['n']} | {r['h']} | {f(r['mean_diff'])} {ci(r)} | "
                     f"{r['classification']} | {f(s['mean_diff'])} {ci(s)} | {s['classification']} |")
        L.append("")

    # (b) library vs continuous
    L += ["## (b) Finite library vs continuous-prior Bayes", "",
          "E-CONT: matched = continuous; the row shows (library - continuous). E-LIB: matched = library; the row shows "
          "(library - continuous). 'material' means abs(mean) >= delta.", ""]
    L += ["| condition | r | K | n | h | library - continuous (95% CI) | z | class | material |", "|---|---|---|---|---|---|---|---|---|"]
    lib_rows = []
    for r in pairs:
        if r["condition"] == "E-CONT" and r["A"] == "matched_reference" and r["B"].startswith("library_K"):
            lib_rows.append((r, -1.0, r["B"][9:]))
        elif r["condition"] == "E-LIB" and r["A"] == "matched_reference" and r["B"] == "continuous_prior_bayes":
            lib_rows.append((r, 1.0, r["K"]))
    for r, sgn, k in sorted(lib_rows, key=lambda t: (t[0]["condition"], -float(t[0]["sigma"]), int(t[2]), int(t[0]["n"]), int(t[0]["h"]))):
        m, se = sgn * float(r["mean_diff"]), float(r["se"])
        L.append(f"| {r['condition']} | {ratio(r['sigma'])} | {k} | {r['n']} | {r['h']} | {m:+.4f} [{m - 1.96 * se:+.4f}, {m + 1.96 * se:+.4f}] | "
                 f"{sgn * float(r['z']):+.1f} | {r['classification']} | {'YES' if abs(m) >= DELTA else 'no'} |")
    L.append("")

    # (c) small relative to uncertainty
    small = [r for r in pairs if abs(float(r["z"])) < 2.0]
    L += ["## (c) Differences that are small relative to their uncertainty (abs(z) < 2)", "",
          f"{len(small)} of {len(pairs)} paired comparisons in the file have abs(z) < 2:", "",
          "| condition | r | K | n | h | A - B | mean | SE | z |", "|---|---|---|---|---|---|---|---|---|"]
    for r in sorted(small, key=lambda r: (r["condition"], r["A"], r["B"], -float(r["sigma"]), int(r["K"]), int(r["n"]))):
        L.append(f"| {r['condition']} | {ratio(r['sigma'])} | {r['K']} | {r['n']} | {r['h']} | {r['A']} - {r['B']} | "
                 f"{f(r['mean_diff'])} | {float(r['se']):.4f} | {float(r['z']):+.2f} |")
    L.append("")

    # (d) G
    ill = [r for r in g_rows if r["ill_conditioned"] == "True"]
    L += ["## (d) Population-knowledge gain G = (S_model - S_ctx)/(S_matched - S_ctx)", "",
          f"Ill-conditioned (abs(denominator) < 3 SE or < delta) in {len(ill)} of {len(g_rows)} rows. The "
          "denominator is matched - frontier. Ill-conditioned rows by (condition, r, n), counted over models and "
          "frontier types:", "", "| condition | r | n | ill-conditioned rows | denominator range |", "|---|---|---|---|---|"]
    groups = {}
    for r in g_rows:
        key = (r["condition"], ratio(r["sigma"]), int(r["n"]))
        groups.setdefault(key, []).append(r)
    for key in sorted(groups):
        rs = groups[key]
        n_ill = sum(r["ill_conditioned"] == "True" for r in rs)
        dens = [float(r["denominator"]) for r in rs]
        L.append(f"| {key[0]} | {key[1]} | {key[2]} | {n_ill}/{len(rs)} | {min(dens):+.4f} .. {max(dens):+.4f} |")
    L += ["", "Well-conditioned G values (frontier_all baseline):", "", "| condition | r | K | n | h | model | G +/- SE |",
          "|---|---|---|---|---|---|---|"]
    for r in g_rows:
        if r["ill_conditioned"] == "False" and r["context_baseline"] == "frontier_all":
            L.append(f"| {r['condition']} | {ratio(r['sigma'])} | {r['K']} | {r['n']} | {r['h']} | {r['model']} | "
                     f"{float(r['G']):.3f} +/- {float(r['G_se']):.3f} |")
    L.append("")

    # baseline performance
    L += ["## Baseline performance (mean log score, E-CONT)", "", "| r | n | h | matched | flat-prior | OLS-t | kernel RO | persistence |",
          "|---|---|---|---|---|---|---|---|"]
    by = {}
    for r in pred:
        if r["condition"] == "E-CONT":
            by.setdefault((r["sigma"], r["n"], r["h"]), {})[r["predictor"]] = float(r["mean_log_score"])
    for (s, n, h), d in sorted(by.items(), key=lambda t: (-float(t[0][0]), int(t[0][1]), int(t[0][2]))):
        L.append(f"| {ratio(s)} | {n} | {h} | {d['matched_reference']:.4f} | {d['flat_prior_bayes']:.4f} | "
                 f"{d['ols_student_t']:.4f} | {d['kernel_rolling_origin']:.4f} | {d['persistence']:.4f} |")
    out = ROOT / "docs" / "STAGE0_RESULTS_REVIEW.md"
    out.write_text("\n".join(L) + "\n", encoding="utf-8", newline="\n")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
