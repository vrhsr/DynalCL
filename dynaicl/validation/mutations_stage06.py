"""Stage 0.6 negative controls: each injected bug must be detected by at least one check in checks_stage06."""

from __future__ import annotations

import contextlib

from dynaicl.baselines.stability_prior import StabilityPriorBayesPredictor
from dynaicl.evaluation import noisy_harness as nh
from dynaicl.references import kalman_quadrature as kq
from dynaicl.systems.context import ContextWindow
from dynaicl.systems.noisy import NoisyObservationModel
from dynaicl.systems.priors import StableCoefficientPrior
from dynaicl.validation.mutations import _patched


@contextlib.contextmanager
def omit_target_noise_variance():
    """MANDATORY: the observation-target predictive variance omits sigma_v^2 (the classic bug)."""
    def bad(a, m, P, model, h):
        mean, var = kq.latent_predictive_moments(a, m, P, model, h)
        return mean, var
    with _patched(kq, "observation_predictive_moments", bad):
        yield


@contextlib.contextmanager
def wrong_sigma_v_in_reference():
    """The population-aware reference uses sigma_v x 1.5 + 0.1 internally, while still declaring the true model."""
    original = kq.noisy_population_reference

    def bad(prior, model, settings=kq.KalmanQuadratureSettings()):
        wrong = NoisyObservationModel(model.sigma_w, 1.5 * model.sigma_v + 0.1, model.x0_sd)
        p = original(prior, wrong, settings)
        p.description = original(prior, model, settings).description
        return p
    with _patched(kq, "noisy_population_reference", bad):
        yield


@contextlib.contextmanager
def prior_mismatch_in_reference():
    """The population-aware reference silently uses a different prior (truncated normal, tau0 = 0.6) whatever it is
    given, while keeping the declared fingerprint."""
    original = kq.noisy_population_reference

    def bad(prior, model, settings=kq.KalmanQuadratureSettings()):
        wrong = StableCoefficientPrior(rho=0.95, sigma=model.sigma_w, shape="truncated_normal", mu0=0.4, tau0=0.6)
        p = original(wrong, model, settings)
        p.description = original(prior, model, settings).description
        return p
    with _patched(kq, "noisy_population_reference", bad):
        yield


@contextlib.contextmanager
def latent_state_passed_to_predictor():
    """Contexts are cut from the LATENT path instead of the observations."""
    with _patched(nh, "noisy_context_source", lambda split: split.latent.trajectories):
        yield


@contextlib.contextmanager
def off_by_one_context_length():
    """The observed context includes one extra value (y_0..y_{n+1})."""
    with _patched(nh, "make_noisy_context",
                  lambda row, n: ContextWindow(row[: n + 2].astype(float, copy=True))):
        yield


@contextlib.contextmanager
def off_by_one_target_index():
    """The target is y_{n+h+1} instead of y_{n+h}."""
    with _patched(nh, "target_index", lambda n, h: n + h + 1):
        yield


class _MislabeledNaiveStability(StabilityPriorBayesPredictor):
    """A noise-NAIVE Stage 0.5 stability predictor carrying the noise-aware comparator's description."""

    def __init__(self, model, bound, settings):
        super().__init__(model.sigma_w, bound)
        self.description = _ORIGINAL_STABILITY(model, bound, settings).description
        self.model = model
        self.settings = settings


_ORIGINAL_STABILITY = kq.noise_aware_stability_predictor


@contextlib.contextmanager
def noise_naive_mislabeled_as_noise_aware():
    """The primary comparator is replaced by the noise-naive Stage 0.5 predictor, labelled noise-aware."""
    def bad(model, bound=0.999, settings=kq.KalmanQuadratureSettings()):
        return _MislabeledNaiveStability(model, bound, settings)
    with _patched(kq, "noise_aware_stability_predictor", bad):
        yield


MUTATIONS_STAGE06 = {
    "omit_target_noise_variance": omit_target_noise_variance,
    "wrong_sigma_v_in_reference": wrong_sigma_v_in_reference,
    "prior_mismatch_in_reference": prior_mismatch_in_reference,
    "latent_state_passed_to_predictor": latent_state_passed_to_predictor,
    "off_by_one_context_length": off_by_one_context_length,
    "off_by_one_target_index": off_by_one_target_index,
    "noise_naive_mislabeled_as_noise_aware": noise_naive_mislabeled_as_noise_aware,
}
