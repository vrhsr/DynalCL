"""F3 map code (docs/STAGE2_F3_MAP_SPEC.md validity checks iii and iv) on the f3_tests seed role.

The library predictor is checked against an independent scalar Kalman filter written here from the model equations
(tolerance 1e-10: both are float64 evaluations of the same closed forms; only rounding differs)."""

from __future__ import annotations

import math

import numpy as np

from dynaicl.evaluation.noisy_harness import build_noisy_evaluation
from dynaicl.rng import NamedStreams
from dynaicl.systems.noisy import NoisyObservationCondition, generate_noisy_split
from dynaicl.systems.splits import SplitRole
from dynaicl_families.stage2 import f3_map as fm
from dynaicl_families.stage2.seeds import role_seed

SEED = role_seed("f3_tests")


def _kalman_loglik_and_pred(y, a, q, r, h):
    """Independent scalar Kalman filter: log p(y_0..y_n | a) and the moments of y_{n+h} | y_0..y_n, a."""
    m, p, ll = 0.0, r * r, 0.0
    for t, yt in enumerate(y):
        if t > 0:
            m, p = a * m, a * a * p + 1.0
        s = p + q
        ll += -0.5 * (math.log(2 * math.pi * s) + (yt - m) ** 2 / s)
        k = p / s
        m, p = m + k * (yt - m), (1 - k) * p
    mean, var = m, p
    for _ in range(h):
        mean, var = a * mean, a * a * var + 1.0
    return ll, mean, var + q


def test_library_predictor_matches_independent_kalman():
    for q, r in ((0.0, 1.0), (2.56, 0.25), (6.5, 4.0)):
        model = fm.model_for(q, r)
        cond = NoisyObservationCondition(fm.population_prior(), model, name="T", stream_code=0)
        split = generate_noisy_split(cond, SplitRole.SELECTION, NamedStreams(SEED), 25, 14)
        es = build_noisy_evaluation(split, (2, 5), (1, 5))
        atoms = fm.library_atoms(SEED, 0)[:4]
        got = fm.library_scores(atoms, model, es.context_matrix, es._targets, (2, 5), (1, 5))
        for (n, h), lp in got.items():
            for i in range(25):
                parts = [_kalman_loglik_and_pred(es.context_matrix[i, :n + 1], a, q, r, h) for a in atoms]
                lw = np.array([p[0] for p in parts])
                lw -= np.logaddexp.reduce(lw)
                y = es._targets[(n, h)][i]
                comp = [lw[k] - 0.5 * (math.log(2 * math.pi * p[2]) + (y - p[1]) ** 2 / p[2]) for k, p in enumerate(parts)]
                assert abs(lp[i] - np.logaddexp.reduce(comp)) <= 1e-10, (q, r, n, h, i)


def test_inlib_systems_are_atoms_and_held_are_not():
    res = fm.inlib_unit(0.755, 1.0, 4, 0, SEED, 200)
    assert res["rows"] and all(row["set"] == "INLIB" for row in res["rows"])
    atoms = fm.library_atoms(SEED, 0)
    model = fm.model_for(0.755, 1.0)
    cond = NoisyObservationCondition(fm.population_prior(), model, name="F3-HELD", stream_code=0)
    held = generate_noisy_split(cond, SplitRole.SELECTION, NamedStreams(SEED), 500, 14)
    assert not np.isin(held.latent.coefficients, atoms).any()


def test_classification_rules():
    assert fm.classify(0.05, 0.005) == "IDENTIFIABLE"
    assert fm.classify(0.01, 0.002) == "UNIDENTIFIABLE"
    assert fm.classify(0.02, 0.005) == "BORDERLINE"
    assert fm.classify_draws(["IDENTIFIABLE"] * 15 + ["BORDERLINE"]) == "IDENTIFIABLE"
    assert fm.classify_draws(["IDENTIFIABLE"] * 14 + ["BORDERLINE"] * 2) == "PARTIAL"
