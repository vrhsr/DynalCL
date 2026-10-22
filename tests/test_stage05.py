"""Stage 0.5 machinery: scale equivariance (MATH 11), classification and decision rules, end-to-end smoke run."""

import math

import numpy as np
import pytest

from dynaicl.baselines.family import build_context_only_family
from dynaicl.config.schema import load_population_config
from dynaicl.experiments import population_advantage as pa
from dynaicl.references.library import FiniteLibraryPredictor
from dynaicl.references.matched import continuous_prior_predictor
from dynaicl.systems.context import ContextWindow
from dynaicl.systems.library import SystemLibrary
from dynaicl.systems.priors import StableCoefficientPrior
from dynaicl.validation.checks import _simulate_context


def _predictors(sigma):
    prior = StableCoefficientPrior(0.95, sigma, "truncated_normal", 0.4, 0.3)
    lib = SystemLibrary(np.array([-0.5, 0.2, 0.7]), np.full(3, sigma), np.full(3, 1 / 3))
    preds = {"matched": continuous_prior_predictor(prior), "library": FiniteLibraryPredictor(lib)}
    preds.update(build_context_only_family(sigma, stability_bound=0.999))
    return preds


@pytest.mark.parametrize("c", [0.25, 7.0])
def test_scale_equivariance_of_paired_differences(c):
    """p_c(c y) = p(y)/c for every predictor (MATH 11), so log scores shift by exactly -log c and paired
    differences and PIT are invariant. Tolerance 1e-8 absolute on log densities: identical arithmetic up to
    rounding of the rescaled data (relative ~1e-15), amplified by at most the tested range of terms."""
    rng = np.random.default_rng(5)
    base, scaled = _predictors(1.0), _predictors(c)
    for n in (1, 3, 10):
        x = _simulate_context(0.6, 1.0, n, rng)
        for h in (1, 5):
            ys = np.array([-2.0, 0.1, 1.5])
            for name in base:
                p1 = base[name].predict(ContextWindow(x), h)
                pc = scaled[name].predict(ContextWindow(c * x), h)
                lp1, lpc = np.asarray(p1.logpdf(ys)), np.asarray(pc.logpdf(c * ys))
                assert np.allclose(lpc, lp1 - math.log(c), rtol=0, atol=1e-8), (name, n, h)
                assert np.allclose(np.asarray(pc.cdf(c * ys)), np.asarray(p1.cdf(ys)), rtol=0, atol=1e-10), (name, n, h)


def test_classification_rules():
    d = 0.02
    assert pa.classify_advantage(0.05, 0.01, d, 2.24) == "MEANINGFUL"         # 0.05 - 0.0224 > 0.02
    assert pa.classify_advantage(0.03, 0.01, d, 2.24) == "INCONCLUSIVE"
    assert pa.classify_advantage(0.0, 0.005, d, 2.24) == "NEGLIGIBLE"         # 0.0112 < 0.02
    assert pa.classify_distinction(-0.05, 0.01, d, 2.24) == "DISTINGUISHABLE"
    assert pa.classify_distinction(0.001, 0.003, d, 2.24) == "EQUIVALENT"
    assert pa.classify_distinction(0.02, 0.01, d, 2.24) == "INCONCLUSIVE"
    assert pa.confirm(["MEANINGFUL", "MEANINGFUL"]) == "MEANINGFUL"
    assert pa.confirm(["MEANINGFUL", "INCONCLUSIVE"]) == "DISCORDANT"


def _rows(classes: dict, contrast=pa.PRIMARY):
    """classes: {(r, n, h): (class_R1, class_R2)} -> synthetic contrast rows for E-CONT."""
    out = []
    for (r, n, h), cls in classes.items():
        for rep, c in zip(("R1", "R2"), cls):
            out.append({"condition": "E-CONT", "K": 0, "r": r, "n": n, "h": h, "replicate": rep, "contrast": contrast,
                        "class": c})
    return out


OK_REL = {"T1_violations": 0, "T2_failures": 0, "max_quadrature_error": 1e-12, "max_matched_capped_rate": 0.0}
M, I = ("MEANINGFUL", "MEANINGFUL"), ("INCONCLUSIVE", "INCONCLUSIVE")


def _cfg():
    return load_population_config("config/stage05_pilot.yaml")   # decision section identical to the main config


def test_decision_proceed_revise_stop():
    cfg = _cfg()
    full = {(1.0, n, h): M for n in (2, 3) for h in (1, 5)} | {(0.25, 2, 1): M, (4.0, 3, 1): M}
    assert pa.decide(cfg, _rows(full), OK_REL)["verdict"] == "PROCEED"
    scale_fragile = {(1.0, n, h): M for n in (2, 3) for h in (1, 5)} | {(0.25, 2, 1): M, (4.0, 3, 1): I}
    assert pa.decide(cfg, _rows(scale_fragile), OK_REL)["verdict"] == "REVISE"
    narrow = {(1.0, 2, 1): M, (1.0, 3, 1): I, (1.0, 2, 5): I}
    assert pa.decide(cfg, _rows(narrow), OK_REL)["verdict"] == "REVISE"
    nothing = {(1.0, n, 1): I for n in (2, 3, 5, 10)}
    assert pa.decide(cfg, _rows(nothing), OK_REL)["verdict"] == "STOP"
    generic_only = _rows(nothing) + _rows({(1.0, 2, 1): M}, contrast="matched_minus_frontier_stage0")
    assert pa.decide(cfg, generic_only, OK_REL)["verdict"] == "REVISE"
    bad = dict(OK_REL, T2_failures=1)
    assert pa.decide(cfg, _rows(full), bad)["verdict"] == "STOP"
    one_rep = [r for r in _rows(full) if r["replicate"] == "R1"]
    assert pa.decide(cfg, one_rep, OK_REL)["verdict"] == "NOT DECIDABLE"


def test_stage05_smoke_run_end_to_end(tmp_path):
    cfg = load_population_config("config/stage05_smoke.yaml")
    rec = pa.run_experiment(cfg, runs_dir=tmp_path, workers=1, run_id="smoke")
    res = rec.dir / "results"
    for f in ("contrasts.csv", "predictors.csv", "t1_optimality.csv", "t2_calibration.csv", "bootstrap.csv",
              "summary.json", "report.md", "item_contrasts.npy", "frontier_selection.json"):
        assert (res / f).is_file(), f
    import json
    s = json.loads((res / "summary.json").read_text())
    assert s["reliability"]["T1_violations"] == 0 and s["reliability"]["T2_failures"] == 0
    assert s["decision"]["verdict"] in ("PROCEED", "REVISE", "STOP")


def test_checkpoint_resume_gives_identical_results(tmp_path):
    """A run resumed from checkpoints (here: all units precomputed, then a second run loads them) writes the same
    results as an uninterrupted run, and a partial checkpoint is completed rather than recomputed from scratch."""
    import json, shutil
    cfg = load_population_config("config/stage05_smoke.yaml")
    ck = tmp_path / "ckpt"
    a = pa.run_experiment(cfg, runs_dir=tmp_path, workers=1, run_id="a", checkpoint_dir=str(ck))
    files = sorted((ck / cfg.config_hash()[:16]).glob("unit_*.pkl"))
    assert len(files) == len(pa.plan_units(cfg))
    files[0].unlink()                                    # simulate an interruption before the last unit
    b = pa.run_experiment(cfg, runs_dir=tmp_path, workers=1, run_id="b", checkpoint_dir=str(ck))
    sa = json.loads((a.dir / "checksums.json").read_text())
    sb = json.loads((b.dir / "checksums.json").read_text())
    for k in sa:
        if k.startswith("results/"):
            assert sa[k] == sb[k], k
