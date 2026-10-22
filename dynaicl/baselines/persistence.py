"""Persistence: point forecast x_n, with predictive variance from context increments (Section 2.5)."""

from __future__ import annotations

import numpy as np

from dynaicl.baselines.common import CONTEXT_ONLY_MUST_NOT_ACCESS, FallbackSettings, variance_floor
from dynaicl.references.base import Predictor, PredictorDescription
from dynaicl.references.predictive import GaussianPredictive
from dynaicl.systems.context import ContextWindow


def persistence_variance(x: np.ndarray, h: int, fallback: FallbackSettings) -> tuple[float, str]:
    """Mean squared h-step increment within the context.

    n >= h      : mean (x_t - x_{t-h})^2 over t = h..n   (the in-context MSE of the persistence rule)
    1 <= n < h  : h * mean (x_t - x_{t-1})^2             (random-walk scaling; documented heuristic)
    n = 0       : h * fallback.predictive_variance        (config-fixed)
    """
    n = x.shape[0] - 1
    if n >= h:
        d = x[h:] - x[:-h]
        v, how = float(np.mean(d * d)), "h_step_increments"
    elif n >= 1:
        d = np.diff(x)
        v, how = float(h * np.mean(d * d)), "one_step_increments_scaled"
    else:
        v, how = float(h * fallback.predictive_variance), "fallback"
    return max(v, variance_floor(x, fallback.variance_relative_floor)), how


class PersistencePredictor(Predictor):
    def __init__(self, fallback: FallbackSettings = FallbackSettings()):
        self.fallback = fallback
        self.description = PredictorDescription(
            name="persistence", category="context-only", assumed_system_distribution=None,
            may_access=("context", "config hyperparameters"), must_not_access=CONTEXT_ONLY_MUST_NOT_ACCESS,
            uses_true_noise_scale=False,
            assumptions="x_{n+h} ~ N(x_n, v); v = mean squared h-step increment in the context",
        )

    def _predict(self, context: ContextWindow, horizon: int) -> GaussianPredictive:
        x = context.values
        v, how = persistence_variance(x, horizon, self.fallback)
        return GaussianPredictive(context.last, v, info={"variance_rule": how, "fallback": how == "fallback"})
