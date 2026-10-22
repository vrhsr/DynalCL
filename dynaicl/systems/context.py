"""Information-access boundary (Section 3).

Predictors receive only a :class:`ContextWindow`: an immutable float64 vector x_0..x_n. Ground
truth (a, sigma, target, future values, seeds) lives in :class:`GroundTruth`, which only the
evaluator holds. ``ContextWindow`` uses ``__slots__`` and a read-only copy of the data, so nothing
else can be attached to it or changed later.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


class ContextWindow:
    """Immutable observed context x_0..x_n (n transitions). x_0 must be the trajectory's initial state."""

    __slots__ = ("_values",)

    def __init__(self, values: np.ndarray):
        if not isinstance(values, np.ndarray):
            raise TypeError("ContextWindow requires a numpy.ndarray")
        if values.dtype != np.float64:
            raise TypeError(f"ContextWindow requires float64 input, got {values.dtype} (cast explicitly)")
        if values.ndim != 1 or values.shape[0] < 1:
            raise ValueError("ContextWindow requires a 1-D array with at least x_0")
        if not np.all(np.isfinite(values)):
            raise ValueError("ContextWindow values must be finite")
        frozen = np.array(values, dtype=np.float64, copy=True)
        frozen.setflags(write=False)
        object.__setattr__(self, "_values", frozen)

    def __setattr__(self, name, value):
        raise AttributeError("ContextWindow is immutable")

    @property
    def values(self) -> np.ndarray:
        """Read-only view of x_0..x_n."""
        return self._values

    @property
    def n_transitions(self) -> int:
        return int(self._values.shape[0] - 1)

    @property
    def last(self) -> float:
        return float(self._values[-1])

    def __len__(self) -> int:
        return int(self._values.shape[0])

    def __repr__(self) -> str:
        return f"ContextWindow(n={self.n_transitions})"

    def __eq__(self, other) -> bool:
        return isinstance(other, ContextWindow) and np.array_equal(self._values, other._values)

    def __hash__(self) -> int:
        return hash(self._values.tobytes())


@dataclass(frozen=True)
class GroundTruth:
    """Evaluator-private truth for one evaluation item. Never passed to a predictor."""

    item_index: int
    a: float
    sigma: float
    system_id: str
    target: float
    horizon: int
    trajectory_sha256: str
