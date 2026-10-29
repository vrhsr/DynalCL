"""F2-V11 mutation matrix (docs/MATH_F2.md section 9): seven injected bugs in the F2 reference pipeline, applied by
monkeypatching module attributes of ``dynaicl_families.stage2.f2_var`` (no source file is edited). Code in that module looks
its globals up at call time, so the patches reach both the tests and the checks.

| name | what goes wrong |
|---|---|
| wrong_prior | population Psi0 = 2 I instead of 4 I (prior mean of Sigma halved) |
| off_by_one_likelihood | regression arrays skip the first transition |
| leaked_target | context window shifted by the horizon, so its last row is the target |
| unmatched_reference | evaluation systems drawn with B0 = 0 while the reference assumes B0 = 0.4 I |
| wrong_truncation | population reference truncated at spectral radius 0.999 instead of 0.95 |
| missing_sigma_integration | p(y | B, D) a Gaussian at the scale matrix instead of the Student-t (Sigma not integrated) |
| wrong_spectral_radius | spectral radius computed as max |diagonal entry| |
"""

from __future__ import annotations

import os

import numpy as np

ENV = "F2_MUTATION"
KNOWN = ("wrong_prior", "off_by_one_likelihood", "leaked_target", "unmatched_reference", "wrong_truncation",
         "missing_sigma_integration", "wrong_spectral_radius")


def apply(name: str | None) -> None:
    if not name:
        return
    if name not in KNOWN:
        raise ValueError(f"unknown F2 mutation {name!r}")
    from dynaicl_families.stage2 import f2_var as fv
    if name == "wrong_prior":
        orig = fv.population_f2
        fv.population_f2 = lambda: fv.MNIWPrior("P_F2", orig().b0, orig().v0, 7.0, 2.0 * np.eye(2), 0.95)
    elif name == "wrong_truncation":
        orig = fv.population_f2
        fv.population_f2 = lambda: fv.MNIWPrior("P_F2", orig().b0, orig().v0, 7.0, 4.0 * np.eye(2), 0.999)
    elif name == "off_by_one_likelihood":
        def regression_arrays(ctx):
            c = np.asarray(ctx, dtype=np.float64)
            return c[:, 1:-1, :], c[:, 2:, :]                       # BUG: transition x_0 -> x_1 skipped
        fv.regression_arrays = regression_arrays
    elif name == "leaked_target":
        def contexts_and_targets(split, n, horizon=1):
            tr = split.trajectories
            ctx = np.array(tr[:, horizon:horizon + n + 1, :], dtype=np.float64)       # BUG: context ends at the target
            return ctx, np.array(tr[:, n + horizon, :], dtype=np.float64)
        fv.contexts_and_targets = contexts_and_targets
    elif name == "unmatched_reference":
        orig_sim = fv.simulate_f2

        def simulate_f2(prior, r, streams, n_items, length, stream_code=11, system_override=None):
            if prior.name == "P_F2" and system_override is None:
                prior = fv.MNIWPrior("P_F2", np.zeros((2, 2)), prior.v0, prior.nu0, prior.psi0, prior.c)   # BUG
            return orig_sim(prior, r, streams, n_items, length, stream_code, system_override)
        fv.simulate_f2 = simulate_f2
    elif name == "missing_sigma_integration":
        def rb_logpdf(post_i, b, y):
            db = b - post_i.bn[0]
            psi_b = post_i.psin[0] + np.swapaxes(db, 1, 2) @ post_i.vn_inv[0] @ db
            loc = np.einsum("jik,i->jk", b, post_i.last[0])
            return fv.mvn_logpdf(y[None, :, :], loc[:, None, :], (psi_b / (post_i.nun + 1.0))[:, None])   # BUG
        fv.rb_logpdf = rb_logpdf
    elif name == "wrong_spectral_radius":
        fv.spectral_radius = lambda a: np.max(np.abs(np.diagonal(a, axis1=-2, axis2=-1)), axis=-1)   # BUG


def apply_from_env() -> str | None:
    name = os.environ.get(ENV) or None
    apply(name)
    return name
