"""Batch h = 1 references (dynaicl_families.ar1_known_sigma) against the frozen references and stored Stage 0.5 items.

Tolerance 1e-9 nats: the frozen Tier-1 tolerance (PREREG_stage06 section 8). The frozen quadrature references converge
to about 1e-13 (MATH 5.3) and the batch forms are closed forms, so any real discrepancy is far above this.
"""

from __future__ import annotations

import csv
from pathlib import Path

import numpy as np
import pytest

from dynaicl.baselines.stability_prior import StabilityPriorBayesPredictor
from dynaicl.evaluation import harness
from dynaicl.references.library import FiniteLibraryPredictor
from dynaicl.references.quadrature import QuadratureSettings, StablePriorQuadraturePredictor
from dynaicl.rng import NamedStreams
from dynaicl.systems.conditions import ContinuousPriorCondition, InitialStateSpec
from dynaicl.systems.library import build_library_from_prior
from dynaicl.systems.priors import StableCoefficientPrior
from dynaicl.systems.splits import SplitRole, generate_split
from dynaicl_families.ar1_known_sigma import (ContextStats, FiniteLibrary, log_ndtr_diff, population_prior,
                                              stability_prior)

TOL = 1e-9
ROOT = Path(__file__).resolve().parents[1]
STAGE05 = ROOT / "runs" / "20261010T053729455237Z_stage05_population_advantage_51c7621b7a" / "results"
POP_FROZEN = StableCoefficientPrior(rho=0.95, sigma=1.0, shape="truncated_normal", mu0=0.4, tau0=0.3)


def _random_contexts(rng, n_ctx, n, r, a_lo=-0.99, a_hi=0.99):
    out = []
    for _ in range(n_ctx):
        a = rng.uniform(a_lo, a_hi)
        x = np.empty(n + 1)
        x[0] = r * rng.standard_normal()
        for t in range(1, n + 1):
            x[t] = a * x[t - 1] + rng.standard_normal()
        out.append(x)
    return np.stack(out)


@pytest.mark.parametrize("n,r", [(1, 0.25), (1, 4.0), (2, 1.0), (3, 1.0), (5, 4.0), (20, 1.0), (80, 0.25)])
def test_truncated_gaussian_matches_frozen_quadrature(n, r):
    rng = np.random.default_rng(1000 + n)
    ctx = _random_contexts(rng, 25, n, r)
    st = ContextStats.from_contexts(ctx)
    pop, stab = population_prior(), stability_prior()
    f_pop = StablePriorQuadraturePredictor(POP_FROZEN, QuadratureSettings())
    f_stab = StabilityPriorBayesPredictor(1.0, 0.999, QuadratureSettings())
    worst = 0.0
    for i in range(ctx.shape[0]):
        cw = harness.make_context(ctx[i], n)
        for batch, frozen in ((pop, f_pop), (stab, f_stab)):
            pred = frozen.predict(cw, 1)
            ys = pred.quantile(np.array([1e-3, 0.1, 0.5, 0.9, 1 - 1e-3]))
            got = batch.logpdf(ContextStats(st.sxx[i:i + 1], st.sxy[i:i + 1], st.last[i:i + 1]), ys[None, :])[0]
            worst = max(worst, float(np.max(np.abs(got - pred.logpdf(ys)))))
    assert worst <= TOL, worst


@pytest.mark.parametrize("k", [1, 2, 8, 64])
def test_library_matches_frozen_library(k):
    lib_frozen = build_library_from_prior(POP_FROZEN, k, NamedStreams(9100 + k))
    lib = FiniteLibrary(lib_frozen.coefficients)
    f = FiniteLibraryPredictor(lib_frozen)
    rng = np.random.default_rng(77 + k)
    worst = 0.0
    for n, r in ((1, 1.0), (3, 4.0), (20, 1.0)):
        ctx = _random_contexts(rng, 15, n, r)
        st = ContextStats.from_contexts(ctx)
        for i in range(ctx.shape[0]):
            pred = f.predict(harness.make_context(ctx[i], n), 1)
            ys = pred.quantile(np.array([1e-3, 0.3, 0.5, 0.7, 1 - 1e-3]))
            got = lib.logpdf(ContextStats(st.sxx[i:i + 1], st.sxy[i:i + 1], st.last[i:i + 1]), ys[None, :])[0]
            worst = max(worst, float(np.max(np.abs(got - pred.logpdf(ys)))))
    assert worst <= TOL, worst


def test_log_ndtr_diff_tails_and_symmetry():
    from scipy import special
    lo = np.array([-1.0, -40.0, 30.0, 5.0, -3.0])
    hi = np.array([1.0, -38.0, 31.0, 6.0, 40.0])
    got = log_ndtr_diff(lo, hi)
    # reference: mpmath-free check with high-precision identities where direct subtraction is safe
    direct = np.log(special.ndtr(hi[[0, 4]]) - special.ndtr(lo[[0, 4]]))
    assert np.allclose(got[[0, 4]], direct, rtol=0, atol=1e-14)
    # reflection symmetry Phi(b) - Phi(a) = Phi(-a) - Phi(-b)
    assert np.allclose(log_ndtr_diff(-hi, -lo), got, rtol=0, atol=1e-12)
    assert np.all(np.isfinite(got))
    with pytest.raises(ValueError):
        log_ndtr_diff(np.array([1.0]), np.array([1.0]))


def _stage05_rows():
    idx = list(csv.DictReader(open(STAGE05 / "item_contrasts_index.csv")))
    return idx, np.load(STAGE05 / "item_contrasts.npy", mmap_mode="r")


@pytest.mark.skipif(not (STAGE05 / "item_contrasts.npy").exists(), reason="Stage 0.5 results not present")
@pytest.mark.parametrize("r_idx", [0, 1, 2])
def test_reproduces_stored_stage05_items(r_idx):
    """Regenerate the first 300 items of every E-CONT, h = 1 cell (seeds from config/stage05.yaml: evaluation
    52101 / 52102, library 52001) and reproduce the stored per-item contrasts matched - stability and
    library_K - matched."""
    r = (0.25, 1.0, 4.0)[r_idx]
    n_items, length = 300, 25           # length = max n (20) + max h (5), as in the Stage 0.5 run
    cond = ContinuousPriorCondition(POP_FROZEN, InitialStateSpec(0.0, r))
    libs = {k: FiniteLibrary(build_library_from_prior(POP_FROZEN, k, NamedStreams(52001)).coefficients)
            for k in (2, 4, 8)}
    pop, stab = population_prior(), stability_prior()
    idx, arr = _stage05_rows()
    worst = 0.0
    checked = 0
    for rep, seed in (("R1", 52101), ("R2", 52102)):
        split = generate_split(cond, SplitRole.EVALUATION, NamedStreams(seed), n_items, length)
        for n in (1, 2, 3, 5, 10, 20):
            ctx = np.stack([harness.make_context(split.trajectories[i], n).values for i in range(n_items)])
            y = np.array(split.trajectories[:, n + 1])
            st = ContextStats.from_contexts(ctx)
            lp, ls = pop.logpdf(st, y), stab.logpdf(st, y)
            want = {f"{rep}|matched_minus_frontier_ctx": lp - ls}
            for k, lib in libs.items():
                want[f"{rep}|library_minus_continuous|K{k}"] = lib.logpdf(st, y) - lp
            for row in idx:
                if (row["condition"] == "E-CONT" and int(row["h"]) == 1 and int(row["n"]) == n
                        and float(row["r"]) == r and row["key"] in want):
                    stored = np.asarray(arr[int(row["row"])][:n_items])
                    worst = max(worst, float(np.max(np.abs(stored - want[row["key"]]))))
                    checked += 1
    assert checked == 2 * 6 * 4, checked
    assert worst <= TOL, worst
