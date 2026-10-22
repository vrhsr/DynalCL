"""Known-system predictor: x_{n+h} | x_n ~ N(a^h x_n, sigma^2 c_h(a)). ANALYTICALLY EXACT.

This is an ORACLE: it reads the true parameters. It is used only in tests (Section 5.C/5.D) and is
never entered into an evaluation as a competitor.
"""

from __future__ import annotations

import numpy as np

from dynaicl.references.base import Predictor, PredictorDescription
from dynaicl.references.predictive import GaussianPredictive
from dynaicl.systems import ar1
from dynaicl.systems.context import ContextWindow


class KnownSystemPredictor(Predictor):
    def __init__(self, a: float, sigma: float):
        if not sigma > 0:
            raise ValueError("sigma must be > 0")
        self.a = float(a)
        self.sigma = float(sigma)
        self.description = PredictorDescription(
            name="known_system_oracle",
            category="oracle",
            assumed_system_distribution=None,
            may_access=("context", "TRUE a and sigma (oracle; tests only)"),
            must_not_access=("future values",),
            uses_true_noise_scale=True,
            assumptions="parameters known exactly",
        )

    def _predict(self, context: ContextWindow, horizon: int) -> GaussianPredictive:
        c = float(ar1.horizon_variance_factor(self.a, horizon))
        mean = float(np.power(self.a, horizon)) * context.last
        ar1.require_representable(mean, self.sigma**2 * c, "known system")
        return GaussianPredictive(mean, self.sigma**2 * c)
