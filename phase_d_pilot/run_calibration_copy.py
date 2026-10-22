"""Run the pre-specified calibration-diagnostic protocol (scripts/stage06_calibration_diagnostic.py, unchanged) on a COPY of the revised
tested files, so the v1 evidence file docs/STAGE06_CALIBRATION_DIAGNOSTIC.md is never overwritten, then store the output as the _v2 file."""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from dynaicl.experiments.stage06_freeze import code_files  # noqa: E402

with tempfile.TemporaryDirectory(prefix="s06_calib_copy_") as td:
    copy = Path(td) / "repo"
    for rel in code_files(ROOT):
        (copy / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / rel, copy / rel)
    (copy / "docs").mkdir(exist_ok=True)
    p = subprocess.run([sys.executable, "-u", "scripts/stage06_calibration_diagnostic.py"], cwd=copy, text=True, capture_output=True,
                       env={"PYTHONPATH": str(copy), **__import__("os").environ})
    print(p.stdout[-600:], p.stderr[-600:])
    if p.returncode:
        raise SystemExit(p.returncode)
    out = ROOT / "docs" / "STAGE06_CALIBRATION_DIAGNOSTIC_v2.md"
    if out.exists():
        raise SystemExit(f"{out} exists; not overwriting")
    shutil.copy2(copy / "docs" / "STAGE06_CALIBRATION_DIAGNOSTIC.md", out)
    print(f"stored {out}")
