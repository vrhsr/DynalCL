"""Configuration schema and run provenance (Section 6)."""

import json

import pytest
import yaml

from dynaicl.config.schema import ConfigError, config_from_dict, load_config
from dynaicl.experiments.separability import run_experiment
from dynaicl.provenance import sha256_file

CONFIGS = ["config/separability.yaml", "config/separability_pilot.yaml", "config/smoke.yaml"]


@pytest.mark.parametrize("path", CONFIGS)
def test_shipped_configs_validate(path):
    assert len(load_config(path).config_hash()) == 64


def _raw():
    return yaml.safe_load(open("config/smoke.yaml"))


@pytest.mark.parametrize("mutate", [
    lambda d: d.update(unexpected=1),
    lambda d: d["grid"].pop("horizons"),
    lambda d: d["grid"].update(horizons=["1"]),
    lambda d: d["prior"].update(rho=1.2),
    lambda d: d["metrics"].update(compute_crps="yes"),
    lambda d: d["replication"].update(n_eval_items=1.5),
])
def test_invalid_configs_rejected(mutate):
    d = _raw()
    mutate(d)
    with pytest.raises(ConfigError):
        config_from_dict(d)


def test_config_hash_ignores_formatting_but_tracks_values():
    d = _raw()
    h = config_from_dict(d).config_hash()
    reordered = dict(reversed(list(d.items())))
    assert config_from_dict(reordered).config_hash() == h
    d["grid"]["horizons"] = [1, 4]
    assert config_from_dict(d).config_hash() != h


def test_run_directory_contents_and_checksums(tmp_path):
    rec = run_experiment(load_config("config/smoke.yaml"), runs_dir=tmp_path, workers=1, run_id="prov")
    d = rec.dir
    for name in ("config.yaml", "config_hash.txt", "provenance.json", "checksums.json", "results/summary.json",
                 "results/predictors.csv", "results/paired_differences.csv", "results/report.md"):
        assert (d / name).is_file(), name
    prov = json.loads((d / "provenance.json").read_text())
    for key in ("config_hash", "git", "packages", "platform", "seeds", "timestamps", "command"):
        assert key in prov, key
    assert prov["git"]["available"] in (True, False)
    if not prov["git"]["available"]:
        assert prov["git"]["reason"]
    assert set(prov["seeds"]["streams"]) >= {"library_systems", "eval_systems", "eval_noise", "monte_carlo"}
    sums = json.loads((d / "checksums.json").read_text())
    for rel, digest in sums.items():
        assert sha256_file(d / rel) == digest, rel
    assert (d / "config_hash.txt").read_text().strip() == prov["config_hash"]
