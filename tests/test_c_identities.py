"""Section 5.C: structural identities. A violation is a bug."""

from dynaicl.validation import checks
from tests._util import assert_check


def test_c1_sequential_and_batch_updating_agree():
    assert_check(checks.check_sequential_equals_batch())


def test_c2_n0_reduces_to_prior_predictive():
    assert_check(checks.check_n0_prior_predictive())


def test_c3_single_atom_library_equals_known_system():
    assert_check(checks.check_single_atom_library_equals_known_system())


def test_c4_chain_rule_h2_equals_marginalised_one_step():
    assert_check(checks.check_chain_rule_h2())
