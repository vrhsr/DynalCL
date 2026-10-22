"""Run provenance (Section 6): every run writes ``runs/<run_id>/`` with

config.yaml (validated, normalised), config_hash, git commit and dirty flag (or the reason they are
unavailable), package versions, platform, per-stream seeds, timestamps, results, and SHA-256
checksums of every output file (``checksums.json``).
"""

from __future__ import annotations

import csv
import datetime as _dt
import hashlib
import io
import json
import platform
import subprocess
import sys
from importlib import metadata
from pathlib import Path

PACKAGES = ("numpy", "scipy", "pyyaml", "pytest")


def utc_now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def git_state(repo: Path) -> dict:
    """Commit hash and dirty flag, or ``available: False`` with the reason (e.g. not a git repository)."""
    try:
        commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo, capture_output=True, text=True, timeout=10)
        if commit.returncode != 0:
            return {"available": False, "reason": commit.stderr.strip() or "git rev-parse failed"}
        status = subprocess.run(["git", "status", "--porcelain"], cwd=repo, capture_output=True, text=True, timeout=10)
        return {"available": True, "commit": commit.stdout.strip(), "dirty": bool(status.stdout.strip())}
    except (OSError, subprocess.SubprocessError) as exc:
        return {"available": False, "reason": f"{type(exc).__name__}: {exc}"}


def package_versions() -> dict:
    out = {}
    for name in PACKAGES:
        try:
            out[name] = metadata.version(name)
        except metadata.PackageNotFoundError:
            out[name] = None
    return out


def platform_info() -> dict:
    return {"python": sys.version, "implementation": platform.python_implementation(),
            "platform": platform.platform(), "machine": platform.machine(), "processor": platform.processor()}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def write_csv_text(rows: list[dict]) -> str:
    """Deterministic CSV: columns in first-seen order (union over rows), floats with repr (round-trip exact)."""
    if not rows:
        return ""
    fields = list(dict.fromkeys(k for r in rows for k in r))
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=fields, restval="", lineterminator="\n")
    writer.writeheader()
    for r in rows:
        writer.writerow({k: (repr(v) if isinstance(v, float) else v) for k, v in r.items()})
    return buf.getvalue()


class RunRecorder:
    """Creates runs/<run_id>/ and records provenance. Results go in ``results/``; timing-dependent
    metadata stays in provenance.json, so results are bitwise comparable across identical runs."""

    def __init__(self, config, runs_dir: str | Path = "runs", repo: str | Path = ".", run_id: str | None = None,
                 command: list[str] | None = None):
        self.config = config
        self.repo = Path(repo).resolve()
        self.started = utc_now()
        stamp = _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        self.run_id = run_id or f"{stamp}_{config.experiment.name}_{config.config_hash()[:10]}"
        self.dir = Path(runs_dir) / self.run_id
        if self.dir.exists():
            raise FileExistsError(f"run directory {self.dir} already exists")
        (self.dir / "results").mkdir(parents=True)
        self.command = command or sys.argv
        from dynaicl.config.schema import dump_config
        (self.dir / "config.yaml").write_text(dump_config(config), encoding="utf-8")
        (self.dir / "config_hash.txt").write_text(config.config_hash() + "\n", encoding="utf-8")

    def write_json(self, rel: str, obj) -> Path:
        path = self.dir / "results" / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(obj, indent=2, sort_keys=True, allow_nan=True, default=_json_default) + "\n",
                        encoding="utf-8")
        return path

    def write_csv(self, rel: str, rows: list[dict]) -> Path:
        path = self.dir / "results" / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(write_csv_text(rows), encoding="utf-8")
        return path

    def write_text(self, rel: str, text: str) -> Path:
        path = self.dir / "results" / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def finalize(self, seeds: dict, extra: dict | None = None) -> Path:
        checksums = {str(p.relative_to(self.dir)).replace("\\", "/"): sha256_file(p)
                     for p in sorted(self.dir.rglob("*")) if p.is_file() and p.name not in ("provenance.json",
                                                                                             "checksums.json")}
        (self.dir / "checksums.json").write_text(json.dumps(checksums, indent=2, sort_keys=True) + "\n",
                                                 encoding="utf-8")
        prov = {
            "run_id": self.run_id,
            "config_hash": self.config.config_hash(),
            "git": git_state(self.repo),
            "packages": package_versions(),
            "platform": platform_info(),
            "seeds": seeds,
            "timestamps": {"started_utc": self.started, "finished_utc": utc_now()},
            "command": list(self.command),
            "output_checksums_file": "checksums.json",
            **(extra or {}),
        }
        path = self.dir / "provenance.json"
        path.write_text(json.dumps(prov, indent=2, sort_keys=True, default=_json_default) + "\n", encoding="utf-8")
        return path


def _json_default(obj):
    import numpy as np
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, np.floating):
        return float(obj)
    if isinstance(obj, np.bool_):
        return bool(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    raise TypeError(f"not JSON serialisable: {type(obj).__name__}")
