"""Sensitivity analyses of the reference maps (docs/STAGE2_SENSITIVITY_SPEC.md): comparator frontier, prior dependence and
the noisy-observation map at higher precision. Reference-only; every reference and simulator is frozen code used read-only.
"""

from __future__ import annotations

import math

import numpy as np

from dynaicl.rng import NamedStreams
from dynaicl.systems.conditions import ContinuousPriorCondition, InitialStateSpec
from dynaicl.systems.context import ContextWindow
from dynaicl.systems.priors import StableCoefficientPrior

DELTA = 0.02
Z = 3.0
NS = (2, 3, 5, 10, 20)
RS = (0.25, 1.0, 4.0)


def decide(mean: float, se: float) -> str:
    if mean - Z * se >= DELTA:
        return "IDENTIFIABLE"
    if mean + Z * se < DELTA:
        return "UNIDENTIFIABLE"
    return "BORDERLINE"


def gap_row(lp_truth: np.ndarray, lp_other: np.ndarray, **keys) -> dict:
    d = lp_truth - lp_other
    mean, se = float(d.mean()), float(d.std(ddof=1) / math.sqrt(d.size))
    return {**keys, "estimate": mean, "se": se, "n_items": int(d.size), "decision": decide(mean, se)}


def ols_t_logpdf(ctx: np.ndarray, y: np.ndarray) -> np.ndarray:
    """The frozen OLS Student-t plug-in, called per context (non-Bayesian context-only comparator)."""
    from dynaicl.baselines.ols import OlsPlugInPredictor
    pred = OlsPlugInPredictor("student_t", min_transitions=2)
    return np.array([pred.predict(ContextWindow(np.array(ctx[i])), 1).logpdf(float(y[i])) for i in range(ctx.shape[0])])


def _known_sigma_sample(tau: float, n: int, r: float, n_items: int, seed: int):
    from dynaicl_families import sampling as sm
    prior = StableCoefficientPrior(rho=0.95, sigma=1.0, shape="truncated_normal", mu0=0.4, tau0=tau)
    split = sm.simulate(ContinuousPriorCondition(prior, InitialStateSpec(0.0, r)), NamedStreams(seed), n_items, n + 1)
    return sm.contexts_and_targets(split, n)


def frontier_known(n: int, r: float, n_items: int, seed: int) -> list[dict]:
    from dynaicl_families import ar1_unknown_sigma as uf
    from dynaicl_families.ar1_known_sigma import ContextStats, TruncatedGaussianPrior, population_prior
    ctx, y = _known_sigma_sample(0.3, n, r, n_items, seed)
    cs = ContextStats.from_contexts(ctx)
    lp = population_prior().logpdf(cs, y)
    others = {"stab_0.999": TruncatedGaussianPrior(rho=0.999).logpdf(cs, y),
              "stab_0.95": TruncatedGaussianPrior(rho=0.95).logpdf(cs, y),
              "stab_0.9999": TruncatedGaussianPrior(rho=0.9999).logpdf(cs, y),
              "sigma_agnostic": uf.context_only_f1().logpdf(uf.F1Stats.from_contexts(ctx), y),
              "ols_t": ols_t_logpdf(ctx, y)}
    return [gap_row(lp, v, analysis="frontier", family="known_sigma", variant=k, r=r, n=n, h=1) for k, v in others.items()]


def _f1_sample(tau: float, alpha0: float, beta0: float, n: int, r: float, n_items: int, seed: int):
    from dynaicl_families import sampling as sm
    cond = sm.F1PopulationCondition(tau0=tau, alpha0=alpha0, beta0=beta0, initial_state=InitialStateSpec(0.0, r))
    split = sm.simulate(cond, NamedStreams(seed), n_items, n + 1)
    return sm.contexts_and_targets(split, n)


def frontier_f1(n: int, r: float, n_items: int, seed: int) -> list[dict]:
    from dynaicl_families import ar1_unknown_sigma as uf
    ctx, y = _f1_sample(0.3, 3.0, 2.0, n, r, n_items, seed)
    st = uf.F1Stats.from_contexts(ctx)
    lp = uf.population_f1().logpdf(st, y)
    coef = uf.CoefficientPrior(0.999)
    others = {f"ctx_logunif_{lo}_{hi}": uf.UnknownScaleReference(coef, uf.LogUniformScale(lo, hi)).logpdf(st, y)
              for lo, hi in ((0.1, 10.0), (0.01, 100.0), (0.001, 1000.0))}
    others["ols_t"] = ols_t_logpdf(ctx, y)
    return [gap_row(lp, v, analysis="frontier", family="unknown_sigma", variant=k, r=r, n=n, h=1) for k, v in others.items()]


def prior_known(tau: float, n: int, r: float, n_items: int, seed: int) -> list[dict]:
    from dynaicl_families.ar1_known_sigma import ContextStats, TruncatedGaussianPrior, stability_prior
    ctx, y = _known_sigma_sample(tau, n, r, n_items, seed)
    cs = ContextStats.from_contexts(ctx)
    lp = TruncatedGaussianPrior(rho=0.95, mu0=0.4, tau0=tau).logpdf(cs, y)
    return [gap_row(lp, stability_prior().logpdf(cs, y), analysis="prior", family="known_sigma", variant=f"tau_{tau}",
                    r=r, n=n, h=1)]


def prior_f1(tau: float, alpha0: float, n: int, r: float, n_items: int, seed: int) -> list[dict]:
    from dynaicl_families import ar1_unknown_sigma as uf
    beta0 = alpha0 - 1.0
    ctx, y = _f1_sample(tau, alpha0, beta0, n, r, n_items, seed)
    st = uf.F1Stats.from_contexts(ctx)
    pop = uf.UnknownScaleReference(uf.CoefficientPrior(0.95, 0.4, tau), uf.InverseGammaScale(alpha0, beta0))
    return [gap_row(pop.logpdf(st, y), uf.context_only_f1().logpdf(st, y), analysis="prior", family="unknown_sigma",
                    variant=f"tau_{tau}_alpha_{alpha0}", r=r, n=n, h=1)]


def f3_precision(q: float, r: float, n_items: int, seed: int, chunk: int = 10000) -> list[dict]:
    """F3 pop vs stab with many more items, scored in chunks (frozen Stage 0.6 references and simulator)."""
    from dynaicl.evaluation.noisy_harness import build_noisy_evaluation
    from dynaicl.references.kalman_quadrature import noise_aware_stability_predictor, noisy_population_reference
    from dynaicl.systems.noisy import NoisyObservationCondition, generate_noisy_split
    from dynaicl.systems.splits import SplitRole
    from dynaicl_families.stage2 import f3_map as fm
    model = fm.model_for(q, r)
    cond = NoisyObservationCondition(fm.population_prior(), model, name="F3-PRECISION", stream_code=0)
    split = generate_noisy_split(cond, SplitRole.SELECTION, NamedStreams(seed), n_items, max(fm.NS) + max(fm.HS))
    es = build_noisy_evaluation(split, fm.NS, fm.HS)
    pop = noisy_population_reference(fm.population_prior(), model)
    stab = noise_aware_stability_predictor(model)
    diffs = {(n, h): [] for n in fm.NS for h in fm.HS}
    for i0 in range(0, n_items, chunk):
        sl = slice(i0, min(n_items, i0 + chunk))
        tg = {k: v[sl] for k, v in es._targets.items()}
        a = pop.batch_scores(es.context_matrix[sl], tg, fm.NS, fm.HS)
        b = stab.batch_scores(es.context_matrix[sl], tg, fm.NS, fm.HS)
        for k in diffs:
            diffs[k].append(a[k][0] - b[k][0])
    rows = []
    for (n, h), parts in diffs.items():
        d = np.concatenate(parts)
        rows.append(gap_row(d, np.zeros_like(d), analysis="f3_precision", family="noisy", variant=f"q_{q}", r=r, n=n, h=h))
    return rows
