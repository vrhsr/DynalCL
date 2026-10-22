"""Run the Stage 1A separability map (docs/STAGE1_SEPARABILITY_MAP_SPEC.md). CPU only; references only; no model.

Usage (box, inside tmux):
    .venv/bin/python scripts/stage1_separability_map.py --out results_stage1/map_1A --workers 24
Smoke (laptop, minutes; NOT the map seed, reduced sizes):
    python scripts/stage1_separability_map.py --smoke --out <scratch dir> --workers 4

Each unit (Q1 per r; Q2 per (K, draw)) is checkpointed atomically to <out>/units/<unit>.json, so an interrupted run
resumes. When every unit exists, rows are concatenated into <out>/map_rows.csv and the summary script is run.
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
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import asdict, replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dynaicl_families.separability import MapConfig, run_q1, run_q2_unit  # noqa: E402

MAP_SEED = 70001          # role stage1_map (docs/STAGE1_SEPARABILITY_MAP_SPEC.md section 2)
SMOKE_SEED = 69999        # smoke runs only; never used for decisions
SOURCES = ["dynaicl_families/ar1_known_sigma.py", "dynaicl_families/kl.py", "dynaicl_families/sampling.py",
           "dynaicl_families/separability.py", "scripts/stage1_separability_map.py",
           "scripts/stage1_separability_summarize.py", "docs/STAGE1_SEPARABILITY_MAP_SPEC.md"]


def config(smoke: bool) -> MapConfig:
    if not smoke:
        return MapConfig(root_seed=MAP_SEED)
    return replace(MapConfig(root_seed=SMOKE_SEED), n_q1=(1, 3, 20), n_q2=(1, 3), k_list=(1, 2, 8),
                   draws_small_k=2, draws_large_k=1, n_q1_held=2000, n_q1_probe_oos=500, n_q2_realized=1000,
                   n_q2_kl=200)


def units(cfg: MapConfig) -> list[tuple]:
    out = [("q1", r, 0) for r in cfg.r_list]
    for k in cfg.k_list:
        out += [("q2", k, d) for d in range(cfg.draws(k))]
    return out


def unit_name(u: tuple) -> str:
    return f"q1_r{u[1]}" if u[0] == "q1" else f"q2_K{u[1]}_d{u[2]}"


def run_unit(cfg_dict: dict, u: tuple) -> tuple[tuple, list[dict], float]:
    cfg = MapConfig(**{k: tuple(v) if isinstance(v, list) else v for k, v in cfg_dict.items()})
    t0 = time.time()
    rows = run_q1(cfg, u[1]) if u[0] == "q1" else run_q2_unit(cfg, u[1], u[2])
    return u, rows, time.time() - t0


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def provenance(cfg: MapConfig, smoke: bool) -> dict:
    def git(*args):
        try:
            return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, timeout=30).stdout.strip()
        except Exception as exc:  # pragma: no cover - provenance only
            return f"unavailable: {exc}"
    import numpy
    import scipy
    return {"smoke": smoke, "config": asdict(cfg), "git_commit": git("rev-parse", "HEAD"),
            "git_dirty": bool(git("status", "--porcelain")), "python": sys.version, "numpy": numpy.__version__,
            "scipy": scipy.__version__, "platform": platform.platform(), "machine": platform.machine(),
            "source_sha256": {s: sha256(ROOT / s) for s in SOURCES if (ROOT / s).exists()},
            "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 2))
    ap.add_argument("--smoke", action="store_true")
    args = ap.parse_args(argv)
    cfg = config(args.smoke)
    out = Path(args.out)
    (out / "units").mkdir(parents=True, exist_ok=True)
    prov_path = out / "provenance.json"
    if not prov_path.exists():
        prov_path.write_text(json.dumps(provenance(cfg, args.smoke), indent=1), encoding="utf-8")
    todo = [u for u in units(cfg) if not (out / "units" / f"{unit_name(u)}.json").exists()]
    total = len(units(cfg))
    print(f"map: {total} units, {total - len(todo)} already done, {len(todo)} to run, "
          f"workers={args.workers}", flush=True)
    t0 = time.time()
    done = 0
    cfg_dict = asdict(cfg)
    with ProcessPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(run_unit, cfg_dict, u): u for u in todo}
        for f in as_completed(futs):
            u, rows, secs = f.result()          # any exception aborts the run (no silent skips)
            tmp = out / "units" / f"{unit_name(u)}.json.tmp"
            tmp.write_text(json.dumps({"unit": list(u), "seconds": secs, "rows": rows}), encoding="utf-8")
            os.replace(tmp, out / "units" / f"{unit_name(u)}.json")
            done += 1
            el = time.time() - t0
            eta = el / done * (len(todo) - done)
            print(f"[{done}/{len(todo)}] {unit_name(u)} {secs:.0f}s | elapsed {el / 60:.1f} min | "
                  f"ETA {eta / 60:.1f} min",
                  flush=True)
    rows = []
    for u in units(cfg):
        rows += json.loads((out / "units" / f"{unit_name(u)}.json").read_text(encoding="utf-8"))["rows"]
    keys = ["family", "set", "r", "n", "pair", "K", "draw", "estimator", "mean", "sd", "n_items"]
    with open(out / "map_rows.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)
    (out / "MAP_DONE.json").write_text(json.dumps({"rows": len(rows), "finished_utc":
                                                   time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}),
                                       encoding="utf-8")
    print(f"wrote {len(rows)} rows to {out / 'map_rows.csv'}", flush=True)
    rc = subprocess.run([sys.executable, str(ROOT / "scripts" / "stage1_separability_summarize.py"), "--out", str(out)])
    sums = {p.name: {"sha256": sha256(p), "bytes": p.stat().st_size} for p in sorted(out.iterdir()) if p.is_file()
            and p.name != "checksums.json"}
    sums["summarize_exit_code"] = rc.returncode
    (out / "checksums.json").write_text(json.dumps(sums, indent=1), encoding="utf-8")
    print(f"summarize exit code {rc.returncode}; checksums written", flush=True)
    return rc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
