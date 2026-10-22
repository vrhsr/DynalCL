"""Shared helpers and config-fixed hyperparameters for context-only predictors (Section 2.5).

"Context-only" means a function of the context plus hyperparameters fixed in the config. Nothing
here may read the training population, the prior, or evaluation data.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

CONTEXT_ONLY_MUST_NOT_ACCESS = ("population", "prior", "library", "evaluation data", "true a", "future values")


@dataclass(frozen=True)
class FallbackSettings:
    """Config-fixed fallbacks for contexts too short for an estimator. Every use is flagged in ``info``."""

    coefficient_mean: float = 0.0       # flat-prior Bayes: proper N(mean, var) prior on a when S_xx = 0
    coefficient_variance: float = 1.0
    predictive_variance: float = 1.0    # persistence with n = 0 (absolute units, per step of horizon)
    variance_relative_floor: float = 1e-12  # variance >= floor * max(mean(x^2), tiny)

    def __post_init__(self) -> None:
        if not (self.coefficient_variance > 0 and self.predictive_variance > 0 and self.variance_relative_floor > 0):
            raise ValueError("fallback variances and floor must be > 0")


def variance_floor(x: np.ndarray, relative_floor: float) -> float:
    """Scale-aware lower bound on an estimated predictive variance (prevents a degenerate zero)."""
    ms = float(np.mean(x * x))
    return relative_floor * max(ms, np.finfo(np.float64).tiny)
