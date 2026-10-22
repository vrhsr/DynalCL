"""Stage 0.6 (Phase C): the frozen analysis, decision rule, Tier-2 criterion and runner. Synthetic or validation-seed
data only; no confirmatory seed is used and no effect size is printed."""

import json
import os

import numpy as np
import pytest

from dynaicl.config.stage06_schema import load_stage06_config
from dynaicl.experiments import stage06_probe as P
from dynaicl.validation import checks_stage06_analysis as CA
from dynaicl.validation.mutations import run_check_safely
from dynaicl.validation.mutations_stage06_analysis import MUTATIONS_STAGE06_ANALYSIS
from tests._util import assert_check

PRIMARY = {"l_region_off_by_one": "V20", "increment_wrong_baseline": "V20", "items_as_independent_units": "V21",
           "independent_indices_per_contrast": "V21", "pointwise_critical_value": "V21",
           "unstudentized_max_statistic": "V21", "bootstrap_failures_dropped": "V21", "go_single_replicate": "V22",
           "go_non_adjacent_pairs": "V22", "go_ignores_increment": "V22", "go_one_scale": "V22",
           "stop_single_replicate": "V22", "negative_gain_not_blocked": "V22", "missing_cell_not_blocked": "V22",
           "gain_flag_uses_upper_bound": "V22", "tier2_unadjusted_cutoff": "V23", "tier2_uninformative_as_pass": "V23",
           "manifest_file_hashes_not_checked": "V24", "checkpoint_checksum_not_checked": "V24",
           "seed_collision_not_checked": "V24", "environment_difference_ignored": "V24"}
skip = pytest.mark.skipif(bool(os.environ.get("DYNAICL_MUTATION")), reason="session-wide mutation active")


@pytest.mark.parametrize("key", ["V20", "V21", "V22", "V23", "V24"])
def test_stage06_analysis_checks(key):
    r = assert_check(CA.ALL_CHECKS_STAGE06_ANALYSIS[key]())
    print(f"\n{r.name}: {json.dumps(r.details, default=str)[:600]}")


def test_mutation_plan_covers_every_analysis_mutation():
    assert set(PRIMARY) == set(MUTATIONS_STAGE06_ANALYSIS)


@skip
@pytest.mark.parametrize("mutation", sorted(MUTATIONS_STAGE06_ANALYSIS))
def test_stage06_analysis_mutation_killed_by_clean_failure(mutation):
    key = PRIMARY[mutation]
    with MUTATIONS_STAGE06_ANALYSIS[mutation]():
        res = run_check_safely(CA.ALL_CHECKS_STAGE06_ANALYSIS[key])
    print(f"\n{mutation}: {key}={res['status']}")
    assert res["status"] == "FAIL", res


def test_runner_end_to_end_resume_and_refusals(tmp_path):
    """Test mode (validation seeds, 12 systems): partial run, resume, analysis outputs; then a checkpoint written under
    one config is refused under another."""
    cfg_path = os.path.join(os.path.dirname(__file__), "..", "config", "stage06_test.yaml")
    ck, runs = tmp_path / "ckpt", tmp_path / "runs"
    base = ["run", "--config", cfg_path, "--checkpoint-dir", str(ck), "--runs-dir", str(runs)]
    assert P.main(base + ["--max-new-units", "4"]) == 0
    cfg = load_stage06_config(cfg_path)
    root = P.checkpoint_root(ck, cfg)
    assert len(list(root.glob("*.json"))) == 4
    assert P.main(["analyze", "--config", cfg_path, "--checkpoint-dir", str(ck), "--runs-dir", str(runs)]) == 3
    assert P.main(base) == 0
    assert len(list(root.glob("*.json"))) == len(P.plan_units(cfg))
    out = next(runs.iterdir())
    summary = json.loads((out / "results" / "summary.json").read_text(encoding="utf-8"))
    assert summary["decision"]["verdict"] in ("GO", "STOP", "REVISE", "BLOCKED")
    assert set(summary["critical_checks"]) == {"integrity", "tier1", "calibration", "numerics", "reproducibility", "tier2"}
    assert summary["tier2"]["outcome"] != "PASS" or summary["critical_checks"]["tier2"]
    assert (out / "checksums.json").is_file() and (out / "provenance.json").is_file()
    # a corrupted array file is refused on resume, never recomputed silently
    f = next(root.glob("primary_1_*.npz"))
    with np.load(f) as z:
        arrays = {k: z[k] + 1 for k in z.files}
    with open(f, "wb") as fh:
        np.savez(fh, **arrays)
    assert P.main(base) == 4        # checksum mismatch is CORRUPT (exit 4), not a policy REFUSED (exit 3)
