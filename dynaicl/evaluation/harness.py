"""Evaluation harness (Sections 2.3, 3, 4).

* Contexts are cut from trajectories in exactly one place, :func:`make_context`, which always starts at
  x_0. Targets are kept in evaluator-private GroundTruth records.
* Predictors are scored on identical items, so every comparison is paired.
* :func:`optimality_diagnostics` refuses to run unless the reference is matched to the condition
  that generated the evaluation set.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field

import numpy as np

from dynaicl.metrics import scoring
from dynaicl.references.base import Predictor
from dynaicl.references import matched as _matched
from dynaicl.references.matched import MatchedBayesReference, UnmatchedReferenceError
from dynaicl.references.predictive import PointForecast
from dynaicl.systems.conditions import EvaluationCondition
from dynaicl.systems.context import ContextWindow, GroundTruth
from dynaicl.systems.splits import DataSplit, SplitRole

FLOAT = np.float64


def make_context(trajectory: np.ndarray, n: int) -> ContextWindow:
    """Context x_0..x_n from a trajectory x_0..x_T. The only place contexts are cut."""
    return ContextWindow(np.array(trajectory[: n + 1], dtype=FLOAT))


@dataclass(frozen=True, eq=False)
class EvaluationSet:
    condition: EvaluationCondition
    role: SplitRole
    n: int
    horizon: int
    contexts: tuple[ContextWindow, ...]
    _truth: tuple[GroundTruth, ...] = field(repr=False)
    identifier: str = ""

    @property
    def size(self) -> int:
        return len(self.contexts)

    def _targets(self) -> np.ndarray:
        return np.array([t.target for t in self._truth], dtype=FLOAT)

    def _true_coefficients(self) -> np.ndarray:
        return np.array([t.a for t in self._truth], dtype=FLOAT)

    def _true_noise_scales(self) -> np.ndarray:
        return np.array([t.sigma for t in self._truth], dtype=FLOAT)


def build_evaluation_set(condition: EvaluationCondition, split: DataSplit, n: int, horizon: int) -> EvaluationSet:
    if split.condition_name != condition.name:
        raise ValueError(f"split was generated under {split.condition_name}, not {condition.name}")
    if split.role is SplitRole.LIBRARY_TRAIN:
        raise ValueError("library training data cannot be used as an evaluation set")
    if n < 0 or horizon < 1 or split.trajectories.shape[1] < n + horizon + 1:
        raise ValueError("trajectories too short for (n, horizon)")
    contexts = []
    truth = []
    for i in range(split.size):
        traj = split.trajectories[i]
        contexts.append(make_context(traj, n))
        truth.append(GroundTruth(i, float(split.coefficients[i]), float(split.noise_scales[i]), split.system_ids[i],
                                 float(traj[n + horizon]), horizon, split.trajectory_sha256(i)))
    h = hashlib.sha256()
    h.update(condition.fingerprint().encode())
    h.update(f"{split.role.value}|{n}|{horizon}|{split.size}".encode())
    for t in truth:
        h.update(t.trajectory_sha256.encode())
    return EvaluationSet(condition, split.role, n, horizon, tuple(contexts), tuple(truth), h.hexdigest())


@dataclass(frozen=True, eq=False)
class ScoreTable:
    """Per-item scores of one predictor on one evaluation set (aligned item by item)."""

    predictor_name: str
    assumed_system_distribution: str | None
    evaluation_set_id: str
    log_score: np.ndarray
    pit: np.ndarray
    crps: np.ndarray | None
    predictive_mean: np.ndarray
    squared_error: np.ndarray
    fallback: np.ndarray
    info: dict = field(default_factory=dict)   # numeric per-item info, e.g. selected kernel multiplier

    def coverage(self, level: float) -> float:
        return float(np.mean(scoring.covered_from_pit(self.pit, level)))


def score_predictor(predictor: Predictor, eval_set: EvaluationSet, compute_crps: bool = False,
                    info_keys: tuple[str, ...] = ()) -> ScoreTable:
    targets = eval_set._targets()
    n_items = eval_set.size
    ls = np.empty(n_items)
    u = np.empty(n_items)
    cr = np.empty(n_items) if compute_crps else None
    mean = np.empty(n_items)
    fb = np.zeros(n_items, dtype=bool)
    info = {k: np.full(n_items, np.nan) for k in info_keys}
    for i, (ctx, y) in enumerate(zip(eval_set.contexts, targets)):
        pred = predictor.predict(ctx, eval_set.horizon)
        if isinstance(pred, PointForecast):
            raise TypeError(f"{predictor.name} is point-only; use score_point_predictor")
        ls[i] = pred.logpdf(y)
        u[i] = pred.cdf(y)
        mean[i] = pred.mean()
        fb[i] = bool(pred.info.get("fallback", False))
        for k in info_keys:
            v = pred.info.get(k)
            if v is not None:
                info[k][i] = float(v)
        if cr is not None:
            cr[i] = scoring.crps(pred, y)
    if not (np.all(np.isfinite(ls)) and np.all(np.isfinite(u)) and np.all(np.isfinite(mean))):
        raise FloatingPointError(f"non-finite scores for {predictor.name}")
    return ScoreTable(predictor.name, predictor.description.assumed_system_distribution, eval_set.identifier,
                      ls, u, cr, mean, (mean - targets) ** 2, fb, info)


def score_point_predictor(predictor: Predictor, eval_set: EvaluationSet,
                          reference: MatchedBayesReference | None = None) -> dict[str, np.ndarray]:
    """Point metrics only: squared error vs the target and, given a matched reference, vs its posterior mean."""
    targets = eval_set._targets()
    forecasts = [predictor.predict(c, eval_set.horizon) for c in eval_set.contexts]
    if not all(isinstance(f, PointForecast) for f in forecasts):
        raise TypeError(f"{predictor.name} is probabilistic; use score_predictor")
    pts = np.array([f.point for f in forecasts])
    out = {"sq_error_target": (pts - targets) ** 2}
    if reference is not None:
        reference.verify(eval_set.condition)
        ref_mean = np.array([reference.predictor.predict(c, eval_set.horizon).mean() for c in eval_set.contexts])
        out["sq_error_reference_mean"] = (pts - ref_mean) ** 2
    return out


@dataclass(frozen=True)
class OptimalityRow:
    competitor: str
    difference: scoring.PairedDifference   # reference log score minus competitor log score
    violates: bool                          # mean difference below -z_crit * SE


def optimality_diagnostics(reference: MatchedBayesReference, eval_set: EvaluationSet, reference_scores: ScoreTable,
                           competitor_scores: dict[str, ScoreTable], z_crit: float) -> list[OptimalityRow]:
    """Theorem T1: under its own condition the matched reference has the highest expected log score.

    Refuses (UnmatchedReferenceError) if the reference is not matched to the condition that
    generated ``eval_set``, or if the score tables were not computed on that exact evaluation set.
    """
    if not isinstance(reference, MatchedBayesReference):
        raise UnmatchedReferenceError("optimality diagnostics require a MatchedBayesReference")
    reference.verify(eval_set.condition)
    _matched.check_system_distribution(reference_scores.assumed_system_distribution, eval_set.condition,
                                       "reference score table")
    if reference_scores.predictor_name != reference.predictor.name:
        raise UnmatchedReferenceError("reference scores do not belong to the reference predictor")
    rows = []
    for name, table in competitor_scores.items():
        if table.evaluation_set_id != eval_set.identifier or reference_scores.evaluation_set_id != eval_set.identifier:
            raise ValueError("score tables must come from the same evaluation set (paired comparison)")
        d = scoring.paired_difference(reference_scores.log_score, table.log_score)
        rows.append(OptimalityRow(name, d, bool(d.mean < -z_crit * d.se) if d.se > 0 else d.mean < -1e-12))
    return rows


def ground_truth_for_validation(eval_set: EvaluationSet) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """(true a, true sigma, targets): for the calibration and validation code only, never for predictors."""
    return eval_set._true_coefficients(), eval_set._true_noise_scales(), eval_set._targets()

