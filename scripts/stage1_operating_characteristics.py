"""Operating characteristics of the Stage 1A Q1 decision rule with synthetic "models" (plan v2 section 8).

Each simulated study has two independent replicates. In each replicate, two arms (CONT, UNIF) of M models are
evaluated on the 10 Q1 cells that the separability map marked IDENTIFIABLE on held-out systems. Per cell the true
values are set by a position pi between the stability reference (pi = 0) and the population reference (pi = 1) plus
an approximation error e shared by both arms:
    R_pop(CONT) = (1 - pi) Delta + e,   R_pop(UNIF) = Delta + e,   G = R_pop(UNIF) - R_pop(CONT) = pi Delta.
Per-model, per-system values follow the crossed model mu + u_m + e_j + eta_mj with seed sd s, system sd kappa x
(the map's per-context sd of KL(pop || stab) in that cell) and an interaction of the same size. To keep the cost
affordable, the 40 000 evaluation systems are represented by N_SIM systems whose sd is scaled by sqrt(N_SIM / 40 000),
which leaves the system part of the standard error unchanged.

Through the real analysis code: ``two_level`` estimates and SEs, ``critical_value_gaussian`` (one critical value per
setting, from the first simulated replicate's estimated covariance; the bootstrap is too expensive inside thousands
of studies, and tests_stage1/test_analysis.py checks the two agree), and ``classify_q1_held``. A class counts only if
both replicates give it; otherwise the cell is INCONCLUSIVE.

Usage: python scripts/stage1_operating_characteristics.py --out <dir> [--quick]
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

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dynaicl_neural.analysis import (Statistic, band, classify_q1_held, covariance_of_estimates,  # noqa: E402
                                     critical_value_gaussian, two_level)

OC_SEED = 70101            # role stage1_oc (synthetic studies only)
N_REAL = 40_000
N_SIM = 40
EPSILON = 0.01
ALPHA = 0.05
#: (r, n, Delta, per-context sd of KL(pop||stab)) for the 10 IDENTIFIABLE held-out Q1 cells of the map
#: (results_stage1/map_1A/map_decisions.csv, branch results-stage1-map-1A, commit a499874; sd = se x sqrt(40000)).
CELLS = [(0.25, 1, 0.0544, 0.070), (0.25, 2, 0.0472, 0.091), (0.25, 3, 0.0409, 0.083), (0.25, 5, 0.0309, 0.072),
         (1.0, 1, 0.0484, 0.093), (1.0, 2, 0.0415, 0.083), (1.0, 3, 0.0359, 0.077), (1.0, 5, 0.0274, 0.066),
         (4.0, 1, 0.0299, 0.077), (4.0, 2, 0.0226, 0.058)]
PROCEED_MIN_CELLS = 7      # of 10: CONT confirmed in the same class in at least 70% of the identifiable cells


def truth_class(pi: float, e: float, gap: float) -> str:
    r_pop, g = (1 - pi) * gap + e, pi * gap
    if r_pop > gap + EPSILON:
        return "WORSE-THAN-STAB"
    if r_pop < gap / 2 and g > gap / 2:
        return "POP-LIKE"
    if r_pop > gap / 2 and abs(g) < gap / 2:
        return "STAB-LIKE"
    return "BOUNDARY"


def one_replicate(rng, m, pi, e, s, kappa):
    stats = []
    scale = math.sqrt(N_SIM / N_REAL)
    for k, (_, _, gap, sd) in enumerate(CELLS):
        sys_eff = rng.normal(0.0, kappa * sd * scale, N_SIM)            # shared by both arms (same systems)
        cont = (1 - pi) * gap + e + rng.normal(0, s, (m, 1)) + sys_eff + rng.normal(0, kappa * sd * scale, (m, N_SIM))
        unif = gap + e + rng.normal(0, s, (m, 1)) + sys_eff + rng.normal(0, kappa * sd * scale, (m, N_SIM))
        stats.append(Statistic(f"R{k}", cont, "HELD"))
        stats.append(Statistic(f"G{k}", unif - cont, "HELD"))
    return stats


def classify_replicate(stats, c):
    out = []
    for k, (_, _, gap, _) in enumerate(CELLS):
        r = band(*two_level(stats[2 * k].values), c)
        g = band(*two_level(stats[2 * k + 1].values), c)
        out.append(classify_q1_held(r, g, gap, EPSILON))
    return out


def run_setting(rng, m, pi, e, s, kappa, sims, alpha=ALPHA):
    c = critical_value_gaussian(covariance_of_estimates(one_replicate(rng, m, pi, e, s, kappa)), alpha, rng, 20000)
    counts = {}
    proceed = 0
    for _ in range(sims):
        a = classify_replicate(one_replicate(rng, m, pi, e, s, kappa), c)
        b = classify_replicate(one_replicate(rng, m, pi, e, s, kappa), c)
        conf = [x if x == y else "INCONCLUSIVE" for x, y in zip(a, b)]
        for x in conf:
            counts[x] = counts.get(x, 0) + 1
        top = max(("POP-LIKE", "STAB-LIKE"), key=conf.count)
        proceed += conf.count(top) >= PROCEED_MIN_CELLS
    tot = sims * len(CELLS)
    return c, {k: v / tot for k, v in counts.items()}, proceed / sims


# ------------------------------------------------------------------------------------------------ Q2 (three references)
#: Representative identifiable Q2 cells from the map (mean over draws of the behavioural separations):
#: (label, sep(lib, pop), sep(lib, stab), sep(pop, stab)).
Q2_CELLS = [("PROBE r=1 n=10 K=4", 0.136, 0.255, 0.045), ("PROBE r=1 n=20 K=8", 0.185, 0.274, 0.022),
            ("OOS r=1 n=10 K=64", 0.563, 0.848, 0.069)]
#: ASSUMED per-context sd of a KL distance = 3 x its mean (KL per context is skewed); the map's per-context sds
#: for these sets are in map_rows.csv, which stays on the box.
Q2_SD_FACTOR = 3.0
N_REAL_Q2 = 2_000


def q2_truth(pi, e, s_lp, s_ls, s_ps):
    """Model on the lib -> pop axis: pi = 0 is the library posterior, pi = 1 the population posterior."""
    return {"lib": pi * s_lp + e, "pop": (1 - pi) * s_lp + e, "stab": (1 - pi) * s_ls + pi * s_ps + e}


def q2_replicate(rng, m, pi, e, s, cell):
    from dynaicl_neural.analysis import classify_behavioural
    _, s_lp, s_ls, s_ps = cell
    truth = q2_truth(pi, e, s_lp, s_ls, s_ps)
    scale = math.sqrt(N_SIM / N_REAL_Q2)
    sys_eff = {k: rng.normal(0, Q2_SD_FACTOR * max(v, 0.005) * scale, N_SIM) for k, v in truth.items()}
    seed_eff = rng.normal(0, s, (m, 1))
    x = {k: v + seed_eff + rng.normal(0, s / 2, (m, 1)) + sys_eff[k][None, :]
         + rng.normal(0, Q2_SD_FACTOR * max(v, 0.005) * scale, (m, N_SIM)) for k, v in truth.items()}
    stats = [Statistic(f"D_{k}", v, "SET") for k, v in x.items()]
    stats += [Statistic(f"C_{a}_{b}", x[a] - x[b], "SET") for a in x for b in x if a != b]
    return stats, classify_behavioural


def q2_classify(stats, c, cell, classify):
    _, s_lp, s_ls, s_ps = cell
    est = {s.name: band(*two_level(s.values), c) for s in stats}
    dist = {k: est[f"D_{k}"] for k in ("lib", "pop", "stab")}
    con = {(a, b): est[f"C_{a}_{b}"] for a in dist for b in dist if a != b}
    from dynaicl_neural.analysis import classify_memorisation
    sep = {("lib", "pop"): s_lp, ("lib", "stab"): s_ls, ("pop", "stab"): s_ps}
    return classify_memorisation(dist, con, sep), classify(dist, con, sep)


def run_q2(rng, out: Path, sims: int, c_override: float | None = None, tag: str = "") -> None:
    rows = []
    for cell, pi, e, s, m in itertools.product(Q2_CELLS, [0.0, 0.5, 1.0], [0.0, 0.01], [0.01, 0.02, 0.05],
                                               [8, 16, 32, 64]):
        stats, classify = q2_replicate(rng, m, pi, e, s, cell)
        c = (critical_value_gaussian(covariance_of_estimates(stats), ALPHA, rng, 20000) if c_override is None
             else c_override)
        counts, counts3 = {}, {}
        for _ in range(sims):
            a, a3 = q2_classify(q2_replicate(rng, m, pi, e, s, cell)[0], c, cell, classify)
            b, b3 = q2_classify(q2_replicate(rng, m, pi, e, s, cell)[0], c, cell, classify)
            k = a if a == b else "INCONCLUSIVE"
            k3 = a3 if a3 == b3 else "INCONCLUSIVE"
            counts[k] = counts.get(k, 0) + 1
            counts3[k3] = counts3.get(k3, 0) + 1
        truth = {0.0: "LIB-LIKE", 1.0: "GENERALISING"}.get(pi, "BETWEEN")
        rows.append({"cell": cell[0], "pi": pi, "e": e, "s": s, "M": m, "truth": truth, "c": c, "sims": sims,
                     **{f"P_{k}": counts.get(k, 0) / sims for k in ("LIB-LIKE", "GENERALISING", "NEITHER",
                                                                    "INCONCLUSIVE")},
                     **{f"P3_{k}": counts3.get(k, 0) / sims for k in ("LIB-LIKE", "POP-LIKE", "STAB-LIKE", "NEITHER",
                                                                     "INCONCLUSIVE")}})
    with open(out / f"oc_q2{tag}.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--q2-only", action="store_true")
    ap.add_argument("--alpha", type=float, default=ALPHA, help="Q1 family level per replicate")
    ap.add_argument("--q2-c", type=float, default=None, help="fixed Q2 critical value (emulates the family size)")
    ap.add_argument("--tag", default="")
    args = ap.parse_args(argv)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    if args.q2_only:
        run_q2(np.random.default_rng(OC_SEED + 1), out, 20 if args.quick else 300, args.q2_c, args.tag)
        return 0
    rng = np.random.default_rng(OC_SEED)
    if args.quick:
        grid = list(itertools.product([0.0, 1.0], [0.005], [0.01], [16], [1.0]))
        sims = 20
    else:
        grid = list(itertools.product([0.0, 0.25, 0.5, 0.75, 1.0], [0.0, 0.005, 0.01], [0.005, 0.01, 0.02, 0.03],
                                      [8, 16, 32, 64], [1.0, 2.0]))
        sims = 300
    rows = []
    t0 = time.time()
    for i, (pi, e, s, m, kappa) in enumerate(grid):
        c, probs, p_proceed = run_setting(rng, m, pi, e, s, kappa, sims, args.alpha)
        truths = {truth_class(pi, e, gap) for _, _, gap, _ in CELLS}
        truth = truths.pop() if len(truths) == 1 else "MIXED"
        wrong = (probs.get("STAB-LIKE", 0.0) if truth == "POP-LIKE" else
                 probs.get("POP-LIKE", 0.0) if truth == "STAB-LIKE" else float("nan"))
        rows.append({"pi": pi, "e": e, "s": s, "M": m, "kappa": kappa, "truth": truth, "c": c, "sims": sims,
                     "P_POP": probs.get("POP-LIKE", 0.0), "P_STAB": probs.get("STAB-LIKE", 0.0),
                     "P_WORSE": probs.get("WORSE-THAN-STAB", 0.0), "P_INCONCLUSIVE": probs.get("INCONCLUSIVE", 0.0),
                     "P_wrong_class": wrong, "P_PROCEED": p_proceed})
        if (i + 1) % 20 == 0 or i + 1 == len(grid):
            print(f"[{i + 1}/{len(grid)}] {time.time() - t0:.0f}s", flush=True)
    with open(out / f"oc_q1{args.tag}.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    (out / f"oc_q1{args.tag}_meta.json").write_text(json.dumps({"seed": OC_SEED, "n_sim": N_SIM, "n_real": N_REAL,
                                                      "cells": CELLS, "alpha": args.alpha, "epsilon": EPSILON,
                                                      "proceed_min_cells": PROCEED_MIN_CELLS, "sims": sims,
                                                      "seconds": time.time() - t0}, indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
