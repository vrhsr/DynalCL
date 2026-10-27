"""Stage 1 authorization issuer and the gate's key-kind check (Amendment 2, disclosure S28).

Only TEST-ONLY keys generated here are used; no real key exists in the repository. The freeze manifest used by the
issuer tests is a temporary one listing the real confirmatory config, so the tests do not depend on which freeze exists."""

from __future__ import annotations

import datetime as dt
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from dynaicl_neural.authorization import verify
from dynaicl_neural.config import load_config

ROOT = Path(__file__).resolve().parents[1]
KEY = "TEST-ONLY-" + "k" * 30
NOW = dt.datetime(2026, 11, 2, 9, 0, tzinfo=dt.timezone.utc)


def _load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture()
def frozen(tmp_path):
    rel = "config/stage1.yaml"
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"schema": "stage1-freeze-manifest/v1",
                                    "files": {rel: hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()}}),
                        encoding="utf-8")
    snapshot = tmp_path / "snapshot.zip"
    snapshot.write_bytes(b"snapshot stand-in")
    decision = tmp_path / "pilot_decision.json"
    decision.write_text('{"status": "RESOLVED", "B": 50000, "M1": 32, "M2": 32}', encoding="utf-8")
    return {"manifest": str(manifest), "sha": hashlib.sha256(manifest.read_bytes()).hexdigest(),
            "snapshot": str(snapshot), "decision": str(decision), "out": tmp_path / "auth" / "A.json"}


def _args(f, **over):
    a = {"config": "config/stage1.yaml", "manifest": f["manifest"], "expected-manifest-sha256": f["sha"],
         "snapshot": f["snapshot"], "decision": f["decision"], "run-id": "stage1-confirm-test", "out": str(f["out"]),
         "hours": "24"}
    a.update(over)
    return [x for k, v in a.items() for x in (f"--{k}", str(v))]


def test_issued_artifact_binds_what_the_gate_checks(frozen):
    issuer = _load("stage1_issue_authorization", "scripts/stage1_issue_authorization.py")
    assert issuer.main(_args(frozen), environ={"DYNAICL_STAGE1_AUTH_KEY": KEY}, now=NOW) == 0
    raw = frozen["out"].read_bytes()
    assert KEY.encode() not in raw                                   # the artifact holds no secret
    runner = _load("stage1_run", "scripts/stage1_run.py")
    cfg, cfg_sha = load_config(ROOT / "config/stage1.yaml")
    binding = runner.binding_for(cfg, cfg_sha, frozen["manifest"], frozen["snapshot"], frozen["decision"])
    payload = verify(raw, KEY.encode(), True, binding, NOW + dt.timedelta(hours=1))
    assert payload["test_only"] and payload["run_id"] == "stage1-confirm-test"
    assert payload["seeds"] == sorted(binding.seeds) and len(payload["seeds"]) == 7     # confirmatory roles only


def test_issuer_refusals(frozen):
    issuer = _load("stage1_issue_authorization", "scripts/stage1_issue_authorization.py")
    env = {"DYNAICL_STAGE1_AUTH_KEY": KEY}
    assert issuer.main(_args(frozen), environ={}, now=NOW) == 3                                  # no key
    assert issuer.main(_args(frozen, out=ROOT / "A_inside.json"), environ=env, now=NOW) == 3     # inside the repo
    assert not (ROOT / "A_inside.json").exists()
    assert issuer.main(_args(frozen, **{"expected-manifest-sha256": "0" * 64}), environ=env, now=NOW) == 3
    assert issuer.main(_args(frozen, hours="73"), environ=env, now=NOW) == 3                     # > 72 h
    assert issuer.main(_args(frozen, config="config/stage1_pilot.yaml"), environ=env, now=NOW) == 3  # not in manifest
    assert not frozen["out"].exists()
    assert issuer.main(_args(frozen), environ=env, now=NOW) == 0
    assert issuer.main(_args(frozen), environ=env, now=NOW) == 3                                 # never overwrite


def test_gate_refuses_test_only_keys_for_the_confirmatory_config(frozen, tmp_path, monkeypatch):
    monkeypatch.chdir(ROOT)
    monkeypatch.setenv("DYNAICL_STAGE1_AUTH_KEY", KEY)
    runner = _load("stage1_run", "scripts/stage1_run.py")
    out = tmp_path / "confirm"
    rc = runner.main(["train", "--config", "config/stage1.yaml", "--out", str(out), "--decision", frozen["decision"],
                      "--manifest", frozen["manifest"], "--expected-manifest-sha256", frozen["sha"],
                      "--snapshot", frozen["snapshot"], "--authorization", str(tmp_path / "none.json"),
                      "--run-id", "stage1-confirm-test", "--device", "cpu"])
    assert rc == 3
    assert "test-only keys can never authorize" in (out / "run_log.txt").read_text(encoding="utf-8")
    assert not (out / "RUN_LOCK.json").exists() and not (out / "models").exists()
