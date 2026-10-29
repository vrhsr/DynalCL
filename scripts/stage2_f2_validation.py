"""F2 reference validation (docs/MATH_F2.md section 9: F2-V9 calibration, F2-V10 optimality; task B2).

Design (fixed before running): cells n in {5, 10, 20} x r in {0.25, 1, 4} (n >= 5: docs/STAGE2_F2_MAP_SPEC.md section 1);
calibration with 1000 items per cell (marginal PIT KS for both coordinates, 50/80/95% coverage of both marginals,
continuous SBC of the spectral radius) and optimality with 2000 items per cell (population vs libraries of 2 / 16 / 64
atoms and the context-only reference, Monte Carlo SE included). Bonferroni over 9 x 9 calibration p-values and 9 x 4
optimality z-tests (117 tests) at family level 0.01. Structural checks: matched guard, leakage, spectral radius. Seed role
f2_validation; per-cell seeds root * 10000 + 10 k + j.

Usage: python scripts/stage2_f2_validation.py --out results_stage2/f2_validation --workers 16
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

NS = (5, 10, 20)
RS = (0.25, 1.0, 4.0)
CAL_ITEMS, OPT_ITEMS, FAMILY_ALPHA = 1000, 2000, 0.01
N_TESTS = len(NS) * len(RS) * (9 + 4)
SOURCES = ["dynaicl_families/stage2/f2_var.py", "dynaicl_families/stage2/f2_map.py", "dynaicl_families/stage2/f2_checks.py",
           "config/stage2_seed_manifest.yaml", "scripts/stage2_f2_validation.py"]


def _cell(args) -> dict:
    kind, k, n, r, root, alpha, z_crit = args
    from dynaicl_families.stage2 import f2_checks as fc
    t0 = time.time()
    if kind == "cal":
        res = fc.calibration_cell(n, r, CAL_ITEMS, root * 10000 + 10 * k + 1, alpha)
    else:
        res = fc.optimality_cell(n, r, OPT_ITEMS, root * 10000 + 10 * k + 2, z_crit)
    res["seconds"] = round(time.time() - t0, 1)
    return res


def main(argv=None) -> int:
    from scipy import stats
    from dynaicl_families.stage2 import f2_checks as fc
    from dynaicl_families.stage2.seeds import role_seed
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--workers", type=int, default=8)
    args = ap.parse_args(argv)
    out = ROOT / args.out
    out.mkdir(parents=True, exist_ok=True)
    root = role_seed("f2_validation")
    alpha = FAMILY_ALPHA / N_TESTS
    z_crit = float(stats.norm.isf(alpha))
    t0 = time.time()
    cells = [(n, r) for n in NS for r in RS]
    jobs = [(kind, k, n, r, root, alpha, z_crit) for kind in ("opt", "cal") for k, (n, r) in enumerate(cells)]
    with ProcessPoolExecutor(max_workers=args.workers) as ex:
        results = list(ex.map(_cell, jobs, chunksize=1))
    structural = [fc.matched_guard(), fc.leakage(root * 10000 + 9500), fc.spectral_radius_check(root * 10000 + 9600)]
    ok = all(r["pass"] for r in results) and all(s["pass"] for s in structural)
    result = {"pass": ok, "family_alpha": FAMILY_ALPHA, "n_tests": N_TESTS, "alpha_per_test": alpha, "z_crit": z_crit,
              "cells": results, "structural": structural, "seconds": round(time.time() - t0, 1)}
    (out / "f2_validation.json").write_text(json.dumps(result, indent=1, default=float), encoding="utf-8")
    lines = ["# F2 reference validation", "", f"Overall: {'PASS' if ok else 'FAIL'}; {N_TESTS} statistical tests, "
             f"per-test level {alpha:.2e} (family 0.01); one-sided z_crit {z_crit:.2f}", "",
             "| check | n | r | smallest p / smallest z (vs) | pass |", "|---|---|---|---|---|"]
    for res in results:
        if res["check"] == "calibration":
            lines.append(f"| calibration | {res['n']} | {res['r']} | {min(res['p_values'].values()):.3g} | {res['pass']} |")
        else:
            worst = min(res["rows"], key=lambda kk: res["rows"][kk]["z"])
            lines.append(f"| optimality | {res['n']} | {res['r']} | {res['rows'][worst]['z']:.2f} ({worst}) | {res['pass']} |")
    lines += ["", "Structural: " + ", ".join(f"{s['check']} {s['pass']}" for s in structural)]
    (out / "f2_validation.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    import numpy, scipy  # noqa: E401
    prov = {"command": " ".join([Path(sys.executable).name, *sys.argv]), "python": platform.python_version(),
            "platform": platform.platform(), "cpu_count": os.cpu_count(), "workers": args.workers,
            "numpy": numpy.__version__, "scipy": scipy.__version__, "seconds": result["seconds"],
            "sources_sha256": {s: hashlib.sha256((ROOT / s).read_bytes()).hexdigest() for s in SOURCES},
            "git_head": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip(),
            "git_dirty_tracked": bool(subprocess.run(["git", "status", "--porcelain", "--untracked-files=no"], cwd=ROOT,
                                                     capture_output=True, text=True).stdout.strip())}
    (out / "provenance.json").write_text(json.dumps(prov, indent=1), encoding="utf-8")
    print("\n".join(lines))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
