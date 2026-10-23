"""Run and summarise the F1 separability map (docs/STAGE1_F1_SEPARABILITY_MAP_SPEC.md). CPU only; references only.

Usage (box, tmux):  .venv/bin/python scripts/stage1_f1_map.py --out results_stage1/map_F1 --workers 20
Smoke (laptop):     python scripts/stage1_f1_map.py --smoke --out <scratch dir> --workers 4

Phase 1: Q1 units (one per r) write rows and a cache (pop / ctx scores and contexts of the first n_q2_items systems of
each set) to <out>/units/. Phase 2: Q2 units (per K and library draw) reuse the caches. Every unit is checkpointed; a
rerun resumes. Then the frozen rules of the spec section 4 are applied: <out>/F1_MAP_REPORT.md, f1_map_decisions.csv,
f1_map_checks.json, checksums.json. Exit 0 if VALID.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import platform
import subprocess
import sys
import time
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import asdict, replace
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dynaicl_families.f1_separability import F1MapConfig, run_q1, run_q2_unit  # noqa: E402
from dynaicl_neural.seeds import role_seed  # noqa: E402

SMOKE_SEED = 69999
DELTA, Z_CELL, DRAW_FRACTION = 0.02, 3.0, 0.9
SOURCES = ["dynaicl_families/ar1_unknown_sigma.py", "dynaicl_families/f1_separability.py",
           "dynaicl_families/sampling.py", "scripts/stage1_f1_map.py", "docs/STAGE1_F1_SEPARABILITY_MAP_SPEC.md",
           "docs/MATH_F1.md"]


def config(smoke: bool) -> F1MapConfig:
    if not smoke:
        return F1MapConfig(root_seed=role_seed("f1_map"))
    return replace(F1MapConfig(root_seed=SMOKE_SEED), r_list=(1.0, 4.0), n_list=(2, 5), k_list=(2, 16),
                   draws_small_k=2, n_items=600, n_q2_items=300, n_inlib=300)


def _cfg(d: dict) -> F1MapConfig:
    return F1MapConfig(**{k: tuple(v) if isinstance(v, list) else v for k, v in d.items()})


def q1_unit(cfg_d: dict, r: float, out: str) -> tuple[str, float]:
    t0 = time.time()
    rows, cache = run_q1(_cfg(cfg_d), r)
    np.savez(Path(out) / "units" / f"q1_cache_r{r}.npz", **cache)
    _write(Path(out) / "units" / f"q1_r{r}.json", rows, time.time() - t0)
    return f"q1_r{r}", time.time() - t0


def q2_unit(cfg_d: dict, k: int, d: int, out: str) -> tuple[str, float]:
    t0 = time.time()
    cfg = _cfg(cfg_d)
    caches = {}
    for r in cfg.r_list:
        with np.load(Path(out) / "units" / f"q1_cache_r{r}.npz") as z:
            caches[r] = {key: z[key] for key in z.files}
    rows = run_q2_unit(cfg, k, d, caches)
    _write(Path(out) / "units" / f"q2_K{k}_d{d}.json", rows, time.time() - t0)
    return f"q2_K{k}_d{d}", time.time() - t0


def _write(path: Path, rows: list, secs: float) -> None:
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps({"seconds": secs, "rows": rows}), encoding="utf-8")
    os.replace(tmp, path)


def _run_parallel(jobs, workers, label):
    t0, done = time.time(), 0
    with ProcessPoolExecutor(max_workers=workers) as ex:
        futs = [ex.submit(*j) for j in jobs]
        for f in as_completed(futs):
            name, secs = f.result()             # any exception aborts the run
            done += 1
            el = time.time() - t0
            print(f"[{label} {done}/{len(jobs)}] {name} {secs:.0f}s | elapsed {el / 60:.1f} min | "
                  f"ETA {el / done * (len(jobs) - done) / 60:.1f} min", flush=True)


def summarise(out: Path) -> int:
    rows = []
    for f in sorted((out / "units").glob("*.json")):
        rows += json.loads(f.read_text(encoding="utf-8"))["rows"]
    keys = ["family", "set", "r", "n", "pair", "K", "draw", "estimator", "mean", "sd", "n_items"]
    with open(out / "f1_map_rows.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)
    checks = [r for r in rows if r["estimator"].startswith("CHECK")]
    worst = max((r["mean"] for r in checks), default=float("nan"))
    valid = bool(checks) and worst <= 1e-6
    dec, groups = [], defaultdict(list)
    for r in rows:
        if r["estimator"].startswith("CHECK"):
            continue
        se = r["sd"] / math.sqrt(r["n_items"])
        m = r["mean"]
        truth_pop = r["pair"] == "pop|ctx" and r["set"] == "HELD"
        lo, hi = (m - Z_CELL * se, m + Z_CELL * se) if truth_pop else (abs(m) - Z_CELL * se, abs(m) + Z_CELL * se)
        if r["pair"] == "pop|ctx":
            d = "IDENTIFIABLE" if lo >= DELTA else ("UNIDENTIFIABLE" if hi < DELTA else "BORDERLINE")
            dec.append({"set": r["set"], "pair": r["pair"], "r": r["r"], "n": r["n"], "K": 0, "estimate": m, "lo": lo,
                        "hi": hi, "draws": 1, "frac_lo_ge_delta": float(lo >= DELTA), "decision": d})
        else:
            groups[(r["set"], r["pair"], r["r"], r["n"], r["K"])].append((m, lo, hi))
    for (s, pair, rr, n, k), v in sorted(groups.items()):
        f_lo = sum(x[1] >= DELTA for x in v) / len(v)
        f_hi = sum(x[2] < DELTA for x in v) / len(v)
        d = "IDENTIFIABLE" if f_lo >= DRAW_FRACTION else ("UNIDENTIFIABLE" if f_hi >= DRAW_FRACTION else "PARTIAL")
        ms = sorted(x[0] for x in v)
        dec.append({"set": s, "pair": pair, "r": rr, "n": n, "K": k, "estimate": sum(ms) / len(ms),
                    "lo": ms[int(0.1 * (len(ms) - 1) + 0.5)], "hi": ms[int(0.9 * (len(ms) - 1) + 0.5)], "draws": len(v),
                    "frac_lo_ge_delta": f_lo, "decision": d})
    with open(out / "f1_map_decisions.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(dec[0]))
        w.writeheader()
        w.writerows(dec)
    (out / "f1_map_checks.json").write_text(json.dumps({"node_doubling_checks": len(checks), "max_abs": worst,
                                                        "valid": valid}, indent=1), encoding="utf-8")
    lines = ["# F1 separability map: report", "", f"**Validity: {'VALID' if valid else 'INVALID'}** "
             f"({len(checks)} node-doubling checks, max {worst:.2e} nats, limit 1e-6).", "",
             "| set | pair | r | n | K | estimate | lo | hi | frac lo>=delta | decision |", "|---|---|---|---|---|---|---|---|---|---|"]
    for d in dec:
        lines.append(f"| {d['set']} | {d['pair']} | {d['r']} | {d['n']} | {d['K']} | {d['estimate']:+.4f} | "
                     f"{d['lo']:+.4f} | {d['hi']:+.4f} | {d['frac_lo_ge_delta']:.2f} | {d['decision']} |")
    (out / "F1_MAP_REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    sums = {p.name: {"sha256": hashlib.sha256(p.read_bytes()).hexdigest(), "bytes": p.stat().st_size}
            for p in sorted(out.iterdir()) if p.is_file() and p.name != "checksums.json"}
    (out / "checksums.json").write_text(json.dumps(sums, indent=1), encoding="utf-8")
    print(f"F1 map {'VALID' if valid else 'INVALID'}: {len(dec)} decisions")
    return 0 if valid else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 2))
    ap.add_argument("--smoke", action="store_true")
    args = ap.parse_args(argv)
    cfg = config(args.smoke)
    out = Path(args.out)
    (out / "units").mkdir(parents=True, exist_ok=True)
    if not (out / "provenance.json").exists():
        git = lambda *a: subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True).stdout.strip()  # noqa
        prov = {"config": asdict(cfg), "smoke": args.smoke, "git_commit": git("rev-parse", "HEAD"),
                "git_status_porcelain": git("status", "--porcelain"), "python": sys.version,
                "numpy": np.__version__, "platform": platform.platform(),
                "source_sha256": {s: hashlib.sha256((ROOT / s).read_bytes()).hexdigest() for s in SOURCES
                                  if (ROOT / s).exists()},
                "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
        (out / "provenance.json").write_text(json.dumps(prov, indent=1), encoding="utf-8")
    cfg_d = asdict(cfg)
    q1 = [(q1_unit, cfg_d, r, str(out)) for r in cfg.r_list if not (out / "units" / f"q1_r{r}.json").exists()]
    _run_parallel(q1, min(args.workers, max(1, len(q1))), "Q1")
    q2 = [(q2_unit, cfg_d, k, d, str(out)) for k in cfg.k_list for d in range(cfg.draws(k))
          if not (out / "units" / f"q2_K{k}_d{d}.json").exists()]
    _run_parallel(q2, args.workers, "Q2")
    rc = summarise(out)
    (out / "F1_MAP_DONE.json").write_text(json.dumps({"exit": rc, "finished_utc":
                                                      time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}),
                                          encoding="utf-8")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
