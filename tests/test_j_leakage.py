"""Section 5.J (and Section 3): leakage controls and the information-access contract."""

import numpy as np
import pytest

from dynaicl.baselines.family import build_context_only_family
from dynaicl.evaluation import harness
from dynaicl.references.matched import continuous_prior_predictor
from dynaicl.rng import NamedStreams
from dynaicl.systems.conditions import ContinuousPriorCondition
from dynaicl.systems.context import ContextWindow, GroundTruth
from dynaicl.systems.library import build_library_from_prior
from dynaicl.systems.splits import LeakageError, SplitRole, assert_no_unintended_overlap, generate_split
from dynaicl.validation import checks
from tests._util import assert_check


def test_j1_perturbing_target_and_future_leaves_predictions_unchanged():
    assert_check(checks.check_future_perturbation_invariance())


def test_j2_library_independent_of_evaluation_stream_seed():
    assert_check(checks.check_stream_independence())


def test_j3_disjointness_and_intentional_overlap():
    r = assert_check(checks.check_split_disjointness())
    print("\nJ3:", r.details)


def test_j4_kernel_selection_respects_time_order_and_gaps():
    assert_check(checks.check_kernel_validation_causality())


def test_j_overlap_detector_has_power():
    """Positive control: a split compared with itself must be flagged."""
    s = generate_split(ContinuousPriorCondition(checks.P_STABLE_TN, checks.X0), SplitRole.EVALUATION,
                       NamedStreams(1), 20, 10)
    with pytest.raises(LeakageError):
        assert_no_unintended_overlap(s, s)


def test_j_predictors_accept_only_context_windows():
    preds = {"cont": continuous_prior_predictor(checks.P_STABLE_TN), **build_context_only_family(1.0)}
    gt = GroundTruth(0, 0.5, 1.0, "x", 0.1, 1, "h")
    for p in preds.values():
        for bad in (np.array([0.1, 0.2]), gt, [0.1, 0.2]):
            with pytest.raises(TypeError):
                p.predict(bad, 1)


def test_j_context_window_is_immutable():
    ctx = ContextWindow(np.array([0.1, 0.2]))
    with pytest.raises(ValueError):
        ctx.values[0] = 5.0
    with pytest.raises(AttributeError):
        ctx.extra = 1


def test_j_evaluation_contexts_end_at_x_n_and_start_at_x0():
    cond = ContinuousPriorCondition(checks.P_STABLE_TN, checks.X0)
    split = generate_split(cond, SplitRole.EVALUATION, NamedStreams(2), 30, 12)
    es = harness.build_evaluation_set(cond, split, 7, 3)
    targets = harness.ground_truth_for_validation(es)[2]
    for i, ctx in enumerate(es.contexts):
        assert np.array_equal(ctx.values, split.trajectories[i, :8])
        assert targets[i] == split.trajectories[i, 10]


def test_j_library_built_only_from_training_stream():
    lib = build_library_from_prior(checks.P_STABLE_TN, 8, NamedStreams(3))
    assert lib.provenance["stream"] == "library_systems"
