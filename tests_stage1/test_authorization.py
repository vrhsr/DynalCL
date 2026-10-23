"""Stage 1 authorization gate: valid artifact verifies; every binding, key, time and lock violation is refused.
Keys here are TEST-ONLY keys generated in the test; no real key exists in the repository."""

from __future__ import annotations

import datetime as dt
import json

import pytest

from dynaicl_neural.authorization import Binding, Refused, build_payload, claim_run, issue, obtain_key, verify

KEY = b"TEST-ONLY-" + b"x" * 30
B = Binding("a" * 64, "b" * 64, "c" * 64, "d" * 64, "e" * 64, (72001, 72101))
NOW = dt.datetime(2026, 11, 1, 12, 0, tzinfo=dt.timezone.utc)


def _art(binding=B, hours=24.0, test_only=True, key=KEY, issued=NOW):
    return issue(build_payload(binding, "stage1-confirm-001", issued, hours, test_only), key)


def test_valid_artifact_verifies():
    assert verify(_art(), KEY, True, B, NOW)["run_id"] == "stage1-confirm-001"


@pytest.mark.parametrize("field", ["manifest_sha256", "snapshot_sha256", "config_sha256", "prereg_sha256",
                                   "pilot_decision_sha256"])
def test_any_binding_change_is_refused(field):
    other = Binding(**{**B.__dict__, field: "f" * 64})
    with pytest.raises(Refused):
        verify(_art(), KEY, True, other, NOW)


def test_seed_set_wrong_key_tampering_time_and_test_flag_are_refused():
    with pytest.raises(Refused):
        verify(_art(), KEY, True, Binding(**{**B.__dict__, "seeds": (72001,)}), NOW)
    with pytest.raises(Refused):
        verify(_art(), b"TEST-ONLY-" + b"y" * 30, True, B, NOW)
    doc = json.loads(_art())
    doc["payload"]["run_id"] = "stage1-confirm-002"
    with pytest.raises(Refused):
        verify(json.dumps(doc).encode(), KEY, True, B, NOW)
    with pytest.raises(Refused):
        verify(_art(), KEY, True, B, NOW + dt.timedelta(hours=25))
    with pytest.raises(Refused):
        verify(_art(test_only=False), KEY, True, B, NOW)        # flag mismatch with a test key
    with pytest.raises(ValueError):
        build_payload(B, "stage1-confirm-001", NOW, 73.0, True)


def test_key_from_environment_only():
    with pytest.raises(Refused):
        obtain_key({})
    with pytest.raises(Refused):
        obtain_key({"DYNAICL_STAGE1_AUTH_KEY": "short"})
    key, is_test = obtain_key({"DYNAICL_STAGE1_AUTH_KEY": KEY.decode()})
    assert key == KEY and is_test


def test_run_lock(tmp_path):
    claim_run(tmp_path, "stage1-confirm-001")
    claim_run(tmp_path, "stage1-confirm-001")
    with pytest.raises(Refused):
        claim_run(tmp_path, "stage1-confirm-002")
