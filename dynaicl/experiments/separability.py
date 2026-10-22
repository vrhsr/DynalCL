"""Reference separability map (Section 7). CPU only, no neural networks.

Question: are the reference strategies (continuous-prior Bayes, finite-library posterior,
context-only frontier) statistically distinguishable at all in the regimes later models will be
tested in? Pre-registered in docs/PREREG_separability.md.

Usage:
    python -m dynaicl.experiments.separability --config config/separability.yaml --workers 8

A work unit is one grid cell: (sigma, condition, K, n, h). E-CONT cells evaluate every library size
as a competitor, so their K is 0. Units are pure functions of (config, unit), because every random
draw comes from name-keyed streams. Results therefore do not depend on the worker count or on
execution order.
"""

from __future__ import annotations

import argparse
import math
import multiprocessing
from pathlib import Path
import sys
import time
from concurrent.futures import ProcessPoolExecutor

import numpy as np
from scipy import stats

from dynaicl.baselines.common import FallbackSettings
from dynaicl.baselines.family import build_context_only_family, select_frontier_member
from dynaicl.baselines.kernel import KernelSettings
from dynaicl.config.schema import SeparabilityConfig, config_from_dict, load_config
from dynaicl.evaluation import harness
from dynaicl.metrics import calibration, scoring
from dynaicl.provenance import RunRecorder, sha256_file
from dynaicl.references import matched as matched_refs
from dynaicl.references.library import FiniteLibraryPredictor
from dynaicl.references.quadrature import QuadratureSettings
from dynaicl.rng import NamedStreams
from dynaicl.systems.conditions import ContinuousPriorCondition, InitialStateSpec, LibraryCondition
from dynaicl.systems.library import build_library_from_prior
from dynaicl.systems.priors import StableCoefficientPrior
from dynaicl.systems.splits import (
    SplitRole,
    assert_no_unintended_overlap,
    assert_parameters_disjoint,
    assert_parameters_within_library,
    generate_library_training_split,
    generate_split,
)

CONTEXT_ONLY = ("flat_prior_bayes", "ols_gaussian", "ols_student_t", "kernel_rolling_origin", "kernel_blocked",
                "kernel_leave_one_out", "persistence")


# --------------------------------------------------------------------------------------- construction


def build_prior(cfg: SeparabilityConfig, sigma: float) -> StableCoefficientPrior:
    p = cfg.prior
    return StableCoefficientPrior(rho=p.rho, sigma=sigma, shape=p.shape, mu0=p.mu0, tau0=p.tau0)


def build_settings(cfg: SeparabilityConfig) -> tuple[QuadratureSettings, KernelSettings, FallbackSettings]:
    q = cfg.numerics.quadrature
    k = cfg.baselines.kernel
    f = cfg.baselines.fallback
    return (QuadratureSettings(q.panels, q.nodes_per_panel, q.log_drop, q.panels_per_cell, q.max_panels),
            KernelSettings(tuple(k.bandwidth_multipliers), k.min_train_pairs, k.n_blocks, k.gap, k.min_pairs,
                           k.min_validation_points),
            FallbackSettings(f.coefficient_mean, f.coefficient_variance, f.predictive_variance,
                             f.variance_relative_floor))


def plan_units(cfg: SeparabilityConfig) -> list[tuple]:
    units = []
    for si, _ in enumerate(cfg.grid.noise_scales):
        for cond in cfg.grid.conditions:
            for k in (cfg.grid.library_sizes if cond == "E-LIB" else (0,)):
                for n in cfg.grid.context_lengths:
                    for h in cfg.grid.horizons:
                        units.append((si, cond, int(k), int(n), int(h)))
    return units


def n_competitors(cfg: SeparabilityConfig, cond: str) -> int:
    """Predictors other than the matched reference scored in a unit of this condition."""
    return len(CONTEXT_ONLY) + (len(cfg.grid.library_sizes) if cond == "E-CONT" else 1)


# ----------------------------------------------------------------------------------------- one unit


def _calibration_summary(tab: harness.ScoreTable, levels) -> dict:
    out = {"pit_ks_p": calibration.ks_uniform_pvalue(tab.pit),
           "pit_hist": np.histogram(tab.pit, bins=10, range=(0, 1))[0].tolist()}
    for lev in levels:
        k = int(scoring.covered_from_pit(tab.pit, lev).sum())
        out[f"coverage_{lev}"] = k / tab.pit.size
        out[f"coverage_{lev}_p"] = calibration.coverage_pvalue(k, tab.pit.size, lev)
    return out


def _g_metric(model: np.ndarray, ctx: np.ndarray, ref: np.ndarray, cfg: SeparabilityConfig) -> dict:
    """G = (S_model - S_ctx)/(S_matched - S_ctx) on paired items, with a delta-method SE.

    Ill-conditioned when the denominator is not clearly away from zero:
    |mean(d2)| < separation_z * SE(d2), or |mean(d2)| < practical_gap_nats.
    """
    d1, d2 = model - ctx, ref - ctx
    n = d1.size
    m1, m2 = float(d1.mean()), float(d2.mean())
    se2 = float(d2.std(ddof=1) / math.sqrt(n))
    ill = abs(m2) < cfg.metrics.separation_z * se2 or abs(m2) < cfg.metrics.practical_gap_nats
    if m2 == 0.0:
        return {"G": float("nan"), "G_se": float("nan"), "denominator": m2, "denominator_se": se2,
                "ill_conditioned": True}
    g = m1 / m2
    c = np.cov(d1, d2, ddof=1)
    var_g = (c[0, 0] - 2 * g * c[0, 1] + g * g * c[1, 1]) / (n * m2 * m2)
    return {"G": g, "G_se": float(math.sqrt(max(var_g, 0.0))), "denominator": m2, "denominator_se": se2,
            "ill_conditioned": bool(ill)}


def classify_pair(d: scoring.PairedDifference, cfg: SeparabilityConfig) -> str:
    """Pre-registered decision rule (docs/PREREG_separability.md section 4)."""
    delta, zs, ze = cfg.metrics.practical_gap_nats, cfg.metrics.separation_z, cfg.metrics.equivalence_z
    if abs(d.mean) >= zs * d.se and abs(d.mean) >= delta:
        return "separable"
    if d.mean - ze * d.se > -delta and d.mean + ze * d.se < delta:
        return "equivalent"
    if abs(d.mean) >= zs * d.se:
        return "detectable_below_delta"
    return "inconclusive"


def run_unit(cfg_dict: dict, unit: tuple, z_t1: float) -> dict:
    cfg = config_from_dict(cfg_dict)
    si, cond_name, k_lib, n, h = unit
    sigma = cfg.grid.noise_scales[si]
    prior = build_prior(cfg, sigma)
    qset, kset, fset = build_settings(cfg)
    x0 = InitialStateSpec(cfg.initial_state.mean, cfg.initial_state.sd)
    streams = NamedStreams(cfg.experiment.root_seed)
    length = max(cfg.grid.context_lengths) + max(cfg.grid.horizons)
    libraries = {k: build_library_from_prior(prior, k, streams) for k in cfg.grid.library_sizes}
    t0 = time.time()

    condition = ContinuousPriorCondition(prior, x0) if cond_name == "E-CONT" else LibraryCondition(libraries[k_lib], x0)
    ev = generate_split(condition, SplitRole.EVALUATION, streams, cfg.replication.n_eval_items, length)
    sel = generate_split(condition, SplitRole.SELECTION, streams, cfg.replication.n_selection_items, length)

    # ---- leakage controls (Section 3): intentional parameter overlap vs unintended data overlap
    leakage = {}
    largest = libraries[max(cfg.grid.library_sizes)]
    train = generate_library_training_split(largest, streams, length, x0)
    assert_no_unintended_overlap(ev, train)
    assert_no_unintended_overlap(sel, train)
    assert_no_unintended_overlap(ev, sel)
    if cond_name == "E-CONT":
        leakage["min_param_distance_eval_vs_library"] = assert_parameters_disjoint(ev, largest)
        assert_parameters_disjoint(sel, largest)
    else:
        assert_parameters_within_library(ev, libraries[k_lib])
        assert_parameters_within_library(sel, libraries[k_lib])
        leakage["intentional_parameter_overlap"] = True

    es = harness.build_evaluation_set(condition, ev, n, h)
    ss = harness.build_evaluation_set(condition, sel, n, h)
    ref = matched_refs.matched_reference_for(condition, qset)

    family = build_context_only_family(sigma, qset, kset, fset, cfg.baselines.ols_min_transitions)
    predictors = {"matched_reference": ref.predictor}
    if cond_name == "E-CONT":
        for k in cfg.grid.library_sizes:
            predictors[f"library_K{k}"] = FiniteLibraryPredictor(libraries[k])
    else:
        predictors["continuous_prior_bayes"] = matched_refs.continuous_prior_predictor(prior, qset)
    predictors.update(family)

    tables = {}
    for name, pred in predictors.items():
        keys = ("multiplier",) if name.startswith("kernel_") else ()
        tables[name] = harness.score_predictor(pred, es, compute_crps=cfg.metrics.compute_crps, info_keys=keys)

    # ---- frontier: best context-only member on the disjoint selection set
    sel_scores = {name: harness.score_predictor(family[name], ss).log_score for name in CONTEXT_ONLY}
    frontier_all = select_frontier_member(sel_scores, family, higher_is_better=True, strict=False)
    frontier_strict = select_frontier_member(sel_scores, family, higher_is_better=True, strict=True)
    tables["frontier_all"] = tables[frontier_all]
    tables["frontier_strict"] = tables[frontier_strict]

    # ---- T1: optimality diagnostics against the matched reference (guarded)
    competitors = {k: v for k, v in tables.items() if k not in ("matched_reference", "frontier_all", "frontier_strict")}
    t1 = harness.optimality_diagnostics(ref, es, tables["matched_reference"], competitors, z_t1)

    # ---- quadrature error estimate for the continuous-prior predictor on a few items
    cont = ref.predictor if cond_name == "E-CONT" else predictors["continuous_prior_bayes"]
    cont_fine = cont.with_settings(qset.refined(2))
    targets = harness.ground_truth_for_validation(es)[2]
    q_err = 0.0
    q_nodes_max = 0
    for i in range(min(cfg.numerics.quadrature_error_check_items, es.size)):
        p1, p2 = cont.predict(es.contexts[i], h), cont_fine.predict(es.contexts[i], h)
        q_err = max(q_err, abs(float(p1.logpdf(targets[i])) - float(p2.logpdf(targets[i]))),
                    abs(float(p1.cdf(targets[i])) - float(p2.cdf(targets[i]))))
        q_nodes_max = max(q_nodes_max, int(p1.info["quadrature"]["n_nodes"]))

    # ---- outputs
    base = {"sigma": sigma, "condition": cond_name, "K": k_lib, "n": n, "h": h}
    predictor_rows = []
    for name, tab in tables.items():
        row = {**base, "predictor": name,
               "member": frontier_all if name == "frontier_all" else frontier_strict if name == "frontier_strict" else name,
               "mean_log_score": float(tab.log_score.mean()),
               "se_log_score": float(tab.log_score.std(ddof=1) / math.sqrt(tab.log_score.size)),
               "mean_sq_error": float(tab.squared_error.mean()), "fallback_rate": float(tab.fallback.mean())}
        if tab.crps is not None:
            row["mean_crps"] = float(tab.crps.mean())
        cal = _calibration_summary(tab, cfg.metrics.coverage_levels)
        row.update({k: v for k, v in cal.items() if k != "pit_hist"})
        row["pit_hist"] = " ".join(str(c) for c in cal["pit_hist"])
        if "multiplier" in tab.info:
            mult = tab.info["multiplier"]
            row["mean_selected_multiplier"] = float(np.nanmean(mult)) if np.any(np.isfinite(mult)) else float("nan")
        predictor_rows.append(row)

    strategy = ["matched_reference", "frontier_all", "frontier_strict", "flat_prior_bayes"]
    strategy += [k for k in tables if k.startswith("library_K")] + (
        ["continuous_prior_bayes"] if cond_name == "E-LIB" else [])
    pair_rows = []
    for i, a in enumerate(strategy):
        for b in strategy[i + 1:]:
            d = scoring.paired_difference(tables[a].log_score, tables[b].log_score)
            pair_rows.append({**base, "A": a, "B": b, "mean_diff": d.mean, "se": d.se, "sd": d.sd, "z": d.z,
                              "classification": classify_pair(d, cfg)})
    for a, b in (("kernel_rolling_origin", "kernel_leave_one_out"), ("kernel_blocked", "kernel_leave_one_out"),
                 ("kernel_rolling_origin", "kernel_blocked")):
        d = scoring.paired_difference(tables[a].log_score, tables[b].log_score)
        pair_rows.append({**base, "A": a, "B": b, "mean_diff": d.mean, "se": d.se, "sd": d.sd, "z": d.z,
                          "classification": classify_pair(d, cfg)})

    g_rows = []
    models = [k for k in tables if k.startswith("library_K")] if cond_name == "E-CONT" else ["continuous_prior_bayes"]
    for model in models:
        for fr in ("frontier_all", "frontier_strict"):
            g = _g_metric(tables[model].log_score, tables[fr].log_score, tables["matched_reference"].log_score, cfg)
            g_rows.append({**base, "model": model, "context_baseline": fr, **g})

    t1_rows = [{**base, "competitor": r.competitor, "mean_ref_minus_comp": r.difference.mean, "se": r.difference.se,
                "z": r.difference.z, "violates": r.violates} for r in t1]

    item_scores = {name: tables[name].log_score for name in tables if not name.startswith("frontier")}
    return {"unit": list(unit), "base": base, "predictor_rows": predictor_rows, "pair_rows": pair_rows,
            "g_rows": g_rows, "t1_rows": t1_rows,
            "unit_info": {**base, "frontier_all": frontier_all, "frontier_strict": frontier_strict,
                          "quadrature_err_estimate": q_err, "quadrature_nodes_max": q_nodes_max, **leakage,
                          "selection_mean_log_scores": {k: float(v.mean()) for k, v in sel_scores.items()}},
            "item_scores": item_scores, "seconds": round(time.time() - t0, 2)}


# ------------------------------------------------------------------------------------- whole run


def t3_identity_checks(cfg: SeparabilityConfig) -> list[dict]:
    """T3 on the experiment's own priors: sequential = batch and the h = 2 chain rule."""
    from dynaicl.validation.checks import _simulate_context
    from dynaicl.references.quadrature import StablePriorQuadraturePredictor, composite_gauss_legendre
    from dynaicl.systems.context import ContextWindow
    from scipy import integrate, special
    rows = []
    rng = np.random.default_rng(cfg.experiment.root_seed)
    qset = build_settings(cfg)[0]
    for sigma in cfg.grid.noise_scales:
        prior = build_prior(cfg, sigma)
        pred = StablePriorQuadraturePredictor(prior, qset)
        for n in sorted(cfg.grid.context_lengths)[:2]:
            a = float(prior.sample_systems(rng, 1)[0][0])
            x = _simulate_context(a, sigma, n, rng)
            post = pred.posterior(ContextWindow(x))
            _, gl_w = composite_gauss_legendre(post.window[0], post.window[1], post.settings.panels,
                                               post.settings.nodes_per_panel)
            seq = np.log(gl_w) + prior.coefficient_logpdf(post.nodes)
            for t in range(1, len(x)):
                seq = seq + stats.norm.logpdf(x[t], post.nodes * x[t - 1], sigma)
            seq -= special.logsumexp(seq)
            seq_err = float(np.max(np.abs(seq - post.log_masses)))
            ctx = ContextWindow(x)
            p1, p2 = pred.predict(ctx, 1), pred.predict(ctx, 2)
            z = float(p2.quantile(0.5))
            val = integrate.quad(lambda w: math.exp(float(p1.logpdf(w)) + float(
                pred.predict(ContextWindow(np.append(x, w)), 1).logpdf(z))), p1.quantile(1e-12),
                p1.quantile(1 - 1e-12), epsabs=1e-13, epsrel=1e-11, limit=400)[0]
            rel = abs(val - math.exp(float(p2.logpdf(z)))) / math.exp(float(p2.logpdf(z)))
            rows.append({"sigma": sigma, "n": n, "sequential_vs_batch_max_abs": seq_err, "chain_rule_rel_err": rel,
                         "pass": seq_err <= 1e-10 and rel <= 1e-8})
    return rows


def run_experiment(cfg: SeparabilityConfig, runs_dir: str = "runs", workers: int = 1, run_id: str | None = None,
                   command: list[str] | None = None) -> RunRecorder:
    recorder = RunRecorder(cfg, runs_dir=runs_dir, run_id=run_id, command=command)
    units = plan_units(cfg)
    total_comp = sum(n_competitors(cfg, u[1]) for u in units)
    z_t1 = float(stats.norm.isf(cfg.metrics.family_alpha / total_comp))
    cfg_dict = cfg.to_dict()
    t0 = time.time()
    if workers > 1:
        # 'spawn' everywhere: the Windows default where this was validated, and it avoids fork-after-BLAS-init
        # issues on Linux (e.g. Google Colab).
        with ProcessPoolExecutor(max_workers=workers, mp_context=multiprocessing.get_context("spawn")) as pool:
            results = list(pool.map(run_unit, [cfg_dict] * len(units), units, [z_t1] * len(units)))
    else:
        results = [run_unit(cfg_dict, u, z_t1) for u in units]
    elapsed = time.time() - t0

    predictor_rows = [r for res in results for r in res["predictor_rows"]]
    pair_rows = [r for res in results for r in res["pair_rows"]]
    g_rows = [r for res in results for r in res["g_rows"]]
    t1_rows = [r for res in results for r in res["t1_rows"]]
    unit_rows = [res["unit_info"] for res in results]

    # T2: calibration of the matched reference, Bonferroni over units x tests
    levels = cfg.metrics.coverage_levels
    n_t2 = len(units) * (1 + len(levels))
    lvl = cfg.metrics.family_alpha / n_t2
    t2_rows = []
    for r in predictor_rows:
        if r["predictor"] != "matched_reference":
            continue
        ps = [r["pit_ks_p"]] + [r[f"coverage_{lev}_p"] for lev in levels]
        t2_rows.append({k: r[k] for k in ("sigma", "condition", "K", "n", "h")} | {
            "min_p": min(ps), "per_test_level": lvl, "pass": min(ps) >= lvl})

    t3_rows = t3_identity_checks(cfg)

    recorder.write_csv("predictors.csv", predictor_rows)
    recorder.write_csv("paired_differences.csv", pair_rows)
    recorder.write_csv("g_metric.csv", g_rows)
    recorder.write_csv("t1_optimality.csv", t1_rows)
    recorder.write_csv("t2_calibration.csv", t2_rows)
    recorder.write_csv("t3_identities.csv", t3_rows)
    recorder.write_csv("units.csv", [{k: v for k, v in u.items() if k != "selection_mean_log_scores"}
                                     for u in unit_rows])
    recorder.write_json("frontier_selection.json", [{k: u[k] for k in ("sigma", "condition", "K", "n", "h",
                                                                         "frontier_all", "frontier_strict",
                                                                         "selection_mean_log_scores")}
                                                    for u in unit_rows])
    # item-level log scores: one float64 matrix + an index (np.save is byte-deterministic)
    index, mats = [], []
    for res in results:
        for name, arr in res["item_scores"].items():
            index.append({**res["base"], "predictor": name, "row": len(index)})
            mats.append(arr)
    np.save(recorder.dir / "results" / "item_log_scores.npy", np.vstack(mats), allow_pickle=False)
    recorder.write_csv("item_log_scores_index.csv", index)

    summary = summarize(cfg, predictor_rows, pair_rows, g_rows, t1_rows, t2_rows, t3_rows, unit_rows)
    recorder.write_json("summary.json", summary)
    recorder.write_text("report.md", render_report(cfg, summary))
    prereg = Path(__file__).resolve().parents[2] / "docs" / "PREREG_separability.md"
    recorder.finalize(NamedStreams(cfg.experiment.root_seed).describe(),
                      extra={"preregistration": ({"path": "docs/PREREG_separability.md", "sha256": sha256_file(prereg)}
                                                 if prereg.is_file() else None),"runtime": {"seconds": round(elapsed, 1), "workers": workers, "n_units": len(units),
                                         "unit_seconds": {"|".join(map(str, res["unit"])): res["seconds"]
                                                          for res in results}},
                             "t1_z_crit": z_t1})
    return recorder


# ------------------------------------------------------------------------------------ summarising


def _rows(rows, **match):
    return [r for r in rows if all(r[k] == v for k, v in match.items())]


def summarize(cfg, predictor_rows, pair_rows, g_rows, t1_rows, t2_rows, t3_rows, unit_rows) -> dict:
    out = {"theorem_checks": {
        "T1_violations": [r for r in t1_rows if r["violates"]],
        "T1_n_comparisons": len(t1_rows),
        "T1_min_z": min(r["z"] for r in t1_rows),
        "T2_failures": [r for r in t2_rows if not r["pass"]],
        "T2_n_cells": len(t2_rows),
        "T2_min_p": min(r["min_p"] for r in t2_rows),
        "T3": t3_rows,
        "T3_all_pass": all(r["pass"] for r in t3_rows),
        "quadrature_err_estimate_max": max(u["quadrature_err_estimate"] for u in unit_rows),
    }}
    # separability of the three strategies
    key_pairs = []
    for r in pair_rows:
        pair = (r["A"], r["B"])
        if r["condition"] == "E-CONT" and r["A"] == "matched_reference" and (
                r["B"].startswith("library_K") or r["B"] in ("frontier_all", "frontier_strict")):
            key_pairs.append(r)
        elif r["condition"] == "E-CONT" and r["A"].startswith("library_K") and r["B"] in ("frontier_all",):
            key_pairs.append(r)
        elif r["condition"] == "E-LIB" and pair in (("matched_reference", "continuous_prior_bayes"),
                                                    ("matched_reference", "frontier_all"),
                                                    ("matched_reference", "frontier_strict"),
                                                    ("frontier_all", "continuous_prior_bayes")):
            key_pairs.append(r)
    counts = {}
    for r in key_pairs:
        counts.setdefault(f"{r['condition']}:{r['A']} vs {r['B'] if not r['B'].startswith('library') else 'library'}",
                          {}).setdefault(r["classification"], 0)
        counts[f"{r['condition']}:{r['A']} vs {r['B'] if not r['B'].startswith('library') else 'library'}"][
            r["classification"]] += 1
    out["separability_counts"] = counts
    # regimes where all three strategies are mutually equivalent
    indist = []
    for u in unit_rows:
        base = {k: u[k] for k in ("sigma", "condition", "K", "n", "h")}
        rows = _rows(pair_rows, **base)
        if u["condition"] == "E-CONT":
            trio = [r for r in rows if (r["A"], r["B"]) in (("matched_reference", "frontier_all"),)
                    or (r["A"] == "matched_reference" and r["B"].startswith("library_K"))]
        else:
            trio = [r for r in rows if (r["A"], r["B"]) in (("matched_reference", "continuous_prior_bayes"),
                                                             ("matched_reference", "frontier_all"),
                                                             ("frontier_all", "continuous_prior_bayes"))]
        if trio and all(r["classification"] == "equivalent" for r in trio):
            indist.append(base)
    out["all_strategies_equivalent_cells"] = indist
    out["all_pairs_separable_regimes"] = separable_regimes(unit_rows, pair_rows, cfg)
    out["n_cells"] = len(unit_rows)
    out["g_ill_conditioned_fraction"] = float(np.mean([r["ill_conditioned"] for r in g_rows])) if g_rows else None
    out["hypotheses"] = hypotheses(cfg, predictor_rows, pair_rows)
    out["frontier_members"] = {f"{u['condition']} s={u['sigma']} K={u['K']} n={u['n']} h={u['h']}":
                               [u["frontier_all"], u["frontier_strict"]] for u in unit_rows}
    return out


def separable_regimes(unit_rows, pair_rows, cfg) -> list[dict]:
    """PREREG section 4: cells (and, under E-CONT, library sizes) in which all three strategy pairs
    (continuous vs library, continuous vs frontier_all, library vs frontier_all) are 'separable'."""
    out = []
    for u in unit_rows:
        base = {k: u[k] for k in ("sigma", "condition", "K", "n", "h")}
        cls = {}
        for r in _rows(pair_rows, **base):
            cls[(r["A"], r["B"])] = cls[(r["B"], r["A"])] = r["classification"]
        if u["condition"] == "E-CONT":
            for k in cfg.grid.library_sizes:
                lib = f"library_K{k}"
                trio = [cls[("matched_reference", lib)], cls[("matched_reference", "frontier_all")],
                        cls[(lib, "frontier_all")]]
                if all(c == "separable" for c in trio):
                    out.append({**base, "library": lib})
        else:
            trio = [cls[("matched_reference", "continuous_prior_bayes")], cls[("matched_reference", "frontier_all")],
                    cls[("frontier_all", "continuous_prior_bayes")]]
            if all(c == "separable" for c in trio):
                out.append({**base, "library": f"library_K{u['K']}"})
    return out


def hypotheses(cfg, predictor_rows, pair_rows) -> dict:
    H = {}
    # H1: E-CONT matched - flat_prior_bayes gap vs n
    h1 = []
    for s in cfg.grid.noise_scales:
        for h in cfg.grid.horizons:
            series = []
            for n in sorted(cfg.grid.context_lengths):
                r = _rows(pair_rows, condition="E-CONT", sigma=s, h=h, n=n, A="matched_reference", B="flat_prior_bayes")
                if r:
                    series.append((n, r[0]["mean_diff"], r[0]["se"]))
            if series:
                gaps = [g for _, g, _ in series]
                h1.append({"sigma": s, "h": h, "series": series,
                           "monotone_decreasing": all(a > b for a, b in zip(gaps, gaps[1:]))})
    H["H1_matched_minus_flat_vs_n"] = h1
    # H2: library coverage on E-CONT vs nominal
    h2 = []
    for r in predictor_rows:
        if r["condition"] == "E-CONT" and r["predictor"].startswith("library_K"):
            row = {k: r[k] for k in ("sigma", "n", "h", "predictor")}
            for lev in cfg.metrics.coverage_levels:
                cov = r[f"coverage_{lev}"]
                se = math.sqrt(lev * (1 - lev) / cfg.replication.n_eval_items)
                row[f"cov{lev}"] = cov
                row[f"cov{lev}_z"] = (cov - lev) / se
            h2.append(row)
    H["H2_library_coverage_E-CONT"] = h2
    # H3: E-CONT library - continuous (= matched) vs K
    h3 = []
    for s in cfg.grid.noise_scales:
        for n in cfg.grid.context_lengths:
            for h in cfg.grid.horizons:
                series = []
                for k in sorted(cfg.grid.library_sizes):
                    r = _rows(pair_rows, condition="E-CONT", sigma=s, n=n, h=h, A="matched_reference",
                              B=f"library_K{k}")
                    if r:
                        series.append((k, -r[0]["mean_diff"], r[0]["se"]))
                if series:
                    gaps = [abs(g) for _, g, _ in series]
                    h3.append({"sigma": s, "n": n, "h": h, "series_library_minus_continuous": series,
                               "abs_gap_monotone_decreasing_in_K": all(a > b for a, b in zip(gaps, gaps[1:]))})
    H["H3_library_minus_continuous_vs_K_E-CONT"] = h3
    # H4: E-LIB library (= matched) - continuous vs n
    h4 = []
    for s in cfg.grid.noise_scales:
        for k in cfg.grid.library_sizes:
            for h in cfg.grid.horizons:
                series = []
                for n in sorted(cfg.grid.context_lengths):
                    r = _rows(pair_rows, condition="E-LIB", sigma=s, K=k, n=n, h=h, A="matched_reference",
                              B="continuous_prior_bayes")
                    if r:
                        series.append((n, r[0]["mean_diff"], r[0]["se"]))
                if series:
                    h4.append({"sigma": s, "K": k, "h": h, "series_library_minus_continuous": series})
    H["H4_library_minus_continuous_vs_n_E-LIB"] = h4
    return H


def _fmt(x, nd=4):
    return "nan" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{x:.{nd}f}"


def render_report(cfg, s: dict) -> str:
    tc = s["theorem_checks"]
    L = [f"# Separability map: {cfg.experiment.name}", "",
         f"config hash: see ../config_hash.txt. Cells: {s['n_cells']}. Items per cell: "
         f"{cfg.replication.n_eval_items} eval, {cfg.replication.n_selection_items} selection.", "",
         "## Theorem-level checks (violations indicate a bug, up to MC error)", "",
         f"- T1 optimality: {len(tc['T1_violations'])} violations / {tc['T1_n_comparisons']} paired comparisons "
         f"(min z = {_fmt(tc['T1_min_z'], 2)}).",
         f"- T2 calibration of the matched reference: {len(tc['T2_failures'])} failing cells / {tc['T2_n_cells']} "
         f"(min p = {tc['T2_min_p']:.2e}).",
         f"- T3 identities on the experiment priors: {'all pass' if tc['T3_all_pass'] else 'FAILURES'}.",
         f"- Max quadrature node-doubling error (logpdf/cdf at targets): {tc['quadrature_err_estimate_max']:.2e}.", "",
         "## Separability classification counts (pre-registered rule)", ""]
    for k, v in sorted(s["separability_counts"].items()):
        L.append(f"- {k}: " + ", ".join(f"{c}={n}" for c, n in sorted(v.items())))
    L += ["", f"Regimes where all three strategy pairs are separable (PREREG section 4): "
              f"{len(s['all_pairs_separable_regimes'])}"]
    L += [f"- {r['condition']} sigma={r['sigma']} n={r['n']} h={r['h']} {r['library']}"
          for r in s["all_pairs_separable_regimes"]]
    L += ["", f"Cells where all three strategies are mutually equivalent: {len(s['all_strategies_equivalent_cells'])}",
          "", f"G ill-conditioned fraction: {_fmt(s['g_ill_conditioned_fraction'], 3)}", "",
          "## Diagnostic hypotheses (measurements, not pass/fail)", "", "### H1: matched - flat-prior Bayes vs n (E-CONT)",
          "", "| sigma | h | n: gap +- SE | monotone decreasing |", "|---|---|---|---|"]
    for r in s["hypotheses"]["H1_matched_minus_flat_vs_n"]:
        L.append(f"| {r['sigma']} | {r['h']} | " + "; ".join(f"{n}: {_fmt(g)} +- {_fmt(se)}" for n, g, se in r["series"])
                 + f" | {r['monotone_decreasing']} |")
    L += ["", "### H2: library coverage on E-CONT (z = (coverage - nominal)/binomial SE)", "",
          "| sigma | n | h | predictor | " + " | ".join(f"cov{lev} (z)" for lev in cfg.metrics.coverage_levels) + " |",
          "|---|---|---|---|" + "---|" * len(cfg.metrics.coverage_levels)]
    for r in s["hypotheses"]["H2_library_coverage_E-CONT"]:
        L.append(f"| {r['sigma']} | {r['n']} | {r['h']} | {r['predictor']} | " + " | ".join(
            f"{r[f'cov{lev}']:.3f} ({r[f'cov{lev}_z']:+.1f})" for lev in cfg.metrics.coverage_levels) + " |")
    L += ["", "### H3: library - continuous vs K (E-CONT)", "", "| sigma | n | h | K: gap +- SE | abs gap decreasing |",
          "|---|---|---|---|---|"]
    for r in s["hypotheses"]["H3_library_minus_continuous_vs_K_E-CONT"]:
        L.append(f"| {r['sigma']} | {r['n']} | {r['h']} | " + "; ".join(
            f"{k}: {_fmt(g)} +- {_fmt(se)}" for k, g, se in r["series_library_minus_continuous"])
                 + f" | {r['abs_gap_monotone_decreasing_in_K']} |")
    L += ["", "### H4: library - continuous vs n (E-LIB)", "", "| sigma | K | h | n: gap +- SE |", "|---|---|---|---|"]
    for r in s["hypotheses"]["H4_library_minus_continuous_vs_n_E-LIB"]:
        L.append(f"| {r['sigma']} | {r['K']} | {r['h']} | " + "; ".join(
            f"{n}: {_fmt(g)} +- {_fmt(se)}" for n, g, se in r["series_library_minus_continuous"]) + " |")
    return "\n".join(L) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--config", required=True)
    ap.add_argument("--workers", type=int, default=1)
    ap.add_argument("--runs-dir", default="runs")
    args = ap.parse_args(argv)
    cfg = load_config(args.config)
    rec = run_experiment(cfg, runs_dir=args.runs_dir, workers=args.workers,
                         command=[sys.executable, "-m", "dynaicl.experiments.separability", *(argv or sys.argv[1:])])
    print(rec.dir)
    print((rec.dir / "results" / "report.md").read_text(encoding="utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
