"""Stage 0.6 confirmatory authorization gate (v2 freeze). Design and threat model: docs/STAGE06_AUTHORIZATION_GATE.md.

A confirmatory ``run`` or ``analyze`` needs, in addition to the frozen manifest, config, seeds and checkpoint rules, an
authorization artifact: a small JSON document whose payload binds the frozen state (manifest, snapshot archive, config,
pre-registration, amendment), the exact seed set, a run id and a validity window, authenticated with HMAC-SHA256 under a
secret key that only the user holds and types or exports at launch (never stored, logged, checkpointed or written to results).

Standard library only. The verifier reads the artifact file ONCE (bytes) and uses only the parsed copy afterwards, so a file
swapped between the check and the use cannot change what the run is bound to.

What this does NOT do: it does not stop a party that can edit and run arbitrary code outside the frozen tree, and a Python
caller that builds a :class:`VerifiedGate` by hand can bypass the API-level guards. It stops accidental, automated or
agent-initiated launches through the frozen runner, because nobody without the key can produce a valid artifact.
"""

from __future__ import annotations

import datetime as _dt
import getpass
import hashlib
import hmac
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path

from dynaicl.experiments.stage06_errors import Corrupt, Refusal

SCHEMA = "stage06-authorization/v1"
PURPOSE = "confirmatory_authorization"
MODE = "confirmatory"
DOMAIN = b"dynaicl-stage06-authorization/v1\n"
KEY_ENV = "DYNAICL_STAGE06_AUTH_KEY"
TEST_KEY_PREFIX = "TEST-ONLY-"
MIN_KEY_CHARS = 24
MAX_VALIDITY = _dt.timedelta(hours=72)
CLOCK_SKEW = _dt.timedelta(minutes=5)
RUN_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{7,63}$")
AMENDMENT_REL = "docs/PREREG_stage06_AMENDMENT_1.md"
PREREG_REL = "docs/PREREG_stage06.md"
LOCK_NAME = "RUN_LOCK.json"
LOCK_SCHEMA = "stage06-run-lock/v1"
TIME_FMT = "%Y-%m-%dT%H:%M:%SZ"

PAYLOAD_TYPES = {"schema": str, "purpose": str, "test_only": bool, "mode": str, "run_id": str, "issued_utc": str,
                 "expires_utc": str, "manifest_sha256": str, "snapshot_sha256": str, "config_hash": str,
                 "config_file_sha256": str, "prereg_sha256": str, "amendment_sha256": str, "seeds": dict,
                 "qualification_sha256": (str, type(None))}
HEX64 = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True)
class Binding:
    """What the artifact must match: the CURRENT frozen state as the runner computes it itself."""

    manifest_sha256: str
    snapshot_sha256: str
    config_hash: str
    config_file_sha256: str
    prereg_sha256: str
    amendment_sha256: str
    evaluation_seeds: tuple
    bootstrap_seed: int
    freeze_created_utc: str
    qualification_sha256: str | None = None


@dataclass(frozen=True)
class VerifiedGate:
    """Evidence that an artifact passed :func:`verify_authorization`. Only that function builds it."""

    run_id: str
    artifact_sha256: str
    issued_utc: str
    expires_utc: str
    test_only: bool
    payload: tuple


# ------------------------------------------------------------------------------------------ payload / signature


def canonical(payload: dict) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("ascii")


def sign(payload: dict, key: bytes) -> str:
    return hmac.new(key, DOMAIN + canonical(payload), hashlib.sha256).hexdigest()


def parse_time(text: str, what: str, path=None) -> _dt.datetime:
    try:
        return _dt.datetime.strptime(text, TIME_FMT).replace(tzinfo=_dt.timezone.utc)
    except (ValueError, TypeError):
        raise Corrupt(f"{what} {text!r} is not a UTC timestamp of the form YYYY-MM-DDTHH:MM:SSZ", path)


def utc_text(t: _dt.datetime) -> str:
    return t.astimezone(_dt.timezone.utc).strftime(TIME_FMT)


def _shape(obj, path) -> tuple[dict, str]:
    if not isinstance(obj, dict) or set(obj) != {"payload", "hmac_sha256"}:
        raise Corrupt("authorization artifact must be a JSON object with exactly the keys 'payload' and 'hmac_sha256'", path)
    payload, sig = obj["payload"], obj["hmac_sha256"]
    if not isinstance(payload, dict) or not isinstance(sig, str) or not HEX64.match(sig):
        raise Corrupt("authorization artifact: 'payload' must be an object and 'hmac_sha256' 64 lowercase hex characters", path)
    if set(payload) != set(PAYLOAD_TYPES):
        raise Corrupt(f"authorization payload fields differ from the schema: missing {sorted(set(PAYLOAD_TYPES) - set(payload))}, "
                      f"unexpected {sorted(set(payload) - set(PAYLOAD_TYPES))}", path)
    for k, t in PAYLOAD_TYPES.items():
        v = payload[k]
        if isinstance(v, bool) != (t is bool) or not isinstance(v, t):
            raise Corrupt(f"authorization payload field {k!r} has the wrong type ({type(v).__name__})", path)
    seeds = payload["seeds"]
    if set(seeds) != {"evaluation", "bootstrap"} or not isinstance(seeds["bootstrap"], int) or isinstance(seeds["bootstrap"], bool) \
            or not isinstance(seeds["evaluation"], list) or not all(isinstance(s, int) and not isinstance(s, bool) for s in seeds["evaluation"]):
        raise Corrupt("authorization payload field 'seeds' must be {'evaluation': [int, ...], 'bootstrap': int}", path)
    for k in ("manifest_sha256", "snapshot_sha256", "config_hash", "config_file_sha256", "prereg_sha256", "amendment_sha256"):
        if not HEX64.match(payload[k]):
            raise Corrupt(f"authorization payload field {k!r} is not a 64-character lowercase SHA-256", path)
    q = payload["qualification_sha256"]
    if q is not None and not HEX64.match(q):
        raise Corrupt("authorization payload field 'qualification_sha256' is not a SHA-256 or null", path)
    return payload, sig


def verify_authorization(raw: bytes, key: bytes, binding: Binding, now: _dt.datetime, *, path=None,
                         allow_test_only: bool = False) -> VerifiedGate:
    """Verify ``raw`` (the artifact's bytes, read once) against the runner's own view of the frozen state. Raises
    :class:`Corrupt` for malformed input and :class:`Refusal` for every policy failure. Order: shape, signature (constant
    time), then each bound field by name, then validity. ``allow_test_only`` exists for the test suite ONLY: no command line
    flag, environment variable or config key reaches it (V25 asserts this)."""
    if not raw.strip():
        raise Corrupt("authorization artifact is empty", path)
    try:
        obj = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError) as exc:
        raise Corrupt(f"authorization artifact is not valid JSON ({type(exc).__name__}: truncated or damaged?)", path)
    payload, sig = _shape(obj, path)
    if not hmac.compare_digest(sig, sign(payload, key)):
        raise Refusal("authorization signature is invalid (wrong key, or the artifact was altered)", path)
    if payload["schema"] != SCHEMA:
        raise Refusal(f"authorization schema {payload['schema']!r} is not {SCHEMA!r}", path)
    if payload["purpose"] != PURPOSE:
        raise Refusal(f"authorization purpose {payload['purpose']!r} is not {PURPOSE!r}", path)
    if payload["test_only"] and not allow_test_only:
        raise Refusal("a test-only authorization artifact can never authorize a confirmatory run", path)
    if payload["mode"] != MODE:
        raise Refusal(f"authorization mode {payload['mode']!r} is not {MODE!r}", path)
    if not RUN_ID_RE.match(payload["run_id"]):
        raise Refusal("authorization run_id is malformed (8-64 characters of A-Z a-z 0-9 . _ -)", path)
    for field, want in (("manifest_sha256", binding.manifest_sha256), ("snapshot_sha256", binding.snapshot_sha256),
                        ("config_hash", binding.config_hash), ("config_file_sha256", binding.config_file_sha256),
                        ("prereg_sha256", binding.prereg_sha256), ("amendment_sha256", binding.amendment_sha256)):
        if payload[field] != want:
            raise Refusal(f"authorization is bound to a different {field} (stale or for another freeze)", path)
    seeds = payload["seeds"]
    if sorted(seeds["evaluation"]) != sorted(binding.evaluation_seeds) or seeds["bootstrap"] != binding.bootstrap_seed:
        raise Refusal("authorization seed set is not equal to the configuration's seed set (subsets or supersets are refused)", path)
    if len(set(seeds["evaluation"]) | {seeds["bootstrap"]}) != len(seeds["evaluation"]) + 1:
        raise Refusal("authorization seeds are not distinct", path)
    q = payload["qualification_sha256"]
    if q is not None and q != binding.qualification_sha256:
        raise Refusal("authorization binds a qualification report that is not the one supplied", path)
    issued, expires = parse_time(payload["issued_utc"], "issued_utc", path), parse_time(payload["expires_utc"], "expires_utc", path)
    freeze = parse_time(binding.freeze_created_utc, "freeze creation time", path)
    if expires <= issued or expires - issued > MAX_VALIDITY:
        raise Refusal(f"authorization validity window is invalid (expires must follow issue, at most {MAX_VALIDITY})", path)
    if issued < freeze:
        raise Refusal("authorization was issued before the current freeze", path)
    if now < issued - CLOCK_SKEW:
        raise Refusal("authorization is not yet valid (issued in the future)", path)
    if now > expires:
        raise Refusal(f"authorization expired at {payload['expires_utc']}", path)
    if not allow_test_only and key.decode("utf-8", "ignore").startswith(TEST_KEY_PREFIX):
        raise Refusal("a test-only key can never authorize a confirmatory run", path)
    return VerifiedGate(run_id=payload["run_id"], artifact_sha256=hashlib.sha256(raw).hexdigest(), issued_utc=payload["issued_utc"],
                        expires_utc=payload["expires_utc"], test_only=payload["test_only"],
                        payload=tuple(sorted((k, json.dumps(v, sort_keys=True)) for k, v in payload.items())))


# ------------------------------------------------------------------------------------------ key handling


def obtain_key(environ=None, prompt=None, interactive: bool | None = None) -> bytes:
    """The key comes from the environment variable (then removed from this process's environment) or an interactive hidden
    prompt. It is never accepted on the command line, printed, logged, checkpointed or written to results."""
    environ = os.environ if environ is None else environ
    key = environ.get(KEY_ENV)
    if key is not None:
        try:
            del environ[KEY_ENV]
        except KeyError:
            pass
    elif (sys.stdin.isatty() if interactive is None else interactive):
        key = (prompt or getpass.getpass)("Stage 0.6 authorization key (input hidden): ")
    if not key or not key.strip():
        raise Refusal(f"no authorization key: export {KEY_ENV} or run in an interactive terminal")
    return key.strip().encode("utf-8")


# ------------------------------------------------------------------------------------------ issuer (used by the issuer script)


def build_payload(binding: Binding, run_id: str, issued: _dt.datetime, hours: float, *, test_only: bool) -> dict:
    expires = issued + _dt.timedelta(hours=hours)
    return {"schema": SCHEMA, "purpose": PURPOSE, "test_only": bool(test_only), "mode": MODE, "run_id": run_id,
            "issued_utc": utc_text(issued), "expires_utc": utc_text(expires), "manifest_sha256": binding.manifest_sha256,
            "snapshot_sha256": binding.snapshot_sha256, "config_hash": binding.config_hash,
            "config_file_sha256": binding.config_file_sha256, "prereg_sha256": binding.prereg_sha256,
            "amendment_sha256": binding.amendment_sha256,
            "seeds": {"evaluation": list(binding.evaluation_seeds), "bootstrap": binding.bootstrap_seed},
            "qualification_sha256": binding.qualification_sha256}


def issue(payload: dict, key: bytes) -> bytes:
    """Serialize a signed artifact. Key policy: a test-only artifact needs a TEST-ONLY- key; a real artifact must not use one
    and needs at least MIN_KEY_CHARS characters."""
    k = key.decode("utf-8")
    if payload["test_only"] != k.startswith(TEST_KEY_PREFIX):
        raise Refusal(f"key policy: test-only artifacts need a key starting with {TEST_KEY_PREFIX!r}, real ones must not use one")
    if not payload["test_only"] and len(k) < MIN_KEY_CHARS:
        raise Refusal(f"key policy: a real key needs at least {MIN_KEY_CHARS} characters")
    if not RUN_ID_RE.match(payload["run_id"]):
        raise Refusal("run_id must be 8-64 characters of A-Z a-z 0-9 . _ -")
    return (json.dumps({"payload": payload, "hmac_sha256": sign(payload, key)}, indent=1, sort_keys=True) + "\n").encode("utf-8")


# ------------------------------------------------------------------------------------------ one run per run id


def results_dir_name(gate: VerifiedGate) -> str:
    return f"{gate.run_id}__stage06_confirmatory"


def claim_run(ckpt_root: Path, gate: VerifiedGate, config_hash: str, manifest_sha256: str) -> str:
    """First invocation creates the lock atomically; later invocations (resume) must carry the same run id. A different run id is
    refused: a second confirmatory run is never started in a directory that already holds one."""
    ckpt_root.mkdir(parents=True, exist_ok=True)
    lock = ckpt_root / LOCK_NAME
    record = {"schema": LOCK_SCHEMA, "run_id": gate.run_id, "config_hash": config_hash, "manifest_sha256": manifest_sha256,
              "first_artifact_sha256": gate.artifact_sha256, "created_utc": utc_text(_dt.datetime.now(_dt.timezone.utc))}
    try:
        fd = os.open(lock, os.O_WRONLY | os.O_CREAT | os.O_EXCL)
    except FileExistsError:
        try:
            have = json.loads(lock.read_text(encoding="utf-8"))
        except (ValueError, OSError) as exc:
            raise Corrupt(f"run lock is unreadable ({type(exc).__name__})", lock)
        if not isinstance(have, dict) or have.get("schema") != LOCK_SCHEMA or not isinstance(have.get("run_id"), str):
            raise Corrupt("run lock has an unexpected structure", lock)
        if have["run_id"] != gate.run_id:
            raise Refusal(f"a confirmatory run with run_id {have['run_id']!r} already exists here; run_id {gate.run_id!r} is "
                          "refused (resume needs the same run id)", lock)
        if have.get("config_hash") != config_hash or have.get("manifest_sha256") != manifest_sha256:
            raise Refusal("run lock was created under a different config or manifest", lock)
        return "resumed"
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(record, indent=1, sort_keys=True) + "\n")
    return "started"


def check_results_dirs(runs_dir: Path, config_hash: str, gate: VerifiedGate, *, allow_own_unfinished: bool = True) -> None:
    """Refuse when a confirmatory results directory for another run id exists, or when this run id already produced results."""
    runs_dir = Path(runs_dir)
    if not runs_dir.is_dir():
        return
    mine = results_dir_name(gate)
    for d in sorted(runs_dir.iterdir()):
        h = d / "config_hash.txt"
        if d.is_dir() and h.is_file() and h.read_text(encoding="utf-8").strip() == config_hash:
            if d.name == mine:
                raise Refusal(f"run_id {gate.run_id!r} already completed: results exist", d)
            raise Refusal("a confirmatory results directory of another run already exists; a second confirmatory run is refused", d)
