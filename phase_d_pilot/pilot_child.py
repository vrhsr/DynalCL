"""PHASE D (PILOT) child-process entry points. NOT part of the frozen file set. Pilot seeds only.

Run as ``python pilot_child.py <mode> --frozen-root R ...``. Each mode imports the FROZEN package from R and, where a test
needs it, patches module attributes IN MEMORY of this process only (no file is edited). Modes:

crash-run     run the frozen runner CLI, dying at a chosen point (KeyboardInterrupt mid-unit, or os._exit at a write stage)
profile-unit  run one frozen unit; report wall/CPU/peak RSS, array hashes, optional checkpoint write/load timing
stub-run      run the frozen runner CLI with the evaluation entry points replaced by stubs (launch-guard tests)
det-analysis  run the frozen analysis on seeded synthetic data and print hashes of the results (thread determinism)
analysis-cost synthetic confirmatory-scale checkpoints + the frozen analyze() path, timed (SYNTHETIC data)
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import pilot_common as PC  # noqa: E402


def array_hash(a) -> str:
    import numpy as np
    return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()


def load_cfg(path):
    from dynaicl.config.stage06_schema import load_stage06_config
    return load_stage06_config(path)


def parse_unit(text: str) -> tuple:
    parts = text.split(",")
    return (parts[0], *[int(x) for x in parts[1:]])


# ------------------------------------------------------------------------------------------ crash-run


def crash_run(a) -> int:
    from dynaicl.experiments import stage06_probe as P
    import numpy as np
    state = {"n": 0}
    if a.point == "interrupt_mid_unit":
        orig = P.run_unit

        def run_unit(cfg_dict, unit):
            state["n"] += 1
            if state["n"] == a.after:
                raise KeyboardInterrupt
            return orig(cfg_dict, unit)
        P.run_unit = run_unit
    else:
        orig_save = P.save_unit

        def save(ckpt, unit, meta, arrays, seconds, cfg, sha):
            state["n"] += 1
            if state["n"] != a.after:
                return orig_save(ckpt, unit, meta, arrays, seconds, cfg, sha)
            name = P.unit_name(unit)
            if a.point == "savez_partial":      # die halfway through writing the arrays file
                buf = io.BytesIO()
                np.savez(buf, **arrays)
                raw = buf.getvalue()
                Path(ckpt).mkdir(parents=True, exist_ok=True)
                with open(Path(ckpt) / f"{name}.npz.tmp", "wb") as fh:
                    fh.write(raw[: len(raw) // 2])
                    fh.flush()
                os._exit(137)
            real_replace = os.replace
            calls = {"k": 0}

            def replace(src, dst):
                calls["k"] += 1
                if (a.point == "before_npz_replace" and calls["k"] == 1) or (a.point == "before_json_replace" and calls["k"] == 2):
                    os._exit(137)
                return real_replace(src, dst)
            os.replace = replace
            try:
                return orig_save(ckpt, unit, meta, arrays, seconds, cfg, sha)
            finally:
                os.replace = real_replace
        P.save_unit = save
    return P.main(a.runner_args)


# ------------------------------------------------------------------------------------------ profile-unit


def profile_unit(a) -> int:
    t_import = time.perf_counter()
    from dynaicl.experiments import stage06_probe as P
    cfg = load_cfg(a.config)
    PC.assert_pilot_config(cfg)
    t_import = time.perf_counter() - t_import
    unit = parse_unit(a.unit)
    c0, w0 = time.process_time(), time.perf_counter()
    meta, arrays, secs = P.run_unit(cfg.to_dict(), unit)
    wall, cpu = time.perf_counter() - w0, time.process_time() - c0
    n_forecasts = None
    if unit[0] == "primary":
        n_forecasts = 2 * len(cfg.grid.horizons) * len(cfg.grid.context_lengths) * cfg.grid.n_systems   # 2 predictors
    elif unit[0] == "naive":
        n_forecasts = (len(P.naive_members(cfg)) * len(cfg.grid.horizons) * len(cfg.secondary.naive_context_lengths)
                       * cfg.secondary.naive_n_systems)
    out = {"run_kind": PC.RUN_KIND, "unit": list(unit), "config": str(a.config), "n_systems": cfg.grid.n_systems,
           "naive_n_systems": cfg.secondary.naive_n_systems, "wall_s": wall, "cpu_s": cpu, "unit_seconds_reported": secs,
           "import_s": t_import, "peak_rss_mb": (PC.peak_rss_bytes() or 0) / 1e6, "n_forecasts": n_forecasts,
           "wall_s_per_forecast": (wall / n_forecasts) if n_forecasts else None,
           "array_sha256": {k: array_hash(v) for k, v in arrays.items()},
           "array_dtypes": {k: str(v.dtype) for k, v in arrays.items()}, "meta_json_sha256": hashlib.sha256(
               json.dumps({k: v for k, v in meta.items()}, sort_keys=True, default=P._json_default).encode()).hexdigest(),
           "threads_env": {k: os.environ.get(k) for k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS")}}
    if a.save_ckpt:
        ck = P.checkpoint_root(Path(a.save_ckpt), cfg)
        t = time.perf_counter()
        P.save_unit(ck, unit, meta, arrays, secs, cfg, None)
        out["ckpt_write_s"] = time.perf_counter() - t
        name = P.unit_name(unit)
        out["ckpt_bytes"] = {"npz": (ck / f"{name}.npz").stat().st_size, "json": (ck / f"{name}.json").stat().st_size}
        t = time.perf_counter()
        P.load_unit(ck, unit, cfg, None)
        out["ckpt_load_verify_s"] = time.perf_counter() - t
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(out, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    return 0


# ------------------------------------------------------------------------------------------ stub-run


def stub_run(a) -> int:
    from dynaicl.experiments import stage06_probe as P
    from dynaicl.experiments import stage06_analysis as A

    def boom(*args, **kw):
        print("STUB_REACHED: the evaluation/analysis entry point was reached (stubbed; nothing computed)", flush=True)
        raise RuntimeError("STUB_REACHED")
    P.run_unit = boom
    A.analyze_replicate = boom
    P.A.analyze_replicate = boom
    try:
        return P.main(a.runner_args)
    except RuntimeError as exc:
        if "STUB_REACHED" in str(exc):
            return 77
        raise


# ------------------------------------------------------------------------------------------ synthetic data


def synthetic_gain_items(seed_root_name: str = "phase_d_synth", N: int = 4000, effect: str = "effect_0.03"):
    """Synthetic per-item gains at (system, noise, horizon, scale, n) resolution from the Phase C dry-run generator
    (the frozen script is only imported). Seeds: design root 61903 sub-streams (synthetic only)."""
    sys.path.insert(0, str(Path(PC_ROOT[0]) / "scripts"))
    import stage06_decision_dry_run as D
    from dynaicl.rng import NamedStreams
    items, _ = D.stage05_items()
    spreads = D.planning_spreads(items)
    S = D.planning_cov(spreads, 2.0, 0.5)
    D.N = N
    out = []
    streams = NamedStreams(D.SEED)
    for rep in range(2):
        out.append(D.synth_items(D.mu_for(effect), S, streams.stream(seed_root_name, rep), "normal"))
    return D, out


PC_ROOT = [None]


def det_analysis(a) -> int:
    from dynaicl.experiments import stage06_analysis as A
    from dynaicl.rng import NamedStreams
    D, reps = synthetic_gain_items(N=a.n_systems)
    cfg = load_cfg(Path(a.frozen_root) / "config/stage06.yaml")
    an = cfg.analysis
    t = time.perf_counter()
    res = A.analyze_replicate(reps[0], D.NS, D.L, D.QS, D.HS, D.RS, an.delta, an.alpha, an.bootstrap_draws, an.bootstrap_chunk,
                              an.critical_value_rel_mc_error, NamedStreams(62999).stream("phase_d_det", 0))
    out = {"run_kind": PC.RUN_KIND, "data": "SYNTHETIC", "seconds": time.perf_counter() - t, "ok": res["ok"],
           "draws": res.get("critical_value", {}).get("draws"),
           "result_sha256": hashlib.sha256(json.dumps(res.get("contrasts"), sort_keys=True).encode()).hexdigest(),
           "c": res.get("critical_value", {}).get("c"), "threads_env": {k: os.environ.get(k) for k in
                                                                         ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS")}}
    Path(a.out).write_text(json.dumps(out, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    return 0


# ------------------------------------------------------------------------------------------ analysis-cost


def analysis_cost(a) -> int:
    """The frozen analyze() on confirmatory-scale SYNTHETIC checkpoints (config variant: mode test, pilot seeds, N = 4000)."""
    import numpy as np
    from dynaicl.experiments import stage06_probe as P
    cfg = load_cfg(a.config)           # phase_d_pilot/config/PILOT_analysis_cost_N4000_mode_test.yaml
    PC.assert_pilot_config(cfg)
    assert cfg.experiment.mode == "test" and cfg.grid.n_systems == 4000
    t0 = time.perf_counter()
    D, reps = synthetic_gain_items(N=cfg.grid.n_systems)
    t_gen = time.perf_counter() - t0
    ns, hs = cfg.grid.context_lengths, cfg.grid.horizons
    ck = Path(a.tmp_dir) / "synthetic_ckpt"
    rng = np.random.default_rng(61903)
    write_t, sizes = 0.0, 0
    units = P.plan_units(cfg)
    for u in units:
        if u[0] == "primary":
            _, rep, qi, ri = u
            q, r = cfg.model.noise_ratios[qi], cfg.model.initial_state_ratios[ri]
            stab = -1.5 + rng.standard_normal((len(hs), len(ns), cfg.grid.n_systems))
            gain = np.stack([reps[rep][(q, h, r)].T for h in hs])
            arrs = {"pop_logscore": stab + gain, "stab_logscore": stab,
                    "pop_pit": rng.random(stab.shape).astype("float32"), "stab_pit": rng.random(stab.shape).astype("float32")}
            meta = {"q": q, "r": r, "replicate": rep, "n_systems": cfg.grid.n_systems,
                    "calibration": [{"n": n, "h": h, "ks_p": 0.5} for n in cfg.checks.calibration_context_lengths for h in hs],
                    "numerics": {"max_gain_change": 1e-12}, "reproducibility": {"max_abs_diff": 1e-15}}
        elif u[0] == "naive":
            k = cfg.secondary.naive_n_systems
            shp = (len(P.naive_members(cfg)), len(hs), len(cfg.secondary.naive_context_lengths), k)
            arrs = {"naive_logscore": -1.5 + rng.standard_normal(shp), "naive_pit": rng.random(shp).astype("float32")}
            meta = {"n_systems": k, "members": P.naive_members(cfg)}
        elif u[0] == "integrity":
            arrs, meta = {}, {"ok": True, "details": {"SYNTHETIC": True}}
        else:
            arrs, meta = {}, {"passed": True, "details": {"SYNTHETIC": True}}
        t = time.perf_counter()
        P.save_unit(ck, u, meta, arrs, 0.0, cfg, None)
        write_t += time.perf_counter() - t
    sizes = sum(f.stat().st_size for f in ck.glob("*"))
    t = time.perf_counter()
    done = {u: P.load_unit(ck, u, cfg, None) for u in units}
    load_t = time.perf_counter() - t
    c0, w0 = time.process_time(), time.perf_counter()
    res = P.analyze(cfg, done)
    wall, cpu = time.perf_counter() - w0, time.process_time() - c0
    out = {"run_kind": PC.RUN_KIND, "data": "SYNTHETIC (no pilot or confirmatory data)", "units": len(units),
           "synthetic_generation_s": t_gen, "checkpoint_write_total_s": write_t, "checkpoint_bytes_total": sizes,
           "checkpoint_load_verify_total_s": load_t, "analyze_wall_s": wall, "analyze_cpu_s": cpu,
           "bootstrap_draws_used": [rp.get("critical_value", {}).get("draws") for rp in res.get("replicates", [])],
           "replicates_ok": [rp["ok"] for rp in res.get("replicates", [])],
           "peak_rss_mb": (PC.peak_rss_bytes() or 0) / 1e6}
    Path(a.out).write_text(json.dumps(out, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=("crash-run", "profile-unit", "stub-run", "det-analysis", "analysis-cost"))
    ap.add_argument("--frozen-root", required=True)
    ap.add_argument("--point")
    ap.add_argument("--after", type=int, default=1)
    ap.add_argument("--config")
    ap.add_argument("--unit")
    ap.add_argument("--out")
    ap.add_argument("--save-ckpt")
    ap.add_argument("--tmp-dir")
    ap.add_argument("--n-systems", type=int, default=4000)
    ap.add_argument("runner_args", nargs="*")
    a = ap.parse_args()
    root = PC.use_frozen_root(a.frozen_root)
    PC_ROOT[0] = str(root)
    os.chdir(root)
    return {"crash-run": crash_run, "profile-unit": profile_unit, "stub-run": stub_run, "det-analysis": det_analysis,
            "analysis-cost": analysis_cost}[a.mode](a)


if __name__ == "__main__":
    raise SystemExit(main())
