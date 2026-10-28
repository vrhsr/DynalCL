"""F1 reference validation at Stage-0 scale (task A2): calibration (PIT KS, 50/80/95% coverage, continuous SBC of a and
sigma^2), optimality (population vs context-only and libraries of 2 / 16 / 256 atoms), the known-sigma limit, leakage and
the matched guard. Checks are in dynaicl_families/stage2/f1_checks.py.

Design (fixed before running): cells n in {2, 3, 5, 10, 20, 40} x r in {0.25, 1, 4}; 5000 items per cell for calibration
and 10000 for optimality; Bonferroni over all 18 x 6 calibration p-values and 18 x 4 optimality z-tests (180 tests) at
family level 0.01 (per test 5.6e-5; one-sided z 3.86). Seeds: role f1_a2_validation; per-cell seeds root * 10000 + 10 k + j
(distinct from every other role's seeds). Known-sigma limit at n in {2, 5, 20}, r = 1, 200 items.

Usage: python scripts/stage2_f1_validation.py --out results_stage2/f1_validation --workers 8
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

NS = (2, 3, 5, 10, 20, 40)
RS = (0.25, 1.0, 4.0)
CAL_ITEMS, OPT_ITEMS = 5000, 10000
FAMILY_ALPHA = 0.01
N_TESTS = len(NS) * len(RS) * (6 + 4)
SOURCES = ["dynaicl_families/ar1_unknown_sigma.py", "dynaicl_families/sampling.py", "dynaicl_families/ar1_known_sigma.py",
           "dynaicl_families/stage2/f1_checks.py", "config/stage2_seed_manifest.yaml", "scripts/stage2_f1_validation.py"]


def _cell(args) -> dict:
    k, n, r, root, alpha, z_crit = args
    from dynaicl_families.stage2 import f1_checks as fc
    t0 = time.time()
    cal = fc.calibration_cell(n, r, CAL_ITEMS, root * 10000 + 10 * k + 1, alpha)
    opt = fc.optimality_cell(n, r, OPT_ITEMS, root * 10000 + 10 * k + 2, z_crit)
    return {"k": k, "n": n, "r": r, "calibration": cal, "optimality": opt, "seconds": round(time.time() - t0, 1)}


def main(argv=None) -> int:
    from scipy import stats
    from dynaicl_families.stage2 import f1_checks as fc
    from dynaicl_families.stage2.seeds import role_seed
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--workers", type=int, default=8)
    args = ap.parse_args(argv)
    out = ROOT / args.out
    out.mkdir(parents=True, exist_ok=True)
    root = role_seed("f1_a2_validation")
    alpha = FAMILY_ALPHA / N_TESTS
    z_crit = float(stats.norm.isf(alpha))
    t0 = time.time()
    jobs = [(k, n, r, root, alpha, z_crit) for k, (n, r) in enumerate((n, r) for n in NS for r in RS)]
    with ProcessPoolExecutor(max_workers=args.workers) as ex:
        cells = list(ex.map(_cell, jobs))
    limit = [fc.known_sigma_limit(n, 1.0, 200, root * 10000 + 9000 + n) for n in (2, 5, 20)]
    structural = [fc.matched_guard(), fc.leakage(root * 10000 + 9500)]
    ok = (all(c["calibration"]["pass"] and c["optimality"]["pass"] for c in cells) and all(x["pass"] for x in limit)
          and all(x["pass"] for x in structural))
    result = {"pass": ok, "family_alpha": FAMILY_ALPHA, "n_tests": N_TESTS, "alpha_per_test": alpha, "z_crit": z_crit,
              "cells": cells, "known_sigma_limit": limit, "structural": structural,
              "seconds": round(time.time() - t0, 1)}
    (out / "f1_validation.json").write_text(json.dumps(result, indent=1, default=float), encoding="utf-8")
    lines = ["# F1 reference validation (task A2)", "", f"Overall: {'PASS' if ok else 'FAIL'}; {N_TESTS} statistical tests, "
             f"Bonferroni per-test level {alpha:.2e} (family 0.01); one-sided optimality z_crit {z_crit:.2f}", "",
             "| n | r | min p (PIT, cov 50/80/95, SBC a, SBC s2) | coverage 50/80/95 | min optimality z (vs) | pass |",
             "|---|---|---|---|---|---|"]
    for c in cells:
        p = c["calibration"]["p_values"]
        cov = c["calibration"]["coverage"]
        rows = c["optimality"]["rows"]
        worst = min(rows, key=lambda kk: rows[kk]["z"])
        lines.append(f"| {c['n']} | {c['r']} | {min(p.values()):.3g} | "
                     f"{cov['0.5']['rate']:.3f} / {cov['0.8']['rate']:.3f} / {cov['0.95']['rate']:.3f} | "
                     f"{rows[worst]['z']:.2f} ({worst}) | {c['calibration']['pass'] and c['optimality']['pass']} |")
    lines += ["", "Known-sigma limit (max |log p_F1 - log p_known| over items; alpha0 = 1e2 .. 1e7):", ""]
    for x in limit:
        lines.append(f"* n = {x['n']}: errors {', '.join(f'{e:.2e}' for e in x['max_err'])}; log-log slope "
                     f"{x['loglog_slope']:.3f}; pass {x['pass']}")
    lines += ["", f"Matched guard: {structural[0]['pass']}; leakage: {structural[1]['pass']}"]
    (out / "f1_validation.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    prov = {"command": " ".join([Path(sys.executable).name, *sys.argv]), "python": platform.python_version(),
            "platform": platform.platform(), "cpu_count": os.cpu_count(), "workers": args.workers,
            "seconds": result["seconds"],
            "sources_sha256": {s: hashlib.sha256((ROOT / s).read_bytes()).hexdigest() for s in SOURCES}}
    import numpy, scipy  # noqa: E401
    prov["numpy"], prov["scipy"] = numpy.__version__, scipy.__version__
    prov["git_head"] = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    prov["git_dirty_tracked"] = bool(subprocess.run(["git", "status", "--porcelain", "--untracked-files=no"], cwd=ROOT,
                                                    capture_output=True, text=True).stdout.strip())
    (out / "provenance.json").write_text(json.dumps(prov, indent=1), encoding="utf-8")
    print("\n".join(lines))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
