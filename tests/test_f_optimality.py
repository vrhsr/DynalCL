"""Section 5.F: the matched reference's mean log score is at least every other predictor's, within paired SE."""

import pytest

from dynaicl.validation import checks
from tests._util import assert_check


@pytest.mark.slow
def test_f_matched_reference_is_optimal_under_its_own_condition():
    r = assert_check(checks.check_matched_reference_optimality())
    print(f"\nF: {r.details['n_comparisons']} comparisons, z_crit {r.details['z_crit']:.2f}, "
          f"min z = {r.details['min_z']:.2f}")
