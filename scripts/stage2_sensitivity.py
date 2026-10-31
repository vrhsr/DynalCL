"""Sensitivity analyses runner (docs/STAGE2_SENSITIVITY_SPEC.md; code dynaicl_families/stage2/sensitivity.py).

Resumable: each unit writes <out>/units/<name>.json. Units: comparator frontier (known sigma, unknown sigma) and prior
dependence (known sigma: 3 tau; unknown sigma: 3 tau + 2 extra alpha0) per (r, n); F3 precision per (q, r).
Seeds: role `sensitivity` (sections 2-3, per-unit seed root * 10000 + unit index) and `f3_precision` (section 4, per-unit seed
root * 100 + unit index); `--smoke` uses the f3_tests role and tiny sizes.

    python scripts/stage2_sensitivity.py --out results_stage2/sensitivity --workers 16
    python scripts/stage2_sensitivity.py --out <dir> --smoke --workers 8
"""

from __future__ import annotations

import argparse
import csv
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

SOURCES = ["dynaicl_families/stage2/sensitivity.py", "dynaicl_families/stage2/f3_map.py", "scripts/stage2_sensitivity.py",
           "docs/STAGE2_SENSITIVITY_SPEC.md", "config/stage2_seed_manifest.yaml", "dynaicl_families/ar1_known_sigma.py",
           "dynaicl_families/ar1_unknown_sigma.py", "dynaicl/baselines/ols.py", "dynaicl/references/kalman_quadrature.py"]


def _unit(job) -> str:
    name, fn, args, path = job
    from dynaicl_families.stage2 import sensitivity as sv
    t0 = time.time()
    rows = getattr(sv, fn)(*args)
    tmp = Path(path).with_suffix(".tmp")
    tmp.write_text(json.dumps({"unit": name, "rows": rows, "seconds": round(time.time() - t0, 1)}), encoding="utf-8")
    os.replace(tmp, path)
    return name


def main(argv=None) -> int:
    from dynaicl_families.stage2 import sensitivity as sv
    from dynaicl_families.stage2.seeds import role_seed
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--smoke", action="store_true")
    args = ap.parse_args(argv)
    out = ROOT / args.out
    (out / "units").mkdir(parents=True, exist_ok=True)
    s_root = role_seed("f3_tests" if args.smoke else "sensitivity")
    p_root = role_seed("f3_tests" if args.smoke else "f3_precision")
    n_items, n_f3 = (300, 2000) if args.smoke else (20000, 200000)
    ns = (2, 10) if args.smoke else sv.NS
    rs = (1.0,) if args.smoke else sv.RS
    specs = []
    for r in rs:
        for n in ns:
            specs.append(("frontier_known", (n, r, n_items)))
            specs.append(("frontier_f1", (n, r, n_items)))
            for tau in (0.15, 0.3, 0.6):
                specs.append(("prior_known", (tau, n, r, n_items)))
                specs.append(("prior_f1", (tau, 3.0, n, r, n_items)))
            for alpha0 in (2.0, 10.0):
                specs.append(("prior_f1", (0.3, alpha0, n, r, n_items)))
    jobs = []
    for k, (fn, a) in enumerate(specs):
        name = fn + "_" + "_".join(str(x) for x in a)
        jobs.append((name, fn, (*a, s_root * 10000 + k), str(out / "units" / f"{name}.json")))
    for k, (q, r) in enumerate((q, r) for q in (0.0, 0.755, 2.56, 6.5) for r in rs):
        name = f"f3_precision_{q}_{r}"
        jobs.append((name, "f3_precision", (q, r, n_f3, p_root * 100 + k), str(out / "units" / f"{name}.json")))
    jobs.sort(key=lambda j: 0 if j[1] == "f3_precision" else 1)            # longest units first
    todo = [j for j in jobs if not Path(j[3]).exists()]
    print(f"sensitivity: {len(jobs)} units, {len(jobs) - len(todo)} done, {len(todo)} to run, workers={args.workers}",
          flush=True)
    t0 = time.time()
    with ProcessPoolExecutor(max_workers=args.workers) as ex:
        for k, name in enumerate(ex.map(_unit, todo, chunksize=1), 1):
            if k % 20 == 0 or k == len(todo):
                print(f"{time.strftime('%H:%M:%S')} [{k}/{len(todo)}] {name}", flush=True)
    rows = [row for j in jobs for row in json.loads(Path(j[3]).read_text(encoding="utf-8"))["rows"]]
    keys = ["analysis", "family", "variant", "r", "n", "h", "estimate", "se", "n_items", "decision"]
    with open(out / "sensitivity.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=keys)
        w.writeheader()
        w.writerows({k: row[k] for k in keys} for row in rows)
    lines = [f"# Sensitivity analyses ({'SMOKE' if args.smoke else 'full'})", "",
             "Largest IDENTIFIABLE n per (analysis, family, variant, r[, h]); '-' none.", "",
             "| analysis | family | variant | r | h | largest identifiable n | max estimate |", "|---|---|---|---|---|---|---|"]
    groups = {}
    for row in rows:
        groups.setdefault((row["analysis"], row["family"], row["variant"], row["r"], row["h"]), []).append(row)
    for key, grp in sorted(groups.items(), key=lambda kv: tuple(str(x) for x in kv[0])):
        ident = [g["n"] for g in grp if g["decision"] == "IDENTIFIABLE"]
        lines.append(f"| {key[0]} | {key[1]} | {key[2]} | {key[3]} | {key[4]} | {max(ident) if ident else '-'} | "
                     f"{max(g['estimate'] for g in grp):+.4f} |")
    (out / "SENSITIVITY_REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    import numpy, scipy  # noqa: E401
    prov = {"command": " ".join([Path(sys.executable).name, *sys.argv]), "python": platform.python_version(),
            "platform": platform.platform(), "cpu_count": os.cpu_count(), "workers": args.workers,
            "numpy": numpy.__version__, "scipy": scipy.__version__, "smoke": args.smoke, "roots": [s_root, p_root],
            "seconds_this_invocation": round(time.time() - t0, 1),
            "sources_sha256": {s: hashlib.sha256((ROOT / s).read_bytes()).hexdigest() for s in SOURCES},
            "git_head": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip(),
            "git_dirty_tracked": bool(subprocess.run(["git", "status", "--porcelain", "--untracked-files=no"], cwd=ROOT,
                                                     capture_output=True, text=True).stdout.strip())}
    (out / "provenance.json").write_text(json.dumps(prov, indent=1), encoding="utf-8")
    (out / "SENSITIVITY_DONE.json").write_text(json.dumps({"units": len(jobs), "rows": len(rows)}), encoding="utf-8")
    print("\n".join(lines[:40]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
