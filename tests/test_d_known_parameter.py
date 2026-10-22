"""Section 5.D: known-parameter behaviour and posterior concentration rates."""

from dynaicl.validation import checks
from tests._util import assert_check


def test_d1_known_system_predictive_matches_closed_form_and_simulation():
    assert_check(checks.check_known_parameter_predictive())


def test_d2_posterior_variance_1_over_n_and_mean_error_n_to_minus_half():
    r = assert_check(checks.check_posterior_concentration())
    print("\nD2:", r.details)
