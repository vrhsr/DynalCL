"""Stage 0.5: does population-aware Bayes beat the strongest context-only estimator by a meaningful amount?

Pre-registered in docs/PREREG_stage05.md. Usage:

    python -m dynaicl.experiments.population_advantage --config config/stage05.yaml --workers 7

Design summary:
* sigma is fixed (log-score differences are invariant to a common rescaling of x and sigma, docs/MATH.md
  section 11). The initial-state-to-noise ratio r = sd(x_0)/sigma is varied.
* Independent root seeds per role: library, selection, each evaluation replicate, bootstrap. The
  frontier is selected once on the selection split and then frozen for every replicate.
* PRIMARY contrast: matched reference - frontier_ctx (best of the 8 context-only members, including
  generic-stability Bayes). SECONDARY: finite library - continuous-prior Bayes.
* A cell's class is "confirmed" only if every evaluation replicate gives the same class.
"""

from __future__ import annotations

import argparse
import math
import multiprocessing
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
from scipy import stats

from dynaicl.baselines.common import FallbackSettings
from dynaicl.baselines.family import build_context_only_family, select_frontier_member
from dynaicl.baselines.kernel import KernelSettings
from dynaicl.config.schema import PopulationAdvantageConfig, load_population_config, population_config_from_dict
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

STAGE0_MEMBERS = ("flat_prior_bayes", "ols_gaussian", "ols_student_t", "kernel_rolling_origin", "kernel_blocked",
                  "kernel_leave_one_out", "persistence")
STABILITY = "stability_prior_bayes"
PRIMARY = "matched_minus_frontier_ctx"
SECONDARY = "library_minus_continuous"
QUADRATURE_PREDICTORS = ("matched_reference", "continuous_prior_bayes", "flat_prior_bayes", STABILITY)


# ------------------------------------------------------------------------------------- classification


def classify_advantage(mean: float, se: float, delta: float, z: float) -> str:
    """MEANINGFUL if mean - z SE > delta; NEGLIGIBLE if mean + z SE < delta; else INCONCLUSIVE."""
    if mean - z * se > delta:
        return "MEANINGFUL"
    if mean + z * se < delta:
        return "NEGLIGIBLE"
    return "INCONCLUSIVE"


def classify_distinction(mean: float, se: float, delta: float, z: float) -> str:
    """DISTINGUISHABLE if the interval excludes [-delta, delta]; EQUIVALENT if it lies inside (-delta, delta)."""
    lo, hi = mean - z * se, mean + z * se
    if lo > delta or hi < -delta:
        return "DISTINGUISHABLE"
    if lo > -delta and hi < delta:
        return "EQUIVALENT"
    return "INCONCLUSIVE"


def confirm(classes: list[str]) -> str:
    """Confirmed class: identical in every replicate, else DISCORDANT."""
    return classes[0] if classes and len(set(classes)) == 1 else "DISCORDANT"


def bootstrap_interval(d: np.ndarray, z: float, resamples: int, rng: np.random.Generator,
                       chunk: int = 100) -> tuple[float, float]:
    """Percentile bootstrap interval of the mean at the same two-sided level as mean +/- z SE."""
    n = d.size
    means = np.empty(resamples)
    for start in range(0, resamples, chunk):
        stop = min(start + chunk, resamples)
        idx = rng.integers(0, n, size=(stop - start, n))
        means[start:stop] = d[idx].mean(axis=1)
    tail = float(stats.norm.sf(z))
    return float(np.quantile(means, tail)), float(np.quantile(means, 1.0 - tail))


# ---------------------------------------------------------------------------------------- one unit


def build_prior(cfg: PopulationAdvantageConfig) -> StableCoefficientPrior:
    p = cfg.prior
    return StableCoefficientPrior(rho=p.rho, sigma=cfg.noise_scale, shape=p.shape, mu0=p.mu0, tau0=p.tau0)


def build_settings(cfg: PopulationAdvantageConfig):
    q, k, f = cfg.numerics.quadrature, cfg.baselines.kernel, cfg.baselines.fallback
    return (QuadratureSettings(q.panels, q.nodes_per_panel, q.log_drop, q.panels_per_cell, q.max_panels),
            KernelSettings(tuple(k.bandwidth_multipliers), k.min_train_pairs, k.n_blocks, k.gap, k.min_pairs,
                           k.min_validation_points),
            FallbackSettings(f.coefficient_mean, f.coefficient_variance, f.predictive_variance,
                             f.variance_relative_floor))


def plan_units(cfg: PopulationAdvantageConfig) -> list[tuple]:
    out = []
    for ri in range(len(cfg.initial_state.sds)):
        for cond in cfg.grid.conditions:
            for k in (cfg.grid.library_sizes if cond == "E-LIB" else (0,)):
                for n in cfg.grid.context_lengths:
                    for h in cfg.grid.horizons:
                        out.append((ri, cond, int(k), int(n), int(h)))
    return out


def n_competitors(cfg: PopulationAdvantageConfig, cond: str) -> int:
    return len(STAGE0_MEMBERS) + 1 + (len(cfg.grid.library_sizes) if cond == "E-CONT" else 1)


def _contrast_row(base, rep, name, a, b, d: np.ndarray, kind: str, cfg, extra=None) -> dict:
    mean, se = float(d.mean()), float(d.std(ddof=1) / math.sqrt(d.size))
    delta, zd, zc = cfg.metrics.practical_effect_nats, cfg.metrics.decision_z, cfg.metrics.ci_z
    cls = classify_advantage(mean, se, delta, zd) if kind == "advantage" else classify_distinction(mean, se, delta, zd)
    row = {**base, "replicate": rep, "contrast": name, "A": a, "B": b, "mean": mean, "se": se,
           "sd": float(d.std(ddof=1)), "n_items": int(d.size), "ci95_lo": mean - zc * se, "ci95_hi": mean + zc * se,
           "decision_lo": mean - zd * se, "decision_hi": mean + zd * se, "kind": kind, "class": cls}
    for eff in cfg.metrics.sensitivity_effects:
        row[f"class_at_{eff:g}"] = (classify_advantage(mean, se, eff, zd) if kind == "advantage"
                                    else classify_distinction(mean, se, eff, zd))
    row.update(extra or {})
    return row


def run_unit(cfg_dict: dict, unit: tuple, z_t1: float) -> dict:
    cfg = population_config_from_dict(cfg_dict)
    ri, cond_name, k_lib, n, h = unit
    r = cfg.initial_state.sds[ri]
    sigma = cfg.noise_scale
    prior = build_prior(cfg)
    qset, kset, fset = build_settings(cfg)
    x0 = InitialStateSpec(cfg.initial_state.mean, r)
    lib_streams = NamedStreams(cfg.seeds.library)
    sel_streams = NamedStreams(cfg.seeds.selection)
    eval_streams = [NamedStreams(s) for s in cfg.seeds.evaluation]
    length = max(cfg.grid.context_lengths) + max(cfg.grid.horizons)
    libraries = {k: build_library_from_prior(prior, k, lib_streams) for k in cfg.grid.library_sizes}
    t0 = time.time()

    condition = (ContinuousPriorCondition(prior, x0) if cond_name == "E-CONT"
                 else LibraryCondition(libraries[k_lib], x0))
    sel = generate_split(condition, SplitRole.SELECTION, sel_streams, cfg.replication.n_selection_items, length)
    evs = [generate_split(condition, SplitRole.EVALUATION, es, cfg.replication.n_eval_items, length)
           for es in eval_streams]

    # ---- leakage controls: selection, every replicate and the library training data share no data
    train = generate_library_training_split(libraries[max(cfg.grid.library_sizes)], lib_streams, length, x0)
    splits = [sel, *evs, train]
    for i in range(len(splits)):
        for j in range(i + 1, len(splits)):
            assert_no_unintended_overlap(splits[i], splits[j])
    for s in (sel, *evs):
        if cond_name == "E-CONT":
            for lib in libraries.values():
                assert_parameters_disjoint(s, lib)
        else:
            assert_parameters_within_library(s, libraries[k_lib])

    ref = matched_refs.matched_reference_for(condition, qset)
    family = build_context_only_family(sigma, qset, kset, fset, cfg.baselines.ols_min_transitions,
                                       stability_bound=cfg.baselines.stability_bound)
    predictors = {"matched_reference": ref.predictor}
    if cond_name == "E-CONT":
        for k in cfg.grid.library_sizes:
            predictors[f"library_K{k}"] = FiniteLibraryPredictor(libraries[k])
    else:
        predictors["continuous_prior_bayes"] = matched_refs.continuous_prior_predictor(prior, qset)
    predictors.update(family)

    # ---- frontier: selected ONCE on the selection split, frozen for all replicates
    ss = harness.build_evaluation_set(condition, sel, n, h)
    sel_scores = {name: harness.score_predictor(p, ss).log_score for name, p in family.items()}
    frontier_ctx = select_frontier_member(sel_scores, family, True, strict=False)
    frontier_stage0 = select_frontier_member({k: sel_scores[k] for k in STAGE0_MEMBERS}, family, True, strict=False)
    frontier_strict = select_frontier_member(sel_scores, family, True, strict=True)

    base = {"r": r, "condition": cond_name, "K": k_lib, "n": n, "h": h}
    out = {"unit": list(unit), "predictor_rows": [], "contrast_rows": [], "t1_rows": [], "t2_rows": [],
           "frontier": {**base, "frontier_ctx": frontier_ctx, "frontier_stage0": frontier_stage0,
                        "frontier_strict": frontier_strict,
                        "selection_mean_log_scores": {k: float(v.mean()) for k, v in sel_scores.items()}},
           "quadrature": [], "items": {}, "bootstrap": []}
    boot_streams = NamedStreams(cfg.seeds.bootstrap)
    cont_name = "matched_reference" if cond_name == "E-CONT" else "continuous_prior_bayes"

    for rep_idx, ev in enumerate(evs):
        rep = f"R{rep_idx + 1}"
        es = harness.build_evaluation_set(condition, ev, n, h)
        tabs = {}
        for name, p in predictors.items():
            keys = ("multiplier",) if name.startswith("kernel_") else (("quadrature_capped",) if name in QUADRATURE_PREDICTORS else ())
            tabs[name] = harness.score_predictor(p, es, info_keys=keys)
        S = {k: v.log_score for k, v in tabs.items()}

        # predictor rows: baseline performance and calibration (a measurement for all but the matched reference)
        for name, t in tabs.items():
            row = {**base, "replicate": rep, "predictor": name, "mean_log_score": float(t.log_score.mean()),
                   "se_log_score": float(t.log_score.std(ddof=1) / math.sqrt(t.log_score.size)),
                   "fallback_rate": float(t.fallback.mean()), "pit_ks_p": calibration.ks_uniform_pvalue(t.pit)}
            for lev in cfg.metrics.coverage_levels:
                kcov = int(scoring.covered_from_pit(t.pit, lev).sum())
                row[f"coverage_{lev}"] = kcov / t.pit.size
                row[f"coverage_{lev}_p"] = calibration.coverage_pvalue(kcov, t.pit.size, lev)
            if "quadrature_capped" in t.info:
                row["quadrature_capped_rate"] = float(np.nansum(t.info["quadrature_capped"]) / t.pit.size)
            if "multiplier" in t.info and np.isfinite(t.info["multiplier"]).any():
                row["mean_selected_multiplier"] = float(np.nanmean(t.info["multiplier"]))
            out["predictor_rows"].append(row)

        m = S["matched_reference"]
        best_member = max(family, key=lambda k: float(S[k].mean()))           # on the evaluation set (optimistic)
        rows = [
            _contrast_row(base, rep, PRIMARY, "matched_reference", frontier_ctx, m - S[frontier_ctx], "advantage", cfg),
            _contrast_row(base, rep, "matched_minus_frontier_stage0", "matched_reference", frontier_stage0,
                          m - S[frontier_stage0], "advantage", cfg),
            _contrast_row(base, rep, "matched_minus_frontier_strict", "matched_reference", frontier_strict,
                          m - S[frontier_strict], "advantage", cfg),
            _contrast_row(base, rep, "matched_minus_flat", "matched_reference", "flat_prior_bayes",
                          m - S["flat_prior_bayes"], "advantage", cfg),
            _contrast_row(base, rep, "matched_minus_stability", "matched_reference", STABILITY, m - S[STABILITY],
                          "advantage", cfg),
            _contrast_row(base, rep, "stability_minus_flat", STABILITY, "flat_prior_bayes",
                          S[STABILITY] - S["flat_prior_bayes"], "advantage", cfg),
            _contrast_row(base, rep, "matched_minus_best_member_on_eval", "matched_reference", best_member,
                          m - S[best_member], "advantage", cfg),
        ]
        if cond_name == "E-CONT":
            for k in cfg.grid.library_sizes:
                rows.append(_contrast_row(base, rep, SECONDARY, f"library_K{k}", "matched_reference",
                                          S[f"library_K{k}"] - m, "distinction", cfg, {"library_K": k}))
        else:
            rows.append(_contrast_row(base, rep, SECONDARY, "matched_reference", "continuous_prior_bayes",
                                      m - S["continuous_prior_bayes"], "distinction", cfg, {"library_K": k_lib}))
        out["contrast_rows"] += rows

        # bootstrap robustness check of the primary contrast
        if cfg.metrics.bootstrap_resamples > 0:
            d = m - S[frontier_ctx]
            code = 0 if cond_name == "E-CONT" else 1
            g = boot_streams.stream("bootstrap", ri, code, k_lib, n, h, rep_idx)
            lo, hi = bootstrap_interval(d, cfg.metrics.decision_z, cfg.metrics.bootstrap_resamples, g)
            delta = cfg.metrics.practical_effect_nats
            boot_cls = "MEANINGFUL" if lo > delta else ("NEGLIGIBLE" if hi < delta else "INCONCLUSIVE")
            out["bootstrap"].append({**base, "replicate": rep, "boot_lo": lo, "boot_hi": hi, "boot_class": boot_cls,
                                     "analytic_class": rows[0]["class"]})

        # T1 (guarded optimality) and T2 (matched calibration)
        comps = {k: v for k, v in tabs.items() if k != "matched_reference"}
        for t1 in harness.optimality_diagnostics(ref, es, tabs["matched_reference"], comps, z_t1):
            out["t1_rows"].append({**base, "replicate": rep, "competitor": t1.competitor,
                                   "mean_ref_minus_comp": t1.difference.mean, "se": t1.difference.se,
                                   "z": t1.difference.z, "violates": t1.violates})
        mrow = next(x for x in out["predictor_rows"] if x["replicate"] == rep and x["predictor"] == "matched_reference")
        ps = [mrow["pit_ks_p"]] + [mrow[f"coverage_{lev}_p"] for lev in cfg.metrics.coverage_levels]
        out["t2_rows"].append({**base, "replicate": rep, "min_p": min(ps),
                               "matched_capped_rate": mrow.get("quadrature_capped_rate", 0.0)})

        # quadrature node-doubling error of the continuous-prior predictor at actual targets
        cont = predictors[cont_name]
        fine = cont.with_settings(qset.refined(2))
        targets = harness.ground_truth_for_validation(es)[2]
        q_err = 0.0
        for i in range(min(cfg.numerics.quadrature_error_check_items, es.size)):
            p1, p2 = cont.predict(es.contexts[i], h), fine.predict(es.contexts[i], h)
            q_err = max(q_err, abs(float(p1.logpdf(targets[i])) - float(p2.logpdf(targets[i]))),
                        abs(float(p1.cdf(targets[i])) - float(p2.cdf(targets[i]))))
        out["quadrature"].append({**base, "replicate": rep, "quadrature_err_estimate": q_err})

        out["items"][f"{rep}|{PRIMARY}"] = m - S[frontier_ctx]
        if cond_name == "E-CONT":
            for k in cfg.grid.library_sizes:
                out["items"][f"{rep}|{SECONDARY}|K{k}"] = S[f"library_K{k}"] - m
        else:
            out["items"][f"{rep}|{SECONDARY}|K{k_lib}"] = m - S["continuous_prior_bayes"]
    out["seconds"] = round(time.time() - t0, 2)
    return out


# ------------------------------------------------------------------------------------------ decision


def confirmed_classes(contrast_rows: list[dict], contrast: str) -> dict:
    """{(condition, K, library_K, r, n, h): confirmed class} over replicates."""
    groups = {}
    for row in contrast_rows:
        if row["contrast"] != contrast:
            continue
        key = (row["condition"], row["K"], row.get("library_K", row["K"]), row["r"], row["n"], row["h"])
        groups.setdefault(key, {})[row["replicate"]] = row["class"]
    return {k: confirm([v[rep] for rep in sorted(v)]) for k, v in groups.items()}


def _has_run(flags: list[bool], length: int) -> bool:
    run = 0
    for f in flags:
        run = run + 1 if f else 0
        if run >= length:
            return True
    return False


def decide(cfg: PopulationAdvantageConfig, contrast_rows: list[dict], reliability: dict) -> dict:
    """Pre-registered decision (docs/PREREG_stage05.md section 6)."""
    D = cfg.decision
    n_reps = len({r["replicate"] for r in contrast_rows})
    p1 = (reliability["T1_violations"] == 0 and reliability["T2_failures"] == 0
          and reliability["max_quadrature_error"] <= D.max_quadrature_error and reliability["max_matched_capped_rate"] == 0)
    prim = confirmed_classes(contrast_rows, PRIMARY)
    stage0 = confirmed_classes(contrast_rows, "matched_minus_frontier_stage0")

    def cls(table, r, n, h):
        return table.get((D.relevant_condition, 0, 0, r, n, h))

    rel_n = list(D.relevant_context_lengths)
    p2_by_h = {h: _has_run([cls(prim, D.relevant_initial_state_sd, n, h) == "MEANINGFUL" for n in rel_n],
                           D.min_consecutive_context_lengths) for h in D.required_horizons}
    p2 = all(p2_by_h.values())
    h_rob = D.required_horizons[0]
    p3_by_r = {r: any(cls(prim, r, n, h_rob) == "MEANINGFUL" for n in rel_n) for r in D.robustness_initial_state_sds}
    p3 = all(p3_by_r.values())
    n_max = max(rel_n)
    any_primary = any(v == "MEANINGFUL" for (c, _, _, r, n, h), v in prim.items()
                      if c == D.relevant_condition and n <= n_max)
    any_stage0 = any(v == "MEANINGFUL" for (c, _, _, r, n, h), v in stage0.items()
                     if c == D.relevant_condition and n <= n_max)
    if n_reps < 2:
        verdict, reason = "NOT DECIDABLE", "fewer than two evaluation replicates (pilot or misconfiguration)"
    elif not p1:
        verdict, reason = "STOP", "reference reliability (P1) failed: results are not interpreted; debug first"
    elif p2 and p3:
        verdict, reason = "PROCEED", "P1, P2 and P3 all hold"
    elif any_primary:
        verdict = "REVISE"
        reason = ("confirmed meaningful advantage exists but " + ("is not stable across context lengths/horizons (P2 failed)"
                  if not p2 else "depends on the initial-state scale (P3 failed)"))
    elif any_stage0:
        verdict, reason = "REVISE", ("advantage is meaningful only against the Stage 0 frontier (no generic-stability "
                                     "member): the measured benefit is generic stability knowledge, not population "
                                     "knowledge; the operational definition must change")
    else:
        verdict, reason = "STOP", "no confirmed meaningful advantage in any relevant-condition cell with n <= " + str(n_max)
    return {"verdict": verdict, "reason": reason, "replicates": n_reps, "P1_reference_reliability": p1,
            "P2_stable_across_n_by_h": {str(k): v for k, v in p2_by_h.items()}, "P2": p2,
            "P3_robust_across_r": {str(k): v for k, v in p3_by_r.items()}, "P3": p3,
            "any_confirmed_meaningful_primary": any_primary, "any_confirmed_meaningful_vs_stage0_frontier": any_stage0}


# ------------------------------------------------------------------------------------------ whole run


def _unit_file(ckpt: Path, unit: tuple) -> Path:
    return ckpt / ("unit_" + "_".join(map(str, unit)) + ".pkl")


def run_units(cfg: PopulationAdvantageConfig, workers: int, z_t1: float, checkpoint_dir: str | None = None) -> list:
    """Run every unit, printing progress. With ``checkpoint_dir``, each finished unit is pickled to
    ``<checkpoint_dir>/<config_hash>/``, and units already there are loaded, not recomputed. Units are pure
    functions of (config, unit), so a resumed run gives the same results as an uninterrupted one."""
    import pickle
    units = plan_units(cfg)
    cfg_dict = cfg.to_dict()
    ckpt = Path(checkpoint_dir) / cfg.config_hash()[:16] if checkpoint_dir else None
    done = {}
    if ckpt is not None:
        ckpt.mkdir(parents=True, exist_ok=True)
        for u in units:
            f = _unit_file(ckpt, u)
            if f.is_file():
                with open(f, "rb") as fh:
                    done[u] = pickle.load(fh)
        print(f"checkpoint {ckpt}: {len(done)}/{len(units)} units already done", flush=True)
    todo = [u for u in units if u not in done]
    t0 = time.time()

    def record(u, res):
        done[u] = res
        if ckpt is not None:
            tmp = _unit_file(ckpt, u).with_suffix(".tmp")
            with open(tmp, "wb") as fh:
                pickle.dump(res, fh)
            tmp.replace(_unit_file(ckpt, u))
        mins = (time.time() - t0) / 60
        print(f"[{len(done):3d}/{len(units)} units, {mins:6.1f} min] {u} ({res['seconds']:.0f}s)", flush=True)

    if workers > 1 and todo:
        from concurrent.futures import as_completed
        with ProcessPoolExecutor(max_workers=workers, mp_context=multiprocessing.get_context("spawn")) as pool:
            futures = {pool.submit(run_unit, cfg_dict, u, z_t1): u for u in todo}
            for fut in as_completed(futures):
                record(futures[fut], fut.result())
    else:
        for u in todo:
            record(u, run_unit(cfg_dict, u, z_t1))
    return [done[u] for u in units]          # fixed unit order: output independent of completion order


def run_experiment(cfg: PopulationAdvantageConfig, runs_dir: str = "runs", workers: int = 1,
                   run_id: str | None = None, command: list[str] | None = None,
                   checkpoint_dir: str | None = None) -> RunRecorder:
    recorder = RunRecorder(cfg, runs_dir=runs_dir, run_id=run_id, command=command)
    units = plan_units(cfg)
    n_reps = len(cfg.seeds.evaluation)
    total_comp = sum(n_competitors(cfg, u[1]) for u in units) * n_reps
    z_t1 = float(stats.norm.isf(cfg.metrics.family_alpha / total_comp))
    t0 = time.time()
    results = run_units(cfg, workers, z_t1, checkpoint_dir)
    elapsed = time.time() - t0

    cat = lambda key: [row for res in results for row in res[key]]  # noqa: E731
    predictor_rows, contrast_rows, t1_rows, t2_rows = cat("predictor_rows"), cat("contrast_rows"), cat("t1_rows"), cat("t2_rows")
    quad_rows, boot_rows = cat("quadrature"), cat("bootstrap")
    n_t2 = len(t2_rows) * (1 + len(cfg.metrics.coverage_levels))
    t2_level = cfg.metrics.family_alpha / n_t2
    for row in t2_rows:
        row["per_test_level"] = t2_level
        row["pass"] = row["min_p"] >= t2_level
    reliability = {"T1_violations": sum(r["violates"] for r in t1_rows), "T1_comparisons": len(t1_rows),
                   "T1_z_crit": z_t1, "T1_min_z": min(r["z"] for r in t1_rows),
                   "T2_failures": sum(not r["pass"] for r in t2_rows), "T2_cells": len(t2_rows),
                   "T2_min_p": min(r["min_p"] for r in t2_rows), "T2_per_test_level": t2_level,
                   "max_quadrature_error": max(r["quadrature_err_estimate"] for r in quad_rows),
                   "max_matched_capped_rate": max(r["matched_capped_rate"] for r in t2_rows)}
    decision = decide(cfg, contrast_rows, reliability)
    boot_agree = sum(b["boot_class"] == b["analytic_class"] for b in boot_rows)

    recorder.write_csv("contrasts.csv", contrast_rows)
    recorder.write_csv("predictors.csv", predictor_rows)
    recorder.write_csv("t1_optimality.csv", t1_rows)
    recorder.write_csv("t2_calibration.csv", t2_rows)
    recorder.write_csv("quadrature.csv", quad_rows)
    recorder.write_csv("bootstrap.csv", boot_rows)
    recorder.write_json("frontier_selection.json", [res["frontier"] for res in results])
    index, mats = [], []
    for res in results:
        for key, arr in res["items"].items():
            ri, cond, k, n, h = res["unit"]
            index.append({"r": cfg.initial_state.sds[ri], "condition": cond, "K": k, "n": n, "h": h, "key": key,
                          "row": len(index)})
            mats.append(arr)
    np.save(recorder.dir / "results" / "item_contrasts.npy", np.vstack(mats), allow_pickle=False)
    recorder.write_csv("item_contrasts_index.csv", index)
    summary = {"decision": decision, "reliability": reliability,
               "bootstrap_agreement": {"agree": boot_agree, "total": len(boot_rows)},
               "confirmed_primary": {"|".join(map(str, k)): v for k, v in confirmed_classes(contrast_rows, PRIMARY).items()},
               "confirmed_secondary": {"|".join(map(str, k)): v
                                       for k, v in confirmed_classes(contrast_rows, SECONDARY).items()}}
    recorder.write_json("summary.json", summary)
    recorder.write_text("report.md", render_report(cfg, summary, contrast_rows, predictor_rows, boot_rows,
                                                   [res["frontier"] for res in results]))
    prereg = Path(__file__).resolve().parents[2] / "docs" / "PREREG_stage05.md"
    seeds = {role: NamedStreams(s).describe() for role, s in
             (("library", cfg.seeds.library), ("selection", cfg.seeds.selection), ("bootstrap", cfg.seeds.bootstrap))}
    seeds.update({f"evaluation_R{i + 1}": NamedStreams(s).describe() for i, s in enumerate(cfg.seeds.evaluation)})
    recorder.finalize(seeds, extra={
        "preregistration": ({"path": "docs/PREREG_stage05.md", "sha256": sha256_file(prereg)} if prereg.is_file() else None),
        "runtime": {"seconds": round(elapsed, 1), "workers": workers, "n_units": len(units),
                    "unit_seconds": {"|".join(map(str, res["unit"])): res["seconds"] for res in results}}})
    return recorder


# --------------------------------------------------------------------------------------------- report


def _fmt_ci(row, lo="decision_lo", hi="decision_hi"):
    return f"{row['mean']:+.4f} [{row[lo]:+.4f}, {row[hi]:+.4f}]"


def render_report(cfg, summary, contrast_rows, predictor_rows, boot_rows, frontiers) -> str:
    dec, rel = summary["decision"], summary["reliability"]
    delta, zd = cfg.metrics.practical_effect_nats, cfg.metrics.decision_z
    reps = sorted({r["replicate"] for r in contrast_rows})
    L = [f"# Stage 0.5: {cfg.experiment.name}", "",
         f"## Decision: **{dec['verdict']}**", "", f"Reason: {dec['reason']}.", "",
         f"P1 reference reliability = {dec['P1_reference_reliability']}; P2 (stable across n) = {dec['P2']} "
         f"{dec['P2_stable_across_n_by_h']}; P3 (robust across r) = {dec['P3']} {dec['P3_robust_across_r']}.", "",
         "## Reference reliability (P1)", "",
         f"- T1 optimality: {rel['T1_violations']} violations / {rel['T1_comparisons']} (z_crit {rel['T1_z_crit']:.2f}, "
         f"min z {rel['T1_min_z']:.2f})",
         f"- T2 calibration of the matched reference: {rel['T2_failures']} failing / {rel['T2_cells']} cell-replicates "
         f"(min p {rel['T2_min_p']:.2e}, per-test level {rel['T2_per_test_level']:.1e})",
         f"- max quadrature node-doubling error at targets: {rel['max_quadrature_error']:.2e} "
         f"(threshold {cfg.decision.max_quadrature_error:g}); max matched quadrature-cap rate: {rel['max_matched_capped_rate']}",
         f"- bootstrap vs analytic primary class agreement: {summary['bootstrap_agreement']['agree']}/"
         f"{summary['bootstrap_agreement']['total']}", "",
         f"## Primary: matched reference - frontier_ctx (nats/forecast; mean [decision interval, z = {zd}]; delta = {delta})", ""]
    for cond in cfg.grid.conditions:
        ks = cfg.grid.library_sizes if cond == "E-LIB" else (0,)
        L += [f"### {cond}", "", "| r | K | n | h | frontier | " + " | ".join(f"{rep}: mean [interval] class" for rep in reps)
              + " | confirmed | vs Stage-0 frontier (R1) | vs strict (R1) | vs stability (R1) |",
              "|---|---|---|---|---|" + "---|" * len(reps) + "---|---|---|---|"]
        for r in cfg.initial_state.sds:
            for k in ks:
                for n in cfg.grid.context_lengths:
                    for h in cfg.grid.horizons:
                        sel = [x for x in contrast_rows if x["condition"] == cond and x["r"] == r and x["K"] == k
                               and x["n"] == n and x["h"] == h]
                        if not sel:
                            continue
                        prim = {x["replicate"]: x for x in sel if x["contrast"] == PRIMARY}
                        get = lambda c: next(x for x in sel if x["contrast"] == c and x["replicate"] == reps[0])  # noqa: E731
                        conf = confirm([prim[rep]["class"] for rep in reps])
                        L.append(f"| {r:g} | {k} | {n} | {h} | {prim[reps[0]]['B']} | "
                                 + " | ".join(f"{_fmt_ci(prim[rep])} {prim[rep]['class']}" for rep in reps)
                                 + f" | **{conf}** | {get('matched_minus_frontier_stage0')['mean']:+.4f} | "
                                 f"{get('matched_minus_frontier_strict')['mean']:+.4f} | "
                                 f"{get('matched_minus_stability')['mean']:+.4f} |")
        L.append("")
    L += ["## Secondary: finite library - continuous-prior Bayes", "",
          "E-CONT: library (mismatched) - continuous (matched). E-LIB: library (matched) - continuous (mismatched).", "",
          "| condition | r | K | n | h | " + " | ".join(f"{rep}: mean [interval] class" for rep in reps) + " | confirmed |",
          "|---|---|---|---|---|" + "---|" * len(reps) + "---|"]
    sec = {}
    for x in contrast_rows:
        if x["contrast"] == SECONDARY:
            sec.setdefault((x["condition"], x["r"], x["library_K"], x["n"], x["h"]), {})[x["replicate"]] = x
    for key in sorted(sec):
        rows = sec[key]
        L.append(f"| {key[0]} | {key[1]:g} | {key[2]} | {key[3]} | {key[4]} | "
                 + " | ".join(f"{_fmt_ci(rows[rep])} {rows[rep]['class']}" for rep in reps)
                 + f" | **{confirm([rows[rep]['class'] for rep in reps])}** |")
    counts = {}
    for key, rows in sec.items():
        c = confirm([rows[rep]["class"] for rep in reps])
        counts.setdefault(key[0], {}).setdefault(c, 0)
        counts[key[0]][c] += 1
    L += ["", "Secondary confirmed-class counts: " + "; ".join(f"{k}: {v}" for k, v in sorted(counts.items())), ""]
    # sensitivity
    L += ["## Sensitivity of the primary classification to the effect threshold (confirmed MEANINGFUL cells, E-CONT)", ""]
    for eff in cfg.metrics.sensitivity_effects:
        groups = {}
        for x in contrast_rows:
            if x["contrast"] == PRIMARY and x["condition"] == "E-CONT":
                groups.setdefault((x["r"], x["n"], x["h"]), []).append(x[f"class_at_{eff:g}"])
        n_mean = sum(confirm(v) == "MEANINGFUL" for v in groups.values())
        L.append(f"- threshold {eff:g} nats: {n_mean}/{len(groups)} cells")
    # baseline performance and calibration
    L += ["", f"## Baseline performance and calibration (E-CONT, replicate {reps[0]})", "",
          "| r | n | h | predictor | mean log score | coverage 0.5 / 0.8 / 0.95 | PIT KS p | fallback | quad cap |",
          "|---|---|---|---|---|---|---|---|---|"]
    for x in predictor_rows:
        if x["condition"] == "E-CONT" and x["replicate"] == reps[0] and not x["predictor"].startswith("library"):
            L.append(f"| {x['r']:g} | {x['n']} | {x['h']} | {x['predictor']} | {x['mean_log_score']:.4f} | "
                     f"{x['coverage_0.5']:.3f} / {x['coverage_0.8']:.3f} / {x['coverage_0.95']:.3f} | {x['pit_ks_p']:.2e} | "
                     f"{x['fallback_rate']:.2f} | {x.get('quadrature_capped_rate', float('nan')):.3f} |")
    return "\n".join(L) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Stage 0.5 population-advantage experiment")
    ap.add_argument("--config", required=True)
    ap.add_argument("--workers", type=int, default=1)
    ap.add_argument("--runs-dir", default="runs")
    ap.add_argument("--checkpoint-dir", default=None,
                    help="persist each finished unit here (e.g. on Google Drive) and resume from it after interruption")
    args = ap.parse_args(argv)
    cfg = load_population_config(args.config)
    rec = run_experiment(cfg, runs_dir=args.runs_dir, workers=args.workers, checkpoint_dir=args.checkpoint_dir,
                         command=[sys.executable, "-m", "dynaicl.experiments.population_advantage", *(argv or sys.argv[1:])])
    print(rec.dir)
    report = (rec.dir / "results" / "report.md").read_text(encoding="utf-8")
    print(report[:4000])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
