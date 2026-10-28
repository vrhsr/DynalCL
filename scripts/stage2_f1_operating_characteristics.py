"""Operating characteristics of the DRAFT F1 neural decision rules (docs/PREREG_stage2_F1.md), with synthetic "models".

Same simulation model, grid and decision rules as the frozen Stage 1A version 2 (scripts/stage1_operating_characteristics.py,
after audit finding A1): the critical value is the analysis's own hierarchical bootstrap (`critical_value_bootstrap` from
the frozen dynaicl_neural.analysis), median over 5 simulated replicates of 1000 draws, alpha = 0.025, two replicates must
agree, P_wrong counts POP <-> CTX swaps and WORSE-THAN-CTX for a POP truth. What changes is the cell set, read from the F1
map (branch results-stage1-step3, results_stage1/map_F1/f1_map_decisions.csv, copied to results_stage2/f1_inputs/ with its
sha256 checked):
* Q1: the 12 HELD pop|ctx cells marked IDENTIFIABLE (r in {0.25, 1, 4} x n in {2, 3, 5, 10}); Delta = estimate,
  per-context sd = SE x sqrt(20 000) with SE = (hi - lo) / 6 (the map's +/- 3 SE bound). PROCEED needs >= 9 of 12 cells
  (the Stage 1A proportion 7 of 10, rounded up).
* Q2: three representative designed-set cells (r = 1): PROBE n = 10 K = 4, PROBE n = 20 K = 8, OOS-A n = 10 K = 64, with
  separations |lib|pop|, |lib|ctx|, |pop|ctx| from the same file; family size for the Bonferroni-t emulation = 480 as Stage 1A
  (ASSUMED until the F1 Q2 family is fixed in the pre-registration).
Seeds: role f1_oc (config/stage2_seed_manifest.yaml). Usage:
    python scripts/stage2_f1_operating_characteristics.py --out results_stage2/f1_oc --workers 16 [--part q1|q2|all] [--quick]
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import itertools
import math
import sys
import time
from pathlib import Path

import numpy as np
from scipy import stats as sps

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dynaicl_families.stage2.seeds import role_seed  # noqa: E402
from dynaicl_neural.analysis import (Statistic, band, classify_memorisation, classify_q1_held,  # noqa: E402
                                     critical_value_bootstrap, two_level)

F1_MAP = ROOT / "results_stage2" / "f1_inputs" / "f1_map_decisions.csv"

N_REAL, N_SIM, EPSILON, ALPHA, MAP_N = 40_000, 40, 0.01, 0.025, 20_000
Q2_SD_FACTOR, N_REAL_Q2, Q2_FAMILY = 3.0, 10_000, 480


def load_map() -> tuple[list, list, str]:
    raw = F1_MAP.read_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    rows = list(csv.DictReader(raw.decode("utf-8").splitlines()))
    cells = []
    for r in rows:
        if r["set"] == "HELD" and r["pair"] == "pop|ctx" and r["decision"] == "IDENTIFIABLE":
            se = (float(r["hi"]) - float(r["lo"])) / 6.0
            cells.append((float(r["r"]), int(r["n"]), float(r["estimate"]), se * math.sqrt(MAP_N)))

    def est(s, pair, n, k):
        for r in rows:
            if (r["set"], r["pair"], r["r"], r["n"], r["K"]) == (s, pair, "1.0", str(n), str(k)):
                return abs(float(r["estimate"]))
        raise KeyError((s, pair, n, k))
    q2 = [(f"{s} r=1 n={n} K={k}", est(s, "lib|pop", n, k), est(s, "lib|ctx", n, k), est(s, "pop|ctx", n, 0))
          for s, n, k in (("PROBE", 10, 4), ("PROBE", 20, 8), ("OOS-A", 10, 64))]
    return cells, q2, sha


CELLS, Q2_CELLS, MAP_SHA = load_map()
PROCEED_MIN_CELLS = math.ceil(0.7 * len(CELLS))


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
        ctx = gap + e + d + u["U"] + rng.normal(0, 0.5 * sd * scale, (m, N_SIM))
        out += [Statistic(f"R{k}", cont, "HELD"), Statistic(f"G{k}", ctx - cont, "HELD")]
    return out


def q1_classify(stats, c):
    return [classify_q1_held(band(*two_level(stats[2 * k].values), c), band(*two_level(stats[2 * k + 1].values), c),
                             gap, EPSILON) for k, (_, _, gap, _) in enumerate(CELLS)]


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


def _q1_job(args):
    i, (pi, e, s, m, rho), sims = args
    rng = np.random.default_rng([role_seed("f1_oc", 0), i])      # per-setting stream: independent of worker count
    c, c_range, probs, p_proceed = q1_setting(rng, m, pi, e, s, rho, sims)
    return i, c, c_range, probs, p_proceed


def run_q1(out: Path, quick: bool, workers: int = 1) -> None:
    if quick:
        grid, sims = list(itertools.product([0.0, 1.0], [0.005], [0.01], [16], [0.0])), 10
    else:
        grid = list(itertools.product([0.0, 0.5, 1.0], [0.0, 0.005, 0.01], [0.005, 0.01, 0.02, 0.03, 0.05],
                                      [16, 32, 64, 128], [0.0, 0.9]))
        sims = 200
    rows, t0 = [], time.time()
    from concurrent.futures import ProcessPoolExecutor
    with ProcessPoolExecutor(max_workers=workers) as ex:
        results = sorted(ex.map(_q1_job, [(i, g, sims) for i, g in enumerate(grid)]), key=lambda x: x[0])
    for i, c, c_range, probs, p_proceed in results:
        pi, e, s, m, rho = grid[i]
        truths = {truth_class(pi, e, gap) for _, _, gap, _ in CELLS}
        truth = truths.pop() if len(truths) == 1 else "MIXED"
        wrong = {"POP-LIKE": probs.get("STAB-LIKE", 0.0) + probs.get("WORSE-THAN-STAB", 0.0),
                 "STAB-LIKE": probs.get("POP-LIKE", 0.0)}.get(truth, float("nan"))
        correct = probs.get(truth, 0.0) if truth in ("POP-LIKE", "STAB-LIKE") else float("nan")
        rows.append({"pi": pi, "e": e, "s": s, "M": m, "rho_cell": rho, "truth": truth, "c_boot_median": c,
                     "c_min": c_range[0], "c_max": c_range[1], "sims": sims, "P_correct": correct, "P_wrong": wrong,
                     "P_POP": probs.get("POP-LIKE", 0.0), "P_STAB": probs.get("STAB-LIKE", 0.0),
                     "P_WORSE": probs.get("WORSE-THAN-STAB", 0.0), "P_INCONCLUSIVE": probs.get("INCONCLUSIVE", 0.0),
                     "P_PROCEED": p_proceed, "map_sha256": MAP_SHA})
    print(f"q1: {len(grid)} settings in {time.time() - t0:.0f}s", flush=True)
    _write(out / "oc_q1_v2.csv", rows)


def q2_replicate(rng, m, pi, e, s, cell):
    _, s_lp, s_ls, s_ps = cell
    truth = {"lib": pi * s_lp + e, "pop": (1 - pi) * s_lp + e, "stab": (1 - pi) * s_ls + pi * s_ps + e}
    scale = math.sqrt(N_SIM / N_REAL_Q2)
    common = rng.normal(0, 1, N_SIM)
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


def _q2_job(args):
    i, (cell, pi, e, s, m), sims = args
    rng = np.random.default_rng([role_seed("f1_oc", 1), i])
    c = float(sps.t.isf(ALPHA / (2 * Q2_FAMILY), m - 1))
    counts = {}
    for _ in range(sims):
        a = q2_classify(q2_replicate(rng, m, pi, e, s, cell), c, cell)
        b = q2_classify(q2_replicate(rng, m, pi, e, s, cell), c, cell)
        k = a if a == b else "INCONCLUSIVE"
        counts[k] = counts.get(k, 0) + 1
    return i, c, counts


def run_q2(out: Path, quick: bool, workers: int = 1) -> None:
    grid = list(itertools.product(Q2_CELLS, [0.0, 1.0], [0.0, 0.01], [0.01, 0.02, 0.05, 0.1], [16, 32, 64, 128]))
    sims = 20 if quick else 300
    rows = []
    grid = grid[:2] if quick else grid
    from concurrent.futures import ProcessPoolExecutor
    with ProcessPoolExecutor(max_workers=workers) as ex:
        results = sorted(ex.map(_q2_job, [(i, g, sims) for i, g in enumerate(grid)]), key=lambda x: x[0])
    for i, c, counts in results:
        cell, pi, e, s, m = grid[i]
        truth = "LIB-LIKE" if pi == 0.0 else "GENERALISING"
        other = "GENERALISING" if truth == "LIB-LIKE" else "LIB-LIKE"
        rows.append({"cell": cell[0], "pi": pi, "e": e, "s": s, "M": m, "truth": truth, "c_bonferroni_t": c,
                     "sims": sims, "P_correct": counts.get(truth, 0) / sims, "P_wrong": counts.get(other, 0) / sims,
                     "P_NEITHER": counts.get("NEITHER", 0) / sims,
                     "P_INCONCLUSIVE": counts.get("INCONCLUSIVE", 0) / sims, "map_sha256": MAP_SHA})
    _write(out / "oc_q2_v2.csv", rows)


def _write(path: Path, rows: list) -> None:
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--part", choices=("q1", "q2", "all"), default="all")
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--workers", type=int, default=1)
    args = ap.parse_args(argv)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    print(f"F1 map {F1_MAP.name} sha256 {MAP_SHA}; {len(CELLS)} Q1 cells; PROCEED needs {PROCEED_MIN_CELLS}", flush=True)
    if args.part in ("q1", "all"):
        run_q1(out, args.quick, args.workers)
    if args.part in ("q2", "all"):
        run_q2(out, args.quick, args.workers)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
