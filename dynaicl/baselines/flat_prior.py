"""Flat-prior Bayes with known sigma (Section 2.5; docs/MATH.md section 7.1).

Posterior N(a_hat, sigma^2 / S_xx) with a_hat = S_xy / S_xx. One-step predictive
N(a_hat x_n, sigma^2 (1 + x_n^2 / S_xx)) (ANALYTICALLY EXACT for the flat prior). h > 1 uses the
same quadrature as P-GAUSS.

S_xx = 0 (always the case for n = 0; for n >= 1 it means x_0 = ... = x_{n-1} = 0) makes the
flat-prior posterior improper. In that case a config-fixed proper prior N(fallback mean,
fallback variance) is used instead, and the prediction is flagged ``fallback``.

Information note: sigma is passed in as a config hyperparameter equal to the condition's sigma.
This is population information about the noise scale, though not about ``a``. The predictor
is therefore flagged ``uses_true_noise_scale`` and excluded from the strict frontier.
"""

from __future__ import annotations

from dynaicl.baselines.common import CONTEXT_ONLY_MUST_NOT_ACCESS, FallbackSettings
from dynaicl.references.base import Predictor, PredictorDescription
from dynaicl.references.conjugate import gaussian_coefficient_horizon_predictive
from dynaicl.references.predictive import Predictive
from dynaicl.references.quadrature import QuadratureSettings
from dynaicl.systems import ar1
from dynaicl.systems.context import ContextWindow


class FlatPriorBayesPredictor(Predictor):
    def __init__(self, sigma: float, settings: QuadratureSettings = QuadratureSettings(),
                 fallback: FallbackSettings = FallbackSettings()):
        if not sigma > 0:
            raise ValueError("sigma must be > 0")
        self.sigma = float(sigma)
        self.settings = settings
        self.fallback = fallback
        self.description = PredictorDescription(
            name="flat_prior_bayes", category="context-only", assumed_system_distribution=None,
            may_access=("context", "config hyperparameters", "sigma (config-fixed; equals the condition's sigma)"),
            must_not_access=CONTEXT_ONLY_MUST_NOT_ACCESS, uses_true_noise_scale=True,
            assumptions="flat (improper) prior on a; sigma known; proper fallback prior when S_xx = 0",
        )

    def coefficient_posterior(self, context: ContextWindow) -> tuple[float, float, bool]:
        s_xx, s_xy, _, _ = ar1.sufficient_statistics(context.values)
        if s_xx > 0.0:
            return s_xy / s_xx, self.sigma**2 / s_xx, False
        return self.fallback.coefficient_mean, self.fallback.coefficient_variance, True

    def _predict(self, context: ContextWindow, horizon: int) -> Predictive:
        m, v, used_fallback = self.coefficient_posterior(context)
        return gaussian_coefficient_horizon_predictive(m, v, context.last, self.sigma, horizon, self.settings,
                                                       info={"fallback": used_fallback})
