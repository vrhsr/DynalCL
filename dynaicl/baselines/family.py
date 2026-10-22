"""The context-only family and the context-only frontier (Section 2.5).

"Strongest context-only estimator" is not canonical, so every member is reported. The frontier is a
DESIGN CHOICE: per (condition, sigma, n, h, metric), pick the member with the best mean score on a
simulated selection set that is disjoint from the evaluation set, then report that member's
evaluation scores. The single discrete choice among members uses population information at the
meta level. Each member's predictions remain context-only.

Two frontiers are reported:
* ``frontier_all``: over every member.
* ``frontier_strict``: excludes members flagged ``uses_true_noise_scale`` (flat-prior Bayes is given
  the condition's sigma as a config hyperparameter).
"""

from __future__ import annotations

from collections.abc import Mapping

import numpy as np

from dynaicl.baselines.common import FallbackSettings
from dynaicl.baselines.flat_prior import FlatPriorBayesPredictor
from dynaicl.baselines.kernel import KernelAnalogPredictor, KernelSettings
from dynaicl.baselines.ols import OlsPlugInPredictor
from dynaicl.baselines.persistence import PersistencePredictor
from dynaicl.baselines.stability_prior import StabilityPriorBayesPredictor
from dynaicl.references.base import Predictor
from dynaicl.references.quadrature import QuadratureSettings


def build_context_only_family(sigma: float, quadrature: QuadratureSettings = QuadratureSettings(),
                              kernel: KernelSettings = KernelSettings(),
                              fallback: FallbackSettings = FallbackSettings(),
                              ols_min_transitions: int = 3,
                              stability_bound: float | None = None) -> dict[str, Predictor]:
    """The context-only family. ``stability_bound`` (Stage 0.5) adds the generic-stability Bayes member;
    Stage 0 used the 7 members without it."""
    members: list[Predictor] = [
        FlatPriorBayesPredictor(sigma, quadrature, fallback),
        OlsPlugInPredictor("gaussian", ols_min_transitions, fallback),
        OlsPlugInPredictor("student_t", ols_min_transitions, fallback),
        KernelAnalogPredictor("rolling_origin", kernel, fallback),
        KernelAnalogPredictor("blocked", kernel, fallback),
        KernelAnalogPredictor("leave_one_out", kernel, fallback),
        PersistencePredictor(fallback),
    ]
    if stability_bound is not None:
        members.append(StabilityPriorBayesPredictor(sigma, stability_bound, quadrature))
    family = {p.name: p for p in members}
    for p in family.values():
        if p.description.category != "context-only" or p.description.assumed_system_distribution is not None:
            raise AssertionError(f"{p.name} is not a context-only predictor")
    return family


def select_frontier_member(selection_scores: Mapping[str, np.ndarray], family: Mapping[str, Predictor],
                           higher_is_better: bool, strict: bool) -> str:
    """Member with the best mean selection score (ties broken by name order, deterministic)."""
    best_name, best_val = None, None
    for name in sorted(selection_scores):
        if strict and family[name].description.uses_true_noise_scale:
            continue
        val = float(np.mean(selection_scores[name]))
        if best_val is None or (val > best_val if higher_is_better else val < best_val):
            best_name, best_val = name, val
    if best_name is None:
        raise ValueError("no eligible frontier member")
    return best_name
