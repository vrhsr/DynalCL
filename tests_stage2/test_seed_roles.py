"""Stage 2 seed roles: unique within the table and disjoint from every seed in the other configs (Stage 0, 0.5, 0.6, 1)."""

from __future__ import annotations

from pathlib import Path

import yaml

from dynaicl_families.stage2.seeds import MANIFEST, load_roles

ROOT = Path(__file__).resolve().parents[1]


def _seed_ints(node, under_seed_key=False):
    if isinstance(node, dict):
        for k, v in node.items():
            yield from _seed_ints(v, under_seed_key or "seed" in str(k).lower())
    elif isinstance(node, list):
        for v in node:
            yield from _seed_ints(v, under_seed_key)
    elif isinstance(node, int) and not isinstance(node, bool) and under_seed_key:
        yield node


def test_stage2_seeds_unique_and_disjoint_from_other_configs():
    roles = load_roles()
    mine = [s for seeds in roles.values() for s in seeds]
    assert len(mine) == len(set(mine))
    others = set()
    for path in sorted((ROOT / "config").glob("*.yaml")):
        if path.resolve() == MANIFEST.resolve():
            continue
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        others |= set(_seed_ints(data))
        if isinstance(data, dict) and "roles" in data:            # seed-role tables: every listed seed
            for spec in data["roles"].values():
                if isinstance(spec, dict):
                    others |= {int(s) for s in spec.get("seeds", [])}
    assert others, "found no seeds in the other configs (the scan is broken)"
    assert not set(mine) & others, sorted(set(mine) & others)
