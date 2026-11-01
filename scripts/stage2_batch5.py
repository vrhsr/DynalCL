"""Batch 5 runner (docs/STAGE2_BATCH5_SPEC.md; code dynaicl_families/stage2/batch5.py).

Box run (sections A-D; resumable, one JSON per unit under <out>/units/):
    python scripts/stage2_batch5.py --out results_stage2/batch5 --workers 16
Local theory quantities (section E; writes <out>/theory.json and theory_provenance.json):
    python scripts/stage2_batch5.py --out results_stage2/batch5 --theory
Smoke (role b5_tests, tiny sizes; never results):
    python scripts/stage2_batch5.py --out <scratch dir> --smoke --workers 8 [--theory]
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

SOURCES = ["dynaicl_families/stage2/batch5.py", "scripts/stage2_batch5.py", "docs/STAGE2_BATCH5_SPEC.md",
           "config/stage2_seed_manifest.yaml", "dynaicl_families/stage2/f2_map.py", "dynaicl_families/stage2/f2_var.py",
           "dynaicl_families/stage2/f3_map.py", "dynaicl_families/ar1_known_sigma.py",
           "dynaicl_families/ar1_unknown_sigma.py", "dynaicl_families/sampling.py",
           "dynaicl/references/kalman_quadrature.py"]


def _unit(job) -> str:
    name, fn, args, path = job
    from dynaicl_families.stage2 import batch5 as b5
    t0 = time.time()
    result = getattr(b5, fn)(*args)
    payload = {"unit": name, "seconds": round(time.time() - t0, 1)}
    if isinstance(result, tuple):
        payload["rows"], payload["lib_rows"] = result
    else:
        payload["rows"] = result
    tmp = Path(path).with_suffix(".tmp")
    tmp.write_text(json.dumps(payload), encoding="utf-8")
    os.replace(tmp, path)
    return name


def _write_csv(path: Path, rows: list[dict]) -> None:
    keys = list(dict.fromkeys(k for row in rows for k in row))
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)


def _provenance(args, roots: dict, seconds: float) -> dict:
    import numpy
    import scipy

    def git(*a: str) -> str:
        return subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True).stdout.strip()

    return {"command": " ".join([Path(sys.executable).name, *sys.argv]), "python": platform.python_version(),
            "platform": platform.platform(), "cpu_count": os.cpu_count(), "workers": args.workers,
            "numpy": numpy.__version__, "scipy": scipy.__version__, "smoke": args.smoke, "roots": roots,
            "seconds_this_invocation": round(seconds, 1),
            "sources_sha256": {s: hashlib.sha256((ROOT / s).read_bytes()).hexdigest() for s in SOURCES},
            "git_head": git("rev-parse", "HEAD"),
            "git_dirty_tracked": bool(git("status", "--porcelain", "--untracked-files=no"))}


def run_theory(args, out: Path) -> int:
    from dynaicl_families.stage2 import batch5 as b5
    from dynaicl_families.stage2.seeds import role_seed
    root = role_seed("b5_tests" if args.smoke else "b5_theory")
    t0 = time.time()
    kw = dict(n_draws=4000, n_sys=200, n_lib=4, n_sys_f2=40, n_lib_f2=2) if args.smoke else {}
    res = b5.theory(root, **kw)
    (out / "theory.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
    (out / "theory_provenance.json").write_text(json.dumps(_provenance(args, {"b5_theory": root}, time.time() - t0),
                                                           indent=1), encoding="utf-8")
    print(json.dumps({k: res[k] for k in ("kl_1a", "kl_f1_total_map_comparator")}, indent=1))
    print(json.dumps(res["kl_f2"], indent=1))
    return 0


def main(argv=None) -> int:
    from dynaicl_families.stage2 import batch5 as b5
    from dynaicl_families.stage2.seeds import role_seed
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--theory", action="store_true", help="section E only (local)")
    args = ap.parse_args(argv)
    out = Path(args.out) if Path(args.out).is_absolute() else ROOT / args.out
    (out / "units").mkdir(parents=True, exist_ok=True)
    if args.theory:
        return run_theory(args, out)
    roles = {r: role_seed("b5_tests" if args.smoke else r) for r in ("b5_f1_split", "b5_f2", "b5_cumulative")}
    s = args.smoke
    rs = (1.0,) if s else b5.RS
    n_f1, n_f2, n_1a, n_f3 = (200, 40, 400, 200) if s else (20000, 4000, 40000, 20000)
    jobs = []

    def add(name, fn, a):
        jobs.append((name, fn, a, str(out / "units" / f"{name}.json")))

    f1_lib_root = b5.unit_seed(roles["b5_f1_split"], "f1_library")
    f2_lib_root = b5.unit_seed(roles["b5_f2"], "f2_library")
    for r in rs:
        seed_a = b5.unit_seed(roles["b5_f1_split"], "f1_split", r)
        seed_c = b5.unit_seed(roles["b5_f1_split"], "f1_library_long", r)
        seed_b = b5.unit_seed(roles["b5_f2"], "f2_heldout", r)
        if s:
            add(f"f1_split_{r}", "f1_split", (r, n_f1, seed_a, (2, 10)))
            add(f"f1_library_long_{r}", "f1_library_long", (r, n_f1, seed_c, f1_lib_root, (20, 40), (4, 16), 4))
            add(f"f2_heldout_{r}", "f2_heldout", (r, n_f2, seed_b, f2_lib_root, (2, 10), (10,), (2, 16), 2))
            add(f"cumulative_1a_{r}", "cumulative_1a", (r, n_1a, b5.unit_seed(roles["b5_cumulative"], "1a", r), 12))
            add(f"cumulative_f1_{r}", "cumulative_f1", (r, n_f1, b5.unit_seed(roles["b5_cumulative"], "f1", r), 6))
            add(f"cumulative_f3_0.755_{r}", "cumulative_f3",
                (0.755, r, n_f3, b5.unit_seed(roles["b5_cumulative"], "f3", 0.755, r), 6))
        else:
            add(f"f1_split_{r}", "f1_split", (r, n_f1, seed_a))
            add(f"f1_library_long_{r}", "f1_library_long", (r, n_f1, seed_c, f1_lib_root))
            add(f"f2_heldout_{r}", "f2_heldout", (r, n_f2, seed_b, f2_lib_root))
            add(f"cumulative_1a_{r}", "cumulative_1a", (r, n_1a, b5.unit_seed(roles["b5_cumulative"], "1a", r)))
            add(f"cumulative_f1_{r}", "cumulative_f1", (r, n_f1, b5.unit_seed(roles["b5_cumulative"], "f1", r)))
            for q in b5.QS:
                seed_d = b5.unit_seed(roles["b5_cumulative"], "f3", q, r)
                add(f"cumulative_f3_{q}_{r}", "cumulative_f3", (q, r, n_f3, seed_d))
    # longest units first (ASSUMED from the smoke timing)
    order = {"cumulative_f1": 0, "f2_heldout": 1, "cumulative_f3": 2, "f1_library_long": 3, "cumulative_1a": 4,
             "f1_split": 5}
    jobs.sort(key=lambda j: order[j[1]])
    todo = [j for j in jobs if not Path(j[3]).exists()]
    print(f"batch5: {len(jobs)} units, {len(jobs) - len(todo)} done, {len(todo)} to run, workers={args.workers}",
          flush=True)
    t0 = time.time()
    with ProcessPoolExecutor(max_workers=args.workers) as ex:
        for k, name in enumerate(ex.map(_unit, todo, chunksize=1), 1):
            print(f"{time.strftime('%H:%M:%S')} [{k}/{len(todo)}] {name}", flush=True)
    units = {j[0]: json.loads(Path(j[3]).read_text(encoding="utf-8")) for j in jobs}
    split = [r for n, u in units.items() if n.startswith(("f1_split", "f2_heldout")) for r in u["rows"]]
    f2_lib = [r for n, u in units.items() if n.startswith("f2_heldout") for r in u["lib_rows"]]
    f1_lib = [r for n, u in units.items() if n.startswith("f1_library_long") for r in u["rows"]]
    cum = [r for n, u in units.items() if n.startswith("cumulative") for r in u["rows"]]
    _write_csv(out / "split.csv", split)
    _write_csv(out / "f2_library_draws.csv", f2_lib)
    _write_csv(out / "f2_library.csv", b5.summarise_draws(f2_lib, ("family", "r", "n", "K")))
    _write_csv(out / "f1_library_long_draws.csv", f1_lib)
    _write_csv(out / "f1_library_long.csv", b5.summarise_draws(f1_lib, ("family", "r", "n", "K")))
    _write_csv(out / "cumulative.csv", cum)
    lines = [f"# Batch 5 ({'SMOKE' if s else 'full'})", "",
             "## Split of the held-out gap (T = total; D = dynamics part; N = noise-level part; symmetric)", "",
             "| family | r | n | T | D | N | decision T | decision pop vs ctx_nm |",
             "|---|---|---|---|---|---|---|---|"]
    idx = {(r["family"], r["r"], r["n"], r["part"]): r for r in split}
    for fam, r, n in sorted({(x["family"], x["r"], x["n"]) for x in split}):
        g = lambda p: idx.get((fam, r, n, p), {})  # noqa: E731
        lines.append(f"| {fam} | {r} | {n} | {g('T').get('estimate', float('nan')):+.4f} | "
                     f"{g('D').get('estimate', float('nan')):+.4f} | {g('N').get('estimate', float('nan')):+.4f} | "
                     f"{g('T').get('decision', '')} | {g('D1').get('decision', '')} |")
    lines += ["", f"Units: {len(jobs)}; seconds per unit: " +
              ", ".join(f"{n} {u['seconds']}" for n, u in sorted(units.items()))]
    (out / "BATCH5_REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    prov = _provenance(args, roles, time.time() - t0)
    (out / "provenance.json").write_text(json.dumps(prov, indent=1), encoding="utf-8")
    (out / "BATCH5_DONE.json").write_text(json.dumps({"units": len(jobs), "split_rows": len(split),
                                                      "cumulative_rows": len(cum)}), encoding="utf-8")
    print("\n".join(lines[:60]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
