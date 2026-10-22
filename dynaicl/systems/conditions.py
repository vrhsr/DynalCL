"""Evaluation conditions (Section 2.3).

An evaluation condition is a data-generating distribution D: a distribution over systems plus the
AR(1) likelihood, with x_0 drawn independently of the system. Its fingerprint identifies the
distribution over systems together with the likelihood. The matched Bayes reference must carry the
same fingerprint (references/matched.py).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from dynaicl.systems.library import SystemLibrary
from dynaicl.systems.priors import (
    LIKELIHOOD_ID,
    ContinuousPrior,
    canonical_fingerprint,
)

FLOAT = np.float64


@dataclass(frozen=True)
class InitialStateSpec:
    """x_0 ~ N(mean, sd^2), independent of the system. sd = 0 gives a fixed x_0 = mean."""

    mean: float = 0.0
    sd: float = 1.0

    def __post_init__(self) -> None:
        if not (np.isfinite(self.mean) and np.isfinite(self.sd) and self.sd >= 0):
            raise ValueError("initial state mean must be finite and sd >= 0")

    def spec(self) -> dict:
        return {"mean": float(self.mean), "sd": float(self.sd), "independent_of_system": True}


@dataclass(frozen=True)
class ContinuousPriorCondition:
    """E-CONT: systems drawn fresh from the continuous prior (held-out systems)."""

    prior: ContinuousPrior
    initial_state: InitialStateSpec = InitialStateSpec()
    name: str = "E-CONT"
    stream_code: int = 0

    def system_distribution_fingerprint(self) -> str:
        """Fingerprint of (system distribution, likelihood); equals ``prior.fingerprint()``."""
        return self.prior.fingerprint()

    def spec(self) -> dict:
        return {"name": self.name, "system_distribution": self.prior.spec(),
                "initial_state": self.initial_state.spec(), "likelihood": LIKELIHOOD_ID}

    def fingerprint(self) -> str:
        return canonical_fingerprint(self.spec())

    def draw_system(self, rng: np.random.Generator) -> tuple[float, float, str]:
        a, s = self.prior.sample_systems(rng, 1)
        return float(a[0]), float(s[0]), "continuous"


@dataclass(frozen=True)
class LibraryCondition:
    """E-LIB: systems drawn from library atoms with the library weights; fresh noise and trajectories."""

    library: SystemLibrary
    initial_state: InitialStateSpec = InitialStateSpec()
    name: str = "E-LIB"
    stream_code: int = 1

    def system_distribution_fingerprint(self) -> str:
        return self.library.fingerprint()

    def spec(self) -> dict:
        return {"name": self.name, "system_distribution": self.library.spec(),
                "initial_state": self.initial_state.spec(), "likelihood": LIKELIHOOD_ID}

    def fingerprint(self) -> str:
        return canonical_fingerprint(self.spec())

    def draw_system(self, rng: np.random.Generator) -> tuple[float, float, str]:
        k = int(rng.choice(self.library.size, p=self.library.weights))
        return float(self.library.coefficients[k]), float(self.library.noise_scales[k]), f"atom-{k}"


EvaluationCondition = ContinuousPriorCondition | LibraryCondition
