"""Scoring rules and calibration helpers (Section 4)."""

import math

import numpy as np
import pytest
from scipy import stats

from dynaicl.metrics import calibration, scoring
from dynaicl.references.predictive import (
    GaussianMixturePredictive,
    GaussianPredictive,
    PointForecast,
    StudentTPredictive,
)

#: Numerical CRPS tolerance: quad's epsabs = 1e-12 and epsrel = 1e-10 over at most six pieces, so 1e-8
#: absolute leaves a margin of more than 100x.
CRPS_TOL = 1e-8


@pytest.mark.parametrize("mu,sd,y", [(0.0, 1.0, 0.3), (2.0, 0.1, 1.5), (-1.0, 5.0, 20.0), (0.0, 1e-3, 0.0)])
def test_numerical_crps_matches_gaussian_closed_form(mu, sd, y):
    g = GaussianPredictive(mu, sd**2)
    assert abs(scoring.crps_numerical(g, y) - scoring.crps_gaussian(mu, sd, y)) <= CRPS_TOL * max(1.0, sd)


def test_mixture_crps_closed_form_matches_numerical():
    rng = np.random.default_rng(0)
    for _ in range(5):
        k = 6
        mix = GaussianMixturePredictive(rng.normal(size=k), rng.normal(size=k) * 2, rng.uniform(0.1, 2, size=k) ** 2)
        for y in (-3.0, 0.0, 1.7):
            assert abs(scoring.crps_gaussian_mixture(mix, y) - scoring.crps_numerical(mix, y)) <= CRPS_TOL


def test_student_t_numerical_crps_matches_monte_carlo():
    """CRPS = E|X - y| - E|X - X'|/2 estimated with 2e6 draws; tolerance 5 MC SE."""
    t = StudentTPredictive(0.5, 2.0, 5.0)
    y = 1.2
    rng = np.random.default_rng(1)
    x1, x2 = t.sample(rng, 2_000_000), t.sample(rng, 2_000_000)
    terms = np.abs(x1 - y) - 0.5 * np.abs(x1 - x2)
    se = terms.std(ddof=1) / math.sqrt(terms.size)
    assert abs(scoring.crps_numerical(t, y) - terms.mean()) <= 5 * se


def test_coverage_from_pit_equals_quantile_interval_membership():
    rng = np.random.default_rng(2)
    preds = [GaussianPredictive(0.3, 2.0), StudentTPredictive(0.0, 1.0, 4.0),
             GaussianMixturePredictive(np.log([0.3, 0.7]), np.array([-1.0, 2.0]), np.array([0.5, 1.0]))]
    for p in preds:
        for y in rng.normal(scale=3, size=200):
            for lev in (0.5, 0.8, 0.95):
                lo, hi = p.quantile((1 - lev) / 2), p.quantile((1 + lev) / 2)
                by_q = lo <= y <= hi
                by_pit = bool(scoring.covered_from_pit(np.array([p.cdf(y)]), lev)[0])
                assert by_q == by_pit or min(abs(y - lo), abs(y - hi)) < 1e-9


def test_point_forecasts_refuse_probabilistic_scores():
    pf = PointForecast(1.0)
    for fn in (scoring.log_score, scoring.pit, scoring.crps):
        with pytest.raises(TypeError):
            fn(pf, 0.5)
    assert scoring.squared_error(pf, 0.5) == 0.25


def test_paired_difference_se_is_sd_over_sqrt_n():
    rng = np.random.default_rng(3)
    a, b = rng.normal(size=500), rng.normal(size=500)
    d = scoring.paired_difference(a, b)
    assert d.se == pytest.approx(np.std(a - b, ddof=1) / math.sqrt(500), rel=1e-14)


def test_sbc_ranks_with_ties_are_uniform_for_a_correct_discrete_posterior():
    """True value drawn from the same discrete distribution as the draws: randomised ranks are uniform."""
    rng = np.random.default_rng(4)
    atoms, w = np.array([0.1, 0.5, 0.9]), np.array([0.2, 0.5, 0.3])
    true = rng.choice(atoms, size=5000, p=w)
    draws = rng.choice(atoms, size=(5000, 99), p=w)
    ranks = calibration.sbc_ranks(true, draws, rng)
    assert calibration.rank_uniformity_pvalue(ranks, 99) > 1e-3


def test_mixture_quantile_inverts_cdf():
    mix = GaussianMixturePredictive(np.log([0.5, 0.5]), np.array([-5.0, 5.0]), np.array([1.0, 1.0]))
    for p in (1e-6, 0.3, 0.5, 0.999):
        assert mix.cdf(mix.quantile(p)) == pytest.approx(p, abs=1e-12)


def test_student_t_against_scipy():
    t = StudentTPredictive(0.3, 1.7, 6.0)
    ref = stats.t(6.0, loc=0.3, scale=math.sqrt(1.7))
    ys = np.linspace(-6, 6, 13)
    assert np.allclose(t.logpdf(ys), ref.logpdf(ys), rtol=0, atol=1e-13)
    assert np.allclose(t.cdf(ys), ref.cdf(ys), rtol=0, atol=1e-14)


def test_point_predictor_scored_only_with_point_metrics():
    """Section 2.6: a point-only predictor is refused by score_predictor and scored by squared error, against
    the target and against the matched reference's posterior mean."""
    from dynaicl.evaluation import harness
    from dynaicl.references.base import PointPredictor, PredictorDescription
    from dynaicl.references.matched import matched_reference_for
    from dynaicl.rng import NamedStreams
    from dynaicl.systems.conditions import ContinuousPriorCondition
    from dynaicl.systems.splits import SplitRole, generate_split
    from dynaicl.validation.checks import P_STABLE_TN, X0

    desc = PredictorDescription("point_persistence", "context-only", None, ("context",), ("future",), False, "x_n")
    point = PointPredictor(lambda ctx, h: ctx.last, desc)
    cond = ContinuousPriorCondition(P_STABLE_TN, X0)
    es = harness.build_evaluation_set(cond, generate_split(cond, SplitRole.EVALUATION, NamedStreams(9), 25, 8), 5, 2)
    with pytest.raises(TypeError):
        harness.score_predictor(point, es)
    out = harness.score_point_predictor(point, es, matched_reference_for(cond))
    assert out["sq_error_target"].shape == (25,) and np.all(np.isfinite(out["sq_error_reference_mean"]))
