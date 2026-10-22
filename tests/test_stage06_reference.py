"""Stage 0.6 (Phase B): noisy-observation reference validation. Tolerance derivations are in the docstrings of
dynaicl/validation/checks_stage06.py. Outputs are pass/fail plus numerical diagnostics only."""

import pytest

from dynaicl.validation import checks_stage06 as C
from tests._util import assert_check


@pytest.mark.parametrize("key", ["V1", "V2", "V3", "V5", "V6", "V7", "V8", "V13", "V15", "V16", "V17", "V18", "V19"])
def test_stage06_numerical_reference(key):
    r = assert_check(C.ALL_CHECKS_STAGE06[key]())
    print(f"\n{r.name}: " + str({k: v for k, v in r.details.items() if k != "table"}))


def test_stage06_parity_null_and_access():
    for key in ("V11", "V12", "V14"):
        r = assert_check(C.ALL_CHECKS_STAGE06[key]())
        print(f"\n{r.name}: {r.details}")


@pytest.mark.slow
def test_stage06_tier1_regression_against_stored_stage05_items():
    r = assert_check(C.check_tier1_regression_stage05())
    print(f"\n{r.name}: {r.details}")


@pytest.mark.slow
def test_stage06_calibration_of_population_reference():
    r = assert_check(C.check_noisy_calibration())
    print(f"\n{r.name}: n_tests={r.details['n_tests']} min_p={r.details['min_p']:.2e} level={r.details['per_test_level']:.1e}")


@pytest.mark.slow
def test_stage06_bayes_optimality_counts_only():
    r = assert_check(C.check_noisy_optimality())
    print(f"\n{r.name}: {r.details}")
