"""Matched Bayes reference selection and the prior-matching guard (Section 2.3).

The matched reference for a condition must use exactly that condition's system distribution and
likelihood. The guard compares fingerprints. Optimality diagnostics are refused for any reference
that is not matched to the condition being evaluated (evaluation/harness.py).
"""

from __future__ import annotations

from dynaicl.references.base import Predictor
from dynaicl.references.conjugate import ConjugateGaussianAr1Predictor, NormalInverseGammaAr1Predictor
from dynaicl.references.library import FiniteLibraryPredictor
from dynaicl.references.quadrature import QuadratureSettings, StablePriorQuadraturePredictor
from dynaicl.systems.conditions import ContinuousPriorCondition, EvaluationCondition, LibraryCondition
from dynaicl.systems.priors import GaussianCoefficientPrior, NormalInverseGammaPrior, StableCoefficientPrior


class UnmatchedReferenceError(RuntimeError):
    """A predictor was used as the matched reference for a condition whose prior it does not share."""


def continuous_prior_predictor(prior, settings: QuadratureSettings = QuadratureSettings()) -> Predictor:
    """The continuous-prior Bayes predictor for ``prior``. As a comparison predictor it may be evaluated
    under any condition, but it is optimal only under the E-CONT condition with this prior."""
    if isinstance(prior, GaussianCoefficientPrior):
        return ConjugateGaussianAr1Predictor(prior, settings)
    if isinstance(prior, NormalInverseGammaPrior):
        return NormalInverseGammaAr1Predictor(prior)
    if isinstance(prior, StableCoefficientPrior):
        return StablePriorQuadraturePredictor(prior, settings)
    raise TypeError(f"no continuous-prior predictor for {type(prior).__name__}")


def check_system_distribution(assumed: str | None, condition: EvaluationCondition, who: str) -> None:
    """The single fingerprint comparison behind every matching guard."""
    expected = condition.system_distribution_fingerprint()
    if assumed is None or assumed != expected:
        raise UnmatchedReferenceError(
            f"{who} assumes system distribution {assumed!r}, but condition {condition.name!r} draws from "
            f"{expected!r}; it cannot serve as the matched reference")


def assert_matched(predictor: Predictor, condition: EvaluationCondition) -> None:
    """Raise unless the predictor's assumed system distribution is the condition's."""
    check_system_distribution(predictor.description.assumed_system_distribution, condition,
                              f"predictor {predictor.name!r}")


class MatchedBayesReference:
    """A (condition, predictor) pair verified to share prior and likelihood."""

    def __init__(self, condition: EvaluationCondition, predictor: Predictor):
        assert_matched(predictor, condition)
        self.condition = condition
        self.predictor = predictor

    @property
    def name(self) -> str:
        return f"matched_reference[{self.condition.name}]"

    def verify(self, condition: EvaluationCondition) -> None:
        """Re-check at use time: the stored condition and the predictor both match ``condition``."""
        if self.condition.fingerprint() != condition.fingerprint():
            raise UnmatchedReferenceError("reference was built for a different evaluation condition")
        assert_matched(self.predictor, condition)


def matched_reference_for(condition: EvaluationCondition,
                          settings: QuadratureSettings = QuadratureSettings()) -> MatchedBayesReference:
    """Select the matched Bayes reference by condition."""
    if isinstance(condition, ContinuousPriorCondition):
        return MatchedBayesReference(condition, continuous_prior_predictor(condition.prior, settings))
    if isinstance(condition, LibraryCondition):
        return MatchedBayesReference(condition, FiniteLibraryPredictor(condition.library))
    raise TypeError(f"unknown condition type {type(condition).__name__}")
