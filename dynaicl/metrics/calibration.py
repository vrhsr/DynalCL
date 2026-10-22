"""Calibration statistics: PIT / rank uniformity, SBC ranks, binomial coverage, Bonferroni.

Every test returns a p-value. Callers compare it with a Bonferroni-corrected per-test level, so a
whole family of checks has a stated false-alarm probability under correct code (Section 5).
"""

from __future__ import annotations

import numpy as np
from scipy import stats


def bonferroni_level(family_alpha: float, n_tests: int) -> float:
    if not (0 < family_alpha < 1) or n_tests < 1:
        raise ValueError("invalid Bonferroni inputs")
    return family_alpha / n_tests


def ks_uniform_pvalue(u: np.ndarray) -> float:
    """Kolmogorov-Smirnov test of U(0, 1) for continuous PIT values."""
    return float(stats.kstest(np.asarray(u, dtype=np.float64), "uniform").pvalue)


def chi2_uniform_pvalue(u: np.ndarray, bins: int = 10) -> float:
    counts, _ = np.histogram(np.asarray(u, dtype=np.float64), bins=bins, range=(0.0, 1.0))
    return float(stats.chisquare(counts).pvalue)


def sbc_ranks(true_values: np.ndarray, posterior_draws: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """Rank of each true value among its L posterior draws, in {0..L}. Ties (discrete posteriors) are
    broken uniformly at random, which makes the rank exactly uniform under a correct posterior."""
    t = np.asarray(true_values, dtype=np.float64)[:, None]
    d = np.asarray(posterior_draws, dtype=np.float64)
    less = (d < t).sum(axis=1)
    ties = (d == t).sum(axis=1)
    return less + rng.integers(0, ties + 1)


def rank_uniformity_pvalue(ranks: np.ndarray, n_draws: int, bins: int = 10) -> float:
    """Chi-square test that ranks in {0..L} are uniform; requires (L + 1) divisible by ``bins``."""
    if (n_draws + 1) % bins:
        raise ValueError("(n_draws + 1) must be divisible by bins so every bin holds equally many ranks")
    per = (n_draws + 1) // bins
    counts = np.bincount(np.asarray(ranks) // per, minlength=bins)
    return float(stats.chisquare(counts).pvalue)


def coverage_pvalue(n_covered: int, n_total: int, level: float) -> float:
    """Exact two-sided binomial test of the coverage rate against its nominal level."""
    return float(stats.binomtest(int(n_covered), int(n_total), level).pvalue)


def binomial_band(n_total: int, level: float, alpha: float) -> tuple[float, float]:
    """Central (1 - alpha) band for the empirical coverage fraction of a correctly calibrated predictor."""
    lo = stats.binom.ppf(alpha / 2, n_total, level) / n_total
    hi = stats.binom.isf(alpha / 2, n_total, level) / n_total
    return float(lo), float(hi)
