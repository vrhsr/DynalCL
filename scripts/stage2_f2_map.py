"""F2 separability map runner (docs/STAGE2_F2_MAP_SPEC.md; code dynaicl_families/stage2/f2_map.py).

Resumable: 15 HELD units (r, n) and 72 INLIB units (r, K, draw) each write <out>/units/<name>.json. Then validity checks,
decisions, report, provenance.

    python scripts/stage2_f2_map.py --out results_stage2/f2_map --workers 16        # the map (seed role f2_map)
    python scripts/stage2_f2_map.py --out <dir> --smoke --workers 8                 # smoke: f2_tests role, tiny sizes
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import io
import json
import os
import platform
import subprocess
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

SOURCES = ["dynaicl_families/stage2/f2_map.py", "dynaicl_families/stage2/f2_var.py", "scripts/stage2_f2_map.py",
           "docs/STAGE2_F2_MAP_SPEC.md", "docs/MATH_F2.md", "config/stage2_seed_manifest.yaml"]


def _unit(job) -> str:
    kind, args, path = job
    from dynaicl_families.stage2 import f2_map as fm
    t0 = time.time()
    res = fm.held_unit(*args) if kind == "held" else fm.inlib_unit(*args)
    res["seconds"] = round(time.time() - t0, 1)
    tmp = Path(path).with_suffix(".tmp")
    tmp.write_text(json.dumps(res), encoding="utf-8")
    os.replace(tmp, path)
    return Path(path).name


def validity(root: int) -> dict:
    from scipy import stats
    from dynaicl.rng import NamedStreams
    from dynaicl_families.stage2 import f2_map as fm
    from dynaicl_families.stage2 import f2_var as fv
    checks = {}
    pop, ctxp = fv.population_f2(), fv.context_only_f2()
    split = fv.simulate_f2(pop, 1.0, NamedStreams(root + 7), 20, 12, stream_code=13)
    ctx, y = fv.contexts_and_targets(split, 10)
    post = fv.posterior(pop, ctx)
    wide = fv.MNIWPrior("wide", pop.b0, pop.v0, pop.nu0, pop.psi0, 50.0)
    err = max(float(np.max(np.abs(fv.truncated_logpdf_item(wide, post.item(i), y[i][None], np.random.default_rng(i)).logpdf
                                  - fv.untruncated_logpdf(post.item(i), y[i][None][None])[0]))) for i in range(20))
    checks["i_large_radius_exact"] = {"max_abs_nats": err, "pass": bool(err <= 1e-12)}
    zs = []
    for prior in (pop, ctxp):
        post = fv.posterior(prior, ctx)
        for i in range(10):
            a = fv.interval_rb_logpdf_item(prior, post.item(i), y[i][None], NamedStreams(root + 8).item("I", i),
                                           target_se=0.01, max_draws=2 ** 20)
            b = fv.truncated_logpdf_item(prior, post.item(i), y[i][None], NamedStreams(root + 9).item("P", i),
                                         target_se=0.01, max_draws=2 ** 22)
            zs.append(float((a.logpdf[0] - b.logpdf[0]) / np.hypot(a.se_log[0], b.se_log[0])))
    checks["ii_interval_vs_production"] = {"max_abs_z": max(abs(z) for z in zs), "n": len(zs),
                                           "pass": bool(max(abs(z) for z in zs) <= 4.0)}
    lib = fm.library_atoms(root, 0)
    got = lib.logpdf(ctx, y[:, None, :])[:, 0]
    worst = 0.0
    for i in range(20):
        lw = np.array([sum(stats.multivariate_normal.logpdf(ctx[i, t + 1], a @ ctx[i, t], s) for t in range(10))
                       for a, s in zip(lib.a, lib.sigma)])
        lw -= np.logaddexp.reduce(lw)
        want = np.logaddexp.reduce(lw + np.array([stats.multivariate_normal.logpdf(y[i], a @ ctx[i, -1], s)
                                                  for a, s in zip(lib.a, lib.sigma)]))
        worst = max(worst, abs(float(got[i] - want)))
    checks["iii_library_vs_scipy"] = {"max_abs_nats": worst, "pass": bool(worst <= 1e-10)}
    return checks


def main(argv=None) -> int:
    from dynaicl_families.stage2 import f2_map as fm
    from dynaicl_families.stage2.seeds import role_seed
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--smoke", action="store_true")
    args = ap.parse_args(argv)
    out = ROOT / args.out
    (out / "units").mkdir(parents=True, exist_ok=True)
    root = role_seed("f2_tests" if args.smoke else "f2_map")
    held_n, inlib_n = (40, 20) if args.smoke else (4000, 1000)
    t0 = time.time()
    jobs = [("held", (r, n, root, held_n), str(out / "units" / f"held_r{r}_n{n}.json")) for r in fm.RS for n in fm.NS]
    jobs += [("inlib", (r, k, d, root, inlib_n), str(out / "units" / f"inlib_r{r}_K{k}_d{d}.json"))
             for r in fm.RS for k in fm.KS for d in range(fm.DRAWS)]
    jobs.sort(key=lambda j: 0 if j[0] == "held" and j[1][1] == 5 else 1)          # longest units first
    todo = [j for j in jobs if not Path(j[2]).exists()]
    print(f"F2 map: {len(jobs)} units, {len(jobs) - len(todo)} done, {len(todo)} to run, workers={args.workers}",
          flush=True)
    with ProcessPoolExecutor(max_workers=args.workers) as ex:
        for k, name in enumerate(ex.map(_unit, todo, chunksize=1), 1):
            print(f"{time.strftime('%H:%M:%S')} [{k}/{len(todo)}] {name}", flush=True)
    units = [json.loads(Path(j[2]).read_text(encoding="utf-8")) for j in jobs]
    rows = [row for u in units for row in u["rows"]]
    checks = validity(root)
    overlap = sum(u.get("held_atom_overlap", 0) for u in units)
    checks["iv_disjointness"] = {"held_systems_equal_to_an_atom": overlap, "pass": bool(overlap == 0)}
    valid = all(c["pass"] for c in checks.values())
    dec = []
    for row in rows:
        if row["pair"] == "pop-ctx":
            dec.append({"set": row["set"], "pair": row["pair"], "r": row["r"], "n": row["n"], "K": "",
                        "estimate": row["mean"], "se": row["se"], "se_mc": row["se_mc"], "draws": 1,
                        "decision": fm.classify(row)})
    groups = {}
    for row in rows:
        if row["pair"] != "pop-ctx":
            groups.setdefault((row["set"], row["pair"], row["r"], row["n"], row["K"]), []).append(row)
    for key, grp in sorted(groups.items()):
        dec.append({"set": key[0], "pair": key[1], "r": key[2], "n": key[3], "K": key[4],
                    "estimate": float(np.mean([g["mean"] for g in grp])), "se": "",
                    "se_mc": max(g["se_mc"] for g in grp), "draws": len(grp),
                    "decision": fm.classify_draws([fm.classify(g) for g in grp])})
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
    (out / "map_checks.json").write_text(json.dumps({"valid": valid, "checks": checks}, indent=1), encoding="utf-8")
    lines = [f"# F2 separability map ({'SMOKE' if args.smoke else 'map'}; seed role {'f2_tests' if args.smoke else 'f2_map'})",
             "", f"Validity: {'VALID' if valid else 'INVALID'}", ""]
    lines += [f"* {k}: {'pass' if c['pass'] else 'FAIL'} {json.dumps({a: b for a, b in c.items() if a != 'pass'})}"
              for k, c in checks.items()]
    lines += ["", "| set | pair | r | n | K | estimate | decision |", "|---|---|---|---|---|---|---|"]
    for d in sorted(dec, key=lambda x: (x["set"], x["pair"], str(x["K"]), x["r"], x["n"])):
        lines.append(f"| {d['set']} | {d['pair']} | {d['r']} | {d['n']} | {d['K']} | {d['estimate']:+.4f} | {d['decision']} |")
    (out / "MAP_REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    import scipy  # noqa: E401
    prov = {"command": " ".join([Path(sys.executable).name, *sys.argv]), "python": platform.python_version(),
            "platform": platform.platform(), "cpu_count": os.cpu_count(), "workers": args.workers,
            "numpy": np.__version__, "scipy": scipy.__version__, "root_seed": root, "smoke": args.smoke,
            "seconds_this_invocation": round(time.time() - t0, 1),
            "sources_sha256": {s: hashlib.sha256((ROOT / s).read_bytes()).hexdigest() for s in SOURCES},
            "git_head": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip(),
            "git_dirty_tracked": bool(subprocess.run(["git", "status", "--porcelain", "--untracked-files=no"], cwd=ROOT,
                                                     capture_output=True, text=True).stdout.strip())}
    (out / "provenance.json").write_text(json.dumps(prov, indent=1), encoding="utf-8")
    (out / "MAP_DONE.json").write_text(json.dumps({"valid": valid, "units": len(jobs)}), encoding="utf-8")
    print("\n".join(lines[:12]))
    return 0 if valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
