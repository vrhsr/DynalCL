"""Evaluation distributions for the Stage 1A separability map, and batch context cutting.

Held-out (population prior) and in-library systems use the frozen conditions (``ContinuousPriorCondition``,
``LibraryCondition``). Two extra system distributions are defined here with the same interface:

* ``ProbeGridCondition``: a drawn uniformly from a fixed grid of coefficient values;
* ``OutOfSupportCondition``: |a| ~ U(lo, hi) with a random sign, outside the population prior's support (0.95, 0.999).

Simulation goes through the frozen ``generate_split`` (same streams, simulator and leakage-relevant layout), and every
context is cut by the frozen ``harness.make_context`` (the only place contexts are cut, CLAUDE.md section 4).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from dynaicl.evaluation import harness
from dynaicl.rng import NamedStreams
from dynaicl.systems.conditions import InitialStateSpec
from dynaicl.systems.priors import LIKELIHOOD_ID, canonical_fingerprint
from dynaicl.systems.splits import DataSplit, SplitRole, generate_split

FLOAT = np.float64


@dataclass(frozen=True)
class ProbeGridCondition:
    grid: tuple[float, ...]
    sigma: float = 1.0
    initial_state: InitialStateSpec = InitialStateSpec()
    name: str = "PROBE"
    stream_code: int = 2

    def system_distribution_fingerprint(self) -> str:
        return canonical_fingerprint({"family": "PROBE-GRID", "grid": [float(g) for g in self.grid],
                                      "sigma": float(self.sigma), "likelihood": LIKELIHOOD_ID})

    def draw_system(self, rng: np.random.Generator) -> tuple[float, float, str]:
        # deterministic cycling needs the item index, which generate_split does not pass; draw uniformly instead
        k = int(rng.integers(len(self.grid)))
        return float(self.grid[k]), float(self.sigma), f"grid-{k}"


@dataclass(frozen=True)
class OutOfSupportCondition:
    lo: float = 0.95
    hi: float = 0.999
    sigma: float = 1.0
    initial_state: InitialStateSpec = InitialStateSpec()
    name: str = "OOS"
    stream_code: int = 3

    def system_distribution_fingerprint(self) -> str:
        return canonical_fingerprint({"family": "OUT-OF-SUPPORT", "lo": self.lo, "hi": self.hi,
                                      "sigma": float(self.sigma), "likelihood": LIKELIHOOD_ID})

    def draw_system(self, rng: np.random.Generator) -> tuple[float, float, str]:
        mag = self.lo + (self.hi - self.lo) * rng.uniform()
        sign = 1.0 if rng.uniform() < 0.5 else -1.0
        return float(sign * mag), float(self.sigma), "oos"


@dataclass(frozen=True)
class F1PopulationCondition:
    """F1 population P_F1 (docs/MATH_F1.md section 1): a ~ TN(mu0, tau0^2; +/-rho), sigma^2 ~ IG(alpha0, beta0),
    independent; x_0 ~ N(0, r^2) independent of both."""

    rho: float = 0.95
    mu0: float = 0.4
    tau0: float = 0.3
    alpha0: float = 3.0
    beta0: float = 2.0
    initial_state: InitialStateSpec = InitialStateSpec()
    name: str = "F1-POP"
    stream_code: int = 4

    def system_distribution_fingerprint(self) -> str:
        return canonical_fingerprint({"family": "F1-POP", "rho": self.rho, "mu0": self.mu0, "tau0": self.tau0,
                                      "alpha0": self.alpha0, "beta0": self.beta0, "likelihood": LIKELIHOOD_ID})

    def draw_system(self, rng: np.random.Generator) -> tuple[float, float, str]:
        from scipy import special
        lo, hi = (-self.rho - self.mu0) / self.tau0, (self.rho - self.mu0) / self.tau0
        plo, phi = special.ndtr(lo), special.ndtr(hi)
        a = self.mu0 + self.tau0 * special.ndtri(plo + rng.uniform() * (phi - plo))
        a = float(np.clip(a, np.nextafter(-self.rho, 0.0), np.nextafter(self.rho, 0.0)))
        sigma2 = self.beta0 / rng.gamma(shape=self.alpha0, scale=1.0)
        return a, float(np.sqrt(sigma2)), "f1"


def simulate(condition, streams: NamedStreams, n_items: int, length: int) -> DataSplit:
    """Trajectories x_0..x_length via the frozen ``generate_split`` (selection-role streams of ``streams``)."""
    return generate_split(condition, SplitRole.SELECTION, streams, n_items, length)


def contexts_and_targets(split: DataSplit, n: int, horizon: int = 1) -> tuple[np.ndarray, np.ndarray]:
    """(N, n + 1) contexts cut one by one with ``harness.make_context``, and the targets x_{n+h} (evaluator side)."""
    if split.trajectories.shape[1] < n + horizon + 1:
        raise ValueError("trajectories too short")
    ctx = np.stack([harness.make_context(split.trajectories[i], n).values for i in range(split.size)])
    return ctx, np.array(split.trajectories[:, n + horizon], dtype=FLOAT)
