"""Section 5.H: numerical edge cases. No NaN or inf anywhere, except a variance that is mathematically
infinite (Student-t with dof <= 2). Non-float64 input is rejected. pyproject.toml turns every
RuntimeWarning (overflow, invalid, divide) into an error, so silent overflow also fails these tests."""

import math

import numpy as np
import pytest

from dynaicl.baselines.family import build_context_only_family
from dynaicl.references.library import FiniteLibraryPredictor
from dynaicl.references.matched import continuous_prior_predictor
from dynaicl.references.predictive import StudentTPredictive
from dynaicl.systems.context import ContextWindow
from dynaicl.systems.library import SystemLibrary
from dynaicl.systems.priors import GaussianCoefficientPrior, NormalInverseGammaPrior, StableCoefficientPrior
from dynaicl.validation.checks import _simulate_context


def assert_finite_predictive(pred, label=""):
    m = pred.mean()
    v = pred.variance()
    assert math.isfinite(m), f"{label}: mean {m}"
    if isinstance(pred, StudentTPredictive) and pred.dof <= 2:
        assert v == math.inf, f"{label}: dof<=2 variance must be +inf"
        sd = math.sqrt(pred.scale2)
    else:
        assert math.isfinite(v) and v > 0, f"{label}: variance {v}"
        sd = math.sqrt(v)
    ys = np.array([m - 50 * sd, m - 3 * sd, m, m + 3 * sd, m + 50 * sd, 0.0])
    lp = np.asarray(pred.logpdf(ys))
    cdf = np.asarray(pred.cdf(ys))
    assert np.all(np.isfinite(lp)), f"{label}: logpdf {lp}"
    assert np.all((cdf >= 0) & (cdf <= 1)) and np.all(np.isfinite(cdf)), f"{label}: cdf {cdf}"
    q = pred.quantile(np.array([0.025, 0.5, 0.975]))
    assert np.all(np.isfinite(q)) and q[0] <= q[1] <= q[2], f"{label}: quantiles {q}"


def all_predictors(sigma=1.0):
    preds = {
        "gauss": continuous_prior_predictor(GaussianCoefficientPrior(0.2, 0.3, sigma)),
        "stable_tn": continuous_prior_predictor(StableCoefficientPrior(0.95, sigma, "truncated_normal", 0.4, 0.3)),
        "stable_u": continuous_prior_predictor(StableCoefficientPrior(0.95, sigma)),
        "library": FiniteLibraryPredictor(SystemLibrary(np.array([-0.9, 0.0, 0.5, 0.99]), np.full(4, sigma),
                                                        np.full(4, 0.25))),
    }
    preds.update(build_context_only_family(sigma))
    return preds


NIG = continuous_prior_predictor(NormalInverseGammaPrior(0.2, 10.0, 3.0, 2.0))


@pytest.mark.parametrize("n", [0, 1, 2])
@pytest.mark.parametrize("h", [1, 5, 50])
def test_h_short_contexts(n, h):
    x = _simulate_context(0.5, 1.0, n, np.random.default_rng(n + 10 * h))
    ctx = ContextWindow(x)
    for name, p in all_predictors().items():
        assert_finite_predictive(p.predict(ctx, h), f"{name} n={n} h={h}")
    if h == 1:
        assert_finite_predictive(NIG.predict(ctx, 1), "nig")


@pytest.mark.parametrize("values", [[0.0, 0.3], [0.0, 0.0, 0.5], [0.0]])
def test_h_sxx_zero_uses_flagged_fallbacks(values):
    ctx = ContextWindow(np.array(values))
    preds = all_predictors()
    for name, p in preds.items():
        for h in (1, 3):
            assert_finite_predictive(p.predict(ctx, h), f"{name} S_xx=0")
    assert preds["flat_prior_bayes"].predict(ctx, 1).info["fallback"] is True
    assert preds["ols_gaussian"].predict(ctx, 1).info["fallback"] is True


@pytest.mark.parametrize("sigma", [1e-6, 1e3])
def test_h_extreme_noise_scales(sigma):
    x = _simulate_context(0.6, sigma, 30, np.random.default_rng(3), x0=sigma)
    ctx = ContextWindow(x)
    for name, p in all_predictors(sigma).items():
        for h in (1, 5):
            assert_finite_predictive(p.predict(ctx, h), f"{name} sigma={sigma}")


@pytest.mark.parametrize("a_true", [0.999, -0.999, 1.1])
def test_h_unit_root_and_explosive_data(a_true):
    x = _simulate_context(a_true, 1.0, 200, np.random.default_rng(4), x0=1.0)
    ctx = ContextWindow(x)
    for name, p in all_predictors().items():
        for h in (1, 10, 50):
            assert_finite_predictive(p.predict(ctx, h), f"{name} a={a_true} h={h}")


def test_h_large_state_magnitude():
    """State far from equilibrium relative to sigma: x_0 = 1e6, sigma = 1, a = 0.9 (x_n ~ 1e6 * 0.9^n)."""
    x = _simulate_context(0.9, 1.0, 20, np.random.default_rng(5), x0=1e6)
    ctx = ContextWindow(x)
    for name, p in all_predictors().items():
        for h in (1, 50):
            assert_finite_predictive(p.predict(ctx, h), f"{name} x_0=1e6 h={h}")


def test_h_outlier_jump_is_finite_or_explicitly_unrepresentable():
    """A single jump to x_n = 1e6 after O(1) values makes P-GAUSS's posterior mean of a ~1e5. The 50-step
    predictive variance (~a^98) then exceeds float64. The required behaviour is an explicit
    FloatingPointError, never a silent inf/NaN. h = 1 is always representable."""
    x = _simulate_context(0.9, 1.0, 20, np.random.default_rng(5))
    x[-1] = 1e6
    ctx = ContextWindow(x)
    for name, p in all_predictors().items():
        assert_finite_predictive(p.predict(ctx, 1), f"{name} outlier h=1")
        try:
            pred = p.predict(ctx, 50)
        except FloatingPointError as exc:
            assert "not representable" in str(exc)
            continue
        assert_finite_predictive(pred, f"{name} outlier h=50")


def test_h_horizon_50_near_unit_root():
    x = _simulate_context(0.98, 1.0, 10, np.random.default_rng(6))
    ctx = ContextWindow(x)
    for name, p in all_predictors().items():
        pred = p.predict(ctx, 50)
        assert_finite_predictive(pred, name)
        if "quadrature" in pred.info:
            assert not pred.info["quadrature"]["capped"], f"{name}: quadrature hit max_panels"


def test_h_logsumexp_underflow_long_context_distant_atoms():
    """n = 5000 transitions from a = 0.9: the a = -0.9 atom's log weight is about -1e4, so its weight
    underflows exp() in float64. Everything must stay finite, including logpdf far from every component."""
    lib = SystemLibrary(np.array([-0.9, 0.9]), np.array([1.0, 1.0]), np.array([0.5, 0.5]))
    x = _simulate_context(0.9, 1.0, 5000, np.random.default_rng(7))
    pred_obj = FiniteLibraryPredictor(lib)
    lw = pred_obj.posterior_log_weights(ContextWindow(x))
    assert np.all(np.isfinite(lw)) and lw.max() == 0.0 and lw.min() < -1000
    pred = pred_obj.predict(ContextWindow(x), 3)
    assert np.isfinite(pred.logpdf(1e4)) and pred.logpdf(1e4) < -1e6
    assert_finite_predictive(pred, "library underflow")


@pytest.mark.parametrize("bad", [np.array([1.0, 2.0], dtype=np.float32), np.array([1, 2]), [1.0, 2.0],
                                 np.array([[1.0, 2.0]])])
def test_h_non_float64_or_malformed_input_rejected(bad):
    with pytest.raises((TypeError, ValueError)):
        ContextWindow(bad)


@pytest.mark.parametrize("bad", [np.array([1.0, np.nan]), np.array([np.inf])])
def test_h_non_finite_input_rejected(bad):
    with pytest.raises(ValueError):
        ContextWindow(bad)


def test_h_explosive_probability_p_gauss_reported_and_correct():
    """P(abs(a) >= 1) under the test P-GAUSS (mu0 = 0.2, tau0 = 0.3) is closed form; checked against MC
    (1e6 draws, 5 SE)."""
    prior = GaussianCoefficientPrior(0.2, 0.3, 1.0)
    p = prior.explosive_probability()
    a, _ = prior.sample_systems(np.random.default_rng(8), 1_000_000)
    mc = float(np.mean(np.abs(a) >= 1))
    se = math.sqrt(p * (1 - p) / a.size)
    print(f"\nP-GAUSS(mu0=0.2, tau0=0.3): P(|a|>=1) = {p:.5f} (MC {mc:.5f})")
    assert abs(mc - p) <= 5 * se
    assert p < 0.005
