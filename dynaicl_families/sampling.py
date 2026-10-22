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


def simulate(condition, streams: NamedStreams, n_items: int, length: int) -> DataSplit:
    """Trajectories x_0..x_length via the frozen ``generate_split`` (selection-role streams of ``streams``)."""
    return generate_split(condition, SplitRole.SELECTION, streams, n_items, length)


def contexts_and_targets(split: DataSplit, n: int, horizon: int = 1) -> tuple[np.ndarray, np.ndarray]:
    """(N, n + 1) contexts cut one by one with ``harness.make_context``, and the targets x_{n+h} (evaluator side)."""
    if split.trajectories.shape[1] < n + horizon + 1:
        raise ValueError("trajectories too short")
    ctx = np.stack([harness.make_context(split.trajectories[i], n).values for i in range(split.size)])
    return ctx, np.array(split.trajectories[:, n + horizon], dtype=FLOAT)
