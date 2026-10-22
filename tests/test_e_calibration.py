"""Section 5.E: calibration of the MATCHED reference under each evaluation condition.

This is a pass condition for the matched reference only. For every other predictor, calibration is a
reported measurement (experiment outputs), not a test.
"""

from dynaicl.validation import checks
from tests._util import assert_check


def test_e_matched_reference_sbc_pit_and_coverage():
    r = assert_check(checks.check_matched_reference_calibration())
    print(f"\nE: {r.details['n_tests']} tests at per-test level {r.details['per_test_level']:.2e}; "
          f"min p = {r.details['min_p']:.4f}")
