"""F3 short-context separability map runner (docs/STAGE2_F3_MAP_SPEC.md; code dynaicl_families/stage2/f3_map.py).

Resumable: each unit (12 HELD units, one per (q, r); 768 INLIB units, one per (q, r, K, draw)) writes
<out>/units/<name>.json and is skipped when that file exists. Then: validity checks (i)-(iv), decisions, report.

    python scripts/stage2_f3_map.py --out results_stage2/f3_map --workers 16            # the map (seed role f3_map)
    python scripts/stage2_f3_map.py --out <dir> --smoke --workers 8                      # smoke: f3_tests role, tiny sizes

Outputs: MAP_REPORT.md, map_decisions.csv, map_checks.json, map_rows.csv.gz, provenance.json, MAP_DONE.json.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import io
import json
import math
import os
import platform
import subprocess
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

STAGE1A_CSV = ROOT / "results_stage2" / "f3_inputs" / "stage1A_map_decisions.csv"
STAGE1A_CSV_SHA256 = "cedb9b62df2c7273432b8ef6d05a59471fcc26de909a9b33b1bc3011ef8f3129"   # results-stage1-map-1A @ a499874
SOURCES = ["dynaicl_families/stage2/f3_map.py", "scripts/stage2_f3_map.py", "docs/STAGE2_F3_MAP_SPEC.md",
           "config/stage2_seed_manifest.yaml", "dynaicl/references/kalman_quadrature.py", "dynaicl/systems/noisy.py",
           "dynaicl/evaluation/noisy_harness.py", "dynaicl/systems/splits.py", "dynaicl/rng.py"]


def _unit(job) -> str:
    kind, args, path = job
    from dynaicl_families.stage2 import f3_map as fm
    t0 = time.time()
    res = fm.held_unit(*args) if kind == "held" else fm.inlib_unit(*args)
    res["seconds"] = round(time.time() - t0, 1)
    tmp = Path(path).with_suffix(".tmp")
    tmp.write_text(json.dumps(res), encoding="utf-8")
    os.replace(tmp, path)
    return Path(path).name


def _independent_kalman_mixture(y_ctx, atoms, q, r, h, y):
    """Scalar Kalman filter written from the model equations (validity check iii)."""
    import numpy as np
    lw, comps = [], []
    for a in atoms:
        m, p, ll = 0.0, r * r, 0.0
        for t, yt in enumerate(y_ctx):
            if t > 0:
                m, p = a * m, a * a * p + 1.0
            s = p + q
            ll += -0.5 * (math.log(2 * math.pi * s) + (yt - m) ** 2 / s)
            k = p / s
            m, p = m + k * (yt - m), (1 - k) * p
        mean, var = m, p
        for _ in range(h):
            mean, var = a * mean, a * a * var + 1.0
        var += q
        lw.append(ll)
        comps.append(-0.5 * (math.log(2 * math.pi * var) + (y - mean) ** 2 / var))
    lw = np.array(lw) - np.logaddexp.reduce(lw)
    return float(np.logaddexp.reduce(lw + np.array(comps)))


def validity(root: int, smoke: bool) -> dict:
    import numpy as np
    from dynaicl.evaluation.noisy_harness import build_noisy_evaluation
    from dynaicl.references.kalman_quadrature import (KalmanQuadratureSettings, noise_aware_stability_predictor,
                                                      noisy_population_reference)
    from dynaicl.rng import NamedStreams
    from dynaicl.systems.noisy import NoisyObservationCondition, generate_noisy_split
    from dynaicl.systems.splits import SplitRole
    from dynaicl_families.stage2 import f3_map as fm
    checks = {}
    # (i) node doubling of pop and stab on 200 HELD contexts per q (r = 1), every n and h
    worst = 0.0
    base, fine = KalmanQuadratureSettings(), KalmanQuadratureSettings().refined(2)
    for q in fm.QS:
        model = fm.model_for(q, 1.0)
        cond = NoisyObservationCondition(fm.population_prior(), model, name="F3-HELD", stream_code=0)
        split = generate_noisy_split(cond, SplitRole.SELECTION, NamedStreams(root), 200, max(fm.NS) + max(fm.HS))
        es = build_noisy_evaluation(split, fm.NS, fm.HS)
        for make in (lambda s: noisy_population_reference(fm.population_prior(), model, s),
                     lambda s: noise_aware_stability_predictor(model, settings=s)):
            a = make(base).batch_scores(es.context_matrix, es._targets, fm.NS, fm.HS)
            b = make(fine).batch_scores(es.context_matrix, es._targets, fm.NS, fm.HS)
            worst = max(worst, max(float(np.max(np.abs(a[k][0] - b[k][0]))) for k in a))
    checks["i_node_doubling"] = {"max_abs_nats": worst, "tolerance": 1e-6, "pass": bool(worst <= 1e-6)}
    # (iii) library predictor vs an independent scalar Kalman filter, 50 contexts
    model = fm.model_for(2.56, 1.0)
    cond = NoisyObservationCondition(fm.population_prior(), model, name="F3-HELD", stream_code=0)
    split = generate_noisy_split(cond, SplitRole.SELECTION, NamedStreams(root), 50, max(fm.NS) + max(fm.HS))
    es = build_noisy_evaluation(split, fm.NS, fm.HS)
    atoms = fm.library_atoms(root, 0)[:16]
    got = fm.library_scores(atoms, model, es.context_matrix, es._targets, (3, 9), (1, 5))
    err = max(abs(got[(n, h)][i] - _independent_kalman_mixture(es.context_matrix[i, :n + 1], atoms, 2.56, 1.0, h,
                                                                es._targets[(n, h)][i]))
              for (n, h) in got for i in range(50))
    checks["iii_library_vs_independent_kalman"] = {"max_abs_nats": err, "tolerance": 1e-10, "pass": bool(err <= 1e-10)}
    # (iv) disjointness: held-out coefficients are never library atoms (in-library systems ARE atoms: asserted per unit)
    overlap = 0
    for q in fm.QS:
        for r in fm.RS:
            cond = NoisyObservationCondition(fm.population_prior(), fm.model_for(q, r), name="F3-HELD", stream_code=0)
            split = generate_noisy_split(cond, SplitRole.SELECTION, NamedStreams(root), 200 if smoke else 2000,
                                         max(fm.NS) + max(fm.HS))
            allatoms = np.concatenate([fm.library_atoms(root, d) for d in range(fm.DRAWS)])
            overlap += int(np.isin(split.latent.coefficients, allatoms).sum())
    checks["iv_disjointness"] = {"held_coefficients_equal_to_an_atom": overlap, "pass": bool(overlap == 0)}
    return checks


def main(argv=None) -> int:
    from dynaicl_families.stage2 import f3_map as fm
    from dynaicl_families.stage2.seeds import role_seed
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--smoke", action="store_true")
    args = ap.parse_args(argv)
    out = ROOT / args.out
    (out / "units").mkdir(parents=True, exist_ok=True)
    root = role_seed("f3_tests" if args.smoke else "f3_map")
    held_n, inlib_n = (200, 100) if args.smoke else (20000, 10000)
    if hashlib.sha256(STAGE1A_CSV.read_bytes()).hexdigest() != STAGE1A_CSV_SHA256:
        raise SystemExit("Stage 1A map input changed")
    t0 = time.time()
    jobs = []
    for q in fm.QS:
        for r in fm.RS:
            jobs.append(("held", (q, r, root, held_n), str(out / "units" / f"held_q{q}_r{r}.json")))
            for k in fm.KS:
                for d in range(fm.DRAWS):
                    jobs.append(("inlib", (q, r, k, d, root, inlib_n),
                                 str(out / "units" / f"inlib_q{q}_r{r}_K{k}_d{d}.json")))
    todo = [j for j in jobs if not Path(j[2]).exists()]
    print(f"F3 map: {len(jobs)} units, {len(jobs) - len(todo)} done, {len(todo)} to run, workers={args.workers}",
          flush=True)
    with ProcessPoolExecutor(max_workers=args.workers) as ex:
        for k, name in enumerate(ex.map(_unit, todo, chunksize=1), 1):
            if k % 25 == 0 or k == len(todo):
                print(f"{time.strftime('%H:%M:%S')} [{k}/{len(todo)}] {name}", flush=True)
    rows = [row for j in jobs for row in json.loads(Path(j[2]).read_text(encoding="utf-8"))["rows"]]
    checks = validity(root, args.smoke)
    # (ii) q = 0 control vs the Stage 1A known-sigma map, HELD pop|stab, h = 1, r = 1, n in {2, 3, 5}
    ref = {}
    with open(STAGE1A_CSV, encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            if row["set"] == "HELD" and row["pair"] == "pop|stab" and float(row["r"]) == 1.0:
                ref[int(row["n"])] = (float(row["estimate"]), float(row["se"]))
    zs = {}
    for n in (2, 3, 5):
        mine = next(r for r in rows if r["set"] == "HELD" and r["pair"] == "pop-stab" and r["q"] == 0.0
                    and r["r"] == 1.0 and r["h"] == 1 and r["n"] == n)
        zs[n] = (mine["mean"] - ref[n][0]) / math.sqrt(mine["se"] ** 2 + ref[n][1] ** 2)
    checks["ii_q0_vs_stage1A_map"] = {"z": zs, "bound": 4.0, "pass": bool(all(abs(z) <= 4.0 for z in zs.values())),
                                      "stage1A": {n: ref[n] for n in (2, 3, 5)}}
    valid = all(c["pass"] for c in checks.values())
    # decisions
    dec = []
    for row in rows:
        if row["pair"] == "pop-stab":
            dec.append({**{k: row[k] for k in ("set", "pair", "q", "r", "h", "n")}, "K": "", "estimate": row["mean"],
                        "se": row["se"], "draws": 1, "decision": fm.classify(row["mean"], row["se"])})
    groups = {}
    for row in rows:
        if row["pair"] != "pop-stab":
            groups.setdefault((row["set"], row["pair"], row["q"], row["r"], row["h"], row["n"], row["K"]), []).append(row)
    for key, grp in sorted(groups.items()):
        labels = [fm.classify(g["mean"], g["se"]) for g in grp]
        dec.append({"set": key[0], "pair": key[1], "q": key[2], "r": key[3], "h": key[4], "n": key[5], "K": key[6],
                    "estimate": sum(g["mean"] for g in grp) / len(grp), "se": "", "draws": len(grp),
                    "decision": fm.classify_draws(labels)})
    with open(out / "map_decisions.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(dec[0].keys()))
        w.writeheader()
        w.writerows(dec)
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=sorted({k for r in rows for k in r}))
    w.writeheader()
    w.writerows(rows)
    with gzip.open(out / "map_rows.csv.gz", "wt", encoding="utf-8") as fh:
        fh.write(buf.getvalue())
    (out / "map_checks.json").write_text(json.dumps({"valid": valid, "checks": checks}, indent=1, default=float),
                                         encoding="utf-8")
    # report
    lines = [f"# F3 short-context separability map ({'SMOKE' if args.smoke else 'map'}; seed role "
             f"{'f3_tests' if args.smoke else 'f3_map'})", "", f"Validity: {'VALID' if valid else 'INVALID'}", ""]
    for name, c in checks.items():
        lines.append(f"* {name}: {'pass' if c['pass'] else 'FAIL'} "
                     f"{json.dumps({k: v for k, v in c.items() if k != 'pass'}, default=float)}")
    lines += ["", "## Q1-type: HELD pop vs stab, largest n with IDENTIFIABLE (n in 2..9; '-' none)", "",
              "| q | h | r = 0.25 | r = 1 | r = 4 |", "|---|---|---|---|---|"]
    for q in fm.QS:
        for h in fm.HS:
            cells = []
            for r in fm.RS:
                ids = [d["n"] for d in dec if d["pair"] == "pop-stab" and d["q"] == q and d["h"] == h and d["r"] == r
                       and d["decision"] == "IDENTIFIABLE"]
                cells.append(str(max(ids)) if ids else "-")
            lines.append(f"| {q} | {h} | " + " | ".join(cells) + " |")
    lines += ["", "## Q2-type: library cells marked IDENTIFIABLE (count of (r, n) cells out of 24, per q, h, K)", "",
              "| set / pair | q | h | K=2 | K=4 | K=16 | K=64 |", "|---|---|---|---|---|---|---|"]
    for sp in (("HELD", "pop-lib"), ("INLIB", "lib-pop"), ("INLIB", "lib-stab")):
        for q in fm.QS:
            for h in fm.HS:
                cnt = [sum(1 for d in dec if (d["set"], d["pair"]) == sp and d["q"] == q and d["h"] == h
                           and d["K"] == k and d["decision"] == "IDENTIFIABLE") for k in fm.KS]
                lines.append(f"| {sp[0]} {sp[1]} | {q} | {h} | " + " | ".join(map(str, cnt)) + " |")
    n_cells = len(dec)
    lines += ["", f"{n_cells} decision cells; per-cell two-sided level about 0.0027, so about {0.0027 * n_cells:.1f} "
              "cells could be mis-marked by chance (no global correction; the map guides design only)."]
    (out / "MAP_REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    import numpy, scipy  # noqa: E401
    prov = {"command": " ".join([Path(sys.executable).name, *sys.argv]), "python": platform.python_version(),
            "platform": platform.platform(), "cpu_count": os.cpu_count(), "workers": args.workers,
            "numpy": numpy.__version__, "scipy": scipy.__version__, "root_seed": root, "smoke": args.smoke,
            "seconds_this_invocation": round(time.time() - t0, 1),
            "sources_sha256": {s: hashlib.sha256((ROOT / s).read_bytes()).hexdigest() for s in SOURCES},
            "stage1A_input_sha256": STAGE1A_CSV_SHA256,
            "git_head": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True,
                                       text=True).stdout.strip(),
            "git_dirty_tracked": bool(subprocess.run(["git", "status", "--porcelain", "--untracked-files=no"], cwd=ROOT,
                                                     capture_output=True, text=True).stdout.strip())}
    (out / "provenance.json").write_text(json.dumps(prov, indent=1), encoding="utf-8")
    (out / "MAP_DONE.json").write_text(json.dumps({"valid": valid, "units": len(jobs)}), encoding="utf-8")
    print("\n".join(lines))
    return 0 if valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
