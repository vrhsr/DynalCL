"""Strict Stage 1 run configuration (config/stage1_pilot.yaml, config/stage1.yaml). Unknown keys are refused."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path

import yaml

SCHEMA = "stage1-config/v1"


@dataclass(frozen=True)
class EvalSizes:
    held_n: int = 40000
    probe_n: int = 10000
    oos_n: int = 10000
    control_n: int = 4000


@dataclass(frozen=True)
class CapRule:
    max_models: int = 128
    gpu_hours_limit: float = 48.0
    safety: float = 1.25
    step: int = 8


@dataclass(frozen=True)
class Stage1Config:
    phase: str                                   # "pilot" or "confirmatory"
    seed_roles: dict
    replicates: int
    primary_arms: tuple[str, ...]
    model: str
    models_per_arm: int | None                   # pilot: fixed; confirmatory: None (from the pilot decision)
    steps: int | None                            # pilot: fixed; confirmatory: None (B from the pilot decision)
    checkpoints: tuple[int, ...] | None
    batch: int = 256
    eval: EvalSizes = field(default_factory=EvalSizes)
    alpha_q1: float = 0.025
    alpha_q2: float = 0.025
    alpha_secondary_total: float = 0.05
    bootstrap_draws: int = 4000
    target_se_q1: float = 0.002
    target_se_q2: float = 0.008
    min_models: int = 32
    ucl_factor: float = 1.35
    epsilon: float = 0.01
    delta: float = 0.02
    cap_rule: CapRule = field(default_factory=CapRule)
    secondary: tuple[str, ...] = ()
    drop_order: tuple[str, ...] = ()
    budgets: tuple[int, ...] = (10000, 25000, 50000, 100000)

    def __post_init__(self) -> None:
        if self.phase not in ("pilot", "confirmatory"):
            raise ValueError("phase must be pilot or confirmatory")
        if self.phase == "pilot" and (self.models_per_arm is None or self.steps is None or not self.checkpoints):
            raise ValueError("the pilot fixes models_per_arm, steps and checkpoints")
        if self.phase == "confirmatory" and (self.models_per_arm is not None or self.steps is not None):
            raise ValueError("confirmatory models_per_arm and steps come from the pilot decision")


def load_config(path: Path) -> tuple[Stage1Config, str]:
    """(config, sha256 of the file bytes)."""
    raw = Path(path).read_bytes()
    d = yaml.safe_load(raw)
    if d.pop("schema", None) != SCHEMA:
        raise ValueError("unknown config schema")
    ev = EvalSizes(**d.pop("eval", {}))
    cap = CapRule(**d.pop("cap_rule", {}))
    for k in ("primary_arms", "checkpoints", "secondary", "drop_order", "budgets"):
        if k in d and d[k] is not None:
            d[k] = tuple(d[k])
    cfg = Stage1Config(eval=ev, cap_rule=cap, **d)
    return cfg, hashlib.sha256(raw).hexdigest()
