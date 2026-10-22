"""Prior-matching rule (Section 2.3): reference selection by condition, and refusal of unmatched references."""

import numpy as np
import pytest

from dynaicl.baselines.family import build_context_only_family
from dynaicl.evaluation import harness
from dynaicl.references.library import FiniteLibraryPredictor
from dynaicl.references.matched import (
    MatchedBayesReference,
    UnmatchedReferenceError,
    continuous_prior_predictor,
    matched_reference_for,
)
from dynaicl.rng import NamedStreams
from dynaicl.systems.conditions import ContinuousPriorCondition, LibraryCondition
from dynaicl.systems.library import build_library_from_prior
from dynaicl.systems.priors import StableCoefficientPrior
from dynaicl.systems.splits import SplitRole, generate_split
from dynaicl.validation.checks import P_STABLE_TN, P_STABLE_U, X0


@pytest.fixture(scope="module")
def setup():
    lib = build_library_from_prior(P_STABLE_TN, 8, NamedStreams(1))
    cont = ContinuousPriorCondition(P_STABLE_TN, X0)
    libc = LibraryCondition(lib, X0)
    return lib, cont, libc


def test_reference_selected_by_condition(setup):
    lib, cont, libc = setup
    assert matched_reference_for(cont).predictor.description.assumed_system_distribution == P_STABLE_TN.fingerprint()
    ref = matched_reference_for(libc)
    assert isinstance(ref.predictor, FiniteLibraryPredictor)
    assert ref.predictor.description.assumed_system_distribution == lib.fingerprint()


def test_unmatched_reference_is_refused(setup):
    lib, cont, libc = setup
    with pytest.raises(UnmatchedReferenceError):
        MatchedBayesReference(libc, continuous_prior_predictor(P_STABLE_TN))
    with pytest.raises(UnmatchedReferenceError):
        MatchedBayesReference(cont, FiniteLibraryPredictor(lib))
    with pytest.raises(UnmatchedReferenceError):   # a different prior (same family) is also unmatched
        MatchedBayesReference(cont, continuous_prior_predictor(P_STABLE_U))
    with pytest.raises(UnmatchedReferenceError):   # context-only predictors assume no system distribution
        MatchedBayesReference(cont, build_context_only_family(1.0)["flat_prior_bayes"])


def test_optimality_diagnostics_refuse_reference_from_another_condition(setup):
    lib, cont, libc = setup
    split = generate_split(libc, SplitRole.EVALUATION, NamedStreams(2), 20, 8)
    es = harness.build_evaluation_set(libc, split, 4, 1)
    wrong_ref = matched_reference_for(cont)   # matched to E-CONT, used on E-LIB data
    tab = harness.score_predictor(wrong_ref.predictor, es)
    with pytest.raises(UnmatchedReferenceError):
        harness.optimality_diagnostics(wrong_ref, es, tab, {}, 4.0)


def test_optimality_diagnostics_refuse_unpaired_tables(setup):
    lib, cont, libc = setup
    s1 = generate_split(cont, SplitRole.EVALUATION, NamedStreams(3), 20, 8)
    s2 = generate_split(cont, SplitRole.EVALUATION, NamedStreams(4), 20, 8)
    es1, es2 = harness.build_evaluation_set(cont, s1, 4, 1), harness.build_evaluation_set(cont, s2, 4, 1)
    ref = matched_reference_for(cont)
    with pytest.raises(ValueError):
        harness.optimality_diagnostics(ref, es1, harness.score_predictor(ref.predictor, es1),
                                       {"other": harness.score_predictor(FiniteLibraryPredictor(lib), es2)}, 4.0)


def test_fingerprints_distinguish_priors_and_libraries():
    a = StableCoefficientPrior(0.95, 1.0, "truncated_normal", 0.4, 0.3)
    b = StableCoefficientPrior(0.95, 1.0, "truncated_normal", 0.4, 0.3)
    c = StableCoefficientPrior(0.95, 1.0, "truncated_normal", 0.4, 0.31)
    d = StableCoefficientPrior(0.95, 0.5, "truncated_normal", 0.4, 0.3)
    assert a.fingerprint() == b.fingerprint() != c.fingerprint() != d.fingerprint()
    lib = build_library_from_prior(a, 4, NamedStreams(5))
    from dynaicl.systems.library import SystemLibrary
    lib2 = SystemLibrary(lib.coefficients, lib.noise_scales, np.array([0.4, 0.2, 0.2, 0.2]))
    assert lib.fingerprint() != lib2.fingerprint()
