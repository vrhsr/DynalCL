"""Stage 0.6 v2 negative controls for the authorization gate, refusal handling and seed roles. Each mutation replaces one function in
memory (module attribute patch); files on disk are never modified. Each must be killed by an assertion-level FAIL of its intended
check (V25-V28), not by a crash."""

from __future__ import annotations

import contextlib
import datetime as dt
import json

from dynaicl.config import stage06_seed_roles as SR
from dynaicl.experiments import stage06_authorization as AU
from dynaicl.experiments import stage06_probe as P
from dynaicl.experiments.stage06_errors import Corrupt
from dynaicl.validation.mutations import _patched

_orig_verify = AU.verify_authorization
_orig_gate_session = P.gate_session
_orig_claim = AU.claim_run
_orig_read_json = P.read_json_object
_orig_load_unit = P.load_unit
_orig_check_mode_seeds = SR.check_mode_seeds


def _resigned(raw: bytes, key: bytes, **over) -> bytes:
    """Rewrite the payload (and re-sign it with the verifier's own key) so that the check under mutation can never see the difference."""
    doc = json.loads(raw.decode("utf-8"))
    doc["payload"].update(over)
    doc["hmac_sha256"] = AU.sign(doc["payload"], key)
    return json.dumps(doc).encode("utf-8")


def _payload(raw: bytes) -> dict | None:
    """The artifact's payload, or None when it cannot be parsed (the mutants then leave the call untouched)."""
    try:
        p = json.loads(raw.decode("utf-8"))["payload"]
        return p if isinstance(p, dict) else None
    except (ValueError, KeyError, TypeError, UnicodeDecodeError):
        return None


HASH_FIELDS = ("manifest_sha256", "snapshot_sha256", "config_hash", "config_file_sha256", "prereg_sha256", "amendment_sha256")


@contextlib.contextmanager
def skip_hash_comparison():
    """The bound manifest / snapshot / config / pre-registration / amendment hashes are not compared (a stale binding is accepted)."""
    def bad(raw, key, binding, now, *, path=None, allow_test_only=False):
        p = _payload(raw)
        if p and any(p.get(f) != getattr(binding, f) for f in HASH_FIELDS):
            raw = _resigned(raw, key, **{f: getattr(binding, f) for f in HASH_FIELDS})
        return _orig_verify(raw, key, binding, now, path=path, allow_test_only=allow_test_only)
    with _patched(AU, "verify_authorization", bad):
        yield


@contextlib.contextmanager
def ignore_mode():
    """The execution mode field is not checked (a pilot-mode artifact is accepted)."""
    def bad(raw, key, binding, now, *, path=None, allow_test_only=False):
        p = _payload(raw)
        if p and p.get("mode") != AU.MODE:
            raw = _resigned(raw, key, mode=AU.MODE)
        return _orig_verify(raw, key, binding, now, path=path, allow_test_only=allow_test_only)
    with _patched(AU, "verify_authorization", bad):
        yield


@contextlib.contextmanager
def accept_subset_of_seeds():
    """An artifact whose seeds are a proper subset of the configuration's seeds is accepted."""
    def bad(raw, key, binding, now, *, path=None, allow_test_only=False):
        p = _payload(raw)
        try:
            s = p["seeds"]
            given = set(s["evaluation"]) | {s["bootstrap"]}
        except (TypeError, KeyError):
            given = None
        want = set(binding.evaluation_seeds) | {binding.bootstrap_seed}
        if given is not None and given < want:
            raw = _resigned(raw, key, seeds={"evaluation": list(binding.evaluation_seeds), "bootstrap": binding.bootstrap_seed})
        return _orig_verify(raw, key, binding, now, path=path, allow_test_only=allow_test_only)
    with _patched(AU, "verify_authorization", bad):
        yield


@contextlib.contextmanager
def accept_expired():
    """Expiry is ignored: when the clock is past the expiry it is pinned inside the validity window."""
    def bad(raw, key, binding, now, *, path=None, allow_test_only=False):
        p = _payload(raw)
        try:
            if now > AU.parse_time(p["expires_utc"], "expires_utc"):
                now = AU.parse_time(p["issued_utc"], "issued_utc") + dt.timedelta(minutes=1)
        except Exception:
            pass
        return _orig_verify(raw, key, binding, now, path=path, allow_test_only=allow_test_only)
    with _patched(AU, "verify_authorization", bad):
        yield


@contextlib.contextmanager
def accept_test_keys():
    """Test-only artifacts and test keys are accepted on the production path."""
    def bad(raw, key, binding, now, *, path=None, allow_test_only=False):
        return _orig_verify(raw, key, binding, now, path=path, allow_test_only=True)
    with _patched(AU, "verify_authorization", bad):
        yield


@contextlib.contextmanager
def skip_reverification_on_resume():
    """Only the first verification is real: a resume or the completion check returns the cached first result."""
    cache = {}

    def bad(cfg, cfg_file_sha, args, pre, **kw):
        key = args.authorization
        if key in cache:
            return cache[key]
        cache[key] = _orig_gate_session(cfg, cfg_file_sha, args, pre, **kw)
        return cache[key]
    with _patched(P, "gate_session", bad):
        yield


@contextlib.contextmanager
def reread_artifact_after_check():
    """The run is bound to a fresh read of the artifact file at use time instead of the bytes that were verified."""
    def bad(ckpt_root, gate, config_hash, manifest_sha256):
        path = P.__dict__.get("_LAST_AUTH_PATH")
        if path:
            try:
                fresh = json.loads(open(path, "rb").read().decode("utf-8"))["payload"]["run_id"]
                gate = AU.VerifiedGate(fresh, gate.artifact_sha256, gate.issued_utc, gate.expires_utc, gate.test_only, gate.payload)
            except (OSError, ValueError, KeyError):
                pass
        return _orig_claim(ckpt_root, gate, config_hash, manifest_sha256)

    def remember(cfg, cfg_file_sha, args, pre, **kw):
        P._LAST_AUTH_PATH = getattr(args, "authorization", None)
        return _orig_gate_session(cfg, cfg_file_sha, args, pre, **kw)
    with _patched(AU, "claim_run", bad), _patched(P, "gate_session", remember):
        yield


@contextlib.contextmanager
def run_lock_not_enforced():
    """A different run id is accepted in a directory that already holds a run (replay)."""
    def bad(ckpt_root, gate, config_hash, manifest_sha256):
        return "started"
    with _patched(AU, "claim_run", bad):
        yield


@contextlib.contextmanager
def env_var_disables_gate():
    """An environment variable switches the gate off for pilot-like launches."""
    import os

    def bad(cfg, cfg_file_sha, args, pre, **kw):
        if os.environ.get("DYNAICL_STAGE06_SKIP_AUTH"):
            return None, None, None
        return _orig_gate_session(cfg, cfg_file_sha, args, pre, **kw)
    with _patched(P, "gate_session", bad):
        yield


@contextlib.contextmanager
def unit_json_error_uncaught():
    """The v1 behaviour: a truncated unit JSON raises the parser's exception instead of a CORRUPT outcome."""
    def bad(path, what):
        return json.loads(open(path, "rb").read().decode("utf-8"))
    with _patched(P, "read_json_object", bad):
        yield


@contextlib.contextmanager
def unit_record_checksum_skipped():
    """The metadata record's own checksum is not verified on load (only the arrays are); saving still computes it."""
    orig = P.record_checksum

    def bad(rec):
        return rec.get("record_sha256") or orig(rec)
    with _patched(P, "record_checksum", bad):
        yield


@contextlib.contextmanager
def seed_roles_not_enforced():
    """The seed-role allocation is not checked: any distinct seeds are accepted for any mode."""
    def bad(roles, mode, evaluation, bootstrap):
        return {"evaluation": list(evaluation), "bootstrap": bootstrap, "role": "unchecked"}
    with _patched(SR, "check_mode_seeds", bad):
        yield


MUTATIONS_STAGE06_GATE = {
    "skip_hash_comparison": skip_hash_comparison, "ignore_mode": ignore_mode, "accept_subset_of_seeds": accept_subset_of_seeds,
    "accept_expired": accept_expired, "accept_test_keys": accept_test_keys, "skip_reverification_on_resume": skip_reverification_on_resume,
    "reread_artifact_after_check": reread_artifact_after_check, "run_lock_not_enforced": run_lock_not_enforced,
    "env_var_disables_gate": env_var_disables_gate, "unit_json_error_uncaught": unit_json_error_uncaught,
    "unit_record_checksum_skipped": unit_record_checksum_skipped, "seed_roles_not_enforced": seed_roles_not_enforced,
}
PRIMARY_DETECTORS = {"skip_hash_comparison": "V25", "ignore_mode": "V25", "accept_subset_of_seeds": "V25", "accept_expired": "V25",
                     "accept_test_keys": "V25", "skip_reverification_on_resume": "V25", "reread_artifact_after_check": "V25",
                     "run_lock_not_enforced": "V25", "env_var_disables_gate": "V25", "unit_json_error_uncaught": "V26",
                     "unit_record_checksum_skipped": "V26", "seed_roles_not_enforced": "V28"}
