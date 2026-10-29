"""F2 validation checks (docs/MATH_F2.md section 9: F2-V9 calibration, F2-V10 optimality) and structural detectors for the
F2 mutation matrix (F2-V11). Every patched name (``fv.population_f2``, ``fv.regression_arrays``, ``fv.contexts_and_targets``,
``fv.rb_logpdf``, ``fv.spectral_radius``, ``fv.simulate_f2``) is looked up through the module at call time.

Monte Carlo quantities use the production truncated estimator (MATH_F2 section 5) at the S34 per-item target 0.01; the
context-only reference is used only for n >= 5 (docs/STAGE2_F2_MAP_SPEC.md section 1).
"""

from __future__ import annotations

import math

import numpy as np
from scipy import special, stats

from dynaicl.rng import NamedStreams

TARGET = 0.01
COVERAGE_LEVELS = (0.5, 0.8, 0.95)


def _fv():
    from dynaicl_families.stage2 import f2_var as fv
    return fv


def population_sample(n: int, r: float, n_items: int, seed: int):
    fv = _fv()
    split = fv.simulate_f2(fv.population_f2(), r, NamedStreams(seed), n_items, n + 1, stream_code=14)
    ctx, y = fv.contexts_and_targets(split, n)
    return ctx, y, split


def matched_guard() -> dict:
    """The population reference's prior must equal the prior the evaluation systems are drawn from (configuration
    constants; exact equality). The simulator takes the prior object, so the check compares the reference with the
    module's population prior used by ``population_sample``."""
    fv = _fv()
    ref = fv.population_f2()
    want = {"b0": [[0.4, 0.0], [0.0, 0.4]], "v0": [[0.09, 0.0], [0.0, 0.09]], "nu0": 7.0,
            "psi0": [[4.0, 0.0], [0.0, 4.0]], "c": 0.95}
    got = {k: v for k, v in ref.params().items() if k != "name"}
    return {"check": "matched_guard", "pass": got == want, "reference": got, "design": want}


def leakage(seed: int) -> dict:
    fv = _fv()
    bad = []
    for n in (2, 5, 20):
        split = fv.simulate_f2(fv.population_f2(), 1.0, NamedStreams(seed + n), 16, n + 3, stream_code=15)
        ctx, y = fv.contexts_and_targets(split, n)
        traj = split.trajectories
        if not np.array_equal(ctx, traj[:, :n + 1, :]):
            bad.append(f"n={n}: context is not x_0..x_n")
        if not np.array_equal(y, traj[:, n + 1, :]):
            bad.append(f"n={n}: target is not x_(n+1)")
        changed = fv.F2Split(split.a, split.sigma, np.concatenate([traj[:, :n + 1], traj[:, n + 1:] + 1000.0], axis=1))
        ctx2, _ = fv.contexts_and_targets(changed, n)
        if not np.array_equal(ctx, ctx2):
            bad.append(f"n={n}: context depends on values after x_n")
    return {"check": "leakage", "pass": not bad, "problems": bad}


def spectral_radius_check(seed: int) -> dict:
    """Closed-form 2 x 2 spectral radius against numpy eigenvalues (relative 1e-12)."""
    fv = _fv()
    a = np.random.default_rng(seed).normal(scale=0.8, size=(5000, 2, 2))
    err = float(np.max(np.abs(fv.spectral_radius(a) - np.max(np.abs(np.linalg.eigvals(a)), axis=-1))
                       / np.maximum(1.0, np.max(np.abs(np.linalg.eigvals(a)), axis=-1))))
    return {"check": "spectral_radius", "pass": err <= 1e-12, "max_rel_err": err}


def _trunc_cdf_item(prior, post_i, y_i: np.ndarray, rng: np.random.Generator, draws: int = 2 ** 16):
    """Marginal CDFs P(Y_k <= y_k | D), k = 0, 1, and the posterior CDF of rho(A) at a given value need samples from the
    truncated posterior: accepted draws of B (Sigma integrated for the marginal t CDFs). Returns (accepted B, marginal
    CDF values (2,), standard errors (2,))."""
    fv = _fv()
    b, _ = fv.sample_mniw(post_i.bn[0], post_i.vn[0], post_i.nun, post_i.psin[0], draws, rng)
    b = b[fv.spectral_radius(b) < prior.c]
    if b.shape[0] < 1000:
        return b, np.full(2, np.nan), np.full(2, np.inf)
    db = b - post_i.bn[0]
    psi_b = post_i.psin[0] + np.swapaxes(db, 1, 2) @ post_i.vn_inv[0] @ db
    dof = post_i.nun + 1.0
    loc = np.einsum("jik,i->jk", b, post_i.last[0])
    scale = np.sqrt(np.stack([psi_b[:, 0, 0], psi_b[:, 1, 1]], axis=1) / dof)
    f = special.stdtr(dof, (y_i[None, :] - loc) / scale)
    return b, f.mean(axis=0), f.std(axis=0, ddof=1) / math.sqrt(f.shape[0])


def calibration_cell(n: int, r: float, n_items: int, seed: int, alpha_per_test: float) -> dict:
    """PIT of each coordinate's marginal predictive (KS), central 50/80/95% coverage of each marginal (binomial z), and a
    continuous SBC of rho(A): the truncated-posterior CDF of rho at the true value must be Uniform(0, 1) (KS). Monte Carlo
    PIT values carry SE <= about 0.002 (2^16 draws), far below the KS resolution at these sample sizes."""
    fv = _fv()
    prior = fv.population_f2()
    ctx, y, split = population_sample(n, r, n_items, seed)
    post = fv.posterior(prior, ctx)
    pit = np.empty((n_items, 2))
    sbc = np.empty(n_items)
    rho_true = fv.spectral_radius(split.a)
    for i in range(n_items):
        b, cdf, _ = _trunc_cdf_item(prior, post.item(i), y[i], NamedStreams(seed).item("pit", i))
        pit[i] = cdf
        sbc[i] = float(np.mean(fv.spectral_radius(b) <= rho_true[i])) if b.shape[0] else np.nan
    p = {}
    for k in range(2):
        p[f"pit_ks_{k}"] = float(stats.kstest(pit[:, k], "uniform").pvalue)
        for lev in COVERAGE_LEVELS:
            hits = int(np.sum(np.abs(pit[:, k] - 0.5) <= lev / 2))
            z = (hits - n_items * lev) / math.sqrt(n_items * lev * (1 - lev))
            p[f"coverage_{k}_{lev}"] = float(2 * stats.norm.sf(abs(z)))
    p["sbc_rho_ks"] = float(stats.kstest(sbc, "uniform").pvalue)
    return {"check": "calibration", "n": n, "r": r, "items": n_items, "p_values": p, "alpha_per_test": alpha_per_test,
            "pass": all(v >= alpha_per_test for v in p.values())}


def optimality_cell(n: int, r: float, n_items: int, seed: int, z_crit: float, lib_ks=(2, 16, 64)) -> dict:
    """E[LS(pop) - LS(other)] >= 0 on population systems (pop is Bayes there); one-sided z with the Monte Carlo SE of the
    truncated estimates included. Others: libraries of K atoms from the population; the context-only reference at n >= 5."""
    fv = _fv()
    from dynaicl_families.stage2 import f2_map as fm
    ctx, y, _ = population_sample(n, r, n_items, seed)
    lp, se, _ = fm.truncated_scores(fv.population_f2(), ctx, y, seed * 10 + 1)
    others = {f"LIB-{k}": fv.library_from_prior(fv.population_f2(), k, NamedStreams(seed).stream(f"lib{k}"))
              for k in lib_ks}
    rows = {}
    for name, lib in others.items():
        d = lp - lib.logpdf(ctx, y[:, None, :])[:, 0]
        s = math.sqrt(d.var(ddof=1) / d.size + float(np.sum(se ** 2)) / d.size ** 2)
        rows[name] = {"mean": float(d.mean()), "se": s, "z": float(d.mean() / s)}
    if n >= 5:
        lc, sc, _ = fm.truncated_scores(fv.context_only_f2(), ctx, y, seed * 10 + 2)
        d = lp - lc
        ok = np.isfinite(d)
        s = math.sqrt(d[ok].var(ddof=1) / ok.sum() + float(np.sum(se[ok] ** 2 + sc[ok] ** 2)) / ok.sum() ** 2)
        rows["context_only"] = {"mean": float(d[ok].mean()), "se": s, "z": float(d[ok].mean() / s),
                                "non_finite": int((~ok).sum())}
    return {"check": "optimality", "n": n, "r": r, "items": n_items, "z_crit": z_crit, "rows": rows,
            "pass": all(v["z"] >= -z_crit for v in rows.values())}
