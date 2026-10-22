"""Section 5.A: algebra vs independent checks (grids, closed forms, quadrature convergence).

Tolerances: 10x the measured numerical error of both methods plus a float64 floor. The derivations
are in the docstrings of dynaicl/validation/checks.py and in docs/MATH.md section 8.
"""

from dynaicl.validation import checks
from tests._util import assert_check


def test_a1_gaussian_reference_matches_raw_likelihood_grid():
    assert_check(checks.check_gaussian_reference_vs_grid())


def test_a2_stable_quadrature_matches_truncnorm_closed_form_and_grid():
    assert_check(checks.check_stable_reference_vs_closed_form_and_grid())


def test_a3_quadrature_converges_in_node_count_including_hard_regimes():
    r = assert_check(checks.check_quadrature_convergence())
    print("\nA3 worst regime:", r.details["worst"])


def test_a4_closed_form_equals_quadrature_at_h1():
    assert_check(checks.check_closed_form_vs_quadrature_h1())


def test_a5_nig_matches_2d_numerical_integration():
    assert_check(checks.check_nig_vs_2d_grid())


def test_a6_library_weights_match_raw_likelihood():
    assert_check(checks.check_library_vs_raw_likelihood())
