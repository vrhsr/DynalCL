"""F2 separability map (docs/STAGE2_F2_MAP_SPEC.md): bivariate VAR(1), references of dynaicl_families/stage2/f2_var.py.

Units: one HELD unit per r (systems from P_F2; truth = pop; gaps pop-ctx and pop-lib for every library draw and K) and one
INLIB unit per (r, K, draw) (systems = the K atoms; truth = lib_K; gaps lib-pop and lib-ctx). Every reference is scored on the
same contexts and targets (common random numbers). Truncated predictives (pop, ctx) are Monte Carlo estimates with a per-item
SE (MATH_F2 section 5); their per-item SEs are carried into every gap's Monte Carlo SE.
"""

from __future__ import annotations

import hashlib
import math
import numpy as np

from dynaicl.rng import NamedStreams
from dynaicl_families.stage2 import f2_var as fv

NS = (2, 3, 5, 10, 20)
NS_CTX = (5, 10, 20)           # pairs with the context-only reference: at n <= 3 it cannot meet the MC criterion (spec 1)
RS = (0.25, 1.0, 4.0)
KS = (2, 16, 64)
DRAWS = 8
DELTA = 0.02
Z_BOUND = 3.0
ITEM_SE_TARGET = 0.01          # S34: per-item SE(log p) target
CELL_MC_SE_MAX = DELTA / 100   # S34: Monte Carlo SE of every reported cell mean
ITEM_SE_FLAG = 0.01            # items above this are counted; > 1% of a cell's items -> cell is MC-LIMITED


def library_atoms(root: int, draw: int, k_max: int = max(KS)) -> fv.VarLibrary:
    return fv.library_from_prior(fv.population_f2(), k_max,
                                 NamedStreams(root).stream(f"f2_map_library/draw{draw}"))


def sub_library(lib: fv.VarLibrary, k: int) -> fv.VarLibrary:
    return fv.VarLibrary(lib.a[:k], lib.sigma[:k])


def inlib_seed(root: int, draw: int, k: int) -> int:
    ss = np.random.SeedSequence(root, spawn_key=(int.from_bytes(hashlib.sha256(b"f2_map_inlib").digest()[:4], "little"),
                                                 draw, k))
    return int(ss.generate_state(1, dtype=np.uint32)[0])


def truncated_scores(prior: fv.MNIWPrior, ctx: np.ndarray, y: np.ndarray, rng_root: int) -> tuple[np.ndarray, np.ndarray,
                                                                                                    np.ndarray]:
    """(log p, per-item SE, capped flags) of the truncated reference at the realised targets; item i uses its own stream."""
    post = fv.posterior(prior, ctx)
    lp, se, cap = np.empty(ctx.shape[0]), np.empty(ctx.shape[0]), np.zeros(ctx.shape[0], dtype=bool)
    for i in range(ctx.shape[0]):
        e = fv.truncated_logpdf_item(prior, post.item(i), y[i][None], NamedStreams(rng_root).item(prior.name, i),
                                     target_se=ITEM_SE_TARGET, batch=2048, min_accepted=1000, max_draws=2 ** 22)
        lp[i], se[i], cap[i] = e.logpdf[0], e.se_log[0], e.capped
    return lp, se, cap


def gap(lp_truth, lp_other, se_truth=None, se_other=None) -> dict:
    """Paired gap with item SE and Monte Carlo SE. Non-finite items (a capped Monte Carlo estimate that is not positive)
    are excluded from the mean and counted in ``items_over_se_flag``, which makes the cell MC-LIMITED if > 1% (spec 3)."""
    d_all = lp_truth - lp_other
    finite = np.isfinite(d_all)
    d = d_all[finite]
    n = d.size
    se_truth = None if se_truth is None else np.where(np.isfinite(se_truth), se_truth, np.inf)[finite]
    se_other = None if se_other is None else np.where(np.isfinite(se_other), se_other, np.inf)[finite]
    item_se = float(d.std(ddof=1) / math.sqrt(n))
    mc_var = 0.0
    for s in (se_truth, se_other):
        if s is not None:
            mc_var += float(np.sum(np.asarray(s) ** 2)) / n ** 2
    mc_se = math.sqrt(mc_var)
    flags = int(np.sum(~finite))
    for s in (se_truth, se_other):
        if s is not None:
            flags += int(np.sum(np.asarray(s) > ITEM_SE_FLAG))
    return {"mean": float(d.mean()), "se_items": item_se, "se_mc": mc_se, "se": math.sqrt(item_se ** 2 + mc_se ** 2),
            "n_items": int(d_all.size), "items_over_se_flag": flags}


def _contexts(split: fv.F2Split, n: int) -> tuple[np.ndarray, np.ndarray]:
    return fv.contexts_and_targets(split, n)


def held_unit(r: float, n: int, root: int, n_items: int) -> dict:
    """HELD set for one (r, n): systems from P_F2 (truth = pop); pop-ctx (n in NS_CTX only) and pop-lib per draw and K."""
    pop, ctxp = fv.population_f2(), fv.context_only_f2()
    split = fv.simulate_f2(pop, r, NamedStreams(root), n_items, max(NS) + 1, stream_code=11)
    libs = [library_atoms(root, d) for d in range(DRAWS)]
    atoms = np.concatenate([lib.a.reshape(-1, 4) for lib in libs])
    overlap = int(sum(bool(np.any(np.all(a.reshape(4) == atoms, axis=1))) for a in split.a))
    ctx, y = _contexts(split, n)
    lp_pop, se_pop, cap_pop = truncated_scores(pop, ctx, y, root * 1000 + 1 + n)
    rows = []
    if n in NS_CTX:
        lp_ctx, se_ctx, cap_ctx = truncated_scores(ctxp, ctx, y, root * 1000 + 101 + n)
        rows.append({"set": "HELD", "pair": "pop-ctx", "r": r, "n": n, **gap(lp_pop, lp_ctx, se_pop, se_ctx),
                     "capped": int(cap_pop.sum() + cap_ctx.sum())})
    for d, lib in enumerate(libs):
        for k in KS:
            lp_lib = sub_library(lib, k).logpdf(ctx, y[:, None, :])[:, 0]
            rows.append({"set": "HELD", "pair": "pop-lib", "r": r, "n": n, "K": k, "draw": d,
                         **gap(lp_pop, lp_lib, se_pop, None), "capped": int(cap_pop.sum())})
    return {"r": r, "n": n, "rows": rows, "held_atom_overlap": overlap}


def inlib_unit(r: float, k: int, draw: int, root: int, n_items: int) -> dict:
    """INLIB set for one (r, K, draw): systems are the K atoms (truth = lib_K); lib-pop for every n, lib-ctx for n in
    NS_CTX."""
    pop, ctxp = fv.population_f2(), fv.context_only_f2()
    lib = sub_library(library_atoms(root, draw), k)
    seed = inlib_seed(root, draw, k)
    pick = np.random.default_rng(seed).integers(k, size=n_items)
    split = fv.simulate_f2(pop, r, NamedStreams(seed), n_items, max(NS) + 1, stream_code=12,
                           system_override=(lib.a[pick], lib.sigma[pick]))
    rows = []
    for n in NS:
        ctx, y = _contexts(split, n)
        lp_lib = lib.logpdf(ctx, y[:, None, :])[:, 0]
        lp_pop, se_pop, cap_pop = truncated_scores(pop, ctx, y, seed * 1000 + 1 + n)
        rows.append({"set": "INLIB", "pair": "lib-pop", "r": r, "n": n, "K": k, "draw": draw,
                     **gap(lp_lib, lp_pop, None, se_pop), "capped": int(cap_pop.sum())})
        if n in NS_CTX:
            lp_ctx, se_ctx, cap_ctx = truncated_scores(ctxp, ctx, y, seed * 1000 + 101 + n)
            rows.append({"set": "INLIB", "pair": "lib-ctx", "r": r, "n": n, "K": k, "draw": draw,
                         **gap(lp_lib, lp_ctx, None, se_ctx), "capped": int(cap_ctx.sum())})
    return {"r": r, "K": k, "draw": draw, "rows": rows}


def classify(row: dict) -> str:
    """MC-LIMITED if the cell's Monte Carlo SE exceeds delta/100 or more than 1% of its items exceed the per-item SE
    flag (S34); otherwise the Stage 1A map rule on mean +/- 3 SE (SE includes the Monte Carlo part)."""
    if row["se_mc"] > CELL_MC_SE_MAX or row["items_over_se_flag"] > 0.01 * row["n_items"]:
        return "MC-LIMITED"
    lo, hi = row["mean"] - Z_BOUND * row["se"], row["mean"] + Z_BOUND * row["se"]
    if lo >= DELTA:
        return "IDENTIFIABLE"
    if hi < DELTA:
        return "UNIDENTIFIABLE"
    return "BORDERLINE"


def classify_draws(labels: list[str]) -> str:
    if sum(lab == "MC-LIMITED" for lab in labels) > 0.1 * len(labels):
        return "MC-LIMITED"
    if sum(lab == "IDENTIFIABLE" for lab in labels) >= 0.9 * len(labels):
        return "IDENTIFIABLE"
    if sum(lab == "UNIDENTIFIABLE" for lab in labels) >= 0.9 * len(labels):
        return "UNIDENTIFIABLE"
    return "PARTIAL"


