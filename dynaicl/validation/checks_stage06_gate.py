"""Stage 0.6 v2 validation of the authorization gate (V25), the refusal/corruption taxonomy (V26), the seeded checkpoint fuzz (V27)
and the seed-role table (V28). Synthetic inputs, temporary directories and TEST-ONLY keys only: no real artifact is ever created,
and V25 asserts that no artifact file remains in the workspace.
"""

from __future__ import annotations

import copy
import datetime as dt
import hashlib
import importlib.util
import io
import json
import os
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path
from types import SimpleNamespace

import numpy as np

from dynaicl.config import stage06_seed_roles as SR
from dynaicl.experiments import stage06_authorization as AU
from dynaicl.experiments import stage06_probe as P
from dynaicl.experiments.stage06_errors import Corrupt, Refusal
from dynaicl.validation.checks import CheckResult
from dynaicl.validation.mutations import _patched

ROOT = Path(__file__).resolve().parents[2]
KEY_TEST = b"TEST-ONLY-key-0001-not-a-secret-xxxxxxxx"
KEY_TEST2 = b"TEST-ONLY-key-0002-another-xxxxxxxxxxxx"
KEY_LAUNCH = b"unit-test-launch-key-not-real-0123456789"      # stands in for the user's key, inside tests only
T0 = "2026-10-11T00:00:00Z"
NOW = dt.datetime(2026, 10, 11, 6, 0, 0, tzinfo=dt.timezone.utc)
HEX_A, HEX_B = "a" * 64, "b" * 64


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


class Fixture:
    """A throwaway 'frozen tree': manifest, pre-registration, amendment, snapshot archive and the real confirmatory config."""

    def __init__(self, tmp: Path, config=ROOT / "config" / "stage06.yaml"):
        self.tmp = Path(tmp)
        self.root = self.tmp / "root"
        (self.root / "docs").mkdir(parents=True)
        for rel in (AU.PREREG_REL, AU.AMENDMENT_REL):
            shutil.copy(ROOT / rel, self.root / rel)
        (self.root / "env.json").write_text(json.dumps({"environment": P.current_environment()}), encoding="utf-8")
        self.manifest_rel = "docs/FREEZE_MANIFEST_STAGE06_v2.json"
        self.manifest_path = self.root / self.manifest_rel
        self.write_manifest()
        self.cfg, self.cfg_sha = P.load_config_once(config)
        self.auth_path = self.tmp / "auth_test_only.json"

    def write_manifest(self):
        files = {AU.PREREG_REL: sha((self.root / AU.PREREG_REL).read_bytes())}
        m = {"schema": P.MANIFEST_SCHEMA, "files": files, "config_hashes": {}, "environment_manifest": "env.json", "created_utc": T0}
        self.manifest_path.write_text(json.dumps(m, sort_keys=True) + "\n", encoding="utf-8")
        self.manifest_sha = sha(self.manifest_path.read_bytes())
        self.snapshot = self.tmp / "snapshot_test_only.zip"
        with zipfile.ZipFile(self.snapshot, "w") as z:
            z.write(self.manifest_path, self.manifest_rel)

    def args(self, **kw):
        base = dict(command="run", manifest=str(self.manifest_path), expected_manifest_sha256=self.manifest_sha,
                    snapshot=str(self.snapshot), authorization=str(self.auth_path), qualification=None)
        return SimpleNamespace(**{**base, **kw})

    def pre(self):
        m = P.verify_manifest(self.manifest_path, self.manifest_sha, self.root)
        return {"manifest": m, "manifest_sha256": m["manifest_sha256"], "environment": {"status": "identical"},
                "seeds": {"evaluation": list(self.cfg.seeds.evaluation), "bootstrap": self.cfg.seeds.bootstrap, "role": "fixture"}}

    def binding(self) -> AU.Binding:
        return P.make_binding(self.cfg, self.cfg_sha, self.pre(), self.snapshot, self.manifest_rel, self.root)

    def payload(self, **over) -> dict:
        p = AU.build_payload(self.binding(), "TEST-RUN-0001", NOW - dt.timedelta(hours=1), 24, test_only=True)
        p.update(over)
        return p

    def artifact(self, payload=None, key=KEY_TEST) -> bytes:
        payload = self.payload() if payload is None else payload
        return json.dumps({"payload": payload, "hmac_sha256": AU.sign(payload, key)}).encode("utf-8")

    def verify(self, raw, key=KEY_TEST, now=NOW, allow_test_only=True, cfg=None, cfg_sha=None):
        return P.authorize_confirmatory(cfg or self.cfg, cfg_sha or self.cfg_sha, self.args(), self.pre(), key, raw, now=now,
                                        root=self.root, allow_test_only=allow_test_only)


def outcome(fn) -> tuple[str, str]:
    """('ok'|'REFUSED'|'CORRUPT'|'EXC:<type>', message). Corrupt is a subclass of Refusal, so test it first."""
    try:
        fn()
        return "ok", ""
    except Corrupt as exc:
        return "CORRUPT", str(exc)
    except Refusal as exc:
        return "REFUSED", str(exc)
    except SystemExit as exc:
        return f"EXIT{exc.code}", ""
    except Exception as exc:           # any other exception type is a taxonomy failure
        return f"EXC:{type(exc).__name__}", str(exc)


class Rec:
    def __init__(self):
        self.rows, self.failed = {}, []

    def expect(self, name, fn, want, contains=None):
        got, msg = outcome(fn)
        ok = got == want and (contains is None or contains in msg)
        self.rows[name] = f"{got}" + ("" if ok else f"  <-- WANTED {want}{' containing ' + repr(contains) if contains else ''}: {msg[:140]}")
        if not ok:
            self.failed.append(name)

    def check(self, name, cond, info=""):
        self.rows[name] = "ok" if cond else f"FAIL {info}"
        if not cond:
            self.failed.append(name)


def flip(value):
    if isinstance(value, bool):
        return not value
    if value is None:
        return HEX_A
    if isinstance(value, str):
        return value[:-1] + ("0" if value[-1] != "0" else "1")
    if isinstance(value, dict):
        return {"evaluation": [value["evaluation"][0] + 1, *value["evaluation"][1:]], "bootstrap": value["bootstrap"]}
    return value


# ------------------------------------------------------------------------------------------ V25: the gate


def _check_authorization_gate_body(r: 'Rec') -> None:
    with tempfile.TemporaryDirectory(prefix="s06_gate_") as td:
        fx = Fixture(Path(td))
        good = fx.artifact()
        r.expect("baseline_test_only_artifact_accepted_by_test_path", lambda: fx.verify(good), "ok")
        r.expect("test_only_artifact_refused_on_production_path", lambda: fx.verify(good, allow_test_only=False), "REFUSED", "test-only")
        # altered: each bound field individually, signature kept
        base = json.loads(good)
        for field in AU.PAYLOAD_TYPES:
            doc = copy.deepcopy(base)
            doc["payload"][field] = flip(doc["payload"][field])
            r.expect(f"altered_field_{field}", lambda d=doc: fx.verify(json.dumps(d).encode()), "REFUSED", "signature")
        # stale / mismatched: correct signature, bound value differs
        for field in ("manifest_sha256", "snapshot_sha256", "config_hash", "config_file_sha256", "prereg_sha256", "amendment_sha256"):
            r.expect(f"mismatch_{field}", lambda f=field: fx.verify(fx.artifact(fx.payload(**{f: HEX_B}))), "REFUSED", field)
        ev, bs = fx.cfg.seeds.evaluation, fx.cfg.seeds.bootstrap
        seeds = {"subset": {"evaluation": list(ev[:1]), "bootstrap": bs}, "superset": {"evaluation": [*ev, 1], "bootstrap": bs},
                 "other_bootstrap": {"evaluation": list(ev), "bootstrap": bs + 1},
                 "bootstrap_swapped_with_replicate": {"evaluation": [ev[0], bs], "bootstrap": ev[1]}}
        for name, s in seeds.items():
            r.expect(f"seeds_{name}", lambda s=s: fx.verify(fx.artifact(fx.payload(seeds=s))), "REFUSED", "seed set")
        r.expect("seeds_reordered_replicates_accepted_as_a_set",
                 lambda: fx.verify(fx.artifact(fx.payload(seeds={"evaluation": list(reversed(ev)), "bootstrap": bs}))), "ok")
        for name, over, kw, msg in (
                ("mode_pilot", {"mode": "pilot"}, {}, "mode"), ("purpose", {"purpose": "x"}, {}, "purpose"),
                ("schema", {"schema": "stage06-authorization/v0"}, {}, "schema"), ("run_id_malformed", {"run_id": "a b"}, {}, "run_id"),
                ("validity_over_72h", {"expires_utc": "2026-10-20T00:00:00Z"}, {}, "validity"),
                ("expires_before_issue", {"expires_utc": "2026-10-10T00:00:00Z"}, {}, "validity"),
                ("issued_before_freeze", {"issued_utc": "2026-10-10T20:00:00Z", "expires_utc": "2026-10-11T20:00:00Z"}, {}, "before the current freeze"),
                ("qualification_binding_mismatch", {"qualification_sha256": HEX_A}, {}, "qualification"),
                ("not_yet_valid", {"issued_utc": "2026-10-11T08:00:00Z", "expires_utc": "2026-10-12T08:00:00Z"}, {}, "not yet valid"),
                ("timestamp_malformed", {"issued_utc": "yesterday"}, {}, "UTC timestamp")):
            exp = "CORRUPT" if name == "timestamp_malformed" else "REFUSED"
            r.expect(name, lambda o=over: fx.verify(fx.artifact(fx.payload(**o))), exp, msg)
        r.expect("expired", lambda: fx.verify(good, now=NOW + dt.timedelta(hours=30)), "REFUSED", "expired")
        # keys
        r.expect("wrong_key", lambda: fx.verify(fx.artifact(key=KEY_TEST2)), "REFUSED", "signature")
        r.expect("artifact_for_the_frozen_hashes_but_signed_with_a_test_key_refused_with_the_launch_key",
                 lambda: fx.verify(good, key=KEY_LAUNCH, allow_test_only=False), "REFUSED", "signature")
        manual = {**fx.payload(), "test_only": False}
        r.expect("test_key_refused_on_production_path", lambda: fx.verify(fx.artifact(manual, KEY_TEST), allow_test_only=False),
                 "REFUSED", "test-only key")
        # malformed artifacts are CORRUPT
        for name, raw in (("empty", b""), ("whitespace", b"  \n"), ("not_json", b"{{{"), ("array", b"[]"),
                          ("extra_key", json.dumps({**base, "x": 1}).encode()),
                          ("missing_hmac", json.dumps({"payload": base["payload"]}).encode()),
                          ("hmac_not_hex", json.dumps({**base, "hmac_sha256": "zz" * 32}).encode()),
                          ("payload_field_missing", json.dumps({"payload": {k: v for k, v in base["payload"].items() if k != "run_id"},
                                                                "hmac_sha256": base["hmac_sha256"]}).encode()),
                          ("payload_wrong_type", json.dumps({"payload": {**base["payload"], "test_only": "yes"},
                                                             "hmac_sha256": base["hmac_sha256"]}).encode())):
            r.expect(f"malformed_{name}", lambda raw=raw: fx.verify(raw), "CORRUPT")
        for k in range(1, 10):
            cut = len(good) * k // 10
            r.expect(f"truncated_at_{k}0pct", lambda cut=cut: fx.verify(good[:cut]), "CORRUPT")
        r.expect("artifact_file_missing", lambda: P.read_artifact_once(fx.tmp / "no_such_artifact.json"), "REFUSED", "not found")

        # run lock: replay, resume, results directories
        ck = fx.tmp / "ckpt" / "rootdir"
        gate = fx.verify(good)
        r.check("claim_first_start", AU.claim_run(ck, gate, "cfg", "man") == "started")
        r.check("claim_resume_same_run_id", AU.claim_run(ck, gate, "cfg", "man") == "resumed")
        other = fx.verify(fx.artifact(fx.payload(run_id="TEST-RUN-0002")))
        r.expect("replay_second_run_id_refused", lambda: AU.claim_run(ck, other, "cfg", "man"), "REFUSED", "already exists")
        r.expect("resume_under_other_manifest_refused", lambda: AU.claim_run(ck, gate, "cfg", "other_manifest"), "REFUSED", "different config or manifest")
        (ck / AU.LOCK_NAME).write_text("{not json", encoding="utf-8")
        r.expect("damaged_lock_is_corrupt", lambda: AU.claim_run(ck, gate, "cfg", "man"), "CORRUPT")
        runs = fx.tmp / "runs"
        (runs / AU.results_dir_name(gate)).mkdir(parents=True)
        (runs / AU.results_dir_name(gate) / "config_hash.txt").write_text("cfg\n", encoding="utf-8")
        r.expect("completed_run_id_refused", lambda: AU.check_results_dirs(runs, "cfg", gate), "REFUSED", "already completed")
        r.expect("other_runs_results_dir_refused", lambda: AU.check_results_dirs(runs, "cfg", other), "REFUSED", "second confirmatory run")
        r.expect("unrelated_results_dir_ignored", lambda: AU.check_results_dirs(runs, "different-config-hash", other), "ok")

        # mode and seed isolation through the real gate_session
        pilot_cfg, pilot_sha = P.load_config_once(ROOT / "config" / "stage06_pilot.yaml")
        test_cfg, test_sha = P.load_config_once(ROOT / "config" / "stage06_test.yaml")
        for name, cfg, csha in (("pilot", pilot_cfg, pilot_sha), ("test", test_cfg, test_sha)):
            r.expect(f"{name}_config_with_authorization_refused",
                     lambda c=cfg, s=csha: P.gate_session(c, s, fx.args(), fx.pre(), key=KEY_TEST, raw=good, allow_test_only=True, root=fx.root), "REFUSED", "take no authorization")
            r.expect(f"confirmatory_artifact_vs_{name}_config", lambda c=cfg, s=csha: fx.verify(good, cfg=c, cfg_sha=s), "REFUSED", "config_hash")
        r.expect("confirmatory_without_authorization_refused",
                 lambda: P.gate_session(fx.cfg, fx.cfg_sha, fx.args(authorization=None), fx.pre(), key=KEY_TEST, root=fx.root), "REFUSED", "needs --authorization")
        r.expect("confirmatory_without_snapshot_refused",
                 lambda: P.gate_session(fx.cfg, fx.cfg_sha, fx.args(snapshot=None), fx.pre(), key=KEY_TEST, raw=good, root=fx.root), "REFUSED", "--snapshot")
        r.expect("snapshot_from_another_freeze_refused", lambda: _other_snapshot(fx, good), "REFUSED", "differs from the verified manifest")

        # start, resume and completion are each verified (frozen files, authorization, expiry)
        fx.auth_path.write_bytes(good)
        s1 = P.gate_session(fx.cfg, fx.cfg_sha, fx.args(), fx.pre(), key=KEY_TEST, raw=good, now=NOW, allow_test_only=True, root=fx.root)
        r.check("start_verified", s1[0] is not None and s1[0].run_id == "TEST-RUN-0001")
        r.expect("resume_after_expiry_refused",
                 lambda: P.gate_session(fx.cfg, fx.cfg_sha, fx.args(), fx.pre(), key=KEY_TEST, raw=good, now=NOW + dt.timedelta(hours=30),
                                        allow_test_only=True, root=fx.root), "REFUSED", "expired")
        (fx.root / AU.PREREG_REL).write_text("tampered after the start\n", encoding="utf-8")
        r.expect("completion_refused_when_a_frozen_file_changed",
                 lambda: P.gate_session(fx.cfg, fx.cfg_sha, fx.args(), fx.pre(), key=KEY_TEST, raw=good, now=NOW, allow_test_only=True, root=fx.root),
                 "REFUSED", "fingerprint mismatch")
        shutil.copy(ROOT / AU.PREREG_REL, fx.root / AU.PREREG_REL)

        # a file swapped between the check and the use cannot change what the run is bound to
        fx.auth_path.write_bytes(good)
        raw_once = P.read_artifact_once(fx.auth_path)
        verified = fx.verify(raw_once)
        fx.auth_path.write_bytes(fx.artifact(fx.payload(run_id="TEST-RUN-SWAP")))        # swapped AFTER the check
        ck2 = fx.tmp / "ckpt2" / "rootdir"
        AU.claim_run(ck2, verified, "cfg", "man")
        lock = json.loads((ck2 / AU.LOCK_NAME).read_text())
        r.check("swap_after_check_does_not_change_the_bound_run_id", lock["run_id"] == "TEST-RUN-0001", str(lock))
        reads = []
        orig = P.read_artifact_once
        with _patched(P, "read_artifact_once", lambda p: (reads.append(p), orig(p))[1]):
            P.gate_session(fx.cfg, fx.cfg_sha, fx.args(), fx.pre(), key=KEY_TEST, raw=raw_once, now=NOW, allow_test_only=True, root=fx.root)
        r.check("gate_session_does_not_reread_the_artifact_when_given_its_bytes", not reads, str(reads))

        # bypass attempts through the real CLI entry point (preflight patched to the fixture; evaluation stubbed to raise)
        def reached(*a, **k):
            raise AssertionError("EVALUATION REACHED")
        cfg_path = str(ROOT / "config" / "stage06.yaml")
        env_names = ("DYNAICL_STAGE06_SKIP_AUTH", "DYNAICL_SKIP_AUTH", "DYNAICL_STAGE06_ALLOW_TEST_ONLY", "DYNAICL_AUTH_DISABLE", "STAGE06_NO_AUTH")
        saved = {k: os.environ.get(k) for k in env_names}
        try:
            for k in env_names:
                os.environ[k] = "1"
            with _patched(P, "ROOT", fx.root), _patched(P, "preflight", lambda *a, **k: fx.pre()), _patched(P, "run_units", reached), _patched(P, "analyze", reached):
                base_args = ["run", "--config", cfg_path, "--manifest", str(fx.manifest_path), "--expected-manifest-sha256", fx.manifest_sha,
                             "--checkpoint-dir", str(fx.tmp / "ck3"), "--runs-dir", str(fx.tmp / "runs3")]
                r.check("cli_run_without_authorization_returns_3", _main_code(base_args) == 3)
                for bad in ("--no-auth", "--allow-test-only", "--skip-authorization"):
                    r.check(f"cli_has_no_flag_{bad}", _main_code(base_args + [bad]) == 2)
                os.environ[AU.KEY_ENV] = KEY_TEST.decode()
                fx.auth_path.write_bytes(good)
                r.check("cli_refuses_test_only_artifact_even_with_the_matching_test_key",
                        _main_code(base_args + ["--authorization", str(fx.auth_path), "--snapshot", str(fx.snapshot)]) == 3)
                r.check("cli_pilot_cfg_with_authorization_returns_3",
                        _main_code(["run", "--config", str(ROOT / "config" / "stage06_pilot.yaml"), "--manifest", str(fx.manifest_path),
                                    "--expected-manifest-sha256", fx.manifest_sha, "--checkpoint-dir", str(fx.tmp / "ck4"),
                                    "--authorization", str(fx.auth_path), "--snapshot", str(fx.snapshot)]) == 3)
            r.check("no_run_or_checkpoint_directory_created_by_refused_launches", not (fx.tmp / "runs3").exists() and not (fx.tmp / "ck3").exists())
        finally:
            for k, v in saved.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v
            os.environ.pop(AU.KEY_ENV, None)
        r.expect("api_guard_run_units_needs_a_gate", lambda: P.run_units(fx.cfg, fx.tmp / "x", None, 1), "REFUSED", "verified authorization")
        r.expect("api_guard_analyze_needs_a_gate", lambda: P.analyze(fx.cfg, {}), "REFUSED", "verified authorization")
        r.expect("api_guard_write_results_needs_a_gate", lambda: P.write_results(fx.cfg, {}, {}, str(fx.tmp), []), "REFUSED", "verified authorization")

        # key hygiene
        env = {AU.KEY_ENV: "x" * 30}
        got = AU.obtain_key(env)
        r.check("key_removed_from_environment_after_reading", AU.KEY_ENV not in env and got == b"x" * 30)
        r.expect("no_key_non_interactive_refused", lambda: AU.obtain_key({}, interactive=False), "REFUSED", "no authorization key")
        r.check("key_prompt_used_when_interactive", AU.obtain_key({}, prompt=lambda _: "typed-secret-value-0123456789", interactive=True) == b"typed-secret-value-0123456789")
        try:
            fx.verify(fx.artifact(key=KEY_TEST2))
        except Refusal as exc:
            r.check("error_messages_never_contain_the_key", KEY_TEST.decode() not in str(exc) and KEY_TEST2.decode() not in str(exc))
        r.check("lock_and_gate_hold_no_key", KEY_TEST.decode() not in (ck2 / AU.LOCK_NAME).read_text() and KEY_TEST.decode() not in repr(verified))

        # issuer (test keys only, in a throwaway root)
        r.rows.update(_issuer_cases(fx, r))
    # no artifact may remain in the workspace
    leftovers = []
    for pth in ROOT.rglob("*.json"):
        if any(part in ("__pycache__", ".git", "runs", "work", "work_v2") for part in pth.parts):
            continue
        try:
            if '"hmac_sha256"' in pth.read_text(encoding="utf-8", errors="ignore"):
                leftovers.append(str(pth))
        except OSError:
            pass
    r.check("no_authorization_artifact_file_in_the_workspace", not leftovers, str(leftovers))



def _main_code(argv) -> int:
    """Run the CLI in-process with a NON-interactive stdin: no test may ever wait for a typed key (a hidden-prompt fallback would hang
    a check run from a terminal)."""
    saved = sys.stdin
    sys.stdin = io.StringIO("")
    try:
        return P.main(argv)
    except SystemExit as exc:
        return int(exc.code)
    except AssertionError as exc:
        return -1 if "EVALUATION REACHED" in str(exc) else -2
    except Exception:                  # an unexpected exception is a failed assertion of the check, never a crash of the check
        return -3
    finally:
        sys.stdin = saved


def _other_snapshot(fx: Fixture, good: bytes):
    other = fx.tmp / "other_freeze.zip"
    with zipfile.ZipFile(other, "w") as z:
        z.writestr(fx.manifest_rel, b'{"not": "the verified manifest"}')
    P.gate_session(fx.cfg, fx.cfg_sha, fx.args(snapshot=str(other)), fx.pre(), key=KEY_TEST, raw=good, now=NOW, allow_test_only=True, root=fx.root)


def _issuer_cases(fx: Fixture, parent: Rec) -> dict:
    spec = importlib.util.spec_from_file_location("stage06_issue_authorization", ROOT / "scripts" / "stage06_issue_authorization.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    r = Rec()
    out = fx.tmp / "issuer_out"
    base = ["--manifest", str(fx.manifest_path), "--snapshot", str(fx.snapshot), "--config", str(ROOT / "config" / "stage06.yaml"),
            "--run-id", "TEST-ISSUE-0001", "--hours", "24", "--out"]

    def run(name, extra, env_key, want_code, **kw):
        path = out / f"{name}.json"
        code = mod.main(base + [str(path)] + extra, root=fx.root, environ={AU.KEY_ENV: env_key} if env_key else {}, now=NOW,
                        interactive=False, **kw)
        r.check(f"issuer_{name}", code == want_code, f"exit {code}")
        return path
    p1 = run("test_only_with_test_key", ["--test-only"], KEY_TEST.decode(), 0)
    r.check("issuer_artifact_verifies_on_the_test_path",
            outcome(lambda: fx.verify(p1.read_bytes(), now=NOW + dt.timedelta(minutes=1)))[0] == "ok")
    r.check("issuer_artifact_is_marked_test_only", json.loads(p1.read_bytes())["payload"]["test_only"] is True)
    run("real_artifact_with_a_test_key_refused", [], KEY_TEST.decode(), 3)
    run("test_only_with_a_real_looking_key_refused", ["--test-only"], KEY_LAUNCH.decode(), 3)
    run("short_real_key_refused", [], "short", 3)
    run("no_key_refused", ["--test-only"], "", 3)
    run("hours_over_72_refused", ["--test-only", "--hours", "100"], KEY_TEST.decode(), 3)
    code = mod.main(base + [str(p1), "--test-only"], root=fx.root, environ={AU.KEY_ENV: KEY_TEST.decode()}, now=NOW, interactive=False)
    r.check("issuer_refuses_to_overwrite", code == 3)
    r.check("issuer_for_the_pilot_config_refused",
            mod.main([*base[:4], "--config", str(ROOT / "config" / "stage06_pilot.yaml"), *base[6:], str(out / "pilot.json"), "--test-only"],
                     root=fx.root, environ={AU.KEY_ENV: KEY_TEST.decode()}, now=NOW, interactive=False) == 3)
    return {**r.rows}


# ------------------------------------------------------------------------------------------ V26 / V27: files


def small_checkpoint(tmp: Path):
    cfg, _ = P.load_config_once(ROOT / "config" / "stage06_test.yaml")
    ck = P.checkpoint_root(tmp / "ckpt", cfg)
    units = [u for u in P.plan_units(cfg)][:6]
    originals = {}
    for i, u in enumerate(units):
        arrays = {k: (np.full(shape, i + 0.5, dtype=dtype)) for k, (shape, dtype) in P.expected_arrays(cfg, u).items()}
        P.save_unit(ck, u, {"note": f"unit {i}", "value": 0.25 * i, "nested": {"a": [1, 2, 3]}}, arrays, 1.5, cfg, None)
        originals[u] = arrays
    return cfg, ck, units, originals


def oracle_record_checksum(rec: dict) -> str:
    """Independent of P.record_checksum (which a mutant may replace)."""
    body = {k: v for k, v in rec.items() if k != "record_sha256"}
    return hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":"), allow_nan=True).encode("utf-8")).hexdigest()


def _json_mutations(good: dict):
    for k in good:
        yield f"missing_{k}", {kk: v for kk, v in good.items() if kk != k}
    wrong = {"schema": 5, "config_hash": 5, "unit": "x", "seconds": "slow", "npz_sha256": 5, "arrays": [], "meta": 3, "record_sha256": 5,
             "manifest_sha256": 5}
    for k, v in wrong.items():
        yield f"wrong_type_{k}", {**good, k: v}


def _check_refusal_taxonomy_body(r: 'Rec') -> None:
    with tempfile.TemporaryDirectory(prefix="s06_tax_") as td:
        td = Path(td)
        cfg, ck, units, orig = small_checkpoint(td)
        u0, u1 = units[0], units[1]
        n0 = P.unit_name(u0)
        js0 = ck / f"{n0}.json"
        good_text = js0.read_text(encoding="utf-8")
        good = json.loads(good_text)
        r.expect("valid_unit_loads", lambda: P.load_unit(ck, u0, cfg, None), "ok")
        r.check("unit_not_done_is_none_not_an_error", P.load_unit(ck, P.plan_units(cfg)[10], cfg, None) is None)

        def setjson(text):
            js0.write_text(text, encoding="utf-8")
        for name, text in (("empty_file", ""), ("whitespace_only", "  \n"), ("not_a_json_object", "[1, 2]"), ("scalar", "7")):
            setjson(text)
            r.expect(f"unit_json_{name}", lambda: P.load_unit(ck, u0, cfg, None), "CORRUPT")
        for k in range(1, 20):
            setjson(good_text[: len(good_text) * k // 20])
            r.expect(f"unit_json_truncated_at_{5 * k}pct", lambda: P.load_unit(ck, u0, cfg, None), "CORRUPT")
        for name, doc in _json_mutations(good):
            setjson(json.dumps(doc))
            r.expect(f"unit_json_{name}", lambda: P.load_unit(ck, u0, cfg, None), "CORRUPT")
        setjson(json.dumps({**good, "schema": "stage06-unit/v1"}))
        r.expect("unit_json_wrong_schema_version", lambda: P.load_unit(ck, u0, cfg, None), "REFUSED", "incompatible output schema")
        other = {**good, "config_hash": "0" * 64}
        other["record_sha256"] = oracle_record_checksum(other)
        setjson(json.dumps(other))
        r.expect("unit_json_other_config_hash_is_a_policy_refusal", lambda: P.load_unit(ck, u0, cfg, None), "REFUSED", "different config or manifest")
        setjson(json.dumps({**good, "seconds": 9.5}))
        r.expect("unit_json_valid_but_edited_without_recomputing_the_checksum", lambda: P.load_unit(ck, u0, cfg, None), "CORRUPT", "metadata")
        setjson(good_text)
        # duplicate unit id: the record of unit 1 stored under unit 0's name
        shutil.copy(ck / f"{P.unit_name(u1)}.json", js0)
        r.expect("duplicate_unit_id_record_under_another_name", lambda: P.load_unit(ck, u0, cfg, None), "CORRUPT", "unit identity")
        setjson(good_text)
        npz0 = ck / f"{n0}.npz"
        good_npz = npz0.read_bytes()
        npz0.write_bytes(good_npz[: len(good_npz) // 2])
        r.expect("arrays_truncated", lambda: P.load_unit(ck, u0, cfg, None), "CORRUPT", "checksum")
        npz0.write_bytes(b"")
        r.expect("arrays_empty", lambda: P.load_unit(ck, u0, cfg, None), "CORRUPT", "checksum")
        npz0.unlink()
        r.expect("arrays_missing", lambda: P.load_unit(ck, u0, cfg, None), "CORRUPT", "missing")
        npz0.write_bytes(good_npz)
        r.expect("restored_unit_loads_again", lambda: P.load_unit(ck, u0, cfg, None), "ok")
        (ck / "primary_9_9_9.json").write_text("{}", encoding="utf-8")
        r.expect("unexpected_unit_file_in_checkpoint_dir", lambda: P.scan_checkpoint_dir(ck, cfg), "CORRUPT", "unexpected file")
        (ck / "primary_9_9_9.json").unlink()
        (ck / "primary_0_0_0.npz.tmp").write_bytes(b"partial")
        r.expect("stale_tmp_file_is_tolerated", lambda: P.scan_checkpoint_dir(ck, cfg), "ok")

        # qualification report and the other inputs
        fx = Fixture(td / "fx", ROOT / "config" / "stage06_test.yaml")
        man = fx.pre()["manifest"]
        env = P.current_environment()
        good_q = {"environment": env, "manifest_sha256": man["manifest_sha256"], "config_hash": fx.cfg.config_hash(), "passed": True,
                  "checks": {}}
        qp = td / "qual.json"

        def qtest(text):
            qp.write_text(text, encoding="utf-8")
            return lambda: P.read_qualification(qp, man, fx.cfg, env)
        r.expect("qualification_valid", qtest(json.dumps(good_q)), "ok")
        r.expect("qualification_path_missing", lambda: P.read_qualification(td / "nope.json", man, fx.cfg, env), "REFUSED", "not found")
        r.expect("qualification_empty", qtest(""), "CORRUPT")
        r.expect("qualification_malformed", qtest("{oops"), "CORRUPT")
        r.expect("qualification_not_an_object", qtest("[]"), "CORRUPT")
        for k in ("environment", "manifest_sha256", "config_hash", "passed"):
            r.expect(f"qualification_missing_{k}", qtest(json.dumps({kk: v for kk, v in good_q.items() if kk != k})), "CORRUPT")
        r.expect("qualification_wrong_type_passed", qtest(json.dumps({**good_q, "passed": "yes"})), "CORRUPT")
        r.expect("qualification_stale_other_manifest", qtest(json.dumps({**good_q, "manifest_sha256": "1" * 64})), "REFUSED", "stale")
        r.expect("qualification_stale_other_environment", qtest(json.dumps({**good_q, "environment": {**env, "machine": "x"}})), "REFUSED", "stale")
        r.expect("qualification_failed", qtest(json.dumps({**good_q, "passed": False})), "REFUSED", "did not pass")
        r.expect("manifest_empty", lambda: (fx.manifest_path.write_text("", encoding="utf-8"), P.verify_manifest(
            fx.manifest_path, sha(b""), fx.root))[1], "CORRUPT")
        fx.manifest_path.write_text('{"schema": "' + P.MANIFEST_SCHEMA + '", "files": {}}', encoding="utf-8")
        r.expect("manifest_missing_fields", lambda: P.verify_manifest(fx.manifest_path, sha(fx.manifest_path.read_bytes()), fx.root), "CORRUPT")
        r.expect("config_file_missing", lambda: P.load_config_once(td / "nope.yaml"), "REFUSED", "not found")
        (td / "bad.yaml").write_text("a: [", encoding="utf-8")
        r.expect("config_file_malformed_yaml", lambda: P.load_config_once(td / "bad.yaml"), "CORRUPT")
        (td / "wrong.yaml").write_text("schema_version: 1\n", encoding="utf-8")
        r.expect("config_file_schema_violation", lambda: P.load_config_once(td / "wrong.yaml"), "REFUSED", "schema")

        # end to end through the CLI: exit codes, named path, nothing written
        runs = td / "runs_cli"
        base = ["analyze", "--config", str(ROOT / "config" / "stage06_test.yaml"), "--checkpoint-dir", str(td / "ckpt"), "--runs-dir", str(runs)]
        js0.write_text(good_text[: len(good_text) // 2], encoding="utf-8")
        r.check("cli_truncated_unit_json_exits_4", _main_code(base) == 4)
        r.check("cli_writes_no_partial_output", not runs.exists())
        js0.write_text(good_text, encoding="utf-8")
        r.check("cli_missing_config_exits_3", _main_code(["analyze", "--config", str(td / "none.yaml"), "--runs-dir", str(runs)]) == 3)
        r.check("cli_missing_qualification_path_exits_3_in_test_mode",
                _main_code([*base[:5], "--qualification", str(td / "none.json"), *base[5:]]) == 3)



def check_checkpoint_fuzz(seed: int = 61021, trials: int = 400) -> CheckResult:
    """Seeded fuzz of unit and checkpoint files. The only acceptable outcomes: (a) a load that returns EXACTLY the original
    record and arrays (checksum-verified), or (b) an explicit REFUSED / CORRUPT. A traceback, a silent skip (None for a unit whose
    metadata exists) or a load with changed content fails."""
    rng = np.random.default_rng(seed)
    tally = {"loaded_identical": 0, "REFUSED": 0, "CORRUPT": 0}
    bad = []
    with tempfile.TemporaryDirectory(prefix="s06_fuzz_") as td:
        cfg, ck, units, orig = small_checkpoint(Path(td))
        pristine = {f.name: f.read_bytes() for f in ck.iterdir()}
        base_rec = {u: P.load_unit(ck, u, cfg, None) for u in units}
        for t in range(trials):
            for name, data in pristine.items():
                (ck / name).write_bytes(data)
            u = units[int(rng.integers(len(units)))]
            name = P.unit_name(u)
            targets = [f"{name}.json", f"{name}.npz"]
            hit = targets[int(rng.integers(2))] if rng.random() < 0.8 else None
            op = int(rng.integers(8))
            files = targets if hit is None else [hit]
            for fn in files:
                data = bytearray(pristine[fn])
                if op == 0:
                    data = data[: int(rng.integers(0, len(data)))]
                elif op == 1:
                    data[int(rng.integers(len(data)))] ^= 1 << int(rng.integers(8))
                elif op == 2:
                    a = int(rng.integers(len(data)))
                    data[a:a + int(rng.integers(1, 64))] = b"\x00" * int(rng.integers(1, 64))
                elif op == 3:
                    a = int(rng.integers(len(data)))
                    del data[a:a + int(rng.integers(1, 32))]
                elif op == 4:
                    a = int(rng.integers(len(data)))
                    data[a:a] = bytes(rng.integers(0, 256, int(rng.integers(1, 16))).astype("uint8"))
                elif op == 5:
                    data = bytearray(rng.integers(0, 256, int(rng.integers(0, 200))).astype("uint8").tobytes())
                elif op == 6:
                    other = units[int(rng.integers(len(units)))]
                    data = bytearray(pristine[f"{P.unit_name(other)}{Path(fn).suffix}"])
                else:
                    data = bytearray()
                (ck / fn).write_bytes(bytes(data))
            try:
                got = P.load_unit(ck, u, cfg, None)
            except Corrupt:
                tally["CORRUPT"] += 1
                continue
            except Refusal:
                tally["REFUSED"] += 1
                continue
            except Exception as exc:
                bad.append((t, op, hit, f"traceback {type(exc).__name__}"))
                continue
            if got is None:
                bad.append((t, op, hit, "silent skip (metadata missing is only legitimate when the file does not exist)"))
                continue
            rec, arrays = got
            same = rec == base_rec[u][0] and all(np.array_equal(arrays[k], base_rec[u][1][k]) for k in arrays) and set(arrays) == set(base_rec[u][1])
            if same:
                tally["loaded_identical"] += 1
            else:
                bad.append((t, op, hit, "loaded with CHANGED content"))
    return CheckResult("V27_checkpoint_fuzz", not bad, {"trials": trials, "seed": seed, "tally": tally, "failures": bad[:5], "n_failures": len(bad)})


# ------------------------------------------------------------------------------------------ V28: seed roles


def _check_seed_roles_body(r: 'Rec') -> None:
    table = ROOT / "config" / "stage06_seed_manifest.yaml"
    roles = SR.load_roles(table)
    r.check("table_defines_exactly_the_required_roles", set(roles) == set(SR.REQUIRED_ROLES))
    cc, _ = P.load_config_once(ROOT / "config" / "stage06.yaml")
    pc, _ = P.load_config_once(ROOT / "config" / "stage06_pilot.yaml")
    r.check("pilot_seed_roles_match_the_pilot_config",
            roles["pilot_evaluation"]["seeds"] == list(pc.seeds.evaluation) and roles["pilot_bootstrap"]["seeds"] == [pc.seeds.bootstrap])
    r.check("confirmatory_seed_roles_match_the_confirmatory_config",
            roles["confirmatory_evaluation"]["seeds"] == list(cc.seeds.evaluation) and roles["confirmatory_bootstrap"]["seeds"] == [cc.seeds.bootstrap])
    r.check("pilot_evaluation_and_bootstrap_roles_are_distinct", not set(roles["pilot_evaluation"]["seeds"]) & set(roles["pilot_bootstrap"]["seeds"]))
    allv = [s for x in roles.values() for s in x["seeds"]]
    r.check("every_seed_in_exactly_one_role", len(allv) == len(set(allv)))
    r.check("each_role_states_allowed_and_forbidden_uses", all(x["allowed_uses"] and x["forbidden_uses"] for x in roles.values()))
    doc = ROOT / "docs" / "STAGE06_SEED_ROLES.md"
    r.check("generated_documentation_agrees_with_the_table", doc.is_file() and doc.read_text(encoding="utf-8") == SR.render_markdown(roles))
    for name in ("stage06.yaml", "stage06_pilot.yaml", "stage06_test.yaml"):
        cfg, _ = P.load_config_once(ROOT / "config" / name)
        r.expect(f"config_{name}_seeds_match_its_mode_role", lambda c=cfg: P.check_seeds(c, table), "ok")
    pilot, _ = P.load_config_once(ROOT / "config" / "stage06_pilot.yaml")
    ev, bs = list(pilot.seeds.evaluation), pilot.seeds.bootstrap

    def with_seeds(evaluation, bootstrap):
        d = pilot.to_dict()
        d["seeds"] = {"evaluation": evaluation, "bootstrap": bootstrap}
        from dynaicl.config.stage06_schema import stage06_config_from_dict
        return stage06_config_from_dict(d)
    sel = roles["selection"]["seeds"][0]
    val = roles["validation"]["seeds"][0]
    conf = roles["confirmatory_evaluation"]["seeds"]
    for name, e, b in (("bootstrap_seed_used_as_evaluation", [bs, ev[1]], ev[0]),
                       ("replicates_swapped", [ev[1], ev[0]], bs), ("selection_seed_in_pilot", [sel, ev[1]], bs),
                       ("validation_seed_in_pilot", ev, val), ("confirmatory_seeds_in_pilot", list(conf), roles["confirmatory_bootstrap"]["seeds"][0]),
                       ("pilot_bootstrap_as_second_evaluation", [ev[0], bs], 62998)):
        try:
            cfg = with_seeds(e, b)
        except Exception:
            r.rows[f"pilot_run_with_{name}"] = "ok (schema already rejects)"
            continue
        r.expect(f"pilot_run_with_{name}_refused", lambda c=cfg: P.check_seeds(c, table), "REFUSED", "allocation")
    # a pilot seed used only in its role in the repository: confirmatory seeds never appear as literals in code or notebooks
    conf_all = [str(s) for k in ("confirmatory_evaluation", "confirmatory_bootstrap") for s in roles[k]["seeds"]]
    hits = []
    import re
    pat = re.compile(r"(?<![\d.])(?:" + "|".join(conf_all) + r")(?![\d])")
    for pth in list(ROOT.rglob("*.py")) + list(ROOT.rglob("*_v2.ipynb")):    # v1 notebooks are preserved, obsolete files
        if any(part in ("__pycache__", ".git", "work", "work_v2", "dist") for part in pth.parts):
            continue
        if pat.search(pth.read_text(encoding="utf-8", errors="ignore")):
            hits.append(str(pth.relative_to(ROOT)))
    r.check("confirmatory_seeds_are_not_literals_in_any_code_or_notebook", not hits, str(hits))
    r.check("seed_collision_across_roles_refused", outcome(lambda: _collide(table))[0] == "REFUSED")



def _collide(table: Path):
    with tempfile.TemporaryDirectory() as td:
        import yaml
        d = yaml.safe_load(table.read_text(encoding="utf-8"))
        d["roles"]["selection"]["seeds"] = d["roles"]["selection"]["seeds"] + [62001]
        p = Path(td) / "t.yaml"
        p.write_text(yaml.safe_dump(d), encoding="utf-8")
        SR.load_roles(p)


def _guarded(name: str, body) -> CheckResult:
    """Run a check body; an unexpected exception (typically because the code under test was mutated) is recorded as a FAILED
    assertion of this check, with the exception named, instead of crashing the check."""
    r = Rec()
    try:
        body(r)
    except Exception as exc:
        r.failed.append(f"UNEXPECTED {type(exc).__name__} after {len(r.rows)} cases: {str(exc)[:160]}")
        r.rows["unexpected_exception"] = f"FAIL {type(exc).__name__}: {str(exc)[:200]}"
    return CheckResult(name, not r.failed, {"cases": len(r.rows), "failed": r.failed, "rows": r.rows})


def check_authorization_gate() -> CheckResult:
    return _guarded("V25_authorization_gate", _check_authorization_gate_body)


def check_refusal_taxonomy() -> CheckResult:
    return _guarded("V26_refusal_taxonomy", _check_refusal_taxonomy_body)


def check_seed_roles() -> CheckResult:
    return _guarded("V28_seed_roles", _check_seed_roles_body)


ALL_CHECKS_STAGE06_GATE = {"V25": check_authorization_gate, "V26": check_refusal_taxonomy, "V27": check_checkpoint_fuzz,
                           "V28": check_seed_roles}
