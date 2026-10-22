"""Strict schema for the Stage 0.6 noisy-observation probe (docs/PREREG_stage06.md).

Built with the same strict builder as the Stage 0 / 0.5 schemas: unknown keys, missing keys, wrong types and
out-of-range values raise :class:`ConfigError`. The config hash is the SHA-256 of the canonical JSON of the
validated config.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

import yaml

from dynaicl.config.schema import SCHEMA_VERSION, ConfigError, StablePriorSection, _build, _fail, _to_plain

MODES = ("confirmatory", "pilot", "test")


@dataclass(frozen=True)
class Stage06ExperimentSection:
    name: str
    mode: str
    description: str = ""

    def __post_init__(self):
        if self.mode not in MODES:
            _fail("experiment.mode", f"one of {MODES}")


@dataclass(frozen=True)
class Stage06SeedsSection:
    """Evaluation roots (one per replicate) and the bootstrap root. Checked against config/stage06_seed_manifest.yaml
    by the runner (the role must match the mode)."""

    evaluation: tuple[int, ...]
    bootstrap: int

    def __post_init__(self):
        seeds = [*self.evaluation, self.bootstrap]
        if any(s < 0 for s in seeds) or len(set(seeds)) != len(seeds):
            _fail("seeds", "non-negative and all distinct")
        if len(self.evaluation) != 2:
            _fail("seeds.evaluation", "exactly two replicates")


@dataclass(frozen=True)
class Stage06ModelSection:
    """sigma_w = 1 (scale equivariance, MATH_STAGE06). q = sigma_v^2 / sigma_w^2; r = sd(x_0) / sigma_w."""

    sigma_w: float
    noise_ratios: tuple[float, ...]
    initial_state_ratios: tuple[float, ...]

    def __post_init__(self):
        if self.sigma_w != 1.0:
            _fail("model.sigma_w", "Stage 0.6 fixes sigma_w = 1")
        q = self.noise_ratios
        if len(q) < 2 or q[0] != 0.0 or any(b <= a for a, b in zip(q, q[1:])):
            _fail("model.noise_ratios", "starts at the zero-noise control 0.0, then strictly increasing positive levels")
        r = self.initial_state_ratios
        if not r or any(v <= 0 for v in r) or len(set(r)) != len(r):
            _fail("model.initial_state_ratios", "non-empty, distinct, each > 0")


@dataclass(frozen=True)
class Stage06ComparatorSection:
    name: str
    stability_bound: float

    def __post_init__(self):
        if self.name != "noise_aware_stability_only":
            _fail("comparator.name", "the primary comparator is LOCKED to noise_aware_stability_only")
        if not 0 < self.stability_bound < 1:
            _fail("comparator.stability_bound", "in (0, 1)")


@dataclass(frozen=True)
class Stage06GridSection:
    context_lengths: tuple[int, ...]
    long_context: tuple[int, ...]
    horizons: tuple[int, ...]
    trajectory_length: int
    n_systems: int

    def __post_init__(self):
        ns, L = self.context_lengths, self.long_context
        if not ns or any(n < 1 for n in ns) or list(ns) != sorted(set(ns)):
            _fail("grid.context_lengths", "non-empty, strictly increasing, each >= 1")
        if not L or list(L) != sorted(set(L)) or not set(L) <= set(ns):
            _fail("grid.long_context", "strictly increasing subset of grid.context_lengths")
        if not self.horizons or any(h < 1 for h in self.horizons) or len(set(self.horizons)) != len(self.horizons):
            _fail("grid.horizons", "non-empty, distinct, each >= 1")
        if self.trajectory_length < max(ns) + max(self.horizons):
            _fail("grid.trajectory_length", "must reach the last target index max(n) + max(h)")
        if self.n_systems < 2:
            _fail("grid.n_systems", ">= 2")


@dataclass(frozen=True)
class Stage06QuadratureSection:
    outer_bound: float
    breakpoints: tuple[float, ...]
    panels_per_unit: int
    nodes_per_panel: int


@dataclass(frozen=True)
class Stage06SecondarySection:
    """Noise-naive (noise-misspecified) context-only baselines: secondary, descriptive, never in the verdict."""

    naive_context_lengths: tuple[int, ...]
    naive_n_systems: int

    def __post_init__(self):
        if not self.naive_context_lengths or self.naive_n_systems < 0:
            _fail("secondary", "non-empty context lengths; naive_n_systems >= 0")


@dataclass(frozen=True)
class Stage06AnalysisSection:
    """Frozen inference (PREREG_stage06 sections 5-7)."""

    delta: float
    alpha: float
    bootstrap_draws: tuple[int, ...]
    bootstrap_chunk: int
    critical_value_rel_mc_error: float
    min_scales: int

    def __post_init__(self):
        if self.delta <= 0 or not 0 < self.alpha < 1:
            _fail("analysis", "delta > 0 and alpha in (0, 1)")
        b = self.bootstrap_draws
        if not b or b[0] < 10_000 or any(y <= x for x, y in zip(b, b[1:])):
            _fail("analysis.bootstrap_draws", "increasing schedule starting at >= 10000 draws")
        if self.bootstrap_chunk < 1 or not 0 < self.critical_value_rel_mc_error < 1 or self.min_scales < 1:
            _fail("analysis", "chunk >= 1, MC tolerance in (0, 1), min_scales >= 1")


@dataclass(frozen=True)
class Stage06Tier2Section:
    """Fresh-seed zero-noise reproduction of Stage 0.5 (PREREG_stage06 section 8)."""

    stage05_run: str
    context_lengths: tuple[int, ...]
    alpha: float
    power: float

    def __post_init__(self):
        if not 0 < self.alpha < 1 or not 0 < self.power < 1:
            _fail("tier2", "alpha and power in (0, 1)")


@dataclass(frozen=True)
class Stage06ChecksSection:
    """In-run critical checks (PREREG_stage06 section 9). Any failure means BLOCKED."""

    tier1_items: int
    tier1_tolerance: float
    numerical_items: int
    error_budget: float
    reproducibility_items: int
    reproducibility_tolerance: float
    calibration_context_lengths: tuple[int, ...]
    calibration_family_alpha: float


@dataclass(frozen=True)
class Stage06Config:
    schema_version: int
    experiment: Stage06ExperimentSection
    seeds: Stage06SeedsSection
    prior: StablePriorSection
    model: Stage06ModelSection
    comparator: Stage06ComparatorSection
    grid: Stage06GridSection
    quadrature: Stage06QuadratureSection
    secondary: Stage06SecondarySection
    analysis: Stage06AnalysisSection
    tier2: Stage06Tier2Section
    checks: Stage06ChecksSection

    def __post_init__(self):
        if self.schema_version != SCHEMA_VERSION:
            _fail("schema_version", f"expected {SCHEMA_VERSION}")
        if not set(self.secondary.naive_context_lengths) <= set(self.grid.context_lengths):
            _fail("secondary.naive_context_lengths", "subset of grid.context_lengths")
        if not set(self.tier2.context_lengths) <= set(self.grid.context_lengths):
            _fail("tier2.context_lengths", "subset of grid.context_lengths")
        if not set(self.checks.calibration_context_lengths) <= set(self.grid.context_lengths):
            _fail("checks.calibration_context_lengths", "subset of grid.context_lengths")
        if self.secondary.naive_n_systems > self.grid.n_systems:
            _fail("secondary.naive_n_systems", "at most grid.n_systems (a prefix of the same systems)")

    def to_dict(self) -> dict:
        return _to_plain(dataclasses.asdict(self))

    def config_hash(self) -> str:
        blob = json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"), allow_nan=False)
        return hashlib.sha256(blob.encode()).hexdigest()


def load_stage06_config(path: str | Path) -> Stage06Config:
    with open(path, encoding="utf-8") as fh:
        return _build(Stage06Config, yaml.safe_load(fh), "")


def stage06_config_from_dict(data: dict) -> Stage06Config:
    return _build(Stage06Config, data, "")


__all__ = ["ConfigError", "Stage06Config", "load_stage06_config", "stage06_config_from_dict"]
