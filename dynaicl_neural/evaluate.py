"""Per-model evaluation statistics (PREREG_stage1 sections 5-6). Pure numpy; models enter only as mixture parameters.

* D_X(model) per context = KL(X || model) by y-quadrature on X's window (dynaicl_families.kl), for each reference X.
* On held-out systems (truth = pop) KL(pop || model) is the model's expected regret against pop given the context
  (DERIVED: the target given the context is distributed as pop), so R_pop = mean of it; G per seed index is
  KL(pop || UNIF_i) - KL(pop || CONT_i).
* realized log scores are computed for the V-RB validity check.
"""

from __future__ import annotations

import numpy as np

from dynaicl_families.ar1_known_sigma import ContextStats
from dynaicl_families.kl import kl_quadrature
from dynaicl_families.separability import MASS_TOL, reference_window
from dynaicl_neural import mutations
from dynaicl_neural.adapter import mixture_logpdf

PANEL_WIDTH = 0.5          # sigma / 2, as in the separability map (dynaicl_families/kl.py)


def _sub(st: ContextStats, idx: np.ndarray) -> ContextStats:
    return ContextStats(st.sxx[idx], st.sxy[idx], st.last[idx])


def kl_reference_to_model(ref, st: ContextStats, params: tuple[np.ndarray, np.ndarray, np.ndarray]) -> np.ndarray:
    """Per-context KL(ref || model) where params = (log weights, means, variances) of the model's predictive."""
    lw, mu, var = params
    lo, hi = reference_window(ref, st)
    kl, mass = kl_quadrature(lambda i, y: ref.logpdf(_sub(st, i), y),
                             lambda i, y: mixture_logpdf(lw[i], mu[i], var[i], y), lo, hi, PANEL_WIDTH)
    err = float(np.max(np.abs(mass - 1.0)))
    if err > MASS_TOL:
        raise FloatingPointError(f"KL window lost mass {err:.2e}")
    return kl


def realized_log_score(params, y: np.ndarray) -> np.ndarray:
    lw, mu, var = params
    return mixture_logpdf(lw, mu, var, y)


def q1_statistics(cont: list, unif: list, st: ContextStats, pop, stab) -> dict[str, np.ndarray]:
    """For one held-out cell: per-model arrays (M, N) R_pop (CONT models) and G (paired by seed index), plus
    Delta = KL(pop || stab) per context (reference-only). ``cont`` / ``unif``: lists of mixture-parameter tuples."""
    if len(cont) != len(unif):
        raise ValueError("CONT and UNIF must have the same seed indices (pairing)")
    truth = stab if mutations.active("wrong_reference") else pop
    r_cont = np.stack([kl_reference_to_model(truth, st, p) for p in cont])
    r_unif = np.stack([kl_reference_to_model(truth, st, p) for p in unif])
    lo, hi = reference_window(pop, st)
    delta, _ = kl_quadrature(lambda i, y: pop.logpdf(_sub(st, i), y), lambda i, y: stab.logpdf(_sub(st, i), y),
                             lo, hi, PANEL_WIDTH)
    return {"R_pop": r_cont, "G": r_unif - r_cont, "Delta": delta}


def behavioural_distances(models: list, st: ContextStats, refs: dict) -> dict[str, np.ndarray]:
    """Per-model arrays (M, N) of D_X = KL(X || model) for every reference X in ``refs``."""
    return {name: np.stack([kl_reference_to_model(ref, st, p) for p in models]) for name, ref in refs.items()}
