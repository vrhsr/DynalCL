"""Stage 2 / 3 seed roles (config/stage2_seed_manifest.yaml); the only way Stage 2 code obtains a seed."""

from __future__ import annotations

from pathlib import Path

import yaml

MANIFEST = Path(__file__).resolve().parents[2] / "config" / "stage2_seed_manifest.yaml"


def load_roles(path: Path = MANIFEST) -> dict[str, list[int]]:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if data.get("schema") != "stage2-seed-roles/v1":
        raise ValueError("unknown stage 2 seed manifest schema")
    roles = {name: [int(s) for s in spec["seeds"]] for name, spec in data["roles"].items()}
    seen: dict[int, str] = {}
    for name, seeds in roles.items():
        for s in seeds:
            if s in seen:
                raise ValueError(f"seed {s} is shared by roles {seen[s]} and {name}")
            seen[s] = name
    return roles


def role_seed(role: str, index: int = 0, path: Path = MANIFEST) -> int:
    return load_roles(path)[role][index]
