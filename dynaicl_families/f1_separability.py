"""F1 separability map (docs/STAGE1_F1_SEPARABILITY_MAP_SPEC.md): AR(1) with unknown noise scale, h = 1, references only.

Separation measure: the expected log-score gap E_D[LS(A) - LS(B)] on each evaluation distribution D, estimated from realized
targets (unbiased). For truth-matched pairs it equals E[KL(A || B)] (DERIVED, as in Stage 1A); for the other sets it is the
score difference under the true system law. The behavioural KL used in Stage 1A is NOT used here: the context-only F1
predictive has polynomial tails (scale-invariant sigma prior), so KL from it into a Gaussian library is infinite at n = 2
(the predictive has no second moment; DERIVED: tails |y|^-(n+1)), and score gaps stay finite and unbiased.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from dynaicl.rng import NamedStreams
from dynaicl.systems.conditions import InitialStateSpec, LibraryCondition
from dynaicl.systems.library import SystemLibrary
from dynaicl.systems.priors import LIKELIHOOD_ID, canonical_fingerprint
from dynaicl.systems.splits import assert_no_unintended_overlap
from dynaicl_families.ar1_unknown_sigma import (F1Stats, ScaleLibrary, UnknownScaleReference, context_only_f1,
                                                population_f1)
from dynaicl_families.sampling import F1PopulationCondition, contexts_and_targets, simulate
from dynaicl_families.separability import derived_seed, summary

FLOAT = np.float64
NODE_DOUBLING_TOL = 1e-6        # nats; MATH_F1 section 6 (four orders below delta)


@dataclass(frozen=True)
class F1ProbeCondition:
    """(a, sigma) drawn uniformly from a fixed grid."""

    a_grid: tuple[float, ...]
    s_grid: tuple[float, ...]
    initial_state: InitialStateSpec = InitialStateSpec()
    name: str = "F1-PROBE"
    stream_code: int = 5

    def system_distribution_fingerprint(self) -> str:
        return canonical_fingerprint({"family": "F1-PROBE", "a": list(self.a_grid), "s": list(self.s_grid),
                                      "likelihood": LIKELIHOOD_ID})

    def draw_system(self, rng: np.random.Generator) -> tuple[float, float, str]:
        i, j = int(rng.integers(len(self.a_grid))), int(rng.integers(len(self.s_grid)))
        return float(self.a_grid[i]), float(self.s_grid[j]), f"grid-{i}-{j}"


@dataclass(frozen=True)
class F1OutOfSupportA:
    """|a| ~ U(0.95, 0.999) with a random sign; sigma^2 from the population IG(3, 2)."""

    initial_state: InitialStateSpec = InitialStateSpec()
    name: str = "F1-OOS-A"
    stream_code: int = 6

    def system_distribution_fingerprint(self) -> str:
        return canonical_fingerprint({"family": "F1-OOS-A", "likelihood": LIKELIHOOD_ID})

    def draw_system(self, rng: np.random.Generator) -> tuple[float, float, str]:
        mag = 0.95 + 0.049 * rng.uniform()
        sign = 1.0 if rng.uniform() < 0.5 else -1.0
        return float(sign * mag), float(np.sqrt(2.0 / rng.gamma(3.0))), "oos-a"


@dataclass(frozen=True)
class F1OutOfScale:
    """sigma ~ U(2.5, 5) (outside the population's bulk: P(sigma > 2.5) = 0.0043 under IG(3, 2), computed); a from P_F1."""

    initial_state: InitialStateSpec = InitialStateSpec()
    name: str = "F1-OOS-SIGMA"
    stream_code: int = 7

    def system_distribution_fingerprint(self) -> str:
        return canonical_fingerprint({"family": "F1-OOS-SIGMA", "likelihood": LIKELIHOOD_ID})

    def draw_system(self, rng: np.random.Generator) -> tuple[float, float, str]:
        a, _, _ = F1PopulationCondition().draw_system(rng)
        return a, float(2.5 + 2.5 * rng.uniform()), "oos-sigma"


@dataclass(frozen=True)
class F1MapConfig:
    root_seed: int
    r_list: tuple[float, ...] = (0.25, 1.0, 4.0)
    n_list: tuple[int, ...] = (2, 3, 5, 10, 20, 40)
    k_list: tuple[int, ...] = (1, 2, 4, 8, 16, 32, 64, 256)
    draws_small_k: int = 32
    draws_large_k: int = 16
    n_items: int = 20000
    n_q2_items: int = 5000          # first items of each Q1 set, reused by every Q2 unit
    n_inlib: int = 10000
    a_grid: tuple[float, ...] = tuple(round(-0.9 + 0.15 * i, 2) for i in range(13))
    s_grid: tuple[float, ...] = (0.3, 0.5, 1.0, 2.0, 3.0)

    def draws(self, k: int) -> int:
        return self.draws_small_k if k <= 64 else self.draws_large_k


def f1_library(root: int, draw: int, k: int) -> SystemLibrary:
    """First K of 256 atoms (a_k, sigma_k) drawn from P_F1 for library draw ``draw`` (nested across K)."""
    streams = NamedStreams(root)
    cond = F1PopulationCondition()
    a = np.empty(256)
    s = np.empty(256)
    for j in range(256):
        a[j], s[j], _ = cond.draw_system(streams.item(f"stage1_f1_library/draw{draw}", j))
    return SystemLibrary(a[:k], s[:k], np.full(k, 1.0 / k), provenance={"root": root, "draw": draw, "K": k})


def _sets(cfg: F1MapConfig, r: float) -> dict:
    x0 = InitialStateSpec(0.0, r)
    return {"HELD": F1PopulationCondition(initial_state=x0), "PROBE": F1ProbeCondition(cfg.a_grid, cfg.s_grid, x0),
            "OOS-A": F1OutOfSupportA(x0), "OOS-SIGMA": F1OutOfScale(x0)}


def _scores(split, n, refs: dict) -> dict:
    ctx, y = contexts_and_targets(split, n)
    st = F1Stats.from_contexts(ctx)
    return {name: ref.logpdf(st, y) for name, ref in refs.items()}


def run_q1(cfg: F1MapConfig, r: float) -> tuple[list[dict], dict]:
    """Q1 pair (pop, ctx) on every set. Also returns, for each (set, n), the pop and ctx scores and the contexts of the
    first ``n_q2_items`` systems, which every Q2 unit reuses (the same systems; pop / ctx do not depend on the library)."""
    refs = {"pop": population_f1(), "ctx": context_only_f1()}
    streams = NamedStreams(cfg.root_seed)
    length = max(cfg.n_list) + 2
    splits = {name: simulate(c, streams, cfg.n_items, length) for name, c in _sets(cfg, r).items()}
    names = list(splits)
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            assert_no_unintended_overlap(splits[names[i]], splits[names[j]])
    rows, cache = [], {}
    for set_name, split in splits.items():
        for n in cfg.n_list:
            ctx, y = contexts_and_targets(split, n)
            st = F1Stats.from_contexts(ctx)
            s = {name: ref.logpdf(st, y) for name, ref in refs.items()}
            # validity check (run time): node doubling of both references on the first 50 contexts, <= 1e-6 nats
            sub = F1Stats(st.n, st.sxx[:50], st.a_hat[:50], st.r_min[:50], st.last[:50])
            for name, ref in refs.items():
                fine = UnknownScaleReference(ref.coef, ref.scale, refine=2)
                err = float(np.max(np.abs(ref.logpdf(sub, y[:50]) - fine.logpdf(sub, y[:50]))))
                if err > NODE_DOUBLING_TOL:
                    raise FloatingPointError(f"F1 node doubling {name} {set_name} r={r} n={n}: {err:.2e}")
                rows.append({"family": "F1", "set": set_name, "r": r, "n": n, "pair": f"{name}", "K": 0, "draw": -1,
                             "estimator": "CHECK node-doubling max abs", "mean": err, "sd": 0.0, "n_items": 50})
            rows.append({"family": "F1", "set": set_name, "r": r, "n": n, "pair": "pop|ctx", "K": 0, "draw": -1,
                         "estimator": "realized LS(pop)-LS(ctx)", **summary(s["pop"] - s["ctx"])})
            q = cfg.n_q2_items
            cache[f"{set_name}|{n}|ctx"] = ctx[:q]
            cache[f"{set_name}|{n}|y"] = y[:q]
            cache[f"{set_name}|{n}|pop"] = s["pop"][:q]
            cache[f"{set_name}|{n}|ctxref"] = s["ctx"][:q]
    return rows, cache


def run_q2_unit(cfg: F1MapConfig, k: int, draw: int, caches: dict[float, dict]) -> list[dict]:
    """Q2 pairs (lib, pop) and (lib, ctx) for one library draw: the four Q1 sets (cached systems and pop / ctx scores
    from ``run_q1``; ``caches[r]``) plus fresh in-library systems."""
    lib_sys = f1_library(cfg.root_seed, draw, k)
    lib = ScaleLibrary(lib_sys.coefficients, lib_sys.noise_scales)
    pop, ctx_ref = population_f1(), context_only_f1()
    inlib_streams = NamedStreams(derived_seed(cfg.root_seed, "stage1_f1_inlib", draw, k))
    length = max(cfg.n_list) + 2
    rows = []
    for r in cfg.r_list:
        cache = caches[r]
        inlib = simulate(LibraryCondition(lib_sys, InitialStateSpec(0.0, r)), inlib_streams, cfg.n_inlib, length)
        for n in cfg.n_list:
            scored = {}
            for set_name in ("HELD", "PROBE", "OOS-A", "OOS-SIGMA"):
                st = F1Stats.from_contexts(cache[f"{set_name}|{n}|ctx"])
                scored[set_name] = (lib.logpdf(st, cache[f"{set_name}|{n}|y"]), cache[f"{set_name}|{n}|pop"],
                                    cache[f"{set_name}|{n}|ctxref"])
            c_in, y_in = contexts_and_targets(inlib, n)
            st_in = F1Stats.from_contexts(c_in)
            scored["INLIB"] = (lib.logpdf(st_in, y_in), pop.logpdf(st_in, y_in), ctx_ref.logpdf(st_in, y_in))
            for set_name, (sl, sp, sc) in scored.items():
                base = {"family": "F1", "set": set_name, "r": r, "n": n, "K": k, "draw": draw}
                rows.append({**base, "pair": "lib|pop", "estimator": "realized LS(lib)-LS(pop)", **summary(sl - sp)})
                rows.append({**base, "pair": "lib|ctx", "estimator": "realized LS(lib)-LS(ctx)", **summary(sl - sc)})
    return rows
