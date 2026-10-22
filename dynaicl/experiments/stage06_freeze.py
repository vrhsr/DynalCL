"""Stage 0.6 freeze tooling: environment manifest, freeze manifest and read-only snapshot, for a NAMED freeze version.

The manifest lists the SHA-256 of every file that can affect the verdict (code, tests, scripts, configs, the seed-role table, the
pre-registration and its amendment, supporting docs, dependency specs, the environment manifest and the Stage 0.5 artifacts used by
Tier-1 / Tier-2). Its own SHA-256 is printed for the user to store OUTSIDE the workspace: a manifest stored beside its files only
protects against accidental change. This is integrity evidence, not version control.

Versions: ``v1`` (the first freeze: its manifest, snapshot and evidence files are preserved untouched and are never regenerated) and
``v2`` (authorization gate, refusal handling, seed-role table; created alongside v1 under new file names).
"""

from __future__ import annotations

import datetime as _dt
import json
import os
import stat
import subprocess
import sys
import zipfile
from dataclasses import dataclass
from pathlib import Path

from dynaicl.config.stage06_schema import load_stage06_config
from dynaicl.experiments.stage06_probe import MANIFEST_SCHEMA, current_environment
from dynaicl.provenance import sha256_file

CONFIGS = ("config/stage06.yaml", "config/stage06_pilot.yaml", "config/stage06_test.yaml")
STAGE05_FILES = ("results/item_contrasts.npy", "results/item_contrasts_index.csv", "checksums.json", "config.yaml")
INFORMATIONAL = ("docs/DISCLOSURE_LOG_STAGE06.md", "CLAUDE.md", "docs/DECISIONS.md", "docs/RISKS.md")
V1_DOCS = ("PREREG_stage06.md", "MATH_STAGE06.md", "STAGE06_AUDIT.md", "STAGE06_VALIDATION_REPORT.md",
           "STAGE06_TESTED_FILES.json", "STAGE06_DECISION_DRY_RUN.md", "STAGE06_DECISION_DRY_RUN.json",
           "STAGE06_CALIBRATION_DIAGNOSTIC.md", "STAGE06_NOISE_LEVEL_VERIFICATION.md", "STAGE06_NOISE_LEVEL_VERIFICATION.json",
           "STAGE06_SELECTION_AUDIT.md", "STAGE06_MUTATION_MATRIX.md", "STAGE06_ENVIRONMENT_MANIFEST.json")


@dataclass(frozen=True)
class Version:
    label: str
    tested_files: str
    manifest: str
    environment_manifest: str
    snapshot: str
    snapshot_sha_file: str
    docs: tuple


VERSIONS = {
    "v1": Version("v1", "docs/STAGE06_TESTED_FILES.json", "docs/FREEZE_MANIFEST_STAGE06.json", "docs/STAGE06_ENVIRONMENT_MANIFEST.json",
                  "dist/stage06_frozen_snapshot.zip", "dist/stage06_frozen_snapshot.sha256", V1_DOCS),
    "v2": Version("v2", "docs/STAGE06_TESTED_FILES_v2.json", "docs/FREEZE_MANIFEST_STAGE06_v2.json",
                  "docs/STAGE06_ENVIRONMENT_MANIFEST_v2.json", "dist/stage06_frozen_snapshot_v2.zip",
                  "dist/stage06_frozen_snapshot_v2.sha256",
                  # v1 evidence files are carried unchanged (byte-identical) so the v2 manifest still covers them
                  tuple(d for d in V1_DOCS) + (
                      "PREREG_stage06_AMENDMENT_1.md", "STAGE06_VALIDATION_REPORT_v2.md", "STAGE06_TESTED_FILES_v2.json",
                      "STAGE06_MUTATION_MATRIX_v2.md", "STAGE06_MUTATION_MATRIX_v2.json", "STAGE06_CALIBRATION_DIAGNOSTIC_v2.md",
                      "STAGE06_ENVIRONMENT_MANIFEST_v2.json", "STAGE06_AUTHORIZATION_GATE.md", "STAGE06_SEED_ROLES.md")),
}


def code_files(root: Path) -> list[str]:
    """Every file whose content is executed or validated: the package, the tests, the Stage 0.6 scripts, configs, the seed-role table,
    dependency specs."""
    out = []
    for pattern in ("dynaicl/**/*.py", "tests/**/*.py", "scripts/stage06_*.py"):
        out += [p for p in root.glob(pattern) if "__pycache__" not in p.parts]
    out += [root / c for c in CONFIGS] + [root / "config" / "stage06_seed_manifest.yaml", root / "requirements.txt",
                                          root / "pyproject.toml"]
    return sorted({str(p.relative_to(root)).replace("\\", "/") for p in out})


def tested_file_hashes(root: Path) -> dict:
    return {rel: sha256_file(root / rel) for rel in code_files(root)}


def write_environment_manifest(root: Path, version: Version) -> Path:
    try:
        import contextlib
        import io

        import numpy as np
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            np.show_config()
        blas = buf.getvalue()
    except Exception as exc:  # recorded, not fatal: BLAS info is descriptive
        blas = f"unavailable: {exc}"
    pip = subprocess.run([sys.executable, "-m", "pip", "freeze"], capture_output=True, text=True, timeout=120)
    doc = {"environment": current_environment(), "python_full": sys.version, "blas_config": blas,
           "pip_freeze": sorted(pip.stdout.split()) if pip.returncode == 0 else None,
           "requirements_txt": (root / "requirements.txt").read_text(encoding="utf-8").splitlines(),
           "compared_keys_note": "the runner compares python, implementation, numpy, scipy, pyyaml, system, machine"}
    path = root / version.environment_manifest
    if path.exists():
        raise FileExistsError(f"{path} exists; a frozen environment manifest is never overwritten")
    path.write_text(json.dumps(doc, indent=1, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    return path


def build_manifest(root: Path, stage05_run: str, version: Version) -> dict:
    files = code_files(root)
    files += [f"docs/{d}" for d in version.docs]
    files += [f"{stage05_run}/{f}" for f in STAGE05_FILES]
    missing = [f for f in files if not (root / f).is_file()]
    if missing:
        raise FileNotFoundError(f"files to freeze are missing: {missing}")
    configs = {}
    for c in CONFIGS:
        cfg = load_stage06_config(root / c)
        configs[c] = {"config_hash": cfg.config_hash(), "mode": cfg.experiment.mode}
    m = {"schema": MANIFEST_SCHEMA, "freeze_version": version.label,
         "created_utc": _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
         "files": {f: sha256_file(root / f) for f in sorted(set(files))},
         "config_hashes": configs, "environment_manifest": version.environment_manifest,
         "informational_unverified": {f: sha256_file(root / f) for f in INFORMATIONAL if (root / f).is_file()},
         "limitations": "SHA-256 integrity evidence for the listed files only; not version control or full provenance. "
                        "The informational entries record files that may change after the freeze (e.g. the "
                        "disclosure log); the runner does not verify them."}
    if version.label != "v1":
        v1 = VERSIONS["v1"]
        m["supersedes"] = {"freeze_version": "v1", "manifest_sha256": sha256_file(root / v1.manifest),
                           "snapshot_sha256": sha256_file(root / v1.snapshot)}
        m["amendment"] = "docs/PREREG_stage06_AMENDMENT_1.md"
    return m


def write_manifest(root: Path, manifest: dict, rel: str) -> tuple[Path, str]:
    path = root / rel
    if path.exists():
        raise FileExistsError(f"{path} exists; a frozen manifest is never overwritten")
    path.write_text(json.dumps(manifest, indent=1, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    return path, sha256_file(path)


def write_snapshot(root: Path, manifest: dict, manifest_rel: str, out: Path) -> str:
    """Zip of every manifest file plus the manifest itself; the archive is then marked read-only."""
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        raise FileExistsError(f"{out} exists; a frozen snapshot is never overwritten")
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for rel in sorted([*manifest["files"], manifest_rel]):
            info = zipfile.ZipInfo(rel, date_time=(2026, 1, 1, 0, 0, 0))
            info.external_attr = (stat.S_IFREG | 0o444) << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, (root / rel).read_bytes())
    os.chmod(out, stat.S_IREAD)
    return sha256_file(out)
