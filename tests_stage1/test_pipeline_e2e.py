"""End-to-end Stage 1A pipeline at toy scale (CPU, test-only seeds and model size): train, evaluate, pilot rule, cap rule,
analysis, verdict. Untrained toy models must fail the capability controls, so the pilot says NOT RESOLVABLE and the
confirmatory-path verdict is BLOCKED; the test checks the plumbing and the shapes of every output, not any effect."""

from __future__ import annotations

from pathlib import Path

import pytest

from dynaicl_neural import pipeline as pl
from dynaicl_neural.config import load_config

PILOT = """schema: stage1-config/v1
phase: pilot
seed_roles: {train: test_train, eval: test_eval, library: test_library, bootstrap: test_bootstrap}
replicates: 1
primary_arms: [CONT, UNIF, LIB-2]
model: XS
models_per_arm: 3
steps: 20
checkpoints: [10, 20]
batch: 16
eval: {held_n: 120, probe_n: 60, oos_n: 60, control_n: 60}
"""
CONFIRM = """schema: stage1-config/v1
phase: confirmatory
seed_roles: {train: test_train, eval: test_eval, library: test_library, bootstrap: test_bootstrap}
replicates: 2
primary_arms: [CONT, UNIF, LIB-2, LIB-4]
model: XS
models_per_arm: null
steps: null
checkpoints: null
batch: 16
eval: {held_n: 120, probe_n: 60, oos_n: 60, control_n: 60}
bootstrap_draws: 40
cap_rule: {max_models: 128, gpu_hours_limit: 48.0, safety: 1.25, step: 8}
"""


@pytest.fixture(scope="module")
def work(tmp_path_factory):
    d = tmp_path_factory.mktemp("e2e")
    (d / "pilot.yaml").write_text(PILOT, encoding="utf-8")
    (d / "confirm.yaml").write_text(CONFIRM, encoding="utf-8")
    return d


def test_pilot_path(work):
    cfg, _ = load_config(work / "pilot.yaml")
    jobs = pl.plan_jobs(cfg)
    assert len(jobs) == 9
    out = work / "pilot"
    pl.run_training(cfg, jobs, out, workers=2, device="cpu", log=lambda m: None)
    sets = pl.evaluation_sets(cfg, 0)
    pl.reference_quantities(cfg, 0, sets, out)
    for j in jobs:
        for st in j.checkpoints:
            pl.evaluate_model(cfg, j, st, sets, out, "cpu", controls_only=True)
    dec = pl.pilot_decision(cfg, jobs, out, cap=128)
    assert dec["status"] == "NOT RESOLVABLE (capability)" and dec["B"] is None
    assert all("pass" in v for v in dec["control_flags"].values())
    assert "s1" in dec and dec["s1"] is None            # no sds computed when no budget passes


def test_cap_rule_monotone():
    cfg, _ = load_config(Path("config/stage1.yaml"))
    fast = pl.cap_from_j0(cfg, sec_per_model_step=0.0005, eval_sec_per_model=30, budget=50000)
    slow = pl.cap_from_j0(cfg, sec_per_model_step=0.005, eval_sec_per_model=30, budget=50000)
    assert 0 <= slow <= fast <= cfg.cap_rule.max_models and fast % cfg.cap_rule.step == 0


def test_confirmatory_analysis_path(work):
    cfg, _ = load_config(work / "confirm.yaml")
    decision = {"status": "RESOLVED", "B": 20, "M1": 3, "M2": 3}
    jobs = pl.plan_jobs(cfg, decision)
    assert len(jobs) == 2 * 4 * 3
    out = work / "confirm"
    pl.run_training(cfg, jobs, out, workers=2, device="cpu", log=lambda m: None)
    for rep in (0, 1):
        sets = pl.evaluation_sets(cfg, rep)
        pl.reference_quantities(cfg, rep, sets, out)
        for j in (x for x in jobs if x.replicate == rep):
            pl.evaluate_model(cfg, j, 20, sets, out, "cpu")
    prim = pl.primary_jobs(cfg, jobs, decision)
    assert prim == jobs                                   # no secondary family kept in this decision
    checks = pl.controls_and_validity(cfg, prim, out)
    q1 = pl.analyse_q1(cfg, [j for j in prim if j.arm in ("CONT", "UNIF")], out)
    q2 = pl.analyse_q2(cfg, [j for j in prim if j.arm.startswith("LIB-")], out)
    beh = pl.analyse_behavioural(cfg, [j for j in prim if j.arm in ("CONT", "UNIF")], out, 0.05)
    assert len(beh["confirmed"]) == 2 * len(pl.BEHAV_CELLS)
    assert set(q1["confirmed"]) == {f"{r}|{n}" for r, n in pl.Q1_CELLS}
    assert all(v in ("POP-LIKE", "STAB-LIKE", "WORSE-THAN-STAB", "INCONCLUSIVE", "INCONCLUSIVE (discordant)")
               for v in q1["confirmed"].values())
    assert set(q2["per_K"]) == {"LIB-2", "LIB-4"}
    assert pl.verdict(checks, q1, q2, decision) == ("BLOCKED" if not checks["all_pass"] else pl.verdict(checks, q1, q2,
                                                                                                         decision))
    assert not checks["all_pass"]                         # untrained toy models fail the capability controls


def test_secondary_planning_projection_and_drop_rule():
    cfg, _ = load_config(Path("config/stage1.yaml"))
    decision = {"status": "RESOLVED", "B": 50000, "M1": 64, "M2": 64}
    j0 = {"single": [{"size": s, "steps": 300, "sec_per_step": v} for s, v in
                     (("S", 0.004), ("M", 0.006), ("L", 0.02), ("DW-shallow", 0.006), ("DW-deep", 0.009),
                      ("GRU", 0.005), ("SSM", 0.008))],
          "concurrent": [{"processes": 8, "wall_seconds": 300 * 0.006 * 8 / 4.0}]}
    proj = pl.project_hours(cfg, decision, j0, eval_sec=60)
    kept = pl.keep_secondary(cfg, proj)
    total = proj["primary_hours"] + sum(proj["secondary_hours"][f] for f in kept)
    assert total <= cfg.cap_rule.gpu_hours_limit or kept == [f for f in cfg.secondary if f not in cfg.drop_order]
    dropped = [f for f in cfg.secondary if f not in kept]
    assert set(dropped) == set(cfg.drop_order[:len(dropped)])      # dropped strictly in the pre-registered order
    jobs = pl.plan_jobs(cfg, {**decision, "secondary_kept": ["training-length-4B", "size-S"]})
    assert {(j.size, j.steps) for j in jobs} == {("M", 50000), ("M", 200000), ("S", 50000)}
    assert len({j.model_dir(Path("o")) for j in jobs}) == len(jobs)  # 4B models never collide with primary M models
