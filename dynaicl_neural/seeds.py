"""Seed roles for Stage 1 (config/stage1_seed_manifest.yaml) and derived per-model seeds.

Every Stage 1 seed comes from the role table. Per-model seeds are derived, never typed: ``derived_seed(root, label,
*path)`` = SeedSequence(root, spawn_key=(sha256(label)[:4], *path)), so adding arms or models never shifts others.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import yaml

from dynaicl.rng import stable_name_key

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "config" / "stage1_seed_manifest.yaml"


def load_roles(path: Path = MANIFEST) -> dict[str, list[int]]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if data.get("schema") != "stage1-seed-roles/v1":
        raise ValueError("unknown seed manifest schema")
    roles = {name: [int(s) for s in spec["seeds"]] for name, spec in data["roles"].items()}
    seen: dict[int, str] = {}
    for name, seeds in roles.items():
        for s in seeds:
            if s in seen:
                raise ValueError(f"seed {s} is shared by roles {seen[s]} and {name}")
            seen[s] = name
    return roles


def role_seed(role: str, index: int = 0, path: Path = MANIFEST) -> int:
    seeds = load_roles(path)[role]
    return seeds[index]


def derived_seed(root: int, label: str, *path: int) -> int:
    """A 32-bit seed for an independent sub-stream (same derivation as dynaicl_families.separability.derived_seed)."""
    ss = np.random.SeedSequence(entropy=int(root), spawn_key=(stable_name_key(label), *[int(p) for p in path]))
    return int(ss.generate_state(1, dtype=np.uint32)[0])
