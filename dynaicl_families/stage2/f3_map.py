"""F3 short-context separability map (docs/STAGE2_F3_MAP_SPEC.md): noisy-observation AR(1), frozen Stage 0.6 references.

Everything numerical is frozen Stage 0.6 code used read-only: ``generate_noisy_split`` (systems, x_0, process and
observation noise), ``make_noisy_context`` via ``build_noisy_evaluation`` (the only context cut), the population and
noise-aware stability references (``NoisyObservationBayesPredictor.batch_scores``), and, for the library, the frozen
``kalman_filter_on_nodes`` / ``observation_predictive_moments`` / ``mixture_logpdf_cdf`` evaluated at the atom values with
uniform prior mass (the library posterior given the atoms; analytically exact in float64).
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

import numpy as np
from scipy import special

from dynaicl.evaluation.noisy_harness import build_noisy_evaluation
from dynaicl.references.kalman_quadrature import (KalmanQuadratureSettings, kalman_filter_on_nodes,
                                                  mixture_logpdf_cdf, noise_aware_stability_predictor,
                                                  noisy_population_reference, observation_predictive_moments)
from dynaicl.rng import NamedStreams
from dynaicl.systems.noisy import NoisyObservationCondition, NoisyObservationModel, generate_noisy_split
from dynaicl.systems.priors import StableCoefficientPrior
from dynaicl.systems.splits import SplitRole

FLOAT = np.float64
QS = (0.0, 0.755, 2.56, 6.5)
RS = (0.25, 1.0, 4.0)
HS = (1, 5)
NS = (2, 3, 4, 5, 6, 7, 8, 9)
KS = (2, 4, 16, 64)
DRAWS = 16
DELTA = 0.02
Z_BOUND = 3.0


def population_prior() -> StableCoefficientPrior:
    """Stage 0.6 population prior P-STABLE: a ~ TN(0.4, 0.3^2) on (-0.95, 0.95), sigma_w = 1."""
    return StableCoefficientPrior(rho=0.95, sigma=1.0, shape="truncated_normal", mu0=0.4, tau0=0.3)


def model_for(q: float, r: float) -> NoisyObservationModel:
    return NoisyObservationModel(sigma_w=1.0, sigma_v=float(np.sqrt(q)), x0_sd=float(r))


@dataclass(frozen=True)
class AtomPrior:
    """Systems drawn uniformly from a finite set of atoms (for in-library evaluation through the frozen split generator)."""

    atoms: tuple[float, ...]
    sigma: float = 1.0
    family: str = "LIBRARY-ATOMS"

    def spec(self) -> dict:
        return {"family": self.family, "atoms": [float(a) for a in self.atoms], "sigma": float(self.sigma)}

    def sample_systems(self, rng: np.random.Generator, size: int) -> tuple[np.ndarray, np.ndarray]:
        k = rng.integers(len(self.atoms), size=size)
        return np.asarray(self.atoms, dtype=FLOAT)[k], np.full(size, self.sigma, dtype=FLOAT)


def library_atoms(root: int, draw: int, k_max: int = max(KS)) -> np.ndarray:
    """Atoms of one library draw, nested across K (the first K of the draw), from the population prior."""
    a, _ = population_prior().sample_systems(NamedStreams(root).stream(f"f3_map_library/draw{draw}"), k_max)
    return a


def library_scores(atoms: np.ndarray, model: NoisyObservationModel, ctx: np.ndarray, targets: dict,
                   ns: tuple[int, ...], hs: tuple[int, ...]) -> dict:
    """Log scores of the library posterior predictive (uniform prior over ``atoms``) for every (n, h)."""
    f = kalman_filter_on_nodes(ctx, atoms, model, ns)
    out = {}
    for n in ns:
        ll = f["loglik"][n]
        lw = ll - special.logsumexp(ll, axis=1, keepdims=True)
        for h in hs:
            mean, var = observation_predictive_moments(atoms[None, :], f["m"][n], f["P"][n][None, :], model, h)
            lp, _ = mixture_logpdf_cdf(lw, mean, var, targets[(n, h)])
            out[(n, h)] = lp
    return out


def inlib_seed(root: int, draw: int, k: int) -> int:
    ss = np.random.SeedSequence(root, spawn_key=(int.from_bytes(hashlib.sha256(b"f3_map_inlib").digest()[:4], "little"),
                                                 draw, k))
    return int(ss.generate_state(1, dtype=np.uint32)[0])


def _gap(lp_truth: np.ndarray, lp_other: np.ndarray) -> dict:
    d = lp_truth - lp_other
    se = float(d.std(ddof=1) / np.sqrt(d.size))
    return {"mean": float(d.mean()), "se": se, "sd": float(d.std(ddof=1)), "n_items": int(d.size)}


def held_unit(q: float, r: float, root: int, n_items: int, settings: KalmanQuadratureSettings | None = None) -> dict:
    """HELD set for one (q, r): gaps (pop, stab) and, per library draw and K, (pop, lib) with truth = pop."""
    settings = settings or KalmanQuadratureSettings()
    model = model_for(q, r)
    cond = NoisyObservationCondition(population_prior(), model, name="F3-HELD", stream_code=0)
    split = generate_noisy_split(cond, SplitRole.SELECTION, NamedStreams(root), n_items, max(NS) + max(HS))
    es = build_noisy_evaluation(split, NS, HS)
    pop = noisy_population_reference(population_prior(), model, settings).batch_scores(es.context_matrix, es._targets,
                                                                                      NS, HS)
    stab = noise_aware_stability_predictor(model, settings=settings).batch_scores(es.context_matrix, es._targets, NS, HS)
    rows = []
    for n in NS:
        for h in HS:
            rows.append({"set": "HELD", "pair": "pop-stab", "q": q, "r": r, "n": n, "h": h,
                         **_gap(pop[(n, h)][0], stab[(n, h)][0])})
    for draw in range(DRAWS):
        atoms = library_atoms(root, draw)
        for k in KS:
            lib = library_scores(atoms[:k], model, es.context_matrix, es._targets, NS, HS)
            for n in NS:
                for h in HS:
                    rows.append({"set": "HELD", "pair": "pop-lib", "q": q, "r": r, "n": n, "h": h, "K": k,
                                 "draw": draw, **_gap(pop[(n, h)][0], lib[(n, h)])})
    return {"q": q, "r": r, "rows": rows, "held_atoms_overlap": 0}


def inlib_unit(q: float, r: float, k: int, draw: int, root: int, n_items: int,
               settings: KalmanQuadratureSettings | None = None) -> dict:
    """INLIB set for one (q, r, K, draw): systems are the K atoms; gaps (lib, pop) and (lib, stab) with truth = lib."""
    settings = settings or KalmanQuadratureSettings()
    model = model_for(q, r)
    atoms = library_atoms(root, draw)[:k]
    cond = NoisyObservationCondition(AtomPrior(tuple(float(a) for a in atoms)), model, name="F3-INLIB", stream_code=5)
    split = generate_noisy_split(cond, SplitRole.SELECTION, NamedStreams(inlib_seed(root, draw, k)), n_items,
                                 max(NS) + max(HS))
    if not np.all(np.isin(split.latent.coefficients, atoms)):
        raise AssertionError("in-library systems must be library atoms")
    es = build_noisy_evaluation(split, NS, HS)
    lib = library_scores(atoms, model, es.context_matrix, es._targets, NS, HS)
    pop = noisy_population_reference(population_prior(), model, settings).batch_scores(es.context_matrix, es._targets,
                                                                                      NS, HS)
    stab = noise_aware_stability_predictor(model, settings=settings).batch_scores(es.context_matrix, es._targets, NS, HS)
    rows = []
    for n in NS:
        for h in HS:
            rows.append({"set": "INLIB", "pair": "lib-pop", "q": q, "r": r, "n": n, "h": h, "K": k, "draw": draw,
                         **_gap(lib[(n, h)], pop[(n, h)][0])})
            rows.append({"set": "INLIB", "pair": "lib-stab", "q": q, "r": r, "n": n, "h": h, "K": k, "draw": draw,
                         **_gap(lib[(n, h)], stab[(n, h)][0])})
    return {"q": q, "r": r, "K": k, "draw": draw, "rows": rows}


def classify(mean: float, se: float) -> str:
    lo, hi = mean - Z_BOUND * se, mean + Z_BOUND * se
    if lo >= DELTA:
        return "IDENTIFIABLE"
    if hi < DELTA:
        return "UNIDENTIFIABLE"
    return "BORDERLINE"


def classify_draws(labels: list[str]) -> str:
    frac_id = sum(lab == "IDENTIFIABLE" for lab in labels) / len(labels)
    frac_un = sum(lab == "UNIDENTIFIABLE" for lab in labels) / len(labels)
    if frac_id >= 0.9:
        return "IDENTIFIABLE"
    if frac_un >= 0.9:
        return "UNIDENTIFIABLE"
    return "PARTIAL"
