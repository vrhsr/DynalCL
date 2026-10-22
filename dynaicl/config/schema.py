"""Strict, typed configuration schema (Section 6). No experimental setting is hard-coded in the experiment.

YAML is validated by building nested frozen dataclasses. Unknown keys, missing keys, wrong types
and out-of-range values all raise :class:`ConfigError` with the offending path. The config hash is
the SHA-256 of the canonical JSON of the *validated* config, so formatting differences in the YAML
do not change it.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
import typing
from dataclasses import dataclass
from pathlib import Path

import yaml

SCHEMA_VERSION = 1


class ConfigError(ValueError):
    pass


def _fail(path: str, msg: str):
    raise ConfigError(f"{path}: {msg}")


@dataclass(frozen=True)
class ExperimentSection:
    name: str
    root_seed: int
    description: str = ""

    def __post_init__(self):
        if self.root_seed < 0:
            _fail("experiment.root_seed", "must be >= 0")


@dataclass(frozen=True)
class StablePriorSection:
    """P-STABLE without sigma: sigma comes from grid.noise_scales."""

    family: str
    shape: str
    rho: float
    mu0: float | None = None
    tau0: float | None = None

    def __post_init__(self):
        if self.family != "P-STABLE":
            _fail("prior.family", "the separability experiment uses P-STABLE")
        if self.shape not in ("uniform", "truncated_normal"):
            _fail("prior.shape", "must be 'uniform' or 'truncated_normal'")
        if not 0 < self.rho < 1:
            _fail("prior.rho", "must be in (0, 1)")
        if self.shape == "truncated_normal" and (self.mu0 is None or self.tau0 is None or self.tau0 <= 0):
            _fail("prior", "truncated_normal requires mu0 and tau0 > 0")
        if self.shape == "uniform" and (self.mu0 is not None or self.tau0 is not None):
            _fail("prior", "uniform takes no mu0/tau0")


@dataclass(frozen=True)
class InitialStateSection:
    mean: float
    sd: float

    def __post_init__(self):
        if self.sd < 0:
            _fail("initial_state.sd", "must be >= 0")


@dataclass(frozen=True)
class GridSection:
    conditions: tuple[str, ...]
    library_sizes: tuple[int, ...]
    context_lengths: tuple[int, ...]
    horizons: tuple[int, ...]
    noise_scales: tuple[float, ...]

    def __post_init__(self):
        if not set(self.conditions) <= {"E-CONT", "E-LIB"} or not self.conditions:
            _fail("grid.conditions", "subset of [E-CONT, E-LIB]")
        for name, vals, lo in (("library_sizes", self.library_sizes, 1), ("context_lengths", self.context_lengths, 0),
                               ("horizons", self.horizons, 1)):
            if not vals or any(v < lo for v in vals) or len(set(vals)) != len(vals):
                _fail(f"grid.{name}", f"non-empty, distinct, each >= {lo}")
        if not self.noise_scales or any(s <= 0 for s in self.noise_scales):
            _fail("grid.noise_scales", "non-empty, each > 0")


@dataclass(frozen=True)
class ReplicationSection:
    n_eval_items: int
    n_selection_items: int
    justification: str = ""

    def __post_init__(self):
        if self.n_eval_items < 2 or self.n_selection_items < 2:
            _fail("replication", "item counts must be >= 2")


@dataclass(frozen=True)
class QuadratureSection:
    panels: int = 16
    nodes_per_panel: int = 8
    log_drop: float = 40.0
    panels_per_cell: float = 2.0
    max_panels: int = 8192


@dataclass(frozen=True)
class NumericsSection:
    quadrature: QuadratureSection
    quadrature_error_check_items: int = 10


@dataclass(frozen=True)
class KernelSection:
    bandwidth_multipliers: tuple[float, ...]
    min_train_pairs: int
    n_blocks: int
    gap: int
    min_pairs: int
    min_validation_points: int


@dataclass(frozen=True)
class FallbackSection:
    coefficient_mean: float
    coefficient_variance: float
    predictive_variance: float
    variance_relative_floor: float


@dataclass(frozen=True)
class BaselinesSection:
    ols_min_transitions: int
    kernel: KernelSection
    fallback: FallbackSection


@dataclass(frozen=True)
class MetricsSection:
    coverage_levels: tuple[float, ...]
    compute_crps: bool
    practical_gap_nats: float
    separation_z: float
    equivalence_z: float
    family_alpha: float

    def __post_init__(self):
        if any(not 0 < c < 1 for c in self.coverage_levels):
            _fail("metrics.coverage_levels", "each in (0, 1)")
        if self.practical_gap_nats <= 0 or self.separation_z <= 0 or self.equivalence_z <= 0:
            _fail("metrics", "gap and z thresholds must be > 0")
        if not 0 < self.family_alpha < 1:
            _fail("metrics.family_alpha", "in (0, 1)")


@dataclass(frozen=True)
class SeparabilityConfig:
    schema_version: int
    experiment: ExperimentSection
    prior: StablePriorSection
    initial_state: InitialStateSection
    grid: GridSection
    replication: ReplicationSection
    numerics: NumericsSection
    baselines: BaselinesSection
    metrics: MetricsSection

    def __post_init__(self):
        if self.schema_version != SCHEMA_VERSION:
            _fail("schema_version", f"expected {SCHEMA_VERSION}")

    def to_dict(self) -> dict:
        return _to_plain(dataclasses.asdict(self))

    def config_hash(self) -> str:
        blob = json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"), allow_nan=False)
        return hashlib.sha256(blob.encode()).hexdigest()


# ------------------------------------------------------------------------------------- Stage 0.5 schema


@dataclass(frozen=True)
class PopulationExperimentSection:
    name: str
    description: str = ""


@dataclass(frozen=True)
class SeedsSection:
    """Independent root seeds per role. Every seed must be fresh (never used to choose conditions)."""

    library: int
    selection: int
    evaluation: tuple[int, ...]
    bootstrap: int

    def __post_init__(self):
        seeds = [self.library, self.selection, *self.evaluation, self.bootstrap]
        if any(s < 0 for s in seeds) or len(set(seeds)) != len(seeds) or not self.evaluation:
            _fail("seeds", "non-negative, all distinct, at least one evaluation seed")


@dataclass(frozen=True)
class InitialStateScalesSection:
    """x_0 ~ N(mean, sd^2) for each sd; with noise_scale fixed, sd = r is the initial-state-to-noise ratio."""

    mean: float
    sds: tuple[float, ...]

    def __post_init__(self):
        if not self.sds or any(s <= 0 for s in self.sds) or len(set(self.sds)) != len(self.sds):
            _fail("initial_state.sds", "non-empty, distinct, each > 0")


@dataclass(frozen=True)
class PopulationGridSection:
    conditions: tuple[str, ...]
    library_sizes: tuple[int, ...]
    context_lengths: tuple[int, ...]
    horizons: tuple[int, ...]

    def __post_init__(self):
        if not self.conditions or not set(self.conditions) <= {"E-CONT", "E-LIB"}:
            _fail("grid.conditions", "subset of [E-CONT, E-LIB]")
        for name, vals, lo in (("library_sizes", self.library_sizes, 1), ("context_lengths", self.context_lengths, 1),
                               ("horizons", self.horizons, 1)):
            if not vals or any(v < lo for v in vals) or len(set(vals)) != len(vals):
                _fail(f"grid.{name}", f"non-empty, distinct, each >= {lo}")


@dataclass(frozen=True)
class PopulationBaselinesSection:
    ols_min_transitions: int
    stability_bound: float
    kernel: KernelSection
    fallback: FallbackSection

    def __post_init__(self):
        if not 0 < self.stability_bound < 1:
            _fail("baselines.stability_bound", "in (0, 1)")


@dataclass(frozen=True)
class PopulationMetricsSection:
    coverage_levels: tuple[float, ...]
    practical_effect_nats: float
    decision_z: float
    ci_z: float
    sensitivity_effects: tuple[float, ...]
    bootstrap_resamples: int
    family_alpha: float

    def __post_init__(self):
        if self.practical_effect_nats <= 0 or self.decision_z <= 0 or self.ci_z <= 0 or self.bootstrap_resamples < 0:
            _fail("metrics", "effect and z values must be > 0; bootstrap_resamples >= 0")
        if not 0 < self.family_alpha < 1:
            _fail("metrics.family_alpha", "in (0, 1)")


@dataclass(frozen=True)
class DecisionSection:
    """Pre-registered decision rule inputs (docs/PREREG_stage05.md section 6)."""

    relevant_condition: str
    relevant_initial_state_sd: float
    relevant_context_lengths: tuple[int, ...]
    required_horizons: tuple[int, ...]
    min_consecutive_context_lengths: int
    robustness_initial_state_sds: tuple[float, ...]
    max_quadrature_error: float


@dataclass(frozen=True)
class PopulationAdvantageConfig:
    schema_version: int
    experiment: PopulationExperimentSection
    seeds: SeedsSection
    prior: StablePriorSection
    noise_scale: float
    initial_state: InitialStateScalesSection
    grid: PopulationGridSection
    replication: ReplicationSection
    numerics: NumericsSection
    baselines: PopulationBaselinesSection
    metrics: PopulationMetricsSection
    decision: DecisionSection

    def __post_init__(self):
        if self.schema_version != SCHEMA_VERSION:
            _fail("schema_version", f"expected {SCHEMA_VERSION}")
        if self.noise_scale <= 0:
            _fail("noise_scale", "must be > 0")

    def to_dict(self) -> dict:
        return _to_plain(dataclasses.asdict(self))

    def config_hash(self) -> str:
        blob = json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"), allow_nan=False)
        return hashlib.sha256(blob.encode()).hexdigest()


def load_population_config(path: str | Path) -> PopulationAdvantageConfig:
    with open(path, encoding="utf-8") as fh:
        return _build(PopulationAdvantageConfig, yaml.safe_load(fh), "")


def population_config_from_dict(data: dict) -> PopulationAdvantageConfig:
    return _build(PopulationAdvantageConfig, data, "")


def _to_plain(obj):
    if isinstance(obj, dict):
        return {k: _to_plain(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_to_plain(v) for v in obj]
    return obj


def _coerce(tp, value, path: str):
    origin = typing.get_origin(tp)
    args = typing.get_args(tp)
    if dataclasses.is_dataclass(tp):
        return _build(tp, value, path)
    if origin in (typing.Union, getattr(__import__("types"), "UnionType", None)):
        if value is None and type(None) in args:
            return None
        inner = [a for a in args if a is not type(None)]
        return _coerce(inner[0], value, path)
    if origin is tuple:
        if not isinstance(value, list):
            _fail(path, f"expected a list, got {type(value).__name__}")
        return tuple(_coerce(args[0], v, f"{path}[{i}]") for i, v in enumerate(value))
    if tp is bool:
        if not isinstance(value, bool):
            _fail(path, f"expected bool, got {value!r}")
        return value
    if tp is int:
        if isinstance(value, bool) or not isinstance(value, int):
            _fail(path, f"expected int, got {value!r}")
        return value
    if tp is float:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            _fail(path, f"expected number, got {value!r}")
        return float(value)
    if tp is str:
        if not isinstance(value, str):
            _fail(path, f"expected str, got {value!r}")
        return value
    _fail(path, f"unsupported schema type {tp}")


def _build(cls, data, path: str):
    if not isinstance(data, dict):
        _fail(path or "<root>", f"expected a mapping, got {type(data).__name__}")
    hints = typing.get_type_hints(cls)
    fields = {f.name: f for f in dataclasses.fields(cls)}
    unknown = set(data) - set(fields)
    if unknown:
        _fail(path or "<root>", f"unknown keys {sorted(unknown)}")
    kwargs = {}
    for name, f in fields.items():
        sub = f"{path}.{name}" if path else name
        if name not in data:
            if f.default is dataclasses.MISSING and f.default_factory is dataclasses.MISSING:
                _fail(sub, "missing required key")
            continue
        kwargs[name] = _coerce(hints[name], data[name], sub)
    try:
        return cls(**kwargs)
    except ConfigError:
        raise
    except (TypeError, ValueError) as exc:
        _fail(path or "<root>", str(exc))


def load_config(path: str | Path) -> SeparabilityConfig:
    with open(path, encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    return _build(SeparabilityConfig, data, "")


def config_from_dict(data: dict) -> SeparabilityConfig:
    return _build(SeparabilityConfig, data, "")


def dump_config(config: SeparabilityConfig) -> str:
    return yaml.safe_dump(config.to_dict(), sort_keys=False)


__all__ = ["ConfigError", "SeparabilityConfig", "load_config", "config_from_dict", "dump_config"]
