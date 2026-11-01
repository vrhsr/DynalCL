"""Q2 operating characteristics and power lookup for the F2 memorisation-transition draft
(docs/STAGE3_F2_DESIGN_CPU_SPEC.md B).

Synthetic "models": the simulation model and rules are the F1 Q2 ones (scripts/stage2_f1_operating_characteristics.py,
`q2_replicate` and `q2_classify` imported unchanged; Bonferroni-t critical value, family size 480 ASSUMED as F1; two
replicates must agree). What changes is the cell set: held-out F2 cells read with `git show` from the pinned F2 map
rows (results-stage2-cpu-batch23 @ 56e73a8), r = 1, n in {10, 20}, K in {16, 64}: s_lp = mean over library draws of
the pop-lib gap, s_ps = the pop-ctx gap, s_ls = |s_ps - s_lp| (paired identity on the same items). The lookup uses the
frozen rule (scripts/stage1_power_lookup.py `lookup`, unchanged). Seeds: role f2_oc (smoke: f2_tests).

    python scripts/stage3_f2_operating_characteristics.py --out results_stage2/f2_oc --workers 8 [--smoke]
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import importlib.util
import io
import itertools
import json
import os
import platform
import subprocess
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
from scipy import stats as sps

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

MAP_REF, MAP_PATH = "56e73a864cdfe6a4ab4d63c43f55ab5aa3bd2ac3", "results_stage2/f2_map/map_rows.csv.gz"
CELL_SPEC = [(1.0, n, k) for n in (10, 20) for k in (16, 64)]
SOURCES = ["scripts/stage3_f2_operating_characteristics.py", "scripts/stage2_f1_operating_characteristics.py",
           "scripts/stage1_power_lookup.py", "docs/STAGE3_F2_DESIGN_CPU_SPEC.md", "config/stage2_seed_manifest.yaml"]


def _load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


F1OC = _load("f1_oc", "scripts/stage2_f1_operating_characteristics.py")
LOOKUP = _load("power_lookup", "scripts/stage1_power_lookup.py")


def load_cells() -> tuple[list, str]:
    raw = subprocess.run(["git", "show", f"{MAP_REF}:{MAP_PATH}"], cwd=ROOT, capture_output=True, check=True).stdout
    rows = list(csv.DictReader(io.StringIO(gzip.decompress(raw).decode("utf-8"))))
    cells = []
    for r, n, k in CELL_SPEC:
        lib = [float(x["mean"]) for x in rows if x["set"] == "HELD" and x["pair"] == "pop-lib" and float(x["r"]) == r
               and int(x["n"]) == n and int(x["K"]) == k]
        ctx = [float(x["mean"]) for x in rows if x["set"] == "HELD" and x["pair"] == "pop-ctx" and float(x["r"]) == r
               and int(x["n"]) == n]
        if not lib or len(ctx) != 1:
            raise SystemExit(f"FAIL: cell r={r} n={n} K={k} not found in the pinned F2 map rows")
        s_lp, s_ps = float(np.mean(lib)), ctx[0]
        cells.append((f"HELD r={r:g} n={n} K={k}", s_lp, abs(s_ps - s_lp), s_ps))
    return cells, hashlib.sha256(raw).hexdigest()


def _job(args):
    i, (cell, pi, e, s, m), sims, root = args
    rng = np.random.default_rng([root, i])                     # per-setting stream: independent of worker count
    c = float(sps.t.isf(F1OC.ALPHA / (2 * F1OC.Q2_FAMILY), m - 1))
    counts = {}
    for _ in range(sims):
        a = F1OC.q2_classify(F1OC.q2_replicate(rng, m, pi, e, s, cell), c, cell)
        b = F1OC.q2_classify(F1OC.q2_replicate(rng, m, pi, e, s, cell), c, cell)
        k = a if a == b else "INCONCLUSIVE"
        counts[k] = counts.get(k, 0) + 1
    return i, c, counts


def main(argv=None) -> int:
    from dynaicl_families.stage2.seeds import role_seed
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--smoke", action="store_true")
    args = ap.parse_args(argv)
    out = Path(args.out) if Path(args.out).is_absolute() else ROOT / args.out
    out.mkdir(parents=True, exist_ok=True)
    cells, sha = load_cells()
    root = role_seed("f2_tests" if args.smoke else "f2_oc")
    grid = list(itertools.product(cells, [0.0, 1.0], [0.0, 0.01], [0.01, 0.02, 0.05, 0.1], [16, 32, 64, 128]))
    sims = 20 if args.smoke else 300
    grid = grid[:4] if args.smoke else grid
    t0 = time.time()
    with ProcessPoolExecutor(max_workers=args.workers) as ex:
        results = sorted(ex.map(_job, [(i, g, sims, root) for i, g in enumerate(grid)]), key=lambda x: x[0])
    rows = []
    for i, c, counts in results:
        cell, pi, e, s, m = grid[i]
        truth = "LIB-LIKE" if pi == 0.0 else "GENERALISING"
        other = "GENERALISING" if truth == "LIB-LIKE" else "LIB-LIKE"
        rows.append({"cell": cell[0], "s_lp": cell[1], "s_ls": cell[2], "s_ps": cell[3], "pi": pi, "e": e, "s": s,
                     "M": m, "truth": truth, "c_bonferroni_t": c, "sims": sims,
                     "P_correct": counts.get(truth, 0) / sims,
                     "P_wrong": counts.get(other, 0) / sims, "P_NEITHER": counts.get("NEITHER", 0) / sims,
                     "P_INCONCLUSIVE": counts.get("INCONCLUSIVE", 0) / sims, "map_rows_sha256": sha})
    with open(out / "oc_q2_f2.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    table = {"Q2": LOOKUP.lookup(rows, {0.0, 0.01}, 32), "min_models": 32, "power": LOOKUP.POWER,
             "cells": [c[0] for c in cells], "map": f"{MAP_REF}:{MAP_PATH}", "map_rows_sha256": sha,
             "max_P_wrong": max(r["P_wrong"] for r in rows), "settings": len(rows), "smoke": args.smoke}
    (out / "f2_power_lookup.json").write_text(json.dumps(table, indent=1), encoding="utf-8")
    import scipy

    def git(*a: str) -> str:
        return subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True).stdout.strip()

    prov = {"command": " ".join([Path(sys.executable).name, *sys.argv]), "python": platform.python_version(),
            "platform": platform.platform(), "numpy": np.__version__, "scipy": scipy.__version__,
            "cpu_count": os.cpu_count(), "workers": args.workers, "role_root": root,
            "seconds": round(time.time() - t0, 1),
            "sources_sha256": {s: hashlib.sha256((ROOT / s).read_bytes()).hexdigest() for s in SOURCES},
            "git_head": git("rev-parse", "HEAD"), "git_dirty_tracked": bool(git("status", "--porcelain",
                                                                               "--untracked-files=no"))}
    (out / "provenance.json").write_text(json.dumps(prov, indent=1), encoding="utf-8")
    print(json.dumps(table, indent=1))
    print(f"{len(rows)} settings in {time.time() - t0:.0f} s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
