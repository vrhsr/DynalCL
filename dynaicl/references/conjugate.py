"""Conjugate references (docs/MATH.md sections 2 and 3).

* P-GAUSS, h = 1: ANALYTICALLY EXACT. Posterior N(m_n, v_n); predictive N(m_n x_n, sigma^2 + v_n x_n^2).
* P-GAUSS, h > 1: posterior still exact. The predictive mixes N(a^h x_n, sigma^2 c_h(a)) over
  N(m_n, v_n) by 1-D quadrature: NUMERICALLY APPROXIMATED with verified convergence.
* P-NIG, h = 1: ANALYTICALLY EXACT Student-t predictive. h > 1 is not implemented in Stage 0.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from scipy import special

from dynaicl.references.base import Predictor, PredictorDescription
from dynaicl.references.predictive import GaussianPredictive, Predictive, StudentTPredictive
from dynaicl.references.quadrature import QuadratureSettings, gaussian_coefficient_quadrature, horizon_mixture
from dynaicl.systems import ar1
from dynaicl.systems.context import ContextWindow
from dynaicl.systems.priors import GaussianCoefficientPrior, NormalInverseGammaPrior

FLOAT = np.float64


# --------------------------------------------------------------------------------------------- P-GAUSS


def gaussian_prior_moments(prior: GaussianCoefficientPrior) -> tuple[float, float]:
    """(prior mean, prior variance) of a. A single function so mutation tests can inject a wrong variance."""
    return float(prior.mu0), float(prior.tau0) ** 2


@dataclass(frozen=True)
class GaussianCoefficientPosterior:
    """a | D ~ N(mean, variance)."""

    mean: float
    variance: float

    def logpdf(self, a) -> np.ndarray:
        a = np.asarray(a, dtype=FLOAT)
        return -0.5 * math.log(2 * math.pi * self.variance) - 0.5 * (a - self.mean) ** 2 / self.variance

    def cdf(self, a) -> np.ndarray:
        return special.ndtr((np.asarray(a, dtype=FLOAT) - self.mean) / math.sqrt(self.variance))

    def sample(self, rng: np.random.Generator, size: int) -> np.ndarray:
        return self.mean + math.sqrt(self.variance) * rng.standard_normal(size)


def conjugate_gaussian_posterior(prior_mean: float, prior_variance: float, sigma: float,
                                 x: np.ndarray) -> GaussianCoefficientPosterior:
    """Batch update: 1/v_n = 1/tau0^2 + S_xx/sigma^2, m_n = v_n (mu0/tau0^2 + S_xy/sigma^2)."""
    s_xx, s_xy, _, _ = ar1.sufficient_statistics(x)
    precision = 1.0 / prior_variance + s_xx / sigma**2
    v = 1.0 / precision
    m = v * (prior_mean / prior_variance + s_xy / sigma**2)
    return GaussianCoefficientPosterior(float(m), float(v))


def conjugate_gaussian_sequential_update(post: GaussianCoefficientPosterior, x_prev: float, x_next: float,
                                         sigma: float) -> GaussianCoefficientPosterior:
    """One-transition update; used by the sequential-equals-batch identity test (Section 5.C)."""
    precision = 1.0 / post.variance + x_prev**2 / sigma**2
    v = 1.0 / precision
    m = v * (post.mean / post.variance + x_prev * x_next / sigma**2)
    return GaussianCoefficientPosterior(float(m), float(v))


def gaussian_coefficient_horizon_predictive(mean: float, variance: float, x_n: float, sigma: float, h: int,
                                            settings: QuadratureSettings, info: dict | None = None) -> Predictive:
    """Predictive of x_{n+h} when a ~ N(mean, variance) and sigma is known.

    h = 1: exact Gaussian N(mean x_n, sigma^2 + variance x_n^2).
    h > 1: quadrature mixture over a.
    """
    if h == 1:
        return GaussianPredictive(mean * x_n, sigma**2 + variance * x_n**2, info=info)
    post = gaussian_coefficient_quadrature(mean, variance, settings)
    return horizon_mixture(post, x_n, sigma, h, info=info)


class ConjugateGaussianAr1Predictor(Predictor):
    """Continuous-prior Bayes predictor under P-GAUSS."""

    def __init__(self, prior: GaussianCoefficientPrior, settings: QuadratureSettings = QuadratureSettings()):
        if not isinstance(prior, GaussianCoefficientPrior):
            raise TypeError("ConjugateGaussianAr1Predictor requires a GaussianCoefficientPrior")
        self.prior = prior
        self.settings = settings
        self.description = PredictorDescription(
            name="continuous_prior_bayes",
            category="continuous-prior-bayes",
            assumed_system_distribution=prior.fingerprint(),
            may_access=("context", "continuous prior P-GAUSS", "known sigma"),
            must_not_access=("true a", "future values", "library"),
            uses_true_noise_scale=True,
            assumptions="a ~ N(mu0, tau0^2) untruncated; sigma known; likelihood conditional on x_0",
        )

    def with_settings(self, settings: QuadratureSettings) -> "ConjugateGaussianAr1Predictor":
        return ConjugateGaussianAr1Predictor(self.prior, settings)

    def posterior(self, context: ContextWindow) -> GaussianCoefficientPosterior:
        mean0, var0 = gaussian_prior_moments(self.prior)
        return conjugate_gaussian_posterior(mean0, var0, self.prior.sigma, context.values)

    def _predict(self, context: ContextWindow, horizon: int) -> Predictive:
        post = self.posterior(context)
        return gaussian_coefficient_horizon_predictive(post.mean, post.variance, context.last, self.prior.sigma,
                                                       horizon, self.settings)


# ----------------------------------------------------------------------------------------------- P-NIG


@dataclass(frozen=True)
class NormalInverseGammaPosterior:
    """a | sigma^2, D ~ N(mu, sigma^2 / lam);  sigma^2 | D ~ InverseGamma(alpha, beta)."""

    mu: float
    lam: float
    alpha: float
    beta: float

    def coefficient_marginal(self) -> tuple[float, float, float]:
        """a | D ~ Student-t(dof = 2 alpha, loc = mu, scale^2 = beta / (alpha lam))."""
        return 2.0 * self.alpha, self.mu, self.beta / (self.alpha * self.lam)

    def coefficient_cdf(self, a) -> np.ndarray:
        dof, loc, s2 = self.coefficient_marginal()
        return special.stdtr(dof, (np.asarray(a, dtype=FLOAT) - loc) / math.sqrt(s2))

    def noise_variance_cdf(self, s2) -> np.ndarray:
        """P(sigma^2 <= s2 | D) = Q(alpha, beta / s2) (regularised upper incomplete gamma)."""
        return special.gammaincc(self.alpha, self.beta / np.asarray(s2, dtype=FLOAT))

    def sample(self, rng: np.random.Generator, size: int) -> tuple[np.ndarray, np.ndarray]:
        s2 = self.beta / rng.gamma(self.alpha, 1.0, size)
        a = self.mu + np.sqrt(s2 / self.lam) * rng.standard_normal(size)
        return a, s2


def nig_posterior(prior: NormalInverseGammaPrior, x: np.ndarray) -> NormalInverseGammaPosterior:
    """lambda_n = lambda0 + S_xx; mu_n = (lambda0 mu0 + S_xy)/lambda_n; alpha_n = alpha0 + n/2;
    beta_n = beta0 + 0.5 [RSS(mu_n) + lambda0 (mu_n - mu0)^2]. This form is equivalent to the spec's
    S_yy + lambda0 mu0^2 - lambda_n mu_n^2 but is free of cancellation (MATH.md section 3.1).
    """
    s_xx, s_xy, _, n = ar1.sufficient_statistics(x)
    lam = prior.lambda0 + s_xx
    mu = (prior.lambda0 * prior.mu0 + s_xy) / lam
    alpha = prior.alpha0 + 0.5 * n
    rss = float(ar1.residual_sum_of_squares(x, mu))
    beta = prior.beta0 + 0.5 * (rss + prior.lambda0 * (mu - prior.mu0) ** 2)
    return NormalInverseGammaPosterior(float(mu), float(lam), float(alpha), float(beta))


def nig_sequential_update(post: NormalInverseGammaPosterior, x_prev: float, x_next: float
                          ) -> NormalInverseGammaPosterior:
    lam = post.lam + x_prev**2
    mu = (post.lam * post.mu + x_prev * x_next) / lam
    alpha = post.alpha + 0.5
    beta = post.beta + 0.5 * ((x_next - mu * x_prev) ** 2 + post.lam * (mu - post.mu) ** 2)
    return NormalInverseGammaPosterior(float(mu), float(lam), float(alpha), float(beta))


class NormalInverseGammaAr1Predictor(Predictor):
    """Continuous-prior Bayes predictor under P-NIG (h = 1 only)."""

    def __init__(self, prior: NormalInverseGammaPrior):
        if not isinstance(prior, NormalInverseGammaPrior):
            raise TypeError("NormalInverseGammaAr1Predictor requires a NormalInverseGammaPrior")
        self.prior = prior
        self.description = PredictorDescription(
            name="continuous_prior_bayes",
            category="continuous-prior-bayes",
            assumed_system_distribution=prior.fingerprint(),
            may_access=("context", "continuous prior P-NIG"),
            must_not_access=("true a", "true sigma", "future values", "library"),
            uses_true_noise_scale=False,
            assumptions="(a, sigma^2) ~ NIG(mu0, lambda0, alpha0, beta0); likelihood conditional on x_0",
        )

    def posterior(self, context: ContextWindow) -> NormalInverseGammaPosterior:
        return nig_posterior(self.prior, context.values)

    def _predict(self, context: ContextWindow, horizon: int) -> Predictive:
        if horizon != 1:
            raise NotImplementedError("P-NIG predictive is implemented for h = 1 only in Stage 0")
        post = self.posterior(context)
        x_n = context.last
        return StudentTPredictive(post.mu * x_n, (post.beta / post.alpha) * (1.0 + x_n**2 / post.lam),
                                  2.0 * post.alpha)
