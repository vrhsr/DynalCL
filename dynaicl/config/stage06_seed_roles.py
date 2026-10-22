"""Stage 0.6 seed-role table: loader, validator and documentation renderer (single source: config/stage06_seed_manifest.yaml)."""

from __future__ import annotations

from pathlib import Path

import yaml

from dynaicl.experiments.stage06_errors import Corrupt, Refusal

REQUIRED_ROLES = ("validation", "design_calculation", "pilot_evaluation", "pilot_bootstrap", "selection",
                  "confirmatory_evaluation", "confirmatory_bootstrap")
ROLE_KEYS = ("purpose", "seeds", "allowed_uses", "forbidden_uses")
MODE_ROLES = {"confirmatory": ("confirmatory_evaluation", "confirmatory_bootstrap"),
              "pilot": ("pilot_evaluation", "pilot_bootstrap"), "test": ("validation", "validation")}


def load_roles(path, strict: bool = True) -> dict:
    p = Path(path)
    try:
        data = yaml.safe_load(p.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise Refusal("seed-role table not found", p)
    except (yaml.YAMLError, UnicodeDecodeError) as exc:
        raise Corrupt(f"seed-role table is not valid YAML ({type(exc).__name__})", p)
    roles = data.get("roles") if isinstance(data, dict) else None
    if not isinstance(roles, dict) or (strict and set(roles) != set(REQUIRED_ROLES)):
        raise Corrupt(f"seed-role table must define exactly the roles {list(REQUIRED_ROLES)}", p)
    for name, r in roles.items():
        if not isinstance(r, dict) or (strict and set(r) != set(ROLE_KEYS)) or "seeds" not in r:
            raise Corrupt(f"role {name!r} must have exactly the keys {list(ROLE_KEYS)}", p)
        if not isinstance(r["seeds"], list) or not r["seeds"] or not all(isinstance(s, int) and not isinstance(s, bool) for s in r["seeds"]):
            raise Corrupt(f"role {name!r}: seeds must be a non-empty list of integers", p)
    allv = [s for r in roles.values() for s in r["seeds"]]
    dup = sorted({s for s in allv if allv.count(s) > 1})
    if dup:
        raise Refusal(f"seed collision across roles: {dup}", p)
    return roles


def role_of(roles: dict, seed: int) -> str | None:
    return next((n for n, r in roles.items() if seed in r["seeds"]), None)


def check_mode_seeds(roles: dict, mode: str, evaluation: list, bootstrap: int) -> dict:
    """The config's seeds must be exactly the table's allocation for its mode (ordered for pilot and confirmatory: replicate 1,
    replicate 2, bootstrap). A seed outside its role is refused."""
    ev_role, bs_role = MODE_ROLES[mode]
    ev, bs = list(evaluation), bootstrap
    if mode == "test":
        ok = set(ev) | {bs} <= set(roles[ev_role]["seeds"])
    else:
        ok = ev == list(roles[ev_role]["seeds"]) and [bs] == list(roles[bs_role]["seeds"])
    if not ok:
        stray = {s: role_of(roles, s) for s in [*ev, bs]}
        raise Refusal(f"seeds {ev} / {bs} are not the seed-role table's allocation for mode {mode} "
                      f"(evaluation role {ev_role}, bootstrap role {bs_role}); roles of the given seeds: {stray}")
    return {"evaluation": ev, "bootstrap": bs, "role": ev_role}


def render_markdown(roles: dict) -> str:
    L = ["# Stage 0.6 seed roles", "",
         "GENERATED from `config/stage06_seed_manifest.yaml` by `dynaicl.config.stage06_seed_roles.render_markdown` and checked against it "
         "by the test suite (V28). Edit the YAML, never this file.", "",
         "| role | seeds | purpose |", "|---|---|---|"]
    for name in REQUIRED_ROLES:
        r = roles[name]
        L.append(f"| `{name}` | {', '.join(str(s) for s in r['seeds'])} | {r['purpose']} |")
    L += ["", "## Allowed and forbidden uses", ""]
    for name in REQUIRED_ROLES:
        r = roles[name]
        L += [f"### `{name}` ({', '.join(str(s) for s in r['seeds'])})", "",
              "* allowed: " + "; ".join(str(x) for x in r["allowed_uses"]),
              "* forbidden: " + "; ".join(str(x) for x in r["forbidden_uses"]), ""]
    return "\n".join(L) + "\n"
