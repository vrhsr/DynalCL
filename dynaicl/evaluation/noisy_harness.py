"""Stage 0.6 evaluation harness for noisy observations.

Indexing (approved): n = number of transitions. The observed context is y_0..y_n (n + 1 values), and the target is
y_{n+h}. Contexts are cut in exactly one place (:func:`make_noisy_context`) from exactly one source
(:func:`noisy_context_source`, the observations, never the latent path). The evaluator keeps the latent path,
a and the targets.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from dynaicl.systems.context import ContextWindow
from dynaicl.systems.noisy import NoisySplit

FLOAT = np.float64


def noisy_context_source(split: NoisySplit) -> np.ndarray:
    """The only array predictors' contexts are cut from: the noisy observations."""
    return split.observations


def make_noisy_context(row: np.ndarray, n: int) -> ContextWindow:
    """Observed context y_0..y_n (n + 1 values)."""
    return ContextWindow(np.array(row[: n + 1], dtype=FLOAT))


def target_index(n: int, h: int) -> int:
    return n + h


@dataclass(frozen=True, eq=False)
class NoisyEvaluationSet:
    """Batch view for vectorised scoring. ``context_matrix`` holds y_0..y_{n_max} for every system. Predictions for a
    context length n use columns 0..n only (causality TESTED). ``_targets`` and ``_truth`` are evaluator-only."""

    ns: tuple[int, ...]
    hs: tuple[int, ...]
    context_matrix: np.ndarray
    _targets: dict = field(repr=False)
    _true_a: np.ndarray = field(repr=False)
    _latent: np.ndarray = field(repr=False)

    def context(self, i: int, n: int) -> ContextWindow:
        return make_noisy_context(self.context_matrix[i], n)

    @property
    def size(self) -> int:
        return int(self.context_matrix.shape[0])


def build_noisy_evaluation(split: NoisySplit, ns: tuple[int, ...], hs: tuple[int, ...]) -> NoisyEvaluationSet:
    src = noisy_context_source(split)
    n_max = max(ns)
    if target_index(n_max, max(hs)) >= split.observations.shape[1]:
        raise ValueError(f"trajectories too short for target index {target_index(n_max, max(hs))}")
    ctx = np.array(src[:, : n_max + 1], dtype=FLOAT)
    for n in ns:   # every context cut must equal the canonical single-context cut (guards the batch path)
        probe = make_noisy_context(src[0], n)
        if not np.array_equal(probe.values, ctx[0, : n + 1]):
            raise AssertionError("batch context matrix disagrees with make_noisy_context")
    ctx.setflags(write=False)
    targets = {(n, h): np.array(split.observations[:, target_index(n, h)], dtype=FLOAT) for n in ns for h in hs}
    return NoisyEvaluationSet(tuple(ns), tuple(hs), ctx, targets, np.array(split.latent.coefficients),
                              np.array(split.latent.trajectories))


def score_noisy_batch(predictor, eset: NoisyEvaluationSet, chunk: int = 128) -> dict:
    """{(n, h): (log score (B,), PIT (B,))} for a :class:`NoisyObservationBayesPredictor`, in chunks of systems."""
    out = {key: (np.empty(eset.size), np.empty(eset.size)) for key in eset._targets}
    for s in range(0, eset.size, chunk):
        e = min(s + chunk, eset.size)
        tg = {k: v[s:e] for k, v in eset._targets.items()}
        res = predictor.batch_scores(eset.context_matrix[s:e], tg, eset.ns, eset.hs)
        for k, (lp, u) in res.items():
            out[k][0][s:e] = lp
            out[k][1][s:e] = u
    return out


def score_noisy_per_context(predictor, eset: NoisyEvaluationSet, ns=None, hs=None, items=None) -> dict:
    """Same output via the canonical per-context ``predict`` (works for every predictor, including the noise-naive ones)."""
    ns, hs = ns or eset.ns, hs or eset.hs
    items = range(eset.size) if items is None else items
    items = list(items)
    out = {(n, h): (np.empty(len(items)), np.empty(len(items))) for n in ns for h in hs}
    for j, i in enumerate(items):
        for n in ns:
            ctx = eset.context(i, n)
            for h in hs:
                p = predictor.predict(ctx, h)
                y = float(eset._targets[(n, h)][i])
                out[(n, h)][0][j] = float(p.logpdf(y))
                out[(n, h)][1][j] = float(p.cdf(y))
    for k, (lp, u) in out.items():
        if not (np.all(np.isfinite(lp)) and np.all(np.isfinite(u))):
            raise FloatingPointError(f"non-finite score for {getattr(predictor, 'name', predictor)} at {k}")
    return out
