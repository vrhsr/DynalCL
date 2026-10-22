"""Build the Phase D PILOT bundle, notebook and pilot-bundle manifest for the v2 freeze. NOT part of the frozen file set.

    python phase_d_pilot/build_phase_d_notebook.py
        -> dist/phase_d_pilot_bundle_v2.zip                      (pilot_common.py, pilot_child.py, pilot_harness.py, README_PHASE_D.md)
        -> colab/pilot/DynaICL_Stage06_PhaseD_PILOT_v2.ipynb
        -> phase_d_pilot/PILOT_BUNDLE_MANIFEST_v2.json

Hash order (no circular hashing, nothing hashes itself): (1) the v2 freeze produces the manifest and the snapshot; (2) this script zips the
pilot tooling and hashes the zip; (3) it builds the notebook embedding the snapshot, manifest and bundle hashes; (4) it writes the
pilot-bundle manifest listing the hashes of the tooling files, the bundle zip, the notebook, the v2 manifest and the v2 snapshot. The
pilot-bundle manifest is hashed by no other file; its own SHA-256 is printed.

The notebook has NO confirmatory cell, no confirmatory seed, no authorization reference and does not mention the confirmatory
config: they are deliberately omitted until Phase E. At run time it asserts that the extracted frozen manifest hashes to the value
embedded here.
"""

from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HERE = Path(__file__).resolve().parent
FILES = ("pilot_common.py", "pilot_child.py", "pilot_harness.py", "README_PHASE_D.md")
SNAPSHOT = "stage06_frozen_snapshot_v2.zip"
MANIFEST_REL = "docs/FREEZE_MANIFEST_STAGE06_v2.json"
BUNDLE = "phase_d_pilot_bundle_v2.zip"


def md(text):
    return {"cell_type": "markdown", "metadata": {}, "source": text.strip("\n").splitlines(keepends=True)}


def code(text):
    return {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [],
            "source": text.strip("\n").splitlines(keepends=True)}


def sha_file(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def build_bundle() -> tuple[Path, str]:
    out = ROOT / "dist" / BUNDLE
    out.parent.mkdir(exist_ok=True)
    if out.exists():
        out.unlink()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for f in FILES:
            info = zipfile.ZipInfo(f"phase_d_pilot/{f}", date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, (HERE / f).read_bytes())
    return out, sha_file(out)


def build_notebook(snap_sha: str, man_sha: str, bundle_sha: str) -> dict:
    D = "/content/drive/MyDrive/dynaicl_stage06_phaseD_v2"
    L = "/content/pilot_work_local"
    H = ("python3 /content/phase_d/phase_d_pilot/pilot_harness.py {task} --frozen-root /content/DynaICL "
         f"--snapshot /content/{SNAPSHOT} --manifest-sha $MANIFEST_SHA")
    cells = [
        md(f"""
# DynaICL Stage 0.6 - Phase D (v2 freeze): operational qualification and PILOT (Google Colab, CPU only)

**Pilot, test and confirmatory execution are separate. This notebook is the PILOT notebook only. It contains no confirmatory
cell, no confirmatory seed, no reference to the confirmatory configuration and no launch credentials of any kind. The confirmatory path is
deliberately omitted until Phase E.** Only the frozen pilot configuration and the pilot seed roles are used.

* Frozen snapshot (v2) sha256: `{snap_sha}`
* Frozen manifest (v2) sha256: `{man_sha}`: compare it with the value you stored outside the workspace. A cell below asserts that the
  extracted manifest hashes to this value.
* Pilot bundle (harness; NOT frozen) sha256: `{bundle_sha}`. Hash order: freeze first, then this bundle, then this notebook; the
  pilot-bundle manifest lists all of them and is hashed by nothing else.

**Order.** Run the cells top to bottom (about 1.5-3 h on 2 vCPU, an estimate). The only manual step is the runtime restart test (section 9).
**Send back:** `phaseD_colab_results.tar.gz` (also on Drive). Everything in it is pilot-labelled.
"""),
        md("## 0. Hardware check (no GPU may be attached; Runtime -> Change runtime type -> CPU)"),
        code("""
!nproc
!lscpu | grep -E "Model name|^CPU\\(s\\)|Thread|Core|MHz|L2|L3"
!free -h
!df -h /content /content/drive 2>/dev/null
!nvidia-smi 2>&1 | head -3
!cat /proc/uptime
"""),
        md("## 1. Mount Drive, get the frozen snapshot and the pilot bundle, verify hashes"),
        code(f"""
import hashlib, os, zipfile, shutil
from google.colab import drive
drive.mount("/content/drive")
os.makedirs("{D}", exist_ok=True)
EXPECTED = {{"snapshot": "{snap_sha}", "bundle": "{bundle_sha}"}}
MANIFEST_SHA = "{man_sha}"
os.environ["MANIFEST_SHA"] = MANIFEST_SHA
def sha(p): return hashlib.sha256(open(p, "rb").read()).hexdigest()
for name in ("{SNAPSHOT}", "{BUNDLE}"):
    on_drive = f"{D}/" + name
    if os.path.exists(on_drive):
        shutil.copy(on_drive, "/content/" + name)            # a restarted runtime finds them on Drive
    else:
        from google.colab import files
        print("upload", name); files.upload()
        shutil.copy("/content/" + name, on_drive)
assert sha("/content/{SNAPSHOT}") == EXPECTED["snapshot"], "snapshot hash mismatch"
assert sha("/content/{BUNDLE}") == EXPECTED["bundle"], "bundle hash mismatch"
shutil.rmtree("/content/DynaICL", ignore_errors=True); shutil.rmtree("/content/phase_d", ignore_errors=True)
zipfile.ZipFile("/content/{SNAPSHOT}").extractall("/content/DynaICL")
zipfile.ZipFile("/content/{BUNDLE}").extractall("/content/phase_d")
os.chdir("/content/DynaICL")
assert sha("/content/DynaICL/{MANIFEST_REL}") == MANIFEST_SHA, "the extracted frozen manifest does not hash to the expected value"
print("hashes OK; the extracted manifest equals MANIFEST_SHA")
"""),
        md("## 2. Install the pinned stack (pip warnings about other Colab packages are harmless)"),
        code("""
!pip install -q -r /content/DynaICL/requirements.txt
!python3 -c "import numpy, scipy, yaml; print('numpy', numpy.__version__, '| scipy', scipy.__version__, '| pyyaml', yaml.__version__)"
"""),
        md("## 3. Integrity bookend (start), environment report, storage probes"),
        code(f"""
%cd /content/DynaICL
!{H.format(task="integrity")} --work {D}/work --label colab_bookend_start
!{H.format(task="env")} --work {D}/work --durable {D} --tag colab
!{H.format(task="storage-probe")} --work {D}/work --dir /content --tag colab_local_disk
!{H.format(task="storage-probe")} --work {D}/work --dir {D} --tag colab_drive
"""),
        md("""
## 4. Environment qualification of the PILOT configuration with the frozen runner

If this environment differs from the frozen environment manifest, the runner refuses until a passing qualification report exists for THIS
environment, THIS manifest and THIS configuration. The report is written to Drive, outside the frozen set. `qualify` runs V4, V6, V11
and V13 (about 5-10 min each on 2 vCPU).
"""),
        code(f"""
%cd /content/DynaICL
!OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python3 -m dynaicl.experiments.stage06_probe verify --config config/stage06_pilot.yaml --manifest {MANIFEST_REL} --expected-manifest-sha256 $MANIFEST_SHA ; echo "exit code (3 = refused, expected before qualification when the environment differs): $?"
!OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python3 -m dynaicl.experiments.stage06_probe qualify --config config/stage06_pilot.yaml --manifest {MANIFEST_REL} --expected-manifest-sha256 $MANIFEST_SHA --out {D}/qualification_pilot_colab.json
!python3 -m dynaicl.experiments.stage06_probe verify --config config/stage06_pilot.yaml --manifest {MANIFEST_REL} --expected-manifest-sha256 $MANIFEST_SHA --qualification {D}/qualification_pilot_colab.json ; echo "exit code (0 = accepted): $?"
!sha256sum {D}/qualification_pilot_colab.json
"""),
        code(f"""
%cd /content/DynaICL
!{H.format(task="qualification-gate")} --work {D}/work --tag colab
"""),
        md("""
## 5. Reference pilot runs of the frozen runner (frozen pilot config; N = 200; pilot seeds)

`ref_drive` keeps checkpoints on Drive (the durable storage you would use); `ref_local` keeps them on the local disk. Both must be
bitwise identical.
"""),
        code(f"""
%cd /content/DynaICL
Q = "{D}/qualification_pilot_colab.json"
!{H.format(task="ref-run")} --work {D}/work --tag ref_drive --workers $(nproc) --qualification $Q
!{H.format(task="ref-run")} --work {L} --tag ref_local --workers $(nproc) --qualification $Q
!diff -rq {D}/work/ref_drive/ckpt {L}/ref_local/ckpt && echo "ref_drive == ref_local (file-level identical)"
"""),
        md("## 6. Interruption and resume (clean interrupt, SIGKILL, self-kill at write stages) on Drive checkpoints"),
        code(f"""
%cd /content/DynaICL
REF = "{D}/work/ref_drive/ckpt"
!{H.format(task="interrupt-tests")} --work {D}/work --tag colab --ref-parent $REF --qualification $Q
"""),
        md("## 7. Corrupted / truncated checkpoint handling (on copies)"),
        code(f"""
%cd /content/DynaICL
!{H.format(task="corruption-tests")} --work {D}/work --tag colab --ref-parent $REF --qualification $Q
"""),
        md("""
## 8. Determinism across thread counts, profile, scaling and confirmatory-size anchors

Run on the LOCAL disk (`/content`) so timings are not dominated by Drive. Do not run anything else at the same time. `anchor` runs
real units at N = 4000 on pilot seeds (about 10-25 min).
"""),
        code(f"""
%cd /content/DynaICL
!{H.format(task="determinism")} --work {L} --tag colab --ref-parent $REF
!{H.format(task="profile-units")} --work {L} --tag colab
!{H.format(task="scaling")} --work {L} --tag colab
!{H.format(task="size-sweep")} --work {L} --tag colab --workers $(nproc)
!{H.format(task="anchor")} --work {L} --tag colab --units primary,0,0,2 primary,0,3,0 naive,0,0,2 integrity tier1
!{H.format(task="analysis-cost")} --work {L} --tag colab
"""),
        md("""
## 9. Runtime-restart test (durable storage only)

**Part A** starts the frozen pilot run on Drive and waits until 20 units are saved, then prints READY. At that moment do
`Runtime -> Disconnect and delete runtime`, reconnect (a new VM, possibly another CPU), rerun sections 1-3 (the zips are on Drive) and run **Part B**.
The harness logs the CPU model in both phases.
"""),
        code(f"""
%cd /content/DynaICL
Q = "{D}/qualification_pilot_colab.json"
!{H.format(task="restart-part-a")} --work {D}/work --durable {D} --workers $(nproc) --qualification $Q
"""),
        code(f"""
# PART B: run AFTER the runtime was deleted and sections 1-3 were rerun
%cd /content/DynaICL
Q = "{D}/qualification_pilot_colab.json"
REF = "{D}/work/ref_drive/ckpt"
!{H.format(task="restart-part-b")} --work {D}/work --durable {D} --workers $(nproc) --ref-parent $REF --tag colab --qualification $Q
"""),
        md("## 10. Completeness, structural analysis, seed search, final integrity, archive"),
        code(f"""
%cd /content/DynaICL
REF = "{D}/work/ref_drive/ckpt"
!{H.format(task="completeness")} --work {D}/work --tag colab --ref-parent $REF
!{H.format(task="structural-analysis")} --work {D}/work --tag colab --ref-parent $REF
!{H.format(task="seed-search")} --work {D}/work --tag colab --dirs {D} {L}
!{H.format(task="integrity")} --work {D}/work --label colab_bookend_end
"""),
        code(f"""
import glob, os, tarfile
out = "/content/phaseD_colab_results.tar.gz"
with tarfile.open(out, "w:gz") as tf:
    for d in ("{D}/work/reports", "{L}/reports"):
        if os.path.isdir(d): tf.add(d, arcname=os.path.basename(os.path.dirname(d)) + "_" + os.path.basename(d))
    for f in glob.glob("{D}/qualification_*.json") + glob.glob("{D}/work/restart_colab/b.log") + glob.glob("{D}/work/restart_colab/a.log"):
        tf.add(f, arcname="extra/" + os.path.basename(f))
os.system(f"cp {{out}} {D}/")
from google.colab import files
files.download(out)
print("The pilot effect-estimate file is not in the archive and must not be opened.")
"""),
    ]
    return {"cells": cells, "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
                                         "language_info": {"name": "python"}, "colab": {"provenance": []}},
            "nbformat": 4, "nbformat_minor": 5}


def main() -> None:
    sha_lines = (ROOT / "dist" / "stage06_frozen_snapshot_v2.sha256").read_text(encoding="utf-8").splitlines()
    snap_sha, man_sha = sha_lines[0].split()[0], sha_lines[1].split()[0]
    bundle, bsha = build_bundle()
    nb = ROOT / "colab" / "pilot" / "DynaICL_Stage06_PhaseD_PILOT_v2.ipynb"
    nb.parent.mkdir(parents=True, exist_ok=True)
    nb.write_text(json.dumps(build_notebook(snap_sha, man_sha, bsha), indent=1) + "\n", encoding="utf-8", newline="\n")
    manifest = {"schema": "stage06-pilot-bundle-manifest/v1", "freeze_version": "v2", "freeze_manifest_sha256": man_sha,
                "freeze_snapshot_sha256": snap_sha, "pilot_bundle_zip": {"path": f"dist/{BUNDLE}", "sha256": bsha},
                "notebook": {"path": str(nb.relative_to(ROOT)).replace("\\", "/"), "sha256": sha_file(nb)},
                "tooling_files": {f"phase_d_pilot/{f}": sha_file(HERE / f) for f in FILES},
                "hash_order": "freeze (manifest, snapshot) -> bundle zip -> notebook (embeds the three hashes) -> this manifest (hashed by nothing)"}
    mp = HERE / "PILOT_BUNDLE_MANIFEST_v2.json"
    mp.write_text(json.dumps(manifest, indent=1, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(f"bundle:   {bundle} sha256 {bsha}\nnotebook: {nb} sha256 {sha_file(nb)}\npilot-bundle manifest: {mp} sha256 {sha_file(mp)}")


if __name__ == "__main__":
    main()
