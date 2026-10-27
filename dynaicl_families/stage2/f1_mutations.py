"""F1-V9 mutation matrix: six injected bugs in the F1 reference pipeline (docs/MATH_F1.md section 6).

Each mutation is applied by monkeypatching module attributes in the running process (the frozen F1 code is never edited).
``apply(name)`` must run before the code under test looks the patched names up: the pytest plugin
``dynaicl_families.stage2.f1_plugin`` applies it in ``pytest_configure`` (before test modules are imported), and the
check functions in ``f1_checks`` look every patched name up through its module at call time.

| name | what goes wrong (a plausible coding error) |
|---|---|
| wrong_prior | population reference built with sigma^2 ~ IG(3, 1) instead of IG(3, 2) (beta0 typo) |
| off_by_one_likelihood | sufficient statistics skip the first transition (loop starts at t = 2) |
| leaked_target | context window shifted by the horizon, so its last value is the target |
| unmatched_reference | evaluation systems drawn with a ~ TN(0.0, ...) while the reference assumes TN(0.4, ...) |
| wrong_truncation | population reference truncates a at the context-only bound 0.999 instead of 0.95 |
| wrong_sigma_integration | inverse-gamma marginal uses beta0 + R instead of beta0 + R/2 (algebra slip) |
"""

from __future__ import annotations

import math
import os
from dataclasses import replace

import numpy as np
from scipy import special

ENV = "F1_MUTATION"
KNOWN = ("wrong_prior", "off_by_one_likelihood", "leaked_target", "unmatched_reference", "wrong_truncation",
         "wrong_sigma_integration")


def apply(name: str | None) -> None:
    """Patch the F1 modules for one mutation (None or '' = clean). Idempotent within a process only for one name."""
    if not name:
        return
    if name not in KNOWN:
        raise ValueError(f"unknown F1 mutation {name!r}")
    from dynaicl_families import ar1_unknown_sigma as uf
    from dynaicl_families import sampling as sm
    from dynaicl.evaluation import harness

    if name == "wrong_prior":
        uf.population_f1 = lambda: uf.UnknownScaleReference(uf.CoefficientPrior(0.95, 0.4, 0.3),
                                                            uf.InverseGammaScale(3.0, 1.0))
    elif name == "wrong_truncation":
        uf.population_f1 = lambda: uf.UnknownScaleReference(uf.CoefficientPrior(0.999, 0.4, 0.3),
                                                            uf.InverseGammaScale(3.0, 2.0))
    elif name == "off_by_one_likelihood":
        def from_contexts(values):
            v = np.asarray(values, dtype=np.float64)
            if v.ndim != 2 or v.shape[1] < 3:
                raise ValueError("F1 contexts must be (N, n + 1) with n >= 2")
            prev, curr = v[:, 1:-1], v[:, 2:]                       # BUG: transition x_0 -> x_1 skipped
            sxx = np.einsum("ij,ij->i", prev, prev)
            a_hat = np.einsum("ij,ij->i", prev, curr) / sxx
            resid = curr - a_hat[:, None] * prev
            return uf.F1Stats(int(v.shape[1] - 2), sxx, a_hat, np.einsum("ij,ij->i", resid, resid), v[:, -1].copy())
        uf.F1Stats.from_contexts = staticmethod(from_contexts)
    elif name == "leaked_target":
        def contexts_and_targets(split, n, horizon=1):
            traj = split.trajectories
            ctx = np.stack([harness.make_context(traj[i, horizon:], n).values for i in range(split.size)])   # BUG
            return ctx, np.array(traj[:, n + horizon], dtype=np.float64)
        sm.contexts_and_targets = contexts_and_targets
    elif name == "unmatched_reference":
        base = sm.F1PopulationCondition

        def condition(**kw):
            return replace(base(**kw), mu0=0.0)                     # BUG: data from another population
        sm.F1PopulationCondition = condition
    elif name == "wrong_sigma_integration":
        def log_marginal(self, n, r):
            a, b = self.alpha0, self.beta0
            return (a * math.log(b) + special.gammaln(a + n / 2.0) - special.gammaln(a)
                    - (a + n / 2.0) * np.log(b + np.asarray(r)))     # BUG: R instead of R / 2
        uf.InverseGammaScale.log_marginal = log_marginal


def apply_from_env() -> str | None:
    name = os.environ.get(ENV) or None
    apply(name)
    return name
