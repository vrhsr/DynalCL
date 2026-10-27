"""Issue a Stage 1 confirmatory authorization artifact (the user runs this on the box, with their own key).

    DYNAICL_STAGE1_AUTH_KEY=<key> python scripts/stage1_issue_authorization.py --config config/stage1.yaml \
        --manifest docs/FREEZE_MANIFEST_STAGE1_v3.json --expected-manifest-sha256 H \
        --snapshot dist/stage1_frozen_snapshot_v3.zip --decision results_stage1/pilot/pilot_decision.json \
        --run-id R --hours 72 --out /path/outside/the/repository/A.json

The artifact binds exactly what the gate in scripts/stage1_run.py checks (the same `binding_for`): freeze manifest,
snapshot, config hash, pre-registration, pilot decision file, the config's seed set, run id and a validity window of at
most 72 h, authenticated with HMAC-SHA256 under the key. The key is read from the environment only (no prompt: no job
may wait for typed input), is never printed, logged or written, and the artifact itself holds no secret. Refuses: a
frozen state that does not verify, a config outside the manifest, an output path inside the repository or one that
already exists. A TEST-ONLY key makes a test artifact, which the gate never accepts (used only by tests).
Exit codes: 0 issued, 3 REFUSED.
"""

from __future__ import annotations

import argparse
import datetime as dt
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dynaicl_neural.authorization import Refused, build_payload, issue, obtain_key, sha256_file  # noqa: E402
from dynaicl_neural.config import load_config  # noqa: E402


def _runner():
    spec = importlib.util.spec_from_file_location("stage1_run", ROOT / "scripts" / "stage1_run.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main(argv=None, environ=None, now: dt.datetime | None = None) -> int:
    ap = argparse.ArgumentParser()
    for name in ("config", "manifest", "expected-manifest-sha256", "snapshot", "decision", "run-id", "out"):
        ap.add_argument(f"--{name}", required=True)
    ap.add_argument("--hours", type=float, default=72.0)
    args = ap.parse_args(argv)
    try:
        key, is_test = obtain_key(environ)
        out = Path(args.out).resolve()
        if out == ROOT or ROOT in out.parents:
            raise Refused("the artifact must be written outside the repository")
        if out.exists():
            raise Refused(f"{out} already exists")
        rc = subprocess.run([sys.executable, str(ROOT / "scripts" / "stage1_freeze.py"), "verify", "--manifest",
                             args.manifest, "--expected-sha256", args.expected_manifest_sha256], cwd=ROOT).returncode
        if rc != 0:
            raise Refused("frozen state does not verify")
        frozen = json.loads((ROOT / args.manifest).read_text(encoding="utf-8"))["files"]
        if Path(args.config).as_posix() not in frozen:
            raise Refused("the config is not in the freeze manifest")
        cfg, cfg_sha = load_config(ROOT / args.config)
        if cfg.phase != "confirmatory":
            raise Refused("only a confirmatory config needs an authorization")
        binding = _runner().binding_for(cfg, cfg_sha, args.manifest, args.snapshot, args.decision)
        issued = (now or dt.datetime.now(dt.timezone.utc)).replace(microsecond=0)
        try:
            payload = build_payload(binding, args.run_id, issued, args.hours, is_test)
        except ValueError as exc:
            raise Refused(str(exc)) from exc
    except Refused as exc:
        print(f"REFUSED: {exc}")
        return 3
    out.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(out, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as fh:
        fh.write(issue(payload, key))
    print(json.dumps(payload, indent=1, sort_keys=True))
    print(f"{'TEST-ONLY ' if is_test else ''}authorization written to {out} (sha256 {sha256_file(out)}); "
          f"valid {payload['issued_utc']} -> {payload['expires_utc']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
