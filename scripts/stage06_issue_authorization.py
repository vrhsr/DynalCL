"""Issue a Stage 0.6 confirmatory authorization artifact (v2 freeze). THE USER runs this in Phase E with their own secret key.

    export DYNAICL_STAGE06_AUTH_KEY='<your secret, at least 24 characters>'      # or type it at the hidden prompt
    python scripts/stage06_issue_authorization.py \\
        --manifest docs/FREEZE_MANIFEST_STAGE06_v2.json --snapshot dist/stage06_frozen_snapshot_v2.zip \\
        --config config/stage06.yaml --run-id <8-64 chars: A-Z a-z 0-9 . _ -> --hours 24 --out <path outside the repo>

The artifact binds the frozen state exactly as the runner recomputes it: manifest SHA-256, snapshot archive SHA-256, confirmatory
config hash and file SHA-256, pre-registration and amendment SHA-256, the exact seed set (both replicates and the bootstrap
seed), the run id, the issue time and an expiry (at most 72 h), and optionally a qualification report's SHA-256 (``--qualification``),
authenticated with HMAC-SHA256 under your key. The key is read from the environment variable (then removed) or a hidden prompt, never
from the command line, and is never written anywhere. The runner needs the same key at launch and for every resume.

``--test-only`` issues a TEST-ONLY artifact; it needs a key starting with ``TEST-ONLY-`` and can never authorize a confirmatory run.
This script is covered by the freeze manifest and is tested only with test keys (V25). Nothing in this repository issues a real
artifact.
"""

from __future__ import annotations

import argparse
import datetime as dt
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dynaicl.experiments import stage06_authorization as AU  # noqa: E402
from dynaicl.experiments import stage06_probe as P  # noqa: E402
from dynaicl.experiments.stage06_errors import Refusal  # noqa: E402
from dynaicl.provenance import sha256_file  # noqa: E402


def build_binding(manifest: Path, snapshot: Path, config: Path, qualification: Path | None, root: Path = ROOT) -> AU.Binding:
    m = P.read_json_object(manifest, "freeze manifest")
    if not isinstance(m.get("created_utc"), str):
        raise Refusal("freeze manifest has no created_utc", manifest)
    manifest_sha = sha256_file(manifest)
    cfg, cfg_sha = P.load_config_once(config)
    if cfg.experiment.mode != "confirmatory":
        raise Refusal("only the confirmatory config can be authorized", config)
    rel = Path(manifest).resolve().relative_to(Path(root).resolve()).as_posix()
    snap = P.snapshot_sha256(snapshot, rel, manifest_sha)
    return AU.Binding(manifest_sha256=manifest_sha, snapshot_sha256=snap, config_hash=cfg.config_hash(), config_file_sha256=cfg_sha,
                      prereg_sha256=sha256_file(root / AU.PREREG_REL), amendment_sha256=sha256_file(root / AU.AMENDMENT_REL),
                      evaluation_seeds=tuple(cfg.seeds.evaluation), bootstrap_seed=cfg.seeds.bootstrap,
                      freeze_created_utc=m["created_utc"],
                      qualification_sha256=sha256_file(qualification) if qualification else None)


def main(argv=None, *, root: Path = ROOT, environ=None, now: dt.datetime | None = None, interactive: bool | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--snapshot", required=True)
    ap.add_argument("--config", required=True)
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--hours", type=float, default=24.0)
    ap.add_argument("--out", required=True)
    ap.add_argument("--qualification", default=None)
    ap.add_argument("--test-only", action="store_true")
    a = ap.parse_args(argv)
    try:
        out = Path(a.out)
        if out.exists():
            raise Refusal("refusing to overwrite an existing file", out)
        if not 0 < a.hours <= AU.MAX_VALIDITY.total_seconds() / 3600:
            raise Refusal(f"--hours must be in (0, {AU.MAX_VALIDITY.total_seconds() / 3600:g}]")
        binding = build_binding(Path(a.manifest), Path(a.snapshot), Path(a.config), Path(a.qualification) if a.qualification else None,
                                root)
        key = AU.obtain_key(environ, interactive=interactive)
        issued = (now or dt.datetime.now(dt.timezone.utc)).replace(microsecond=0)
        payload = AU.build_payload(binding, a.run_id, issued, a.hours, test_only=a.test_only)
        data = AU.issue(payload, key)
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "xb") as fh:
            fh.write(data)
    except Refusal as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return exc.exit_code
    import hashlib
    print(f"{'TEST-ONLY ' if a.test_only else ''}authorization written to {out}\n  run_id {a.run_id}\n  valid {payload['issued_utc']} to "
          f"{payload['expires_utc']}\n  artifact sha256 {hashlib.sha256(data).hexdigest()}\n  (the key was not stored anywhere)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
