"""F2 bivariate head floor (docs/STAGE3_F2_DESIGN_CPU_SPEC.md A): how many components m must a mixture of bivariate
Gaussians (full covariances) have to represent each F2 reference predictive within 0.001 nats?

Per context the reference predictive p is an explicit mixture that can be sampled and evaluated exactly: lib_K is the
Gaussian mixture of MATH_F2 section 7 (posterior weights over its K atoms); pop is the mixture of the
Rao-Blackwellised Student-t predictives of J accepted draws from its untruncated posterior (the production estimator
R's mixture, MATH_F2 sections 4-5). As the F1 head floor (weighted EM on quadrature nodes of p), in two dimensions: a
G x G tan-substitution Gauss-Legendre grid on coordinates whitened by p's moments (mass error checked per context
against MASS_TOL, else the run aborts); q_m maximises sum_i a_i log q(y_i) with a_i = w_i p(y_i) (two starts), which
minimises the quadrature KL(p || q_m) = sum_i a_i (log p - log q_m); the floor for m is the minimum over m' <= m
(nested families; local optima make each value an upper bound). Decision rule (Stage 1A / F1): the smallest m whose
mean floor is <= 0.001 nats in every cell. Seed role f2n_head_floor (smoke: f2_tests).

    python scripts/stage3_f2_head_floor.py --out results_stage2/f2_head_floor --workers 16
    python scripts/stage3_f2_head_floor.py --out <scratch> --smoke --workers 8
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
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
from scipy import special

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

NS = (2, 3, 5, 10, 20)
RS = (0.25, 1.0, 4.0)
MS = (1, 2, 4, 8)
KS = (2, 16, 64, 256, 1024)
CONTEXTS, J_POP, G_NODES = 40, 2000, 96
FLOOR, SE_FLAG, MASS_TOL = 0.001, 2e-4, 1e-5
SOURCES = ["scripts/stage3_f2_head_floor.py", "dynaicl_families/stage2/f2_var.py", "docs/STAGE3_F2_DESIGN_CPU_SPEC.md",
           "config/stage2_seed_manifest.yaml"]
JOBS = [("HELD", "pop")] + [(s, f"lib{k}") for k in KS for s in ("HELD", "OWN")]


# ------------------------------------------------------------------------------------------------ reference mixtures

def _inv_logdet(cov: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    det = cov[..., 0, 0] * cov[..., 1, 1] - cov[..., 0, 1] * cov[..., 1, 0]
    inv = np.stack([np.stack([cov[..., 1, 1], -cov[..., 0, 1]], -1), np.stack([-cov[..., 1, 0], cov[..., 0, 0]], -1)],
                   -2) / det[..., None, None]
    return inv, np.log(det)


def _quad(y: np.ndarray, loc: np.ndarray, inv: np.ndarray) -> np.ndarray:
    """(y - loc_k)^T inv_k (y - loc_k) for y (G, 2), loc (K, 2), inv (K, 2, 2) -> (G, K), written out for 2 x 2."""
    d0, d1 = y[:, 0, None] - loc[None, :, 0], y[:, 1, None] - loc[None, :, 1]
    return inv[None, :, 0, 0] * d0 * d0 + 2.0 * inv[None, :, 0, 1] * d0 * d1 + inv[None, :, 1, 1] * d1 * d1


class StudentTMixture:
    """Equal-weight mixture of bivariate Student-t components (loc (J, 2), scale (J, 2, 2), common dof)."""

    def __init__(self, loc, scale, dof):
        self.loc, self.scale, self.dof = loc, scale, float(dof)
        self.inv, self.logdet = _inv_logdet(scale)
        self.chol = np.linalg.cholesky(scale)

    def sample(self, size, rng):
        j = rng.integers(self.loc.shape[0], size=size)
        z = np.einsum("nij,nj->ni", self.chol[j], rng.standard_normal((size, 2)))
        return self.loc[j] + z / np.sqrt(rng.chisquare(self.dof, size) / self.dof)[:, None]

    def logpdf(self, y, chunk=1000):
        nu, out = self.dof, np.empty(y.shape[0])
        const = special.gammaln((nu + 2) / 2) - special.gammaln(nu / 2) - math.log(nu * math.pi) - 0.5 * self.logdet
        for i0 in range(0, y.shape[0], chunk):
            q = _quad(y[i0:i0 + chunk], self.loc, self.inv)                                   # (G, J)
            out[i0:i0 + chunk] = special.logsumexp(const[None] - 0.5 * (nu + 2) * np.log1p(q / nu), axis=1)
        return out - math.log(self.loc.shape[0])


class GaussMixture:
    """Weighted mixture of bivariate Gaussians (weights (K,), mean (K, 2), cov (K, 2, 2))."""

    def __init__(self, logw, mean, cov):
        self.logw, self.mean, self.cov = logw - special.logsumexp(logw), mean, cov
        self.inv, self.logdet = _inv_logdet(cov)
        self.chol = np.linalg.cholesky(cov)

    def sample(self, size, rng):
        k = rng.choice(self.mean.shape[0], size=size, p=np.exp(self.logw))
        return self.mean[k] + np.einsum("nij,nj->ni", self.chol[k], rng.standard_normal((size, 2)))

    def logpdf(self, y, chunk=1000):
        out = np.empty(y.shape[0])
        const = self.logw - math.log(2 * math.pi) - 0.5 * self.logdet
        for i0 in range(0, y.shape[0], chunk):
            q = _quad(y[i0:i0 + chunk], self.mean, self.inv)
            out[i0:i0 + chunk] = special.logsumexp(const[None] - 0.5 * q, axis=1)
        return out


def pop_mixture(fv, prior, post_i, rng, j_target=J_POP, batch=4096, max_draws=2 ** 21) -> tuple[StudentTMixture, int]:
    """J accepted draws of B from the untruncated posterior (rho(B) < c), each giving its Sigma-integrated Student-t."""
    kept, tried = [], 0
    while sum(len(b) for b in kept) < j_target and tried < max_draws:
        b, _ = fv.sample_mniw(post_i.bn[0], post_i.vn[0], post_i.nun, post_i.psin[0], batch, rng)
        tried += batch
        kept.append(b[fv.spectral_radius(b) < prior.c])
    b = np.concatenate(kept)[:j_target]
    db = b - post_i.bn[0]
    psi_b = post_i.psin[0] + np.swapaxes(db, 1, 2) @ post_i.vn_inv[0] @ db
    dof = post_i.nun + 1.0
    return StudentTMixture(np.einsum("jik,i->jk", b, post_i.last[0]), psi_b / dof, dof), b.shape[0]


def lib_mixture(lib, ctx_i) -> GaussMixture:
    lw = lib.log_weights(ctx_i[None])[0]
    return GaussMixture(lw, np.einsum("kij,j->ki", lib.a, ctx_i[-1]), lib.sigma.copy())


# ------------------------------------------------------------------------------------------------ EM fit of q_m

def quad_nodes(p, rng, g: int = G_NODES) -> tuple[np.ndarray, np.ndarray, np.ndarray, float]:
    """Tan-substitution Gauss-Legendre grid (g x g) on coordinates whitened by the moments of p (estimated from
    samples): y = mu + L tan(u). Returns nodes (g*g, 2), normalised weights a = w p / sum(w p), log p at the nodes,
    and the mass error |sum w p - 1|."""
    s = p.sample(20_000, rng)
    mu, chol = s.mean(axis=0), np.linalg.cholesky(np.cov(s.T))
    x, w = np.polynomial.legendre.leggauss(g)
    u, wu = 0.5 * np.pi * x, 0.5 * np.pi * w
    z, jac = np.tan(u), wu / np.cos(u) ** 2
    zz = np.stack(np.meshgrid(z, z, indexing="ij"), -1).reshape(-1, 2)
    wz = np.outer(jac, jac).ravel() * abs(np.linalg.det(chol))
    y = mu[None] + zz @ chol.T
    lp = p.logpdf(y)
    wp = wz * np.exp(lp)
    mass = float(wp.sum())
    return y, wp / mass, lp, abs(mass - 1.0)


def fit_gmm_weighted(y: np.ndarray, a: np.ndarray, m: int, rng, starts: int = 2, iters: int = 300,
                     tol: float = 1e-8) -> GaussMixture:
    """EM maximising sum_i a_i log q(y_i) (= minimising the quadrature KL(p || q)); 2 x 2 algebra written out."""
    mu = a @ y
    d = y - mu
    cov0 = (a[:, None] * d).T @ d
    reg = 1e-9 * float(np.trace(cov0)) / 2
    best, best_ll = None, -np.inf
    for _ in range(starts if m > 1 else 1):
        mean = y[rng.choice(y.shape[0], m, replace=False, p=a)] if m > 1 else mu[None]
        cov = np.repeat(cov0[None], m, axis=0)
        logw, prev = np.full(m, -math.log(m)), -np.inf
        for _ in range(iters if m > 1 else 1):
            inv, logdet = _inv_logdet(cov)
            lq = logw[None] - math.log(2 * math.pi) - 0.5 * logdet[None] - 0.5 * _quad(y, mean, inv)
            tot = special.logsumexp(lq, axis=1)
            ll = float(a @ tot)
            resp = a[:, None] * np.exp(lq - tot[:, None])
            nk = resp.sum(axis=0) + 1e-300
            logw = np.log(nk)
            mean = (resp.T @ y) / nk[:, None]
            d0, d1 = y[:, 0, None] - mean[None, :, 0], y[:, 1, None] - mean[None, :, 1]
            c00, c01, c11 = ((resp * d0 * d0).sum(0) / nk + reg, (resp * d0 * d1).sum(0) / nk,
                             (resp * d1 * d1).sum(0) / nk + reg)
            cov = np.stack([np.stack([c00, c01], -1), np.stack([c01, c11], -1)], -2)
            if abs(ll - prev) <= tol * max(1.0, abs(ll)):
                break
            prev = ll
        final = GaussMixture(logw, mean, cov)
        ll = float(a @ final.logpdf(y))
        if ll > best_ll:
            best, best_ll = final, ll
    return best


def floors(p, rng) -> tuple[list[float], float]:
    """Quadrature KL(p || q_m), minimum over m' <= m, for every m in MS; and the grid's mass error."""
    y, a, lp, mass_err = quad_nodes(p, rng)
    out, best = [], np.inf
    for m in MS:
        best = min(best, float(a @ (lp - fit_gmm_weighted(y, a, m, rng).logpdf(y))))
        out.append(best)
    return out, mass_err


# ------------------------------------------------------------------------------------------------ jobs

def _job(job) -> list[dict]:
    from dynaicl.rng import NamedStreams
    from dynaicl_families.stage2 import f2_var as fv
    from dynaicl_families.stage2.seeds import role_seed
    r, n, contexts, role, set_name, ref_name = job
    root = role_seed(role)
    rng = np.random.default_rng([root, JOBS.index((set_name, ref_name)), int(r * 100), n])
    pop = fv.population_f2()
    library = fv.library_from_prior(pop, max(KS), NamedStreams(root).stream("f2_head_floor_library"))
    if set_name == "HELD":
        split = fv.simulate_f2(pop, r, NamedStreams(root), contexts, n + 1, stream_code=11)
    else:
        k = int(ref_name[3:])
        pick = np.random.default_rng([root, 7, k, int(r * 100), n]).integers(k, size=contexts)
        split = fv.simulate_f2(pop, r, NamedStreams(root), contexts, n + 1, stream_code=12,
                               system_override=(library.a[:k][pick], library.sigma[:k][pick]))
    ctx, _ = fv.contexts_and_targets(split, n)
    per_ctx, j_min, mass_max = [], None, 0.0
    if ref_name == "pop":
        post = fv.posterior(pop, ctx)
    else:
        k = int(ref_name[3:])
        lib = fv.VarLibrary(library.a[:k], library.sigma[:k])
    for i in range(contexts):
        if ref_name == "pop":
            p, j = pop_mixture(fv, pop, post.item(i), rng)
            j_min = j if j_min is None else min(j_min, j)
        else:
            p = lib_mixture(lib, ctx[i])
        fl, mass_err = floors(p, rng)
        if mass_err > MASS_TOL:
            raise FloatingPointError(f"{set_name} {ref_name} r={r} n={n} context {i}: mass error {mass_err:.2e}")
        per_ctx.append(fl)
        mass_max = max(mass_max, mass_err)
    arr = np.array(per_ctx)                                                   # (contexts, len(MS))
    return [{"set": set_name, "ref": ref_name, "r": r, "n": n, "m": m, "mean_floor": float(arr[:, a].mean()),
             "se": float(arr[:, a].std(ddof=1) / math.sqrt(contexts)), "max_floor": float(arr[:, a].max()),
             "contexts": contexts, "pop_min_accepted": j_min, "max_mass_err": mass_max} for a, m in enumerate(MS)]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--smoke", action="store_true", help="role f2_tests, r = 1, n in {2, 20}, 3 contexts")
    args = ap.parse_args(argv)
    out = Path(args.out) if Path(args.out).is_absolute() else ROOT / args.out
    out.mkdir(parents=True, exist_ok=True)
    role = "f2_tests" if args.smoke else "f2n_head_floor"
    rs, ns, contexts = ((1.0,), (2, 20), 3) if args.smoke else (RS, NS, CONTEXTS)
    tasks = [(r, n, contexts, role, s, ref) for r in rs for n in ns for s, ref in JOBS]
    tasks.sort(key=lambda t: 0 if t[5] == "pop" else 1)
    t0 = time.time()
    with ProcessPoolExecutor(max_workers=args.workers) as ex:
        rows = []
        for k, res in enumerate(ex.map(_job, tasks, chunksize=1), 1):
            rows += res
            print(f"{time.strftime('%H:%M:%S')} [{k}/{len(tasks)}] {res[0]['set']} {res[0]['ref']} r={res[0]['r']} "
                  f"n={res[0]['n']}", flush=True)
    with open(out / "f2_head_floor.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    chosen = next((m for m in MS if all(r["mean_floor"] <= FLOOR for r in rows if r["m"] == m)), None)
    worst = {m: max((r for r in rows if r["m"] == m), key=lambda x: x["mean_floor"]) for m in MS}
    summary = {"role": role, "chosen_m": chosen, "rule": "smallest m with mean floor <= 0.001 in every cell",
               "worst_cell_per_m": {m: {k: worst[m][k] for k in ("set", "ref", "r", "n", "mean_floor", "se")}
                                    for m in MS},
               "cells_with_se_over_flag": sum(1 for r in rows if r["se"] > SE_FLAG),
               "settings": {"contexts": contexts, "J_pop": J_POP, "grid": G_NODES, "MS": MS},
               "max_mass_err": max(r["max_mass_err"] for r in rows),
               "seconds": round(time.time() - t0, 1)}
    (out / "f2_head_floor_summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
    import scipy

    def git(*a: str) -> str:
        return subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True).stdout.strip()

    prov = {"command": " ".join([Path(sys.executable).name, *sys.argv]), "python": platform.python_version(),
            "platform": platform.platform(), "numpy": np.__version__, "scipy": scipy.__version__,
            "cpu_count": os.cpu_count(), "workers": args.workers,
            "sources_sha256": {s: hashlib.sha256((ROOT / s).read_bytes()).hexdigest() for s in SOURCES},
            "git_head": git("rev-parse", "HEAD"),
            "git_dirty_tracked": bool(git("status", "--porcelain", "--untracked-files=no"))}
    (out / "provenance.json").write_text(json.dumps(prov, indent=1), encoding="utf-8")
    print(json.dumps(summary, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
