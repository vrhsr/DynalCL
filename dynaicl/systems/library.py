"""Finite library of K AR(1) systems with prior weights pi_k (Section 2.4)."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field

import numpy as np

from dynaicl.rng import NamedStreams
from dynaicl.systems.priors import LIKELIHOOD_ID, canonical_fingerprint

FLOAT = np.float64


def parameter_hash(a: float, sigma: float) -> str:
    """Bitwise hash of one system's parameters (float64 bytes). Used for disjointness checks."""
    return hashlib.sha256(np.array([a, sigma], dtype=FLOAT).tobytes()).hexdigest()


@dataclass(frozen=True, eq=False)
class SystemLibrary:
    """K atoms (a_k, sigma_k) with weights pi_k. Arrays are read-only."""

    coefficients: np.ndarray
    noise_scales: np.ndarray
    weights: np.ndarray
    provenance: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        a = np.array(self.coefficients, dtype=FLOAT, copy=True)
        s = np.array(self.noise_scales, dtype=FLOAT, copy=True)
        w = np.array(self.weights, dtype=FLOAT, copy=True)
        if not (a.ndim == s.ndim == w.ndim == 1 and a.shape == s.shape == w.shape and a.size >= 1):
            raise ValueError("library arrays must be 1-D with equal length K >= 1")
        if not (np.all(np.isfinite(a)) and np.all(s > 0) and np.all(w > 0)):
            raise ValueError("library atoms must be finite, sigma_k > 0, pi_k > 0")
        if abs(w.sum() - 1.0) > 1e-12:
            raise ValueError("library weights must sum to 1 (within 1e-12)")
        for arr in (a, s, w):
            arr.setflags(write=False)
        object.__setattr__(self, "coefficients", a)
        object.__setattr__(self, "noise_scales", s)
        object.__setattr__(self, "weights", w)

    @property
    def size(self) -> int:
        return int(self.coefficients.shape[0])

    def spec(self) -> dict:
        return {
            "family": "FINITE-LIBRARY",
            "atoms_sha256": hashlib.sha256(
                self.coefficients.tobytes() + self.noise_scales.tobytes()).hexdigest(),
            "weights_sha256": hashlib.sha256(self.weights.tobytes()).hexdigest(),
            "K": self.size,
            "likelihood": LIKELIHOOD_ID,
        }

    def fingerprint(self) -> str:
        return canonical_fingerprint(self.spec())

    def parameter_hashes(self) -> frozenset[str]:
        return frozenset(parameter_hash(a, s) for a, s in zip(self.coefficients, self.noise_scales))


def build_library_from_prior(prior, size: int, streams: NamedStreams, weights: np.ndarray | None = None,
                             stream_name: str = "library_systems") -> SystemLibrary:
    """Draw K atoms iid from ``prior``, using one child generator per atom.

    Libraries are nested: the first K atoms of a K' > K library equal the K-atom library.
    """
    if size < 1:
        raise ValueError("library size must be >= 1")
    a = np.empty(size, dtype=FLOAT)
    s = np.empty(size, dtype=FLOAT)
    for k in range(size):
        ak, sk = prior.sample_systems(streams.item(stream_name, k), 1)
        a[k], s[k] = ak[0], sk[0]
    w = np.full(size, 1.0 / size, dtype=FLOAT) if weights is None else np.asarray(weights, dtype=FLOAT)
    return SystemLibrary(a, s, w, provenance={"prior": prior.spec(), "stream": stream_name,
                                              "root_seed": streams.root_seed, "K": size})
