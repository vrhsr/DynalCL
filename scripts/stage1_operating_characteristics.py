"""Operating characteristics of the Stage 1A decision rules with synthetic "models" (version 2, after the independent
audit: findings A1, A2, A3, A9, A10; docs/DISCLOSURE_LOG_STAGE1.md S15). Version 1 is in git history.

Q1. Two independent replicates; in each, CONT and UNIF arms of M models are evaluated on the 10 Q1 cells. Truth per cell:
a position pi between the stability reference (0) and the population reference (1), an approximation error e shared by
both arms, Delta = the map's KL(pop || stab). Per model and system j:
    R_CONT = (1 - pi) Delta + e + (1 - pi) d_j + u^C_mk + eta,     R_UNIF = Delta + e + d_j + u^U_mk + eta',
    G = R_UNIF - R_CONT = pi Delta + pi d_j + (u^U - u^C) + (eta' - eta),
d_j the per-system fluctuation of KL(pop || stab) (sd = the map's per-context sd; so G's system variance grows with pi,
audit A3), u_mk the seed effect: one model-level effect shared across cells with correlation rho_cell (audit A2), sd s,
eta an interaction (sd = half the system sd). The 40 000 evaluation systems are represented by N_SIM systems with the
system sds scaled by sqrt(N_SIM / 40 000), which leaves the system part of every SE unchanged (DERIVED; audit confirmed).
**Critical value: the analysis's own procedure, the hierarchical bootstrap (`critical_value_bootstrap`)** at alpha =
0.025, computed per setting as the median over 5 simulated replicates with 1000 draws each (a bootstrap inside every one
of thousands of studies is unaffordable; the range of c across the 5 replicates is reported). Classification
`classify_q1_held`; a class counts only if both replicates agree. P_wrong counts POP <-> STAB swaps AND
WORSE-THAN-STAB for a POP truth (audit A10). PROCEED = >= 7 of 10 cells confirmed in one class and none in the other.

Q2. The two-way rule `classify_memorisation` on three representative cells. The real Q2 family has 480 statistics; its
critical value is emulated by the Bonferroni t value with M - 1 df (two-sided, alpha 0.025 over 480), which is
conservative relative to a max-statistic band (audit A9). Per-system distances are positively correlated (0.5).

Usage: python scripts/stage1_operating_characteristics.py --out <dir> [--part q1|q2|all] [--quick]
"""

from __future__ import annotations

import argparse
import csv
import itertools
import json
import math
import sys
import time
from pathlib import Path

import numpy as np
from scipy import stats as sps

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dynaicl_neural.analysis import (Statistic, band, classify_memorisation, classify_q1_held,  # noqa: E402
                                     critical_value_bootstrap, two_level)
from dynaicl_neural.seeds import role_seed  # noqa: E402

N_REAL, N_SIM, EPSILON, ALPHA = 40_000, 40, 0.01, 0.025
#: (r, n, Delta, per-context sd of KL(pop||stab)) for the 10 IDENTIFIABLE held-out Q1 cells of the map
#: (results_stage1/map_1A/map_decisions.csv, branch results-stage1-map-1A, commit a499874; sd = se x sqrt(40000)).
CELLS = [(0.25, 1, 0.0544, 0.070), (0.25, 2, 0.0472, 0.091), (0.25, 3, 0.0409, 0.083), (0.25, 5, 0.0309, 0.072),
         (1.0, 1, 0.0484, 0.093), (1.0, 2, 0.0415, 0.083), (1.0, 3, 0.0359, 0.077), (1.0, 5, 0.0274, 0.066),
         (4.0, 1, 0.0299, 0.077), (4.0, 2, 0.0226, 0.058)]
PROCEED_MIN_CELLS = 7


def truth_class(pi: float, e: float, gap: float) -> str:
    r_pop, g = (1 - pi) * gap + e, pi * gap
    if r_pop > gap + EPSILON:
        return "WORSE-THAN-STAB"
    if r_pop < gap / 2 and g > gap / 2:
        return "POP-LIKE"
    if r_pop > gap / 2 and abs(g) < gap / 2:
        return "STAB-LIKE"
    return "BOUNDARY"


def q1_replicate(rng, m, pi, e, s, rho):
    scale = math.sqrt(N_SIM / N_REAL)
    shared = {a: rng.normal(0.0, s, (m, 1)) for a in ("C", "U")}
    out = []
    for k, (_, _, gap, sd) in enumerate(CELLS):
        d = rng.normal(0.0, sd * scale, N_SIM)[None, :]
        u = {a: math.sqrt(rho) * shared[a] + math.sqrt(1 - rho) * rng.normal(0.0, s, (m, 1)) for a in ("C", "U")}
        cont = (1 - pi) * gap + e + (1 - pi) * d + u["C"] + rng.normal(0, 0.5 * sd * scale, (m, N_SIM))
        unif = gap + e + d + u["U"] + rng.normal(0, 0.5 * sd * scale, (m, N_SIM))
        out += [Statistic(f"R{k}", cont, "HELD"), Statistic(f"G{k}", unif - cont, "HELD")]
    return out


def q1_classify(stats, c):
    res = []
    for k, (_, _, gap, _) in enumerate(CELLS):
        res.append(classify_q1_held(band(*two_level(stats[2 * k].values), c),
                                    band(*two_level(stats[2 * k + 1].values), c), gap, EPSILON))
    return res


def q1_setting(rng, m, pi, e, s, rho, sims, c_reps=5, c_draws=1000):
    cs = [critical_value_bootstrap(q1_replicate(rng, m, pi, e, s, rho), ALPHA, c_draws, rng)[0] for _ in range(c_reps)]
    c = float(np.median(cs))
    counts, proceed = {}, 0
    for _ in range(sims):
        a = q1_classify(q1_replicate(rng, m, pi, e, s, rho), c)
        b = q1_classify(q1_replicate(rng, m, pi, e, s, rho), c)
        conf = [x if x == y else "INCONCLUSIVE" for x, y in zip(a, b)]
        for x in conf:
            counts[x] = counts.get(x, 0) + 1
        top = max(("POP-LIKE", "STAB-LIKE"), key=conf.count)
        other = "STAB-LIKE" if top == "POP-LIKE" else "POP-LIKE"
        proceed += conf.count(top) >= PROCEED_MIN_CELLS and conf.count(other) == 0
    tot = sims * len(CELLS)
    return c, (min(cs), max(cs)), {k: v / tot for k, v in counts.items()}, proceed / sims


def run_q1(out: Path, quick: bool) -> None:
    rng = np.random.default_rng(role_seed("stage1_oc", 0))
    if quick:
        grid, sims = list(itertools.product([0.0, 1.0], [0.005], [0.01], [16], [0.0])), 10
    else:
        grid = list(itertools.product([0.0, 0.5, 1.0], [0.0, 0.005, 0.01], [0.005, 0.01, 0.02, 0.03],
                                      [16, 32, 64, 128], [0.0, 0.9]))
        sims = 200
    rows, t0 = [], time.time()
    for i, (pi, e, s, m, rho) in enumerate(grid):
        c, c_range, probs, p_proceed = q1_setting(rng, m, pi, e, s, rho, sims)
        truths = {truth_class(pi, e, gap) for _, _, gap, _ in CELLS}
        truth = truths.pop() if len(truths) == 1 else "MIXED"
        wrong = {"POP-LIKE": probs.get("STAB-LIKE", 0.0) + probs.get("WORSE-THAN-STAB", 0.0),
                 "STAB-LIKE": probs.get("POP-LIKE", 0.0)}.get(truth, float("nan"))
        correct = probs.get(truth, 0.0) if truth in ("POP-LIKE", "STAB-LIKE") else float("nan")  # 0 if never seen
        rows.append({"pi": pi, "e": e, "s": s, "M": m, "rho_cell": rho, "truth": truth, "c_boot_median": c,
                     "c_min": c_range[0], "c_max": c_range[1], "sims": sims, "P_correct": correct, "P_wrong": wrong,
                     "P_POP": probs.get("POP-LIKE", 0.0), "P_STAB": probs.get("STAB-LIKE", 0.0),
                     "P_WORSE": probs.get("WORSE-THAN-STAB", 0.0), "P_INCONCLUSIVE": probs.get("INCONCLUSIVE", 0.0),
                     "P_PROCEED": p_proceed})
        print(f"[q1 {i + 1}/{len(grid)}] {time.time() - t0:.0f}s", flush=True)
    _write(out / "oc_q1_v2.csv", rows)


# ------------------------------------------------------------------------------------------------ Q2
Q2_CELLS = [("PROBE r=1 n=10 K=4", 0.136, 0.255, 0.045), ("PROBE r=1 n=20 K=8", 0.185, 0.274, 0.022),
            ("OOS r=1 n=10 K=64", 0.563, 0.848, 0.069)]
Q2_SD_FACTOR, N_REAL_Q2, Q2_FAMILY = 3.0, 10_000, 480


def q2_replicate(rng, m, pi, e, s, cell):
    _, s_lp, s_ls, s_ps = cell
    truth = {"lib": pi * s_lp + e, "pop": (1 - pi) * s_lp + e, "stab": (1 - pi) * s_ls + pi * s_ps + e}
    scale = math.sqrt(N_SIM / N_REAL_Q2)
    common = rng.normal(0, 1, N_SIM)                                   # positively correlated per-system distances
    seed = rng.normal(0, s, (m, 1))
    x = {}
    for k, v in truth.items():
        sd = Q2_SD_FACTOR * max(v, 0.005) * scale
        sysk = sd * (math.sqrt(0.5) * common + math.sqrt(0.5) * rng.normal(0, 1, N_SIM))
        x[k] = v + seed + rng.normal(0, s / 2, (m, 1)) + sysk[None, :] + rng.normal(0, sd, (m, N_SIM))
    return x


def q2_classify(x, c, cell):
    _, s_lp, s_ls, s_ps = cell
    dist = {k: band(*two_level(v), c) for k, v in x.items()}
    con = {(a, b): band(*two_level(x[a] - x[b]), c) for a in x for b in x if a != b}
    return classify_memorisation(dist, con, {("lib", "pop"): s_lp, ("lib", "stab"): s_ls, ("pop", "stab"): s_ps})


def run_q2(out: Path, quick: bool) -> None:
    rng = np.random.default_rng(role_seed("stage1_oc", 1))
    grid = list(itertools.product(Q2_CELLS, [0.0, 1.0], [0.0, 0.01], [0.01, 0.02, 0.05], [16, 32, 64, 128]))
    sims = 20 if quick else 300
    rows = []
    for cell, pi, e, s, m in (grid[:2] if quick else grid):
        c = float(sps.t.isf(ALPHA / (2 * Q2_FAMILY), m - 1))
        counts = {}
        for _ in range(sims):
            a = q2_classify(q2_replicate(rng, m, pi, e, s, cell), c, cell)
            b = q2_classify(q2_replicate(rng, m, pi, e, s, cell), c, cell)
            k = a if a == b else "INCONCLUSIVE"
            counts[k] = counts.get(k, 0) + 1
        truth = "LIB-LIKE" if pi == 0.0 else "GENERALISING"
        other = "GENERALISING" if truth == "LIB-LIKE" else "LIB-LIKE"
        rows.append({"cell": cell[0], "pi": pi, "e": e, "s": s, "M": m, "truth": truth, "c_bonferroni_t": c,
                     "sims": sims, "P_correct": counts.get(truth, 0) / sims, "P_wrong": counts.get(other, 0) / sims,
                     "P_NEITHER": counts.get("NEITHER", 0) / sims,
                     "P_INCONCLUSIVE": counts.get("INCONCLUSIVE", 0) / sims})
    _write(out / "oc_q2_v2.csv", rows)


def _write(path: Path, rows: list) -> None:
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--part", choices=("q1", "q2", "all"), default="all")
    ap.add_argument("--quick", action="store_true")
    args = ap.parse_args(argv)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    if args.part in ("q1", "all"):
        run_q1(out, args.quick)
    if args.part in ("q2", "all"):
        run_q2(out, args.quick)
    (out / f"oc_meta_v2_{args.part}.json").write_text(json.dumps({"seconds": time.time() - t0, "alpha": ALPHA,
                                                                 "cells": CELLS, "n_sim": N_SIM, "quick": args.quick},
                                                                indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
