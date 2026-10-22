"""Stage 0.6 negative controls: every injected bug is detected by at least one check that FAILS cleanly
(an exception is not accepted as the only evidence)."""

import os
from functools import partial

import pytest

from dynaicl.validation import checks_stage06 as C
from dynaicl.validation.mutations import run_check_safely
from dynaicl.validation.mutations_stage06 import MUTATIONS_STAGE06

V9_SMALL = partial(C.check_noisy_calibration, n_items=300, ns=(2, 10), qs=(0.755,), rs=(1.0,))
DETECTORS = {
    "omit_target_noise_variance": {"V2": C.check_target_noise_variance, "V7": C.check_independent_integration},
    "wrong_sigma_v_in_reference": {"V7": C.check_independent_integration, "V11": C.check_parity_null},
    "prior_mismatch_in_reference": {"V7": C.check_independent_integration, "V11": C.check_parity_null},
    "latent_state_passed_to_predictor": {"V12": C.check_information_access_noisy},
    "off_by_one_context_length": {"V12": C.check_information_access_noisy},
    "off_by_one_target_index": {"V12": C.check_information_access_noisy},
    "noise_naive_mislabeled_as_noise_aware": {"V7": C.check_independent_integration, "V11": C.check_parity_null},
}
skip = pytest.mark.skipif(bool(os.environ.get("DYNAICL_MUTATION")), reason="session-wide mutation active")


@skip
def test_stage06_detectors_pass_without_mutation():
    for fn in {f for d in DETECTORS.values() for f in d.values()} | {V9_SMALL}:
        assert run_check_safely(fn)["status"] == "pass"


@skip
@pytest.mark.parametrize("mutation", sorted(MUTATIONS_STAGE06))
def test_stage06_mutation_detected_by_clean_failure(mutation):
    with MUTATIONS_STAGE06[mutation]():
        res = {k: run_check_safely(f) for k, f in DETECTORS[mutation].items()}
    print(f"\n{mutation}: " + ", ".join(f"{k}={v['status']}" for k, v in res.items()))
    assert any(v["status"] == "FAIL" for v in res.values()), res
