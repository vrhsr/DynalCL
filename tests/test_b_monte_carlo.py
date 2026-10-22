"""Section 5.B: independent Monte Carlo (prior importance sampling + forward simulation)."""

from dynaicl.validation import checks
from tests._util import assert_check


def test_b1_predictive_moments_and_quantiles_match_importance_sampling():
    r = assert_check(checks.check_predictive_monte_carlo())
    print(f"\nB1 max |z| = {r.details['max_abs_z']:.2f} (z_crit {r.details['z_crit']:.2f}), "
          f"min ESS = {r.details['min_ess']:.0f}")


def test_b2_library_posterior_matches_importance_sampling():
    assert_check(checks.check_library_importance_sampling())
