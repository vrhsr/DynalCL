"""Stage 1 confirmatory authorization gate (same design as the frozen Stage 0.6 gate;
docs/STAGE06_AUTHORIZATION_GATE.md).

A confirmatory ``train`` / ``analyze`` needs an artifact whose payload binds the Stage 1 freeze manifest, snapshot,
config,
pre-registration, pilot decision file, exact seed set, run id and a validity window (<= 72 h), authenticated with
HMAC-SHA256 under a key only the user holds (environment variable DYNAICL_STAGE1_AUTH_KEY at launch; never stored,
logged or
written to results). Test-only keys (prefix TEST-ONLY-) can never authorize a non-test artifact, and vice versa.
One run id per output directory (RUN_LOCK.json). Standard library only.

Limits (as Stage 0.6): it does not stop someone who edits code outside the frozen tree or holds the key; it stops
accidental, automated or agent-initiated launches through the frozen runner.
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import hmac
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path

SCHEMA = "stage1-authorization/v1"
DOMAIN = b"dynaicl-stage1-authorization/v1\n"
KEY_ENV = "DYNAICL_STAGE1_AUTH_KEY"
TEST_KEY_PREFIX = "TEST-ONLY-"
MIN_KEY_CHARS = 24
MAX_VALIDITY = _dt.timedelta(hours=72)
CLOCK_SKEW = _dt.timedelta(minutes=5)
RUN_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{7,63}$")
TIME_FMT = "%Y-%m-%dT%H:%M:%SZ"
BOUND_FIELDS = ("manifest_sha256", "snapshot_sha256", "config_sha256", "prereg_sha256", "pilot_decision_sha256")


class Refused(RuntimeError):
    """The gate refuses: the run must not start (or continue)."""


@dataclass(frozen=True)
class Binding:
    manifest_sha256: str
    snapshot_sha256: str
    config_sha256: str
    prereg_sha256: str
    pilot_decision_sha256: str
    seeds: tuple[int, ...]


def sha256_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canonical(payload: dict) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")


def sign(payload: dict, key: bytes) -> str:
    return hmac.new(key, DOMAIN + canonical(payload), hashlib.sha256).hexdigest()


def _key_from(raw: str) -> tuple[bytes, bool]:
    if len(raw) < MIN_KEY_CHARS:
        raise Refused(f"authorization key shorter than {MIN_KEY_CHARS} characters")
    return raw.encode("utf-8"), raw.startswith(TEST_KEY_PREFIX)


def obtain_key(environ=None) -> tuple[bytes, bool]:
    """The key from the environment only (no interactive prompt: no test or job may wait for typed input)."""
    env = os.environ if environ is None else environ
    raw = env.get(KEY_ENV, "")
    if not raw:
        raise Refused(f"{KEY_ENV} is not set")
    return _key_from(raw)


def build_payload(binding: Binding, run_id: str, issued: _dt.datetime, hours: float, test_only: bool) -> dict:
    if not RUN_ID_RE.match(run_id):
        raise ValueError("invalid run id")
    if not (0 < hours <= MAX_VALIDITY.total_seconds() / 3600):
        raise ValueError("validity must be in (0, 72] hours")
    return {"schema": SCHEMA, "test_only": bool(test_only), "run_id": run_id,
            "issued_utc": issued.strftime(TIME_FMT),
            "expires_utc": (issued + _dt.timedelta(hours=hours)).strftime(TIME_FMT),
            **{f: getattr(binding, f) for f in BOUND_FIELDS}, "seeds": sorted(int(s) for s in binding.seeds)}


def issue(payload: dict, key: bytes) -> bytes:
    return json.dumps({"payload": payload, "hmac_sha256": sign(payload, key)}, indent=1, sort_keys=True).encode("utf-8")


def verify(raw: bytes, key: bytes, key_is_test: bool, binding: Binding, now: _dt.datetime) -> dict:
    """Return the verified payload or raise Refused."""
    try:
        doc = json.loads(raw.decode("utf-8"))
        payload, mac = doc["payload"], doc["hmac_sha256"]
    except Exception as exc:
        raise Refused(f"authorization artifact unreadable: {exc}") from exc
    if not hmac.compare_digest(sign(payload, key), str(mac)):
        raise Refused("authorization HMAC does not verify (wrong key or modified artifact)")
    if payload.get("schema") != SCHEMA:
        raise Refused("wrong authorization schema")
    if bool(payload.get("test_only")) != key_is_test:
        raise Refused("test-only keys and artifacts cannot authorize real runs (and vice versa)")
    for f in BOUND_FIELDS:
        if payload.get(f) != getattr(binding, f):
            raise Refused(f"authorization is bound to a different {f}")
    if payload.get("seeds") != sorted(int(s) for s in binding.seeds):
        raise Refused("authorization is bound to a different seed set")
    issued = _dt.datetime.strptime(payload["issued_utc"], TIME_FMT).replace(tzinfo=_dt.timezone.utc)
    expires = _dt.datetime.strptime(payload["expires_utc"], TIME_FMT).replace(tzinfo=_dt.timezone.utc)
    if expires - issued > MAX_VALIDITY:
        raise Refused("authorization validity exceeds 72 h")
    if now < issued - CLOCK_SKEW or now > expires:
        raise Refused("authorization is not valid at this time")
    if not RUN_ID_RE.match(str(payload.get("run_id", ""))):
        raise Refused("invalid run id in authorization")
    return payload


def claim_run(out_dir: Path, run_id: str) -> None:
    """One run id per output directory: create RUN_LOCK.json, or refuse if it names another run id."""
    out_dir.mkdir(parents=True, exist_ok=True)
    lock = out_dir / "RUN_LOCK.json"
    if lock.exists():
        held = json.loads(lock.read_text(encoding="utf-8")).get("run_id")
        if held != run_id:
            raise Refused(f"{out_dir} belongs to run id {held!r}")
        return
    lock.write_text(json.dumps({"run_id": run_id}), encoding="utf-8")
