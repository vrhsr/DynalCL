"""Finite-library posterior predictor (docs/MATH.md section 6). ANALYTICALLY EXACT given the library.

w_k(D) is proportional to pi_k * prod_t N(x_t; a_k x_{t-1}, sigma_k^2), computed in log space with
residuals summed directly. The h-step predictive is sum_k w_k N(a_k^h x_n, sigma_k^2 c_h(a_k)).
"""

from __future__ import annotations

import math

import numpy as np
from scipy import special

from dynaicl.references.base import Predictor, PredictorDescription
from dynaicl.references.predictive import GaussianMixturePredictive
from dynaicl.systems import ar1
from dynaicl.systems.context import ContextWindow
from dynaicl.systems.library import SystemLibrary


class FiniteLibraryPredictor(Predictor):
    """Bayes predictor that treats the library (atoms + weights) as the system distribution."""

    def __init__(self, library: SystemLibrary):
        if not isinstance(library, SystemLibrary):
            raise TypeError("FiniteLibraryPredictor requires a SystemLibrary")
        self.library = library
        self._log_prior = np.log(library.weights)
        self._log_two_pi_var = np.log(2.0 * math.pi * library.noise_scales**2)
        self.description = PredictorDescription(
            name="finite_library",
            category="finite-library",
            assumed_system_distribution=library.fingerprint(),
            may_access=("context", "library atoms and weights (training stream only)"),
            must_not_access=("true a", "future values", "evaluation systems under E-CONT"),
            uses_true_noise_scale=True,
            assumptions="system is exactly one of the K atoms, chosen with probability pi_k",
        )

    def posterior_log_weights(self, context: ContextWindow) -> np.ndarray:
        prev, curr = ar1.transition_pairs(context.values)
        n = curr.shape[0]
        a = self.library.coefficients
        s2 = self.library.noise_scales**2
        resid = curr[None, :] - a[:, None] * prev[None, :]
        rss = np.einsum("kt,kt->k", resid, resid)
        loglik = -0.5 * n * self._log_two_pi_var - 0.5 * rss / s2
        lw = self._log_prior + loglik
        return lw - special.logsumexp(lw)

    def _predict(self, context: ContextWindow, horizon: int) -> GaussianMixturePredictive:
        lw = self.posterior_log_weights(context)
        a = self.library.coefficients
        with np.errstate(over="ignore", invalid="ignore"):
            means = np.power(a, horizon) * context.last
            variances = self.library.noise_scales**2 * ar1.horizon_variance_factor(a, horizon)
        ar1.require_representable(means, variances, "finite library")
        return GaussianMixturePredictive(lw, means, variances, info={"K": self.library.size})
