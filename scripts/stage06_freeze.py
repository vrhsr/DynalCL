"""Stage 0.6 freeze steps (order: finalize code -> full validation -> validation report -> manifest -> snapshot -> manifest hash).

    python scripts/stage06_freeze.py --version v2 record-tested   # before the final validation: hashes of every code/test/config file
    python scripts/stage06_freeze.py --version v2 verify-tested   # after it: the same files are unchanged (marks the record verified; ONCE)
    python scripts/stage06_freeze.py --version v2 freeze          # environment manifest, freeze manifest, read-only snapshot

``freeze`` refuses unless the tested-file record is verified and every tested file still has its tested hash; the manifest therefore
contains exactly the hashes that were validated. It prints the manifest SHA-256 (store it OUTSIDE the workspace) and the snapshot SHA-256.
Version v1 is frozen and preserved: every command refuses it, and no existing manifest, snapshot or record is ever overwritten.
``verify-tested`` and ``record-tested`` rewrite the tested-file record: never run them after ``freeze``; the tool refuses to.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dynaicl.config.stage06_schema import load_stage06_config  # noqa: E402
from dynaicl.experiments import stage06_freeze as F  # noqa: E402


def now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--version", required=True)
    ap.add_argument("command", choices=("record-tested", "verify-tested", "freeze"))
    a = ap.parse_args(argv)
    if a.version == "v1" or a.version not in F.VERSIONS:
        print("refused: v1 is frozen and preserved; only v2 can be produced")
        return 3
    v = F.VERSIONS[a.version]
    tested, manifest_path = ROOT / v.tested_files, ROOT / v.manifest
    if manifest_path.exists():
        print(f"refused: {v.manifest} already exists; the freeze is done and its files must never be rewritten")
        return 3
    if a.command == "record-tested":
        rec = {"recorded_utc": now(), "files": F.tested_file_hashes(ROOT), "verified_after_validation": False}
        tested.write_text(json.dumps(rec, indent=1, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
        print(f"recorded {len(rec['files'])} tested files -> {tested}")
        return 0
    if a.command == "verify-tested":
        rec = json.loads(tested.read_text(encoding="utf-8"))
        cur = F.tested_file_hashes(ROOT)
        diff = sorted(set(cur) ^ set(rec["files"])) + sorted(k for k in cur if k in rec["files"] and cur[k] != rec["files"][k])
        if diff:
            print(f"CHANGED since the record: {diff}")
            return 1
        rec.update({"verified_after_validation": True, "verified_utc": now()})
        tested.write_text(json.dumps(rec, indent=1, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
        print(f"verified: {len(cur)} tested files unchanged since {rec['recorded_utc']}")
        return 0
    rec = json.loads(tested.read_text(encoding="utf-8"))
    if not rec.get("verified_after_validation"):
        print("refused: the tested-file record was not verified after the final validation")
        return 1
    if F.tested_file_hashes(ROOT) != rec["files"]:
        print("refused: code/test/config files differ from the validated hashes")
        return 1
    F.write_environment_manifest(ROOT, v)
    stage05 = load_stage06_config(ROOT / "config" / "stage06.yaml").tier2.stage05_run
    manifest = F.build_manifest(ROOT, stage05, v)
    mismatch = [k for k, h in rec["files"].items() if manifest["files"].get(k) != h]
    if mismatch:
        print(f"refused: manifest hashes differ from the tested hashes: {mismatch}")
        return 1
    path, sha = F.write_manifest(ROOT, manifest, v.manifest)
    snap_sha = F.write_snapshot(ROOT, manifest, v.manifest, ROOT / v.snapshot)
    (ROOT / v.snapshot_sha_file).write_text(f"{snap_sha}  {Path(v.snapshot).name}\n{sha}  {v.manifest}\n", encoding="utf-8", newline="\n")
    print(f"files frozen: {len(manifest['files'])}")
    print(f"MANIFEST SHA-256: {sha}  ({v.manifest})")
    print(f"SNAPSHOT SHA-256: {snap_sha}  ({v.snapshot})")
    for c, h in manifest["config_hashes"].items():
        print(f"config {c}: {h['mode']} {h['config_hash']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
