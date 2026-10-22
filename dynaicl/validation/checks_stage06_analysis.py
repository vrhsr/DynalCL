"""Stage 0.6 validation of the frozen analysis, decision and runner code (V20-V24). Synthetic inputs only.

V20 L-estimand and contrast construction vs an independent loop implementation.
V21 cluster bootstrap: shared indices across contrasts, system-level SE, critical-value calibration (Sidak / identical
    columns), simultaneous coverage, failure surfacing.
V22 decision rule truth table (hand-derived verdicts from PREREG_stage06 section 7) and the flag definitions.
V23 Tier-2 criterion: Bonferroni cutoff, precision condition, UNINFORMATIVE never a pass.
V24 runner refusals on temporary copies (manifest, config, seeds, environment, checkpoints, missing units).
"""

from __future__ import annotations

import json
import math
import tempfile
from pathlib import Path

import numpy as np
from scipy import stats

from dynaicl.experiments import stage06_analysis as A
from dynaicl.validation.checks import CheckResult

QS = (0.0, 0.755, 2.56, 6.5)
HS = (1, 5)
RS = (0.25, 1.0, 4.0)
NS = tuple(range(2, 41))
L = tuple(range(10, 41))
CELLS = [(q, h, r) for q in QS for h in HS for r in RS]
POS = [c for c in CELLS if c[0] > 0]
ROOT = Path(__file__).resolve().parents[2]


# ------------------------------------------------------------------------------------------ V20


def check_l_estimand(seed: int = 61021, n_sys: int = 40) -> CheckResult:
    """Frozen L-average and 36-contrast table vs explicit loops: per system, sum over n in 10..40 of the item divided
    by 31; increments = gain(q) - gain(0) per system. Also the frozen contrast order and the missing-cell handling."""
    rng = np.random.default_rng(seed)
    items = {c: rng.standard_normal((n_sys, len(NS))) + 0.1 * i for i, c in enumerate(CELLS)}
    sys_gain = {c: A.long_context_average(v, NS, L) for c, v in items.items()}
    names, X, missing = A.contrast_table(sys_gain, QS, HS, RS)
    ref = {}
    for c, v in items.items():
        col = np.empty(n_sys)
        for s in range(n_sys):
            tot = 0.0
            for j, n in enumerate(NS):
                if 10 <= n <= 40:
                    tot += v[s, j]
            col[s] = tot / 31.0
        ref[c] = col
    err = 0.0
    for k, (kind, q, h, r) in enumerate(names):
        want = ref[(q, h, r)] - (ref[(0.0, h, r)] if kind == "increment" else 0.0)
        err = max(err, float(np.max(np.abs(X[:, k] - want))))
    order_ok = (len(names) == 36 and not missing and names[:18] == [("gain", *c) for c in POS]
                and names[18:] == [("increment", *c) for c in POS])
    partial = dict(sys_gain)
    del partial[(0.0, 1, 1.0)]
    _, X2, miss2 = A.contrast_table(partial, QS, HS, RS)
    miss_ok = sorted(miss2) == sorted(("increment", q, 1, 1.0) for q in QS[1:]) and X2.shape[1] == 33
    ok = err <= 1e-12 and order_ok and miss_ok
    return CheckResult("V20_l_estimand_and_contrasts", ok, {"max_abs_err_vs_loops": err, "order_ok": order_ok,
                                                           "missing_handling_ok": miss_ok})


# ------------------------------------------------------------------------------------------ V21


def _correlated_items(rng, n_sys, scale=0.1, within=0.02):
    u = rng.standard_normal((n_sys, len(CELLS))) @ np.linalg.cholesky(0.5 * np.eye(len(CELLS)) + 0.5).T * scale
    return {c: 0.01 + u[:, k:k + 1] + within * rng.standard_normal((n_sys, len(NS))) for k, c in enumerate(CELLS)}


def check_bootstrap(seed: int = 61022) -> CheckResult:
    rng = np.random.default_rng(seed)
    det = {}
    # (a) the same resampled systems for every contrast in a draw
    x = rng.standard_normal(300)
    X = np.column_stack([x, x + 5.0, 2.0 * x])
    a_err = 0.0
    for th, se in A.bootstrap_draws(X, 2000, rng, 500):
        a_err = max(a_err, float(np.max(np.abs(th[:, 1] - th[:, 0] - 5.0))), float(np.max(np.abs(th[:, 2] - 2 * th[:, 0]))),
                    float(np.max(np.abs(se[:, 2] - 2 * se[:, 0]))), float(np.max(np.abs(se[:, 1] - se[:, 0]))))
    det["shared_indices_max_err"] = a_err
    # (b) system-level SE through the full replicate path (items correlated within systems)
    n_sys = 400
    items = _correlated_items(rng, n_sys)
    res = A.analyze_replicate(items, NS, L, QS, HS, RS, 0.02, 0.05, (10000,), 500, 0.5, rng)
    lavg = {c: v[:, [NS.index(n) for n in L]].mean(axis=1) for c, v in items.items()}
    b_err, n_ok = float("inf"), False
    if res["ok"]:
        b_err = 0.0
        for c in res["contrasts"]:
            col = lavg[(c["q"], c["h"], c["r"])] - (lavg[(0.0, c["h"], c["r"])] if c["kind"] == "increment" else 0.0)
            b_err = max(b_err, abs(c["se"] - col.std(ddof=1) / math.sqrt(n_sys)) / c["se"],
                        abs(c["estimate"] - col.mean()))
        n_ok = res["n_systems"] == n_sys
    det["system_level_se_rel_err"] = b_err
    det["n_systems_ok"] = n_ok
    # bootstrap SD of theta* vs analytic SE (cluster bootstrap reproduces the system-level SE)
    Xb = np.column_stack([lavg[c] for c in POS[:4]])
    th_all = np.vstack([th for th, _ in A.bootstrap_draws(Xb, 4000, rng, 500)])
    sd_ratio = th_all.std(axis=0, ddof=1) / (Xb.std(axis=0, ddof=1) / math.sqrt(n_sys))
    det["bootstrap_sd_over_se"] = [float(v) for v in sd_ratio]
    # (c) critical-value calibration
    K = 36
    sidak = float(stats.norm.isf((1 - 0.95 ** (1 / K)) / 2))
    Xi = rng.standard_normal((2000, K)) * np.logspace(-2, 0, K)
    c_ind = A.simultaneous_band(Xi, 0.05, (10000,), 500, rng, 1.0)["c"]
    Xd = np.repeat(rng.standard_normal((2000, 1)), K, axis=1) * np.logspace(-2, 0, K)
    c_id = A.simultaneous_band(Xd, 0.05, (10000,), 500, rng, 1.0)["c"]
    det.update({"c_independent": c_ind, "sidak": sidak, "c_identical": c_id})
    # (d) simultaneous coverage over synthetic datasets with known means
    reps, cover = 300, 0
    C = np.linalg.cholesky(0.5 * np.eye(K) + 0.5)
    scales = np.logspace(-2, 0, K)
    for _ in range(reps):
        Xc = (rng.standard_normal((300, K)) @ C.T) * scales + 1.0
        band = A.simultaneous_band(Xc, 0.05, (1000,), 500, rng, 1.0)
        cover += bool(np.all((band["lo"] <= 1.0) & (band["hi"] >= 1.0)))
    half = 3.29 * math.sqrt(reps * 0.95 * 0.05)
    det["coverage"] = cover / reps
    cov_ok = abs(cover - 0.95 * reps) <= half
    # (e) failures are raised, never dropped
    fails = {}
    for name, (Xf, sched, tol) in {
        "three_systems_degenerate_draws": (rng.standard_normal((3, 3)), (10000,), 0.9),   # ~1/9 of draws degenerate
        "non_finite": (np.where(np.arange(30)[:, None] == 3, np.nan, rng.standard_normal((30, 3))), (10000,), 0.9),
        "constant_column": (np.column_stack([np.ones(30), rng.standard_normal(30)]), (10000,), 0.9),
        "mc_tolerance_unmet": (rng.standard_normal((200, 3)), (10000, 20000), 1e-6),
    }.items():
        try:
            A.simultaneous_band(Xf, 0.05, sched, 500, rng, tol)
            fails[name] = "not raised"
        except A.BootstrapFailure:
            fails[name] = "raised"
    bad = dict(items)
    bad[(2.56, 1, 1.0)] = bad[(2.56, 1, 1.0)].copy()
    bad[(2.56, 1, 1.0)][0, NS.index(20)] = np.nan
    r2 = A.analyze_replicate(bad, NS, L, QS, HS, RS, 0.02, 0.05, (10000,), 500, 0.5, rng)
    fails["replicate_returns_not_ok"] = "raised" if (not r2["ok"] and r2["error"]) else "not raised"
    det["failures"] = fails
    ok = (a_err <= 1e-12 and b_err <= 1e-10 and n_ok and bool(np.all(np.abs(sd_ratio - 1) <= 0.06))
          and abs(c_ind - sidak) <= 0.1 and abs(c_id - stats.norm.isf(0.025)) <= 0.1 and cov_ok
          and all(v == "raised" for v in fails.values()))
    return CheckResult("V21_cluster_bootstrap", ok, det)


# ------------------------------------------------------------------------------------------ V22


def _flags(sup=(), gplus=(), iplus=(), gminus=(), neg=()):
    out = {}
    for c in POS:
        gp = c in gplus or c in sup
        ip = c in iplus or c in sup
        out[c] = {"G+": gp, "I+": ip, "G-": c in gminus, "NEG": c in neg, "SUPPORTED": gp and ip}
    return out


def _rep(flags, ok=True):
    return {"ok": ok, "error": None if ok else "synthetic failure", "flags": flags}


def check_decision_rule() -> CheckResult:
    """Hand-derived verdicts (PREREG_stage06 section 7). q1, q2, q3 = 0.755, 2.56, 6.5."""
    q1, q2, q3 = QS[1:]
    crit = {"tier1": True, "tier2": True}
    two_scales_h1 = [(q, 1, r) for q in (q1, q2) for r in (0.25, 1.0)]
    mixed_pairs = [(q1, 1, 0.25), (q2, 1, 0.25), (q2, 1, 1.0), (q3, 1, 1.0)]
    all_minus = _flags(gminus=POS)
    cases = {
        "all_supported": ([_rep(_flags(sup=POS))] * 2, crit, "GO", True),
        "adjacent_pair_two_scales": ([_rep(_flags(sup=two_scales_h1))] * 2, crit, "GO", True),
        "one_replicate_only": ([_rep(_flags(sup=two_scales_h1)), _rep(_flags())], crit, "REVISE", None),
        "non_adjacent_pair": ([_rep(_flags(sup=[(q, 1, r) for q in (q1, q3) for r in (0.25, 1.0)]))] * 2, crit, "REVISE", None),
        "one_scale_per_horizon": ([_rep(_flags(sup=[(q1, 1, 0.25), (q2, 1, 0.25), (q1, 5, 1.0), (q2, 5, 1.0)]))] * 2,
                                  crit, "REVISE", None),
        "gain_without_increment": ([_rep(_flags(gplus=two_scales_h1))] * 2, crit, "REVISE", None),
        "different_pairs_per_scale": ([_rep(_flags(sup=mixed_pairs))] * 2, crit, "GO", False),
        "stop_all_below": ([_rep(all_minus)] * 2, crit, "STOP", None),
        "stop_one_replicate_only": ([_rep(all_minus), _rep(_flags(gminus=POS[1:]))], crit, "REVISE", None),
        "negative_gain": ([_rep(_flags(gminus=POS, neg=[POS[5]])), _rep(all_minus)], crit, "BLOCKED", None),
        "missing_cell": ([_rep({k: v for k, v in _flags(sup=POS).items() if k != POS[0]}), _rep(_flags(sup=POS))],
                         crit, "BLOCKED", None),
        "critical_failure": ([_rep(_flags(sup=POS))] * 2, {"tier1": True, "tier2": False}, "BLOCKED", None),
        "replicate_invalid": ([_rep(_flags(sup=POS), ok=False), _rep(_flags(sup=POS))], crit, "BLOCKED", None),
        "three_replicates": ([_rep(_flags(sup=POS))] * 3, crit, "BLOCKED", None),
    }
    results, ok = {}, True
    for name, (reps, cr, want, strict) in cases.items():
        d = A.decide(reps, cr, QS, HS, RS, 2)
        good = d["verdict"] == want and (strict is None or d["strict_variant_holds"] == strict)
        results[name] = f"{d['verdict']} (want {want}{'' if strict is None else f', strict={strict}'})" + ("" if good else " WRONG")
        ok &= good
    # flag definitions from bounds
    names = [("gain", q1, 1, 1.0), ("increment", q1, 1, 1.0), ("gain", q2, 1, 1.0), ("increment", q2, 1, 1.0),
             ("gain", q3, 1, 1.0), ("increment", q3, 1, 1.0), ("gain", q1, 5, 1.0), ("increment", q1, 5, 1.0)]
    band = {"lo": np.array([0.021, 0.001, 0.019, 0.5, -0.05, -0.001, 0.03, -0.001]),
            "hi": np.array([0.05, 0.02, 0.06, 0.6, -0.001, 0.01, 0.04, 0.02])}
    f = A.cell_flags(names, band, 0.02)
    want = {(q1, 1, 1.0): (True, True, False, False, True), (q2, 1, 1.0): (False, True, False, False, False),
            (q3, 1, 1.0): (False, False, True, True, False),
            (q1, 5, 1.0): (True, False, False, False, False)}         # G+ without I+ is NOT supported
    flag_ok = all(tuple(f[c][k] for k in ("G+", "I+", "G-", "NEG", "SUPPORTED")) == v for c, v in want.items())
    results["flag_definitions"] = "ok" if flag_ok else f"WRONG {f}"
    ok &= flag_ok
    return CheckResult("V22_decision_rule", bool(ok), results)


# ------------------------------------------------------------------------------------------ V23


def _with_mean(rng, n, mean, sd=0.1):
    x = rng.standard_normal(n)
    x = (x - x.mean()) / x.std(ddof=1) * sd
    return x + mean


def check_tier2_rule(seed: int = 61023) -> CheckResult:
    rng = np.random.default_rng(seed)
    crit = A.tier2_criterion(12, 0.01, 0.8, 0.02)
    z_ok = abs(crit["z_crit"] - stats.norm.isf(0.01 / 24)) < 1e-12
    se_ok = abs(crit["max_combined_se"] - 0.02 / (stats.norm.isf(0.01 / 24) + stats.norm.ppf(0.8))) < 1e-12
    keys = [(f"R{k}", r, h) for k in (1, 2) for r in RS for h in HS]

    def case(n6, n5, z_planted=0.0, at=None):
        s05 = {(r, h): _with_mean(rng, n5, 0.03) for r in RS for h in HS}
        s06 = {}
        for key in keys:
            se = math.sqrt(0.1 ** 2 / n6 + 0.1 ** 2 / n5)
            s06[key] = _with_mean(rng, n6, 0.03 + (z_planted * se if key == at else 0.0))
        return A.tier2_compare(s06, s05, 0.01, 0.8, 0.02)["outcome"]

    out = {"equal_means": case(4000, 6756), "z_3.0": case(4000, 6756, 3.0, keys[3]),
           "z_3.6": case(4000, 6756, 3.6, keys[3]), "imprecise": case(60, 60)}
    want = {"equal_means": "PASS", "z_3.0": "PASS", "z_3.6": "FAIL", "imprecise": "UNINFORMATIVE"}
    ok = z_ok and se_ok and out == want
    return CheckResult("V23_tier2_rule", ok, {"outcomes": out, "expected": want, "z_crit": crit["z_crit"],
                                              "max_combined_se": crit["max_combined_se"]})


# ------------------------------------------------------------------------------------------ V24


def check_runner_refusals() -> CheckResult:
    """Each refusal is exercised on a temporary copy; nothing in the workspace is modified. 'accept' rows confirm the
    unmodified copy passes the same gate."""
    from dynaicl.config.stage06_schema import load_stage06_config
    from dynaicl.experiments import stage06_probe as P
    from dynaicl.provenance import sha256_file
    cfg = load_stage06_config(ROOT / "config" / "stage06_test.yaml")
    out = {}

    def expect(name, fn, refuse):
        try:
            fn()
            got = "accepted"
        except P.Refusal:
            got = "refused"
        except Exception as exc:                       # any other exception is not a clean refusal
            got = f"error {type(exc).__name__}: {exc}"
        out[name] = got + ("" if got == ("refused" if refuse else "accepted") else "  <-- UNEXPECTED")

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "pkg").mkdir()
        (root / "pkg" / "a.py").write_text("x = 1\n", encoding="utf-8")
        (root / "doc.md").write_text("frozen\n", encoding="utf-8")
        env = {"environment": P.current_environment()}
        (root / "env.json").write_text(json.dumps(env), encoding="utf-8")
        files = {rel: sha256_file(root / rel) for rel in ("pkg/a.py", "doc.md", "env.json")}
        man = {"schema": P.MANIFEST_SCHEMA, "files": files, "environment_manifest": "env.json",
               "created_utc": "2026-01-01T00:00:00Z",
               "config_hashes": {"config/stage06_test.yaml": {"config_hash": cfg.config_hash(), "mode": "test"}}}
        mp = root / "manifest.json"
        mp.write_text(json.dumps(man), encoding="utf-8")
        sha = sha256_file(mp)
        expect("manifest_ok", lambda: P.verify_manifest(mp, sha, root), False)
        expect("manifest_wrong_expected_sha", lambda: P.verify_manifest(mp, "0" * 64, root), True)
        (root / "doc.md").write_text("tampered\n", encoding="utf-8")
        expect("frozen_file_changed", lambda: P.verify_manifest(mp, sha, root), True)
        (root / "doc.md").write_text("frozen\n", encoding="utf-8")
        (root / "pkg" / "a.py").unlink()
        expect("frozen_file_missing", lambda: P.verify_manifest(mp, sha, root), True)
        (root / "pkg" / "a.py").write_text("x = 1\n", encoding="utf-8")
        expect("manifest_restored_ok", lambda: P.verify_manifest(mp, sha, root), False)
        m = {**man, "manifest_sha256": sha}
        expect("config_frozen_ok", lambda: P.check_config_frozen(cfg, m), False)
        expect("config_not_frozen", lambda: P.check_config_frozen(
            cfg, {**m, "config_hashes": {"x": {"config_hash": "0" * 64, "mode": "test"}}}), True)
        # seeds
        seeds_ok = root / "seeds_ok.yaml"
        seeds_ok.write_text("roles:\n  validation:\n    seeds: [61024, 61025, 61026]\n  other:\n    seeds: [1, 2]\n",
                            encoding="utf-8")
        seeds_dup = root / "seeds_dup.yaml"
        seeds_dup.write_text("roles:\n  validation:\n    seeds: [61024, 61025, 61026]\n  other:\n    seeds: [61025]\n",
                             encoding="utf-8")
        seeds_wrong = root / "seeds_wrong.yaml"
        seeds_wrong.write_text("roles:\n  validation:\n    seeds: [61024, 61026]\n", encoding="utf-8")
        expect("seeds_ok", lambda: P.check_seeds(cfg, seeds_ok), False)
        expect("seed_collision", lambda: P.check_seeds(cfg, seeds_dup), True)
        expect("seed_not_allocated", lambda: P.check_seeds(cfg, seeds_wrong), True)
        # environment
        expect("environment_identical", lambda: P.check_environment(m, None, cfg, root), False)
        (root / "env.json").write_text(json.dumps({"environment": {**env["environment"], "numpy": "0.0.0"}}),
                                       encoding="utf-8")
        expect("environment_differs_no_qualification", lambda: P.check_environment(m, None, cfg, root), True)
        qual = root / "qual.json"
        base_q = {"environment": P.current_environment(), "manifest_sha256": sha, "config_hash": cfg.config_hash(),
                  "passed": True}
        qual.write_text(json.dumps({**base_q, "manifest_sha256": "1" * 64}), encoding="utf-8")
        expect("qualification_other_manifest", lambda: P.check_environment(m, qual, cfg, root), True)
        qual.write_text(json.dumps({**base_q, "passed": False}), encoding="utf-8")
        expect("qualification_failed", lambda: P.check_environment(m, qual, cfg, root), True)
        qual.write_text(json.dumps({**base_q, "environment": {**base_q["environment"], "machine": "other"}}),
                        encoding="utf-8")
        expect("qualification_other_environment", lambda: P.check_environment(m, qual, cfg, root), True)
        qual.write_text(json.dumps(base_q), encoding="utf-8")
        expect("qualification_valid", lambda: P.check_environment(m, qual, cfg, root), False)
        # checkpoints
        ck = root / "ckpt"
        unit = ("primary", 0, 0, 0)
        arrays = {k: np.zeros(s, dtype=d) for k, (s, d) in P.expected_arrays(cfg, unit).items()}
        P.save_unit(ck, unit, {"note": "synthetic"}, arrays, 0.0, cfg, sha)
        expect("checkpoint_ok", lambda: P.load_unit(ck, unit, cfg, sha), False)
        expect("checkpoint_other_manifest", lambda: P.load_unit(ck, unit, cfg, "2" * 64), True)
        with open(ck / "primary_0_0_0.npz", "wb") as fh:          # a valid file with different contents
            np.savez(fh, **{k: v + 1 for k, v in arrays.items()})
        expect("checkpoint_invalid_checksum", lambda: P.load_unit(ck, unit, cfg, sha), True)
        P.save_unit(ck, unit, {"note": "synthetic"}, arrays, 0.0, cfg, sha)
        rec = json.loads((ck / "primary_0_0_0.json").read_text(encoding="utf-8"))
        (ck / "primary_0_0_0.json").write_text(json.dumps({**rec, "schema": "stage06-unit/v0"}), encoding="utf-8")
        expect("checkpoint_incompatible_schema", lambda: P.load_unit(ck, unit, cfg, sha), True)
        wrong = {**arrays, "pop_logscore": np.zeros((1, 1, 1))}
        P.save_unit(ck, unit, {"note": "synthetic"}, wrong, 0.0, cfg, sha)
        expect("checkpoint_wrong_array_shape", lambda: P.load_unit(ck, unit, cfg, sha), True)
        expect("analyze_missing_units", lambda: P.analyze(cfg, {}), True)
    ok = all("UNEXPECTED" not in v for v in out.values())
    return CheckResult("V24_runner_refusals", ok, out)


ALL_CHECKS_STAGE06_ANALYSIS = {"V20": check_l_estimand, "V21": check_bootstrap, "V22": check_decision_rule,
                               "V23": check_tier2_rule, "V24": check_runner_refusals}
