"""Stage 1 freeze tooling: build or verify the Stage 1 freeze manifest and its read-only snapshot.

    python scripts/stage1_freeze.py build  --out docs/FREEZE_MANIFEST_STAGE1.json --snapshot dist/stage1_frozen_snapshot.zip
    python scripts/stage1_freeze.py verify --manifest docs/FREEZE_MANIFEST_STAGE1.json --expected-sha256 <hash>

`build` refuses if the manifest already exists (a freeze happens once; a re-freeze needs a new versioned name and the
user's approval). The manifest lists every frozen file with its SHA-256; its own SHA-256 is printed and must be stored by
the user outside the workspace. `verify` exits 3 (REFUSED) on any mismatch or missing file.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FROZEN_GLOBS = [
    "docs/PREREG_stage1.md", "docs/STAGE1_SEPARABILITY_MAP_SPEC.md", "docs/STAGE1_F1_SEPARABILITY_MAP_SPEC.md",
    "docs/MATH_F1.md", "docs/STAGE1_INDEPENDENT_AUDIT.md",
    "config/stage1.yaml", "config/stage1_pilot.yaml", "config/stage1_seed_manifest.yaml", "config/stage1_power_lookup.json",
    "requirements-stage1.txt",
    "dynaicl_families/*.py", "dynaicl_neural/*.py", "tests_stage1/*.py",
    "scripts/stage1_*.py", "scripts/stage1_*.sh",
    "results_stage1/j0/j0.json", "results_stage1/eng_smoke/eng_smoke.json",   # inputs of the frozen cap and V-REPRO rules
]
SCHEMA = "stage1-freeze-manifest/v1"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def frozen_files() -> list[Path]:
    files = set()
    for g in FROZEN_GLOBS:
        files |= {p for p in ROOT.glob(g) if p.is_file()}
    return sorted(files)


def build(out: Path, snapshot: Path) -> int:
    if out.exists() or snapshot.exists():
        print(f"REFUSED: {out} or {snapshot} already exists (a freeze happens once)")
        return 3
    entries = {str(p.relative_to(ROOT)).replace("\\", "/"): sha256(p) for p in frozen_files()}
    manifest = {"schema": SCHEMA, "files": entries}
    out.write_text(json.dumps(manifest, indent=1, sort_keys=True), encoding="utf-8")
    snapshot.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(snapshot, "w", zipfile.ZIP_DEFLATED) as z:
        for rel in entries:
            z.write(ROOT / rel, rel)
        z.write(out, str(out.relative_to(ROOT)).replace("\\", "/"))
    snapshot.chmod(0o444)
    print(f"manifest {out}: {len(entries)} files, sha256 {sha256(out)}")
    print(f"snapshot {snapshot}: sha256 {sha256(snapshot)}")
    return 0


def verify(manifest: Path, expected: str) -> int:
    if sha256(manifest) != expected:
        print(f"REFUSED: manifest sha256 {sha256(manifest)} != expected {expected}")
        return 3
    data = json.loads(manifest.read_text(encoding="utf-8"))
    bad = [rel for rel, h in data["files"].items() if not (ROOT / rel).exists() or sha256(ROOT / rel) != h]
    if bad:
        print("REFUSED: changed or missing frozen files:\n  " + "\n  ".join(bad))
        return 3
    print(f"verified {len(data['files'])} frozen files")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("--out", required=True)
    b.add_argument("--snapshot", required=True)
    v = sub.add_parser("verify")
    v.add_argument("--manifest", required=True)
    v.add_argument("--expected-sha256", required=True)
    a = ap.parse_args(argv)
    if a.cmd == "build":
        return build(ROOT / a.out, ROOT / a.snapshot)
    return verify(ROOT / a.manifest, a.expected_sha256)


if __name__ == "__main__":
    sys.exit(main())
