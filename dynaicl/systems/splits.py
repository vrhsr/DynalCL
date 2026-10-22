"""Immutable data splits with role tags, and leakage / disjointness assertions (Section 3).

Intentional *parameter* overlap (E-LIB evaluation systems are library atoms) is distinguished from
unintended *trajectory, noise or target* overlap. The latter must never occur in either condition.
"""

from __future__ import annotations

import enum
import hashlib
from dataclasses import dataclass

import numpy as np

from dynaicl.rng import NamedStreams
from dynaicl.systems.ar1 import simulate_ar1
from dynaicl.systems.conditions import EvaluationCondition, InitialStateSpec
from dynaicl.systems.library import SystemLibrary, parameter_hash

FLOAT = np.float64


class LeakageError(AssertionError):
    """Raised when splits share data they must not share."""


class SplitRole(enum.Enum):
    LIBRARY_TRAIN = "library_train"
    SELECTION = "selection"
    EVALUATION = "evaluation"


#: (systems stream, noise stream) for each role. Separate named streams per role.
ROLE_STREAMS = {
    SplitRole.LIBRARY_TRAIN: ("library_systems", "library_noise"),
    SplitRole.SELECTION: ("selection_systems", "selection_noise"),
    SplitRole.EVALUATION: ("eval_systems", "eval_noise"),
}


def _readonly(arr: np.ndarray) -> np.ndarray:
    out = np.array(arr, copy=True)
    out.setflags(write=False)
    return out


def _row_hashes(arr: np.ndarray) -> frozenset[str]:
    return frozenset(hashlib.sha256(np.ascontiguousarray(r).tobytes()).hexdigest() for r in arr)


@dataclass(frozen=True, eq=False)
class DataSplit:
    """One role's simulated systems and trajectories. Every array is read-only."""

    role: SplitRole
    condition_name: str
    coefficients: np.ndarray       # (N,)
    noise_scales: np.ndarray       # (N,)
    system_ids: tuple[str, ...]
    innovations: np.ndarray        # (N, T) standard normals eps_1..eps_T
    trajectories: np.ndarray       # (N, T + 1) x_0..x_T
    initial_state: InitialStateSpec

    def __post_init__(self) -> None:
        for name in ("coefficients", "noise_scales", "innovations", "trajectories"):
            object.__setattr__(self, name, _readonly(getattr(self, name)))

    @property
    def size(self) -> int:
        return int(self.coefficients.shape[0])

    def parameter_hashes(self) -> frozenset[str]:
        return frozenset(parameter_hash(a, s) for a, s in zip(self.coefficients, self.noise_scales))

    def trajectory_hashes(self) -> frozenset[str]:
        return _row_hashes(self.trajectories)

    def innovation_hashes(self) -> frozenset[str]:
        return _row_hashes(self.innovations)

    def trajectory_sha256(self, i: int) -> str:
        return hashlib.sha256(self.trajectories[i].tobytes()).hexdigest()


def generate_split(condition: EvaluationCondition, role: SplitRole, streams: NamedStreams,
                   n_items: int, length: int) -> DataSplit:
    """Simulate ``n_items`` trajectories x_0..x_length for ``role`` under ``condition``.

    Item i takes its system from child ``(systems_stream, i, condition.stream_code)`` and its x_0
    and noise from child ``(noise_stream, i, condition.stream_code)``. Items therefore do not
    depend on ``n_items``, and the role streams are independent of one another.
    """
    if role is SplitRole.LIBRARY_TRAIN:
        raise ValueError("use generate_library_training_split for library training data")
    sys_name, noise_name = ROLE_STREAMS[role]
    a = np.empty(n_items, dtype=FLOAT)
    s = np.empty(n_items, dtype=FLOAT)
    ids = []
    x0 = np.empty(n_items, dtype=FLOAT)
    eps = np.empty((n_items, length), dtype=FLOAT)
    for i in range(n_items):
        a[i], s[i], sid = condition.draw_system(streams.item(sys_name, i, condition.stream_code))
        ids.append(sid)
        g = streams.item(noise_name, i, condition.stream_code)
        x0[i] = condition.initial_state.mean + condition.initial_state.sd * g.standard_normal()
        eps[i] = g.standard_normal(length)
    traj = simulate_ar1(a, s, x0, eps)
    return DataSplit(role, condition.name, a, s, tuple(ids), eps, traj, condition.initial_state)


def generate_library_training_split(library: SystemLibrary, streams: NamedStreams, length: int,
                                    initial_state: InitialStateSpec) -> DataSplit:
    """One training trajectory per atom, from the ``library_noise`` stream (training stream only)."""
    k = library.size
    x0 = np.empty(k, dtype=FLOAT)
    eps = np.empty((k, length), dtype=FLOAT)
    for j in range(k):
        g = streams.item("library_noise", j)
        x0[j] = initial_state.mean + initial_state.sd * g.standard_normal()
        eps[j] = g.standard_normal(length)
    traj = simulate_ar1(library.coefficients, library.noise_scales, x0, eps)
    return DataSplit(SplitRole.LIBRARY_TRAIN, "library", library.coefficients, library.noise_scales,
                     tuple(f"atom-{j}" for j in range(k)), eps, traj, initial_state)


def assert_no_unintended_overlap(first: DataSplit, second: DataSplit) -> None:
    """No shared trajectories, noise sequences, or individual noise / state values (exact float equality).

    Two independent continuous draws coincide exactly with probability about 2^-52 per pair.
    For the sizes used here (< 1e8 pairs) the chance of an accidental match is below 1e-7, so any
    exact match means data was reused. x_0 is excluded when it is fixed (sd = 0) by design.
    """
    if first.trajectory_hashes() & second.trajectory_hashes():
        raise LeakageError(f"{first.role.value} and {second.role.value} share whole trajectories")
    if first.innovation_hashes() & second.innovation_hashes():
        raise LeakageError(f"{first.role.value} and {second.role.value} share noise sequences")
    if np.intersect1d(first.innovations.ravel(), second.innovations.ravel()).size:
        raise LeakageError(f"{first.role.value} and {second.role.value} share individual noise values")
    start = 0 if (first.initial_state.sd > 0 and second.initial_state.sd > 0) else 1
    if np.intersect1d(first.trajectories[:, start:].ravel(), second.trajectories[:, start:].ravel()).size:
        raise LeakageError(f"{first.role.value} and {second.role.value} share state/target values")


#: Minimum |a_eval - a_atom| under E-CONT. Copied atoms would agree to within a few ulps (~1e-16).
#: Independent continuous draws are separated by about 2 rho / (N K) ~ 1e-7 or more for our sizes.
#: 1e-12 therefore separates "reused" from "fresh" with a wide margin on both sides (DERIVED in docs).
MIN_PARAMETER_DISTANCE = 1e-12


def assert_parameters_disjoint(evaluation: DataSplit, library: SystemLibrary,
                               min_distance: float = MIN_PARAMETER_DISTANCE) -> float:
    """E-CONT: evaluation systems must not be library atoms. Returns the observed minimum distance."""
    if evaluation.parameter_hashes() & library.parameter_hashes():
        raise LeakageError("E-CONT evaluation systems coincide bitwise with library atoms")
    lib = np.sort(library.coefficients)
    idx = np.clip(np.searchsorted(lib, evaluation.coefficients), 1, lib.size - 1) if lib.size > 1 else None
    if lib.size == 1:
        dmin = float(np.min(np.abs(evaluation.coefficients - lib[0])))
    else:
        dmin = float(np.min(np.minimum(np.abs(evaluation.coefficients - lib[idx - 1]),
                                       np.abs(evaluation.coefficients - lib[idx]))))
    if dmin <= min_distance:
        raise LeakageError(f"E-CONT evaluation coefficient within {dmin:.3e} of a library atom")
    return dmin


def assert_parameters_within_library(evaluation: DataSplit, library: SystemLibrary) -> None:
    """E-LIB: parameter overlap with the library is intentional; every evaluation system is an atom."""
    missing = evaluation.parameter_hashes() - library.parameter_hashes()
    if missing:
        raise LeakageError(f"E-LIB evaluation systems not in the library: {len(missing)} systems")
