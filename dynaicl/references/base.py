"""Predictor base class: interface enforcement and declared information access (Section 3)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from dynaicl.references.predictive import PointForecast, Predictive
from dynaicl.systems.context import ContextWindow


@dataclass(frozen=True)
class PredictorDescription:
    """What a predictor assumes and what it may access.

    ``assumed_system_distribution`` is the fingerprint of the system distribution (with likelihood)
    the predictor treats as true, or ``None`` for predictors that use no population information.
    Only a predictor whose fingerprint equals a condition's may serve as that condition's matched
    reference.
    """

    name: str
    category: str                      # "continuous-prior-bayes" | "finite-library" | "context-only" | "oracle"
    assumed_system_distribution: str | None
    may_access: tuple[str, ...]
    must_not_access: tuple[str, ...]
    uses_true_noise_scale: bool
    assumptions: str
    #: Stage 0.6: the observation model the predictor assumes. "noise-free" (Stages 0/0.5) or
    #: "additive-gaussian(sigma_v=...)". Used by the information-parity audit.
    observation_model: str = "noise-free"


class Predictor(ABC):
    """Maps an immutable ContextWindow (and a horizon) to a Predictive. Never sees GroundTruth."""

    description: PredictorDescription

    def predict(self, context: ContextWindow, horizon: int) -> Predictive | PointForecast:
        if not isinstance(context, ContextWindow):
            raise TypeError(f"predictors accept only ContextWindow, got {type(context).__name__}")
        if isinstance(horizon, bool) or not isinstance(horizon, int) or horizon < 1:
            raise ValueError("horizon must be an int >= 1")
        return self._predict(context, horizon)

    @abstractmethod
    def _predict(self, context: ContextWindow, horizon: int) -> Predictive | PointForecast: ...

    @property
    def name(self) -> str:
        return self.description.name


class PointPredictor(Predictor):
    """Wraps a point-forecast function. Scored with point metrics only (Section 2.6)."""

    def __init__(self, point_fn, description: PredictorDescription):
        self._point_fn = point_fn
        self.description = description

    def _predict(self, context: ContextWindow, horizon: int) -> PointForecast:
        return PointForecast(float(self._point_fn(context, horizon)))
