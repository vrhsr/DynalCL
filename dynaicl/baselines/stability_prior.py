"""Generic-stability Bayes: a context-only predictor that knows only that the system is stable (Stage 0.5).

Prior a ~ Uniform(-b, b) with a config-fixed bound b close to 1 (default 0.999), and known sigma. It uses
no population information: no data from any system, and no parameter of the population prior. It
encodes only the structural fact that the systems are stationary. It counts as context-only under
the Stage 0 definition (context plus config-fixed hyperparameters).

Why it exists: at short contexts, part of the matched reference's advantage over flat-prior Bayes
may come from this generic constraint rather than from population knowledge. Including it in the
frontier makes the primary Stage 0.5 contrast measure population-specific knowledge
(docs/PREREG_stage05.md, docs/DECISIONS.md D-25). It is flagged ``uses_true_noise_scale`` and
therefore excluded from the strict frontier.

NUMERICALLY APPROXIMATED with verified convergence: it reuses the P-STABLE quadrature machinery.
"""

from __future__ import annotations

from dynaicl.baselines.common import CONTEXT_ONLY_MUST_NOT_ACCESS
from dynaicl.references.base import Predictor, PredictorDescription
from dynaicl.references.quadrature import QuadratureSettings, StablePriorQuadraturePredictor
from dynaicl.systems.context import ContextWindow
from dynaicl.systems.priors import StableCoefficientPrior


class StabilityPriorBayesPredictor(Predictor):
    def __init__(self, sigma: float, bound: float = 0.999, settings: QuadratureSettings = QuadratureSettings()):
        if not 0.0 < bound < 1.0:
            raise ValueError("stability bound must be in (0, 1)")
        self.bound = float(bound)
        self._inner = StablePriorQuadraturePredictor(StableCoefficientPrior(rho=bound, sigma=sigma, shape="uniform"),
                                                     settings)
        self.description = PredictorDescription(
            name="stability_prior_bayes", category="context-only", assumed_system_distribution=None,
            may_access=("context", "config hyperparameters", "sigma (config-fixed; equals the condition's sigma)",
                        f"generic stability bound abs(a) < {bound}"),
            must_not_access=CONTEXT_ONLY_MUST_NOT_ACCESS, uses_true_noise_scale=True,
            assumptions="uniform prior on (-bound, bound): generic stationarity only, no population information",
        )

    def with_settings(self, settings: QuadratureSettings) -> "StabilityPriorBayesPredictor":
        return StabilityPriorBayesPredictor(self._inner.prior.sigma, self.bound, settings)

    def _predict(self, context: ContextWindow, horizon: int):
        return self._inner.predict(context, horizon)
