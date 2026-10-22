"""Section 5.G: negative controls. Each injected bug must be detected by at least one validation check.

For speed, this file runs a targeted detector subset per mutation. The full matrix (every check, and the
whole pytest suite, under every mutation) comes from scripts/mutation_report.py.
"""

import os
from functools import partial

import pytest

from dynaicl.systems.conditions import ContinuousPriorCondition, LibraryCondition
from dynaicl.validation import checks
from dynaicl.validation.mutations import MUTATIONS, detected, run_check_safely

E_GAUSS = partial(checks.check_matched_reference_calibration, n_items=1000, ns=(2, 10), hs=(1, 3),
                  conditions=[ContinuousPriorCondition(checks.P_GAUSS, checks.X0)])
E_LIB = partial(checks.check_matched_reference_calibration, n_items=1000, ns=(2, 10), hs=(1,),
                conditions=[LibraryCondition(checks._calibration_library(), checks.X0)])
F_LIB = partial(checks.check_matched_reference_optimality, n_items=2000, ns=(3, 10), hs=(1, 3),
                conditions=[LibraryCondition(checks._calibration_library(), checks.X0)])

DETECTORS = {
    "wrong_prior_variance": {"A1": checks.check_gaussian_reference_vs_grid, "C1": checks.check_sequential_equals_batch,
                             "E_gauss": E_GAUSS},
    "off_by_one_likelihood": {"A1": checks.check_gaussian_reference_vs_grid,
                              "A6": checks.check_library_vs_raw_likelihood,
                              "C1": checks.check_sequential_equals_batch},
    "future_leak": {"J1": checks.check_future_perturbation_invariance, "E_gauss": E_GAUSS},
    "unmatched_reference": {"E_lib": E_LIB, "F_lib": F_LIB},
    "unmatched_reference_guard_bypassed": {"E_lib": E_LIB, "F_lib": F_LIB},
}

skip_if_session_mutated = pytest.mark.skipif(bool(os.environ.get("DYNAICL_MUTATION")),
                                             reason="a session-wide mutation is already active")


@skip_if_session_mutated
def test_g_detector_variants_pass_without_mutation():
    """Baseline: the reduced-size detector variants used below pass on the unmutated code."""
    for fn in (E_GAUSS, E_LIB, F_LIB):
        res = run_check_safely(fn)
        assert res["status"] == "pass", res


@skip_if_session_mutated
@pytest.mark.parametrize("mutation", sorted(MUTATIONS))
def test_g_mutation_is_detected(mutation):
    with MUTATIONS[mutation]():
        results = {name: run_check_safely(fn) for name, fn in DETECTORS[mutation].items()}
    caught = {name: r["status"] for name, r in results.items() if detected(r)}
    print(f"\n{mutation}: " + ", ".join(f"{k}={v['status']}" for k, v in results.items()))
    assert caught, f"{mutation} was not detected by any of {list(results)}"
