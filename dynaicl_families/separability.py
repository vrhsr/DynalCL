"""Separability map for Stage 1A (scalar AR(1), known sigma, h = 1): where do the Bayes references differ by >= delta?

Spec: docs/STAGE1_SEPARABILITY_MAP_SPEC.md (written before the map was run). References only, CPU only, no model.

Estimands per (evaluation set, r, n, pair):
* truth-matched pairs (A is Bayes for the evaluation distribution D): gap = E_D[LS(A) - LS(B)] = E_D[KL(A || B)];
  estimated by realized targets (unbiased) and, where cheap, by per-context KL (Rao-Blackwellised);
* other pairs: behavioural divergences E[KL(A || B)] and E[KL(B || A)] (both reported; the map uses the smaller).

Window constants (DERIVED; each excluded mass is far below the 1e-8 mass check enforced at run time):
* A_WINDOW_SD = 10: a Gaussian posterior kernel's mass beyond 10 sd is about 1.5e-23;
* PINNED_SD = 6: if the kernel's mode lies beyond the support edge by more than 10 sd, the truncated density decays
  at least like exp(-10 t / s) inward, so beyond t = 6 s it is below e^-60;
* Y_HALF_WIDTH = 12 sigma: each predictive component is N(a c, sigma^2) and the mass beyond 12 sd is about 3.6e-33;
* LIB_LOG_WEIGHT_FLOOR = -60: library atoms whose relative posterior weight is below e^-60 only place the window;
  they are still included in every density evaluation.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from dynaicl.rng import NamedStreams, stable_name_key
from dynaicl.systems.conditions import ContinuousPriorCondition, InitialStateSpec, LibraryCondition
from dynaicl.systems.library import build_library_from_prior
from dynaicl.systems.priors import StableCoefficientPrior
from dynaicl.systems.splits import assert_no_unintended_overlap, assert_parameters_disjoint
from dynaicl_families.ar1_known_sigma import (ContextStats, FiniteLibrary, TruncatedGaussianPrior, population_prior,
                                              stability_prior)
from dynaicl_families.kl import kl_quadrature
from dynaicl_families.sampling import OutOfSupportCondition, ProbeGridCondition, contexts_and_targets, simulate

FLOAT = np.float64
A_WINDOW_SD = 10.0
PINNED_SD = 6.0
Y_HALF_WIDTH = 12.0
LIB_LOG_WEIGHT_FLOOR = -60.0
MASS_TOL = 1e-8

#: The frozen population prior object (for simulation through the frozen conditions).
POP_FROZEN = StableCoefficientPrior(rho=0.95, sigma=1.0, shape="truncated_normal", mu0=0.4, tau0=0.3)


def reference_window(ref, st: ContextStats) -> tuple[np.ndarray, np.ndarray]:
    """y-window [lo, hi] holding all but a negligible fraction of ref's one-step predictive mass, per context."""
    c = st.last
    if isinstance(ref, TruncatedGaussianPrior):
        m, s = ref.posterior(st)
        lo_a = np.maximum(-ref.rho, m - A_WINDOW_SD * s)
        hi_a = np.minimum(ref.rho, m + A_WINDOW_SD * s)
        pinned = lo_a > hi_a                       # kernel more than 10 sd outside the support
        pin_hi = pinned & (m > 0)                  # mass piles at +rho
        pin_lo = pinned & (m < 0)                  # mass piles at -rho
        lo_a = np.where(pin_hi, np.maximum(-ref.rho, ref.rho - PINNED_SD * s), lo_a)
        hi_a = np.where(pin_hi, ref.rho, hi_a)
        hi_a = np.where(pin_lo, np.minimum(ref.rho, -ref.rho + PINNED_SD * s), hi_a)
        lo_a = np.where(pin_lo, -ref.rho, lo_a)
        e1, e2 = lo_a * c, hi_a * c
        sig = ref.sigma
    elif isinstance(ref, FiniteLibrary):
        lw = ref.posterior_log_weights(st)
        keep = lw >= LIB_LOG_WEIGHT_FLOOR
        mu = ref.atoms[None, :] * c[:, None]
        e1 = np.where(keep, mu, np.inf).min(axis=1)
        e2 = np.where(keep, mu, -np.inf).max(axis=1)
        sig = ref.sigma
    else:
        raise TypeError(f"no window rule for {type(ref).__name__}")
    lo = np.minimum(e1, e2) - Y_HALF_WIDTH * sig
    hi = np.maximum(e1, e2) + Y_HALF_WIDTH * sig
    return lo, hi


def _sub(st: ContextStats, idx: np.ndarray) -> ContextStats:
    return ContextStats(st.sxx[idx], st.sxy[idx], st.last[idx])


def kl_per_context(p, q, st: ContextStats, panel_width: float = 0.5) -> np.ndarray:
    """KL(p || q) per context; raises if the window misses more than MASS_TOL of p's mass."""
    lo, hi = reference_window(p, st)
    kl, mass = kl_quadrature(lambda i, y: p.logpdf(_sub(st, i), y), lambda i, y: q.logpdf(_sub(st, i), y),
                             lo, hi, panel_width)
    err = float(np.max(np.abs(mass - 1.0)))
    if err > MASS_TOL:
        raise FloatingPointError(f"KL window lost mass {err:.2e} > {MASS_TOL}")
    return kl


def summary(d: np.ndarray) -> dict:
    d = np.asarray(d, dtype=FLOAT)
    return {"mean": float(d.mean()), "sd": float(d.std(ddof=1)), "n_items": int(d.size)}


@dataclass(frozen=True)
class MapConfig:
    root_seed: int
    r_list: tuple[float, ...] = (0.25, 1.0, 4.0)
    n_q1: tuple[int, ...] = (1, 2, 3, 5, 10, 20, 40, 80)
    n_q2: tuple[int, ...] = (1, 2, 3, 5, 10, 20)
    k_list: tuple[int, ...] = (1, 2, 4, 8, 16, 32, 64, 256)
    draws_small_k: int = 32          # K <= 64
    draws_large_k: int = 16          # K = 256
    n_q1_held: int = 40000
    n_q1_probe_oos: int = 10000
    n_q2_realized: int = 20000
    n_q2_kl: int = 2000
    probe_grid: tuple[float, ...] = tuple(round(-0.95 + 0.05 * i, 2) for i in range(39))
    oos_lo: float = 0.95
    oos_hi: float = 0.999

    def draws(self, k: int) -> int:
        return self.draws_small_k if k <= 64 else self.draws_large_k


def derived_seed(root: int, label: str, *path: int) -> int:
    """A 32-bit seed for an independent sub-experiment, from SeedSequence(root, spawn_key=(sha256(label), *path))."""
    ss = np.random.SeedSequence(entropy=int(root), spawn_key=(stable_name_key(label), *[int(p) for p in path]))
    return int(ss.generate_state(1, dtype=np.uint32)[0])


def _conditions(cfg: MapConfig, r: float) -> dict:
    x0 = InitialStateSpec(0.0, r)
    return {"HELD": ContinuousPriorCondition(POP_FROZEN, x0),
            "PROBE": ProbeGridCondition(cfg.probe_grid, 1.0, x0),
            "OOS": OutOfSupportCondition(cfg.oos_lo, cfg.oos_hi, 1.0, x0)}


def run_q1(cfg: MapConfig, r: float) -> list[dict]:
    """Q1 pair (pop, stab) on held-out, probe and out-of-support systems, for one initial scale r."""
    pop, stab = population_prior(), stability_prior()
    streams = NamedStreams(cfg.root_seed)
    conds = _conditions(cfg, r)
    length = max(cfg.n_q1) + 2
    splits = {"HELD": simulate(conds["HELD"], streams, cfg.n_q1_held, length),
              "PROBE": simulate(conds["PROBE"], streams, cfg.n_q1_probe_oos, length),
              "OOS": simulate(conds["OOS"], streams, cfg.n_q1_probe_oos, length)}
    names = list(splits)
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            assert_no_unintended_overlap(splits[names[i]], splits[names[j]])
    rows = []
    for set_name, split in splits.items():
        for n in cfg.n_q1:
            ctx, y = contexts_and_targets(split, n)
            st = ContextStats.from_contexts(ctx)
            base = {"family": "1A", "set": set_name, "r": r, "n": n, "pair": "pop|stab", "K": 0, "draw": -1}
            d = pop.logpdf(st, y) - stab.logpdf(st, y)
            k_ps = kl_per_context(pop, stab, st)
            rows.append({**base, "estimator": "realized LS(pop)-LS(stab)", **summary(d)})
            rows.append({**base, "estimator": "KL(pop||stab)", **summary(k_ps)})
            rows.append({**base, "estimator": "KL(stab||pop)", **summary(kl_per_context(stab, pop, st))})
            if set_name == "HELD":       # validity check: paired realized minus Rao-Blackwell (expectation 0)
                rows.append({**base, "estimator": "CHECK realized-minus-KL", **summary(d - k_ps)})
    return rows


def run_q2_unit(cfg: MapConfig, k: int, draw: int) -> list[dict]:
    """Q2 pairs (lib_K, pop) and (lib_K, stab) for one library draw: held-out, in-library, probe, out-of-support."""
    pop, stab = population_prior(), stability_prior()
    lib_frozen = build_library_from_prior(POP_FROZEN, k, NamedStreams(cfg.root_seed),
                                          stream_name=f"stage1_map_library/draw{draw}")
    lib = FiniteLibrary(lib_frozen.coefficients)
    streams = NamedStreams(cfg.root_seed)
    inlib_streams = NamedStreams(derived_seed(cfg.root_seed, "stage1_map_inlib", draw, k))
    rows = []
    length = max(cfg.n_q2) + 2
    for r in cfg.r_list:
        conds = _conditions(cfg, r)
        held = simulate(conds["HELD"], streams, cfg.n_q2_realized, length)
        assert_parameters_disjoint(held, lib_frozen)
        inlib = simulate(LibraryCondition(lib_frozen, InitialStateSpec(0.0, r)), inlib_streams, cfg.n_q2_realized,
                         length)
        probe = simulate(conds["PROBE"], streams, cfg.n_q2_kl, length)
        oos = simulate(conds["OOS"], streams, cfg.n_q2_kl, length)
        assert_no_unintended_overlap(held, inlib)
        for n in cfg.n_q2:
            base = {"family": "1A", "r": r, "n": n, "K": k, "draw": draw}
            ctx, y = contexts_and_targets(held, n)
            st = ContextStats.from_contexts(ctx)
            d = pop.logpdf(st, y) - lib.logpdf(st, y)
            rows.append({**base, "set": "HELD", "pair": "lib|pop", "estimator": "realized LS(pop)-LS(lib)",
                         **summary(d)})
            sub = np.arange(min(cfg.n_q2_kl, st.size))
            sk = _sub(st, sub)
            k_pl = kl_per_context(pop, lib, sk)
            rows.append({**base, "set": "HELD", "pair": "lib|pop", "estimator": "KL(pop||lib)", **summary(k_pl)})
            rows.append({**base, "set": "HELD", "pair": "lib|pop", "estimator": "CHECK realized-minus-KL",
                         **summary(d[sub] - k_pl)})
            rows.append({**base, "set": "HELD", "pair": "lib|stab", "estimator": "KL(lib||stab)",
                         **summary(kl_per_context(lib, stab, sk))})
            rows.append({**base, "set": "HELD", "pair": "lib|stab", "estimator": "KL(stab||lib)",
                         **summary(kl_per_context(stab, lib, sk))})
            ctx, y = contexts_and_targets(inlib, n)
            st = ContextStats.from_contexts(ctx)
            ll = lib.logpdf(st, y)
            rows.append({**base, "set": "INLIB", "pair": "lib|pop", "estimator": "realized LS(lib)-LS(pop)",
                         **summary(ll - pop.logpdf(st, y))})
            rows.append({**base, "set": "INLIB", "pair": "lib|stab", "estimator": "realized LS(lib)-LS(stab)",
                         **summary(ll - stab.logpdf(st, y))})
            for set_name, split in (("PROBE", probe), ("OOS", oos)):
                ctx, _ = contexts_and_targets(split, n)
                st = ContextStats.from_contexts(ctx)
                for other_name, other in (("pop", pop), ("stab", stab)):
                    rows.append({**base, "set": set_name, "pair": f"lib|{other_name}",
                                 "estimator": f"KL(lib||{other_name})", **summary(kl_per_context(lib, other, st))})
                    rows.append({**base, "set": set_name, "pair": f"lib|{other_name}",
                                 "estimator": f"KL({other_name}||lib)", **summary(kl_per_context(other, lib, st))})
    return rows
