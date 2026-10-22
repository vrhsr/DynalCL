"""Section 5.I: reproducibility. Identical config and seed give bitwise-identical results (independent of
the worker count). A different seed gives different results. Changing one named stream leaves the
others unchanged."""

import json
from dataclasses import replace

import numpy as np

from dynaicl.config.schema import load_config
from dynaicl.experiments.separability import run_experiment
from dynaicl.rng import NamedStreams
from dynaicl.systems.conditions import ContinuousPriorCondition
from dynaicl.systems.library import build_library_from_prior
from dynaicl.systems.splits import SplitRole, generate_split
from dynaicl.validation.checks import P_STABLE_TN, X0

SMOKE = "config/smoke.yaml"


def _result_checksums(run_dir):
    sums = json.loads((run_dir / "checksums.json").read_text())
    return {k: v for k, v in sums.items() if k.startswith("results/")}


def test_i_same_config_and_seed_bitwise_identical_across_runs_and_worker_counts(tmp_path):
    cfg = load_config(SMOKE)
    r1 = run_experiment(cfg, runs_dir=tmp_path, workers=1, run_id="a")
    r2 = run_experiment(cfg, runs_dir=tmp_path, workers=1, run_id="b")
    r3 = run_experiment(cfg, runs_dir=tmp_path, workers=2, run_id="c")
    c1, c2, c3 = _result_checksums(r1.dir), _result_checksums(r2.dir), _result_checksums(r3.dir)
    assert c1 and c1 == c2 == c3
    a = np.load(r1.dir / "results" / "item_log_scores.npy")
    b = np.load(r3.dir / "results" / "item_log_scores.npy")
    assert a.tobytes() == b.tobytes()


def test_i_different_seed_gives_different_outputs(tmp_path):
    cfg = load_config(SMOKE)
    cfg2 = replace(cfg, experiment=replace(cfg.experiment, root_seed=cfg.experiment.root_seed + 1))
    r1 = run_experiment(cfg, runs_dir=tmp_path, workers=1, run_id="a")
    r2 = run_experiment(cfg2, runs_dir=tmp_path, workers=1, run_id="b")
    a = np.load(r1.dir / "results" / "item_log_scores.npy")
    b = np.load(r2.dir / "results" / "item_log_scores.npy")
    assert a.shape == b.shape and not np.array_equal(a, b)


def test_i_changing_one_stream_leaves_others_unchanged():
    base = NamedStreams(31)
    alt = NamedStreams(31, (("eval_noise", 5),))
    cond = ContinuousPriorCondition(P_STABLE_TN, X0)
    ev0, ev1 = (generate_split(cond, SplitRole.EVALUATION, s, 100, 20) for s in (base, alt))
    sel0, sel1 = (generate_split(cond, SplitRole.SELECTION, s, 100, 20) for s in (base, alt))
    lib0, lib1 = (build_library_from_prior(P_STABLE_TN, 16, s) for s in (base, alt))
    assert np.array_equal(ev0.coefficients, ev1.coefficients)          # eval_systems untouched
    assert not np.array_equal(ev0.innovations, ev1.innovations)        # eval_noise changed
    assert np.array_equal(sel0.trajectories, sel1.trajectories)        # selection streams untouched
    assert np.array_equal(lib0.coefficients, lib1.coefficients)        # library stream untouched


def test_i_items_do_not_depend_on_item_count():
    s = NamedStreams(32)
    cond = ContinuousPriorCondition(P_STABLE_TN, X0)
    small = generate_split(cond, SplitRole.EVALUATION, s, 10, 15)
    large = generate_split(cond, SplitRole.EVALUATION, s, 50, 15)
    assert np.array_equal(small.trajectories, large.trajectories[:10])


def test_i_libraries_are_nested_across_sizes():
    s = NamedStreams(33)
    l16 = build_library_from_prior(P_STABLE_TN, 16, s)
    l64 = build_library_from_prior(P_STABLE_TN, 64, s)
    assert np.array_equal(l16.coefficients, l64.coefficients[:16])
