"""F1 head-family floor (docs/PREREG_stage2_F1.md section 4): how well can an m-component Gaussian mixture represent each
F1 reference's one-step predictive? Same method and decision rule as the frozen Stage 1A head floor
(scripts/stage1_head_floor.py, whose `moment_matched_floor` and `fit_floor_batch` are imported unchanged): per context,
q_m minimising KL(p || q_m) by weighted EM on quadrature nodes of p; the fitted KL is an UPPER bound on the true floor
(local optimum, two starts; the floor for m is the minimum over m' <= m because the families are nested).

What differs for F1: the predictives are Student-t mixtures (very heavy-tailed for the context-only reference at small n), so
the nodes cover the whole real line: y = c + s tan(u), u in (-pi/2, pi/2), with the centre c and scale s (median and IQR / 1.35)
taken from a coarse pass of the same substitution; 1001 Gauss-Legendre-in-u nodes. The mass error |sum w p - 1| is reported per
context and must be <= 1e-6 or the run aborts (the KL would otherwise be meaningless).

Sets: HELD (P_F1 systems) for every reference; OWN (each arm's training law: CTX systems for ctx, the library's atoms for lib_K).
References: pop, ctx, lib_K for K in {2, 16, 256}. Cells n in {2, 3, 5, 10, 20} x r in {0.25, 1, 4}; m in {1, 2, 4, 8}.
Decision rule (as Stage 1A): the head uses the smallest m whose mean floor is <= epsilon / 10 = 0.001 nats in every cell.
Seed role f1n_head_floor (config/stage2_seed_manifest.yaml).

Usage: python scripts/stage2_f1_head_floor.py --out results_stage2/f1_head_floor --contexts 100 --workers 16
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import os
import platform
import subprocess
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dynaicl.systems.conditions import InitialStateSpec  # noqa: E402

NS = (2, 3, 5, 10, 20)
RS = (0.25, 1.0, 4.0)
MS = (1, 2, 4, 8)
KS = (2, 16, 256)
G = 1001                 # tan-substitution nodes; the mass error is checked against MASS_TOL per context
MASS_TOL = 1e-6
SOURCES = ["scripts/stage2_f1_head_floor.py", "scripts/stage1_head_floor.py", "dynaicl_families/ar1_unknown_sigma.py",
           "dynaicl_families/sampling.py", "config/stage2_seed_manifest.yaml"]


def _frozen_head_floor():
    spec = importlib.util.spec_from_file_location("stage1_head_floor", ROOT / "scripts" / "stage1_head_floor.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@dataclass(frozen=True)
class F1ContextOnlyCondition:
    """Systems from the context-only law: a ~ U(-0.999, 0.999), log sigma ~ U(log 0.01, log 100), independent."""

    initial_state: InitialStateSpec = InitialStateSpec()
    name: str = "F1-CTX"
    stream_code: int = 6

    def system_distribution_fingerprint(self) -> str:
        from dynaicl.systems.priors import LIKELIHOOD_ID, canonical_fingerprint
        return canonical_fingerprint({"family": "F1-CTX", "a": [-0.999, 0.999], "log_sigma": [np.log(0.01), np.log(100)],
                                      "likelihood": LIKELIHOOD_ID})

    def draw_system(self, rng: np.random.Generator):
        a = -0.999 + 1.998 * rng.uniform()
        sigma = float(np.exp(np.log(0.01) + (np.log(100) - np.log(0.01)) * rng.uniform()))
        return float(a), sigma, "f1ctx"


@dataclass(frozen=True)
class AtomCondition:
    a: tuple
    sigma: tuple
    initial_state: object = None
    name: str = "F1-ATOMS"
    stream_code: int = 7

    def system_distribution_fingerprint(self) -> str:
        from dynaicl.systems.priors import LIKELIHOOD_ID, canonical_fingerprint
        return canonical_fingerprint({"family": "F1-ATOMS", "a": list(self.a), "sigma": list(self.sigma),
                                      "likelihood": LIKELIHOOD_ID})

    def draw_system(self, rng: np.random.Generator):
        k = int(rng.integers(len(self.a)))
        return float(self.a[k]), float(self.sigma[k]), f"atom-{k}"


def tan_nodes(ref, st, centre, scale):
    """(C, G) nodes, weights (u-space GL weights x dy/du) and log p for a tan substitution around centre / scale."""
    x, w = np.polynomial.legendre.leggauss(G)
    u = 0.5 * np.pi * x                                     # Gauss-Legendre on (-pi/2, pi/2)
    wu = 0.5 * np.pi * w
    y = centre[:, None] + scale[:, None] * np.tan(u)[None, :]
    wt = scale[:, None] * (wu / np.cos(u) ** 2)[None, :]
    return y, wt, ref.logpdf(st, y)


def floors_for(ref, st, rng, hf) -> dict:
    """Mean and max KL floor per m (minimum over m' <= m), plus the worst mass error."""
    c0 = st.a_hat * st.last
    s0 = np.sqrt(st.r_min / max(st.n - 1, 1)) + 1e-3
    y, wt, lp = tan_nodes(ref, st, c0, s0)
    p = np.exp(lp) * wt
    cdf = np.cumsum(p, axis=1) / p.sum(axis=1, keepdims=True)
    med = np.array([np.interp(0.5, cdf[i], y[i]) for i in range(y.shape[0])])
    iqr = np.array([np.interp(0.75, cdf[i], y[i]) - np.interp(0.25, cdf[i], y[i]) for i in range(y.shape[0])])
    y, wt, lp = tan_nodes(ref, st, med, np.maximum(iqr / 1.35, 1e-6))
    wp = np.exp(lp) * wt
    mass_err = float(np.max(np.abs(wp.sum(axis=1) - 1.0)))
    if mass_err > MASS_TOL:
        raise FloatingPointError(f"quadrature mass error {mass_err:.2e} > {MASS_TOL}")
    wp = wp / wp.sum(axis=1, keepdims=True)
    out, best = {"mass_err": mass_err}, None
    for m in MS:
        f = hf.moment_matched_floor(y, wp, lp) if m == 1 else hf.fit_floor_batch(y, wp, lp, m, rng)
        best = f if best is None else np.minimum(best, f)
        out[m] = {"mean": float(best.mean()), "max": float(best.max())}
    return out


JOBS = [("HELD", "pop"), ("HELD", "ctx"), ("OWN", "ctx")] + [(st, f"lib{k}") for k in KS for st in ("HELD", "OWN")]


def _job(job) -> list[dict]:
    """One (r, n, set, reference) task; systems are regenerated deterministically from the seed role in every task."""
    from dynaicl.rng import NamedStreams
    from dynaicl_families import ar1_unknown_sigma as uf
    from dynaicl_families import sampling as sm
    from dynaicl_families.stage2.seeds import role_seed
    r, n, contexts, role, set_name, ref_name = job
    hf = _frozen_head_floor()
    root = role_seed(role)
    rng = np.random.default_rng([root, int(r * 100), n, JOBS.index((set_name, ref_name))])
    streams = NamedStreams(root)
    x0 = InitialStateSpec(0.0, r)
    lib_rng = np.random.default_rng([root, 999])
    cond = sm.F1PopulationCondition()
    atoms = [cond.draw_system(lib_rng)[:2] for _ in range(max(KS))]

    def stats_for(condition):
        split = sm.simulate(condition, streams, contexts, n + 1)
        c, _ = sm.contexts_and_targets(split, n)
        return uf.F1Stats.from_contexts(c)
    if ref_name == "pop":
        ref = uf.population_f1()
    elif ref_name == "ctx":
        ref = uf.context_only_f1()
    else:
        k = int(ref_name[3:])
        ref = uf.ScaleLibrary(np.array([a for a, _ in atoms[:k]]), np.array([s for _, s in atoms[:k]]))
    if set_name == "HELD":
        st = stats_for(sm.F1PopulationCondition(initial_state=x0))
    elif ref_name == "ctx":
        st = stats_for(F1ContextOnlyCondition(initial_state=x0))
    else:
        st = stats_for(AtomCondition(tuple(ref.a), tuple(ref.sigma), x0))
    res = floors_for(ref, st, rng, hf)
    return [{"set": set_name, "ref": ref_name, "r": r, "n": n, "m": m, "mean_floor": res[m]["mean"],
             "max_floor": res[m]["max"], "mass_err": res["mass_err"], "contexts": contexts} for m in MS]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--contexts", type=int, default=100)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--role", default="f1n_head_floor", help="seed role; f1_tests for local smoke runs")
    ap.add_argument("--smoke", action="store_true", help="r = 1 and n in {2, 20} only (local check of the machinery)")
    args = ap.parse_args(argv)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    with ProcessPoolExecutor(max_workers=args.workers) as ex:
        rs, ns = ((1.0,), (2, 20)) if args.smoke else (RS, NS)
        tasks = [(r, n, args.contexts, args.role, st, ref) for r in rs for n in ns for st, ref in JOBS]
        rows = [row for res in ex.map(_job, tasks, chunksize=1) for row in res]
    with open(out / "f1_head_floor.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    chosen = None
    for m in MS:
        if all(row["mean_floor"] <= 0.001 for row in rows if row["m"] == m):
            chosen = m
            break
    worst = {m: max((row for row in rows if row["m"] == m), key=lambda x: x["mean_floor"]) for m in MS}
    summary = {"role": args.role, "chosen_m": chosen, "rule": "smallest m with mean floor <= 0.001 in every cell (Stage 1A rule)",
               "worst_cell_per_m": {m: {k: worst[m][k] for k in ("set", "ref", "r", "n", "mean_floor", "max_floor")}
                                    for m in MS},
               "max_mass_err": max(row["mass_err"] for row in rows), "seconds": round(time.time() - t0, 1)}
    (out / "f1_head_floor_summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
    import scipy  # noqa: E401
    prov = {"command": " ".join([Path(sys.executable).name, *sys.argv]), "python": platform.python_version(),
            "platform": platform.platform(), "numpy": np.__version__, "scipy": scipy.__version__,
            "cpu_count": os.cpu_count(), "workers": args.workers,
            "sources_sha256": {s: hashlib.sha256((ROOT / s).read_bytes()).hexdigest() for s in SOURCES},
            "git_head": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip(),
            "git_dirty_tracked": bool(subprocess.run(["git", "status", "--porcelain", "--untracked-files=no"], cwd=ROOT,
                                                     capture_output=True, text=True).stdout.strip())}
    (out / "provenance.json").write_text(json.dumps(prov, indent=1), encoding="utf-8")
    print(json.dumps(summary, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
