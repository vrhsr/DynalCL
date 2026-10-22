"""OLS plug-in predictor (Section 2.5; docs/MATH.md section 7.2). NON-BAYESIAN.

a_hat = S_xy / S_xx and sigma_hat^2 = RSS(a_hat) / (n - 1).

* Gaussian variant: N(a_hat^h x_n, sigma_hat^2 c_h(a_hat)). Ignores parameter uncertainty, so it is
  potentially overconfident at short n.
* Student-t variant: t_{n-1}(a_hat^h x_n, sigma_hat^2 [c_h(a_hat) + (h a_hat^{h-1} x_n)^2 / S_xx]).
  At h = 1 this is the classical prediction distribution (also the Bayes predictive under
  p(a, sigma^2) proportional to 1/sigma^2). For h > 1 the parameter-uncertainty term is a
  delta-method heuristic.

When n < min_transitions or S_xx = 0 the estimator is undefined, and the predictor falls back to the
persistence predictive. The fallback is flagged.
"""

from __future__ import annotations

import numpy as np

from dynaicl.baselines.common import CONTEXT_ONLY_MUST_NOT_ACCESS, FallbackSettings, variance_floor
from dynaicl.baselines.persistence import persistence_variance
from dynaicl.references.base import Predictor, PredictorDescription
from dynaicl.references.predictive import GaussianPredictive, Predictive, StudentTPredictive
from dynaicl.systems import ar1
from dynaicl.systems.context import ContextWindow


class OlsPlugInPredictor(Predictor):
    def __init__(self, variant: str = "gaussian", min_transitions: int = 3,
                 fallback: FallbackSettings = FallbackSettings()):
        if variant not in ("gaussian", "student_t"):
            raise ValueError("variant must be 'gaussian' or 'student_t'")
        if min_transitions < 2:
            raise ValueError("OLS needs min_transitions >= 2 (sigma_hat uses n - 1)")
        self.variant = variant
        self.min_transitions = int(min_transitions)
        self.fallback = fallback
        self.description = PredictorDescription(
            name=f"ols_{variant}", category="context-only", assumed_system_distribution=None,
            may_access=("context", "config hyperparameters"), must_not_access=CONTEXT_ONLY_MUST_NOT_ACCESS,
            uses_true_noise_scale=False,
            assumptions="NON-BAYESIAN plug-in; potentially overconfident at short n",
        )

    def _predict(self, context: ContextWindow, horizon: int) -> Predictive:
        x = context.values
        s_xx, s_xy, _, n = ar1.sufficient_statistics(x)
        if n < self.min_transitions or s_xx <= 0.0:
            v, how = persistence_variance(x, horizon, self.fallback)
            return GaussianPredictive(context.last, v, info={"fallback": True, "fallback_rule": "persistence/" + how})
        a_hat = s_xy / s_xx
        rss = float(ar1.residual_sum_of_squares(x, a_hat))
        s2 = max(rss / (n - 1), variance_floor(x, self.fallback.variance_relative_floor))
        a = np.float64(a_hat)
        with np.errstate(over="ignore", invalid="ignore"):   # overflow -> inf, turned into an explicit error
            c_h = ar1.horizon_variance_factor(a, horizon)
            loc = np.power(a, horizon) * context.last
            grad = horizon * np.power(a, horizon - 1) * context.last
            var_t = s2 * (c_h + grad * grad / s_xx)
        ar1.require_representable(loc, var_t, f"OLS (a_hat={a_hat:.3g})")
        info = {"fallback": False, "a_hat": a_hat, "sigma2_hat": s2}
        if self.variant == "gaussian":
            return GaussianPredictive(float(loc), float(s2 * c_h), info=info)
        return StudentTPredictive(float(loc), float(var_t), float(n - 1), info=info)
