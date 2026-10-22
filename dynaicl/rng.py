"""Named, independent random streams built on ``numpy.random.SeedSequence``.

Each stream is keyed by its *name* (a stable hash) rather than by spawn order, so:

* adding a new stream name never shifts an existing stream;
* drawing more numbers from one stream never shifts another (each stream has its own generator);
* per-item children are keyed by ``(name, item_index)``, so item ``i`` is identical whether 10 or
  10,000 items are drawn. Paired comparisons and the reproducibility tests (Section 5.I) rely on
  this property.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

import numpy as np

#: Stream names used by the project. Others are allowed, but these are the documented roles.
STANDARD_STREAMS = (
    "library_systems",
    "library_noise",
    "selection_systems",
    "selection_noise",
    "eval_systems",
    "eval_noise",
    "monte_carlo",
)


def stable_name_key(name: str) -> int:
    """Map a stream name to a 32-bit integer key, stable across processes and Python versions.

    ``hash()`` is salted per process, so SHA-256 is used instead.
    """
    if not isinstance(name, str) or not name:
        raise ValueError("stream name must be a non-empty string")
    return int.from_bytes(hashlib.sha256(name.encode("utf-8")).digest()[:4], "little")


@dataclass(frozen=True)
class NamedStreams:
    """Factory of independent generators derived from one root seed.

    ``root_seed`` is the only entropy source. ``stream(name)`` and ``item(name, i)`` are pure
    functions of ``(root_seed, name[, i])``.
    """

    root_seed: int
    #: Optional per-stream entropy overrides, e.g. (("eval_systems", 123),). Used to show that changing
    #: one named stream leaves every other stream bitwise unchanged (Section 5.I).
    overrides: tuple[tuple[str, int], ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.root_seed, (int, np.integer)) or self.root_seed < 0:
            raise ValueError("root_seed must be a non-negative integer")
        for name, seed in self.overrides:
            stable_name_key(name)
            if not isinstance(seed, (int, np.integer)) or seed < 0:
                raise ValueError("override seeds must be non-negative integers")

    def entropy_for(self, name: str) -> int:
        return int(dict(self.overrides).get(name, self.root_seed))

    def seed_sequence(self, name: str, *path: int) -> np.random.SeedSequence:
        for p in path:
            if not isinstance(p, (int, np.integer)) or p < 0:
                raise ValueError("stream path entries must be non-negative integers")
        return np.random.SeedSequence(
            entropy=self.entropy_for(name),
            spawn_key=(stable_name_key(name), *[int(p) for p in path]),
        )

    def stream(self, name: str, *path: int) -> np.random.Generator:
        """A generator for the named stream (optionally a sub-path such as a grid cell)."""
        return np.random.Generator(np.random.PCG64(self.seed_sequence(name, *path)))

    def item(self, name: str, index: int, *path: int) -> np.random.Generator:
        """Generator for item ``index`` of the named stream; independent of how many items exist."""
        return self.stream(name, *path, index)

    def describe(self, names: tuple[str, ...] = STANDARD_STREAMS) -> dict:
        """Provenance record: root entropy and the spawn key of every named stream."""
        return {
            "root_seed": int(self.root_seed),
            "bit_generator": "PCG64",
            "derivation": "SeedSequence(entropy=entropy_for(name), spawn_key=(sha256(name)[:4] as uint32 LE, *path))",
            "streams": {n: {"entropy": self.entropy_for(n), "spawn_key_prefix": [stable_name_key(n)]}
                        for n in names},
        }
