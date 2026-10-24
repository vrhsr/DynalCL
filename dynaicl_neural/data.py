"""Training-sequence samplers for the Stage 1A arms (PREREG_stage1 section 3).

* Arms differ only in the law of a: CONT (population prior P), UNIF (U(-0.999, 0.999)), LIB-K (uniform over K atoms).
* Common random numbers: for seed index i the uniforms that pick a, the choice of r, x_0's standard normal and the
  innovations come from one stream keyed by (data root, "stage1_data", i), which does NOT depend on the arm. Each arm
  maps
  the same uniform u to its own a by its inverse CDF (LIB-K: atom floor(u K)).
* Library atoms for seed i are the first K of 256 atoms drawn from P with the frozen prior sampler, one child stream per
  atom, so libraries are nested across K.
* Sequences x_0..x_L start at x_0 (no burn-in; CLAUDE.md section 4). sigma = 1.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import special

from dynaicl.rng import NamedStreams, stable_name_key
from dynaicl.systems.library import build_library_from_prior
from dynaicl.systems.priors import StableCoefficientPrior
from dynaicl_neural import mutations

FLOAT = np.float64
POP = StableCoefficientPrior(rho=0.95, sigma=1.0, shape="truncated_normal", mu0=0.4, tau0=0.3)
UNIF_BOUND = 0.999
R_CHOICES = (0.25, 1.0, 4.0)
MAX_LIBRARY = 256


@dataclass(frozen=True)
class ArmSpec:
    kind: str           # "CONT", "UNIF" or "LIB"
    k: int = 0

    def __post_init__(self) -> None:
        if self.kind not in ("CONT", "UNIF", "LIB"):
            raise ValueError(f"unknown arm {self.kind!r}")
        if self.kind == "LIB" and not (1 <= self.k <= MAX_LIBRARY):
            raise ValueError("LIB arm needs 1 <= K <= 256")
        if self.kind != "LIB" and self.k != 0:
            raise ValueError("only LIB arms take K")

    @property
    def name(self) -> str:
        return f"LIB-{self.k}" if self.kind == "LIB" else self.kind


def library_atoms(library_root: int, seed_index: int, k: int) -> np.ndarray:
    """First K of the 256 atoms of model seed ``seed_index`` (nested across K)."""
    streams = NamedStreams(library_root)
    if mutations.active("library_not_nested"):
        lib = build_library_from_prior(POP, k, streams, stream_name=f"stage1_library/seed{seed_index}/K{k}")
        return np.array(lib.coefficients)
    lib = build_library_from_prior(POP, MAX_LIBRARY, streams, stream_name=f"stage1_library/seed{seed_index}")
    return np.array(lib.coefficients[:k])


def a_from_uniform(arm: ArmSpec, u: np.ndarray, atoms: np.ndarray | None = None) -> np.ndarray:
    """Each arm's inverse CDF applied to the same uniforms."""
    if arm.kind == "UNIF":
        return -UNIF_BOUND + 2.0 * UNIF_BOUND * u
    if arm.kind == "CONT":
        mu0 = 0.2 if mutations.active("wrong_prior_cont") else POP.mu0
        lo, hi = (-POP.rho - mu0) / POP.tau0, (POP.rho - mu0) / POP.tau0
        plo, phi = special.ndtr(lo), special.ndtr(hi)
        a = mu0 + POP.tau0 * special.ndtri(plo + u * (phi - plo))
        return np.clip(a, np.nextafter(-POP.rho, 0.0), np.nextafter(POP.rho, 0.0))
    idx = np.minimum((u * atoms.size).astype(int), atoms.size - 1)
    return atoms[idx]


class SequenceSampler:
    """Fresh training batches for one (arm, model seed). Deterministic given (data_root, library_root, seed_index)."""

    def __init__(self, arm: ArmSpec, data_root: int, library_root: int, seed_index: int, batch: int, length: int = 20):
        self.arm, self.batch, self.length = arm, int(batch), int(length)
        key = (stable_name_key("stage1_data"), int(seed_index))
        if mutations.active("unpaired_seeds"):
            key = key + (stable_name_key(arm.name),)
        self.rng = np.random.Generator(np.random.PCG64(np.random.SeedSequence(int(data_root), spawn_key=key)))
        self.atoms = library_atoms(library_root, seed_index, arm.k) if arm.kind == "LIB" else None

    def next_batch(self) -> tuple[np.ndarray, np.ndarray]:
        """(sequences x_0..x_L of shape (B, L + 1), the coefficients a used) in float64."""
        u = self.rng.uniform(size=self.batch)
        r = np.asarray(R_CHOICES)[self.rng.integers(len(R_CHOICES), size=self.batch)]
        z0 = self.rng.standard_normal(self.batch)
        eps = self.rng.standard_normal((self.batch, self.length))
        a = a_from_uniform(self.arm, u, self.atoms)
        x = np.empty((self.batch, self.length + 1), dtype=FLOAT)
        x[:, 0] = r * z0
        for t in range(1, self.length + 1):
            x[:, t] = a * x[:, t - 1] + eps[:, t - 1]
        return x, a
