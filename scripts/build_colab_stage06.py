"""Build the Stage 0.6 Colab notebook from the FROZEN snapshot (run after scripts/stage06_freeze.py freeze).

    python scripts/build_colab_stage06.py   -> colab/DynaICL_Stage06_Colab.ipynb

The notebook is deliberately outside the freeze manifest (it embeds the manifest and snapshot hashes, which exist only
after the freeze). The code it runs comes only from the frozen snapshot, whose hash it checks.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SNAP = "stage06_frozen_snapshot.zip"


def md(text: str) -> dict:
    return {"cell_type": "markdown", "metadata": {}, "source": text.strip("\n").splitlines(keepends=True)}


def code(text: str) -> dict:
    return {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [],
            "source": text.strip("\n").splitlines(keepends=True)}


def build(snapshot_sha: str, manifest_sha: str) -> dict:
    drive = "/content/drive/MyDrive/dynaicl_stage06"
    env = "OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1"
    common = (f"--manifest docs/FREEZE_MANIFEST_STAGE06.json --expected-manifest-sha256 $MANIFEST_SHA "
              f"--qualification {drive}/qualification.json")
    cells = [
        md(f"""
# DynaICL Stage 0.6: noisy-observation probe (Google Colab, CPU only)

Runs the **frozen** Stage 0.6 code (`docs/PREREG_stage06.md`) from the frozen snapshot `{SNAP}`.

* Snapshot sha256: `{snapshot_sha}`
* Manifest sha256: `{manifest_sha}`. Compare it with the value **you** stored outside the workspace.

**Sections**
* Sections 1-3: setup, environment qualification and a manifest check. Safe to run at any time.
* This notebook contains NO cell that launches a run. The Phase D pilot has its own notebook
  (`colab/pilot/DynaICL_Stage06_PhaseD_PILOT.ipynb`); the confirmatory run has none (removed before Phase D).

"""),
        code("!python3 --version\n!nproc"),
        md("## 1. Mount Drive and unpack the frozen snapshot"),
        code(f"""
import hashlib, os, zipfile
from google.colab import drive
drive.mount("/content/drive")
os.makedirs("{drive}", exist_ok=True)
SNAPSHOT_ON_DRIVE = ""          # optional: e.g. "/content/drive/MyDrive/{SNAP}"
EXPECTED_SNAPSHOT = "{snapshot_sha}"
MANIFEST_SHA = "{manifest_sha}"      # must equal the value you stored outside the workspace
if SNAPSHOT_ON_DRIVE:
    src = SNAPSHOT_ON_DRIVE
else:
    from google.colab import files
    src = next(iter(files.upload()))       # pick {SNAP}
sha = hashlib.sha256(open(src, "rb").read()).hexdigest()
assert sha == EXPECTED_SNAPSHOT, f"snapshot sha256 mismatch: {{sha}}"
os.makedirs("/content/DynaICL", exist_ok=True)
zipfile.ZipFile(src).extractall("/content/DynaICL")
os.chdir("/content/DynaICL")
os.environ["MANIFEST_SHA"] = MANIFEST_SHA
print("snapshot OK; manifest file sha256:", hashlib.sha256(open("docs/FREEZE_MANIFEST_STAGE06.json", "rb").read()).hexdigest())
"""),
        md("## 2. Install the pinned stack (pip warnings about other Colab packages are harmless)"),
        code("""
!pip install -q -r /content/DynaICL/requirements.txt
!python3 -c "import numpy, scipy, yaml; print('numpy', numpy.__version__, '| scipy', scipy.__version__, '| pyyaml', yaml.__version__)"
"""),
        md("""
## 3. Environment qualification (a few minutes)

If this environment differs from the frozen environment manifest (Python version, packages or platform), the runner
refuses unless this qualification passes here: V4 (full Tier-1), V6 (quadrature convergence), V11 (parity null) and
V13 (batch = per-context). The report is written to Drive, outside the frozen file set.
"""),
        code(f"""
%cd /content/DynaICL
!{env} python3 -m dynaicl.experiments.stage06_probe qualify --config config/stage06.yaml --manifest docs/FREEZE_MANIFEST_STAGE06.json --expected-manifest-sha256 $MANIFEST_SHA --out {drive}/qualification.json
!{env} python3 -m dynaicl.experiments.stage06_probe qualify --config config/stage06_pilot.yaml --manifest docs/FREEZE_MANIFEST_STAGE06.json --expected-manifest-sha256 $MANIFEST_SHA --out {drive}/qualification_pilot.json
!python3 -m dynaicl.experiments.stage06_probe verify --config config/stage06.yaml {common}
"""),
        md("## 4. Archive a finished run and download it"),
        code(f"""
import glob, os, tarfile
runs = sorted(glob.glob("{drive}/runs/*") + glob.glob("{drive}/pilot_runs/*"), key=os.path.getmtime)
run = runs[-1]
print(run)
archive = "/content/" + os.path.basename(run) + ".tar.gz"
with tarfile.open(archive, "w:gz") as tf:
    tf.add(run, arcname=os.path.basename(run))
os.system(f"cp {{archive}} {drive}/")
from google.colab import files
files.download(archive)
"""),
    ]
    return {"cells": cells, "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
                                         "language_info": {"name": "python"}, "colab": {"provenance": []}},
            "nbformat": 4, "nbformat_minor": 5}


def main() -> None:
    lines = (ROOT / "dist" / "stage06_frozen_snapshot.sha256").read_text(encoding="utf-8").splitlines()
    snap_sha, manifest_sha = lines[0].split()[0], lines[1].split()[0]
    out = ROOT / "colab" / "DynaICL_Stage06_Colab.ipynb"
    out.write_text(json.dumps(build(snap_sha, manifest_sha), indent=1) + "\n", encoding="utf-8", newline="\n")
    print(f"notebook: {out} (snapshot {snap_sha[:16]}..., manifest {manifest_sha[:16]}...)")


if __name__ == "__main__":
    main()
