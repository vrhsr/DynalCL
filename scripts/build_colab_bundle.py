"""Build the Google Colab hand-off: a code bundle (zip) plus a notebook that runs the remote validation pipeline.

    python scripts/build_colab_bundle.py

Writes:
    dist/dynaicl_stage0_bundle.zip      the project (code, tests, configs, docs, scripts), plus MANIFEST.sha256
    colab/DynaICL_Stage0_Colab.ipynb    Stage 0 validation pipeline (mutation matrix)
    colab/DynaICL_Stage05_Colab.ipynb   Stage 0.5 confirmatory run (resumable via Drive checkpoints)

Rebuild both whenever the code changes, so the notebook never runs stale code.
"""

from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INCLUDE_DIRS = ("dynaicl", "tests", "config", "scripts", "docs")
INCLUDE_FILES = ("pyproject.toml", "requirements.txt", "README.md", "CLAUDE.md", "PLAN.md", ".flake8", ".gitignore")
EXCLUDE_PARTS = {"__pycache__", ".pytest_cache", "runs", "dist", "colab"}
BUNDLE_NAME = "dynaicl_stage0_bundle.zip"


def bundle_files() -> list[Path]:
    files = [ROOT / f for f in INCLUDE_FILES]
    for d in INCLUDE_DIRS:
        files += [p for p in sorted((ROOT / d).rglob("*")) if p.is_file() and not (set(p.parts) & EXCLUDE_PARTS)
                  and p.suffix != ".pyc"]
    return files


def build_zip(out: Path) -> dict:
    manifest = {}
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for p in bundle_files():
            rel = p.relative_to(ROOT).as_posix()
            data = p.read_bytes()
            manifest[rel] = hashlib.sha256(data).hexdigest()
            info = zipfile.ZipInfo(rel, date_time=(2026, 1, 1, 0, 0, 0))   # fixed timestamps: deterministic bundle
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (0o755 if rel.endswith(".sh") else 0o644) << 16
            zf.writestr(info, data)
        text = "".join(f"{h}  {rel}\n" for rel, h in sorted(manifest.items()))
        info = zipfile.ZipInfo("MANIFEST.sha256", date_time=(2026, 1, 1, 0, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED
        zf.writestr(info, text)
    return manifest


def md(text: str) -> dict:
    return {"cell_type": "markdown", "metadata": {}, "source": text.strip("\n").splitlines(keepends=True)}


def code(text: str) -> dict:
    return {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [],
            "source": text.strip("\n").splitlines(keepends=True)}


def build_notebook(bundle_sha: str, n_files: int) -> dict:
    cells = [
        md(f"""
# DynaICL Stage 0: remote validation pipeline (Google Colab)

Runs the long, CPU-only validation that is too big for the local machine:

1. the full pytest suite (baseline),
2. the **full mutation-detection matrix**: every validation check, and the whole pytest suite, under every injected bug,
3. optionally, the main separability experiment again (cross-machine check).

**Before you start**
* `Runtime -> Change runtime type -> CPU`. **No GPU is needed**; this is pure numpy/scipy.
* Expected time on the free tier (2 vCPU): about **1-1.5 h**. This is an estimate from local timings, not measured on Colab.
  High-CPU runtimes are faster (the pytest phase parallelises over cores).
* Keep this tab open while it runs. When it finishes, the results archive is saved to your Google Drive and also downloaded.

**You need:** `{BUNDLE_NAME}` (SHA-256 `{bundle_sha[:16]}...`, {n_files} files). Then `Runtime -> Run all`.
"""),
        md("## 1. Runtime check"),
        code("""
!python3 --version
!nproc
!free -h | head -2
"""),
        md("""
## 2. Get the code bundle
Leave `BUNDLE_ON_DRIVE = ""` to upload the zip from your computer when prompted. Or put the zip on Google Drive
and set the path, e.g. `"/content/drive/MyDrive/dynaicl_stage0_bundle.zip"`.
"""),
        code(f"""
import hashlib, os, zipfile
BUNDLE_ON_DRIVE = ""          # optional Drive path to {BUNDLE_NAME}
EXPECTED_SHA256 = "{bundle_sha}"

if BUNDLE_ON_DRIVE:
    from google.colab import drive
    drive.mount("/content/drive")
    src = BUNDLE_ON_DRIVE
else:
    from google.colab import files
    uploaded = files.upload()          # pick {BUNDLE_NAME}
    src = next(iter(uploaded))

sha = hashlib.sha256(open(src, "rb").read()).hexdigest()
print("bundle sha256:", sha, "(matches the bundle this notebook was built with)" if sha == EXPECTED_SHA256
      else "WARNING: different bundle than this notebook was built with; continuing")
os.makedirs("/content/DynaICL", exist_ok=True)
zipfile.ZipFile(src).extractall("/content/DynaICL")
os.chdir("/content/DynaICL")

# integrity check of every extracted file against the bundle manifest
bad = []
for line in open("MANIFEST.sha256"):
    h, rel = line.rstrip("\\n").split("  ", 1)
    if hashlib.sha256(open(rel, "rb").read()).hexdigest() != h:
        bad.append(rel)
print("manifest check:", "OK" if not bad else f"MISMATCH in {{bad}}")
"""),
        md("""
## 3. Install the pinned stack
These are the exact versions the suite was validated with locally (numpy 2.2.2, scipy 1.15.1, pyyaml 6.0.2,
pytest 9.0.2). Pip may warn about conflicts with other preinstalled Colab packages. That is harmless here,
because everything runs in fresh subprocesses that use only these packages.
"""),
        code("""
!pip install -q -r /content/DynaICL/requirements.txt
!python3 -c "import numpy, scipy, yaml, pytest; print('numpy', numpy.__version__, '| scipy', scipy.__version__, '| pyyaml', yaml.__version__, '| pytest', pytest.__version__)"
"""),
        md("## 4. Fast smoke test (about 1-2 min): fail early if the environment is broken"),
        code("""
%cd /content/DynaICL
!python3 -m pytest -q -p no:cacheprovider tests/test_c_identities.py tests/test_h_numerics.py tests/test_j_leakage.py tests/test_metrics.py
"""),
        md("""
## 5. The pipeline (the long step)
`RUN_EXPERIMENT=1` also reruns the main separability experiment (about 30+ min extra on 2 vCPU). It is optional.
"""),
        code("""
%cd /content/DynaICL
!JOBS=$(nproc) RUN_EXPERIMENT=0 bash scripts/remote_validation_pipeline.sh 2>&1 | tee /content/pipeline_log.txt
"""),
        md("## 6. Results summary"),
        code("""
%cd /content/DynaICL
!cat remote_results_*/STATUS.txt
!echo; cat remote_results_*/mutation_report_*/matrix.md
!echo; tail -n 3 remote_results_*/pytest_baseline.txt
"""),
        md("""
## 7. Save the results archive (Drive + download)
Send back the `remote_results_<UTC>.tar.gz`. If the download is blocked, it is also in `MyDrive/dynaicl_results/`.
"""),
        code("""
import glob, os, shutil
%cd /content/DynaICL
archive = sorted(glob.glob("remote_results_*.tar.gz"))[-1]
print("archive:", archive, os.path.getsize(archive), "bytes")
try:
    from google.colab import drive
    drive.mount("/content/drive")
    os.makedirs("/content/drive/MyDrive/dynaicl_results", exist_ok=True)
    shutil.copy(archive, "/content/drive/MyDrive/dynaicl_results/")
    shutil.copy("/content/pipeline_log.txt", "/content/drive/MyDrive/dynaicl_results/" + archive.replace(".tar.gz", "_log.txt"))
    print("copied to MyDrive/dynaicl_results/")
except Exception as exc:
    print("Drive copy skipped:", exc)
from google.colab import files
files.download(archive)
"""),
    ]
    return {"cells": cells, "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
                                         "language_info": {"name": "python"}, "colab": {"provenance": []}},
            "nbformat": 4, "nbformat_minor": 5}


def build_stage05_notebook(bundle_sha: str, n_files: int, prereg_sha: str, config_hash: str) -> dict:
    drive = "/content/drive/MyDrive/dynaicl_stage05"
    cells = [
        md(f"""
# DynaICL Stage 0.5: confirmatory population-advantage run (Google Colab)

Runs the **pre-registered** confirmatory experiment (`docs/PREREG_stage05.md`, frozen, sha256 `{prereg_sha[:16]}...`):
matched population-aware Bayes vs the strongest context-only frontier (primary), and finite library vs
continuous prior (secondary). 144 cells x 2 independent replicates x 3378 items. CPU only.

**Before you start**
* `Runtime -> Change runtime type -> CPU`. **No GPU is needed.**
* Expected time on the free tier (2 vCPU): about **2-2.5 h**. This is estimated from the local pilot, not measured on Colab.
* **Interruption-safe:** each finished cell is saved to Google Drive (`MyDrive/dynaicl_stage05/checkpoints`).
  If the session dies, open the notebook again, do `Runtime -> Run all`, upload the zip again, and it **resumes**.
  The results are identical to an uninterrupted run. The final results are written straight to Drive.

**You need:** `{BUNDLE_NAME}` (sha256 `{bundle_sha[:16]}...`, {n_files} files). Then `Runtime -> Run all`.
"""),
        code("""
!python3 --version
!nproc
"""),
        md("## 1. Mount Drive (needed for checkpoints and results) and get the code bundle"),
        code(f"""
import hashlib, os, zipfile
from google.colab import drive
drive.mount("/content/drive")
os.makedirs("{drive}", exist_ok=True)

BUNDLE_ON_DRIVE = ""          # optional: e.g. "/content/drive/MyDrive/{BUNDLE_NAME}"
EXPECTED = {{"bundle": "{bundle_sha}", "prereg": "{prereg_sha}", "config_hash": "{config_hash}"}}
if BUNDLE_ON_DRIVE:
    src = BUNDLE_ON_DRIVE
else:
    from google.colab import files
    src = next(iter(files.upload()))       # pick {BUNDLE_NAME}
sha = hashlib.sha256(open(src, "rb").read()).hexdigest()
print("bundle sha256 matches:", sha == EXPECTED["bundle"])
os.makedirs("/content/DynaICL", exist_ok=True)
zipfile.ZipFile(src).extractall("/content/DynaICL")
os.chdir("/content/DynaICL")
bad = [rel for h, rel in (l.rstrip(chr(10)).split("  ", 1) for l in open("MANIFEST.sha256"))
       if hashlib.sha256(open(rel, "rb").read()).hexdigest() != h]
print("manifest check:", "OK" if not bad else f"MISMATCH {{bad}}")
print("pre-registration sha256 matches the frozen one:",
      hashlib.sha256(open("docs/PREREG_stage05.md", "rb").read()).hexdigest() == EXPECTED["prereg"])
"""),
        md("## 2. Install the pinned stack (pip conflict warnings about other Colab packages are harmless here)"),
        code("""
!pip install -q -r /content/DynaICL/requirements.txt
!python3 -c "import numpy, scipy, yaml, pytest; print('numpy', numpy.__version__, '| scipy', scipy.__version__, '| pyyaml', yaml.__version__, '| pytest', pytest.__version__)"
"""),
        md("## 3. Quick checks (about 1 min): Stage 0.5 tests and the config hash"),
        code(f"""
%cd /content/DynaICL
!python3 -m pytest -q -p no:cacheprovider tests/test_stage05.py
!python3 -c "from dynaicl.config.schema import load_population_config as L; h=L('config/stage05.yaml').config_hash(); print('config hash', h[:12], 'OK' if h=='{config_hash}' else 'MISMATCH')"
"""),
        md("""
## 4. The confirmatory run (the long step; prints one line per finished cell; resumes from Drive checkpoints)
"""),
        code(f"""
%cd /content/DynaICL
!OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 python3 -m dynaicl.experiments.population_advantage --config config/stage05.yaml --workers $(nproc) --checkpoint-dir {drive}/checkpoints --runs-dir {drive}/runs 2>&1 | tee -a {drive}/log.txt
"""),
        md("## 5. Summary and archive (the run directory is already on Drive; this also downloads a tar.gz)"),
        code(f"""
import glob, os, tarfile
run = sorted(glob.glob("{drive}/runs/*_stage05_population_advantage_*"))[-1]
print(run)
print(open(os.path.join(run, "results", "report.md")).read()[:6000])
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
    dist = ROOT / "dist"
    dist.mkdir(exist_ok=True)
    out = dist / BUNDLE_NAME
    manifest = build_zip(out)
    sha = hashlib.sha256(out.read_bytes()).hexdigest()
    nb_dir = ROOT / "colab"
    nb_dir.mkdir(exist_ok=True)
    nb_path = nb_dir / "DynaICL_Stage0_Colab.ipynb"
    nb_path.write_text(json.dumps(build_notebook(sha, len(manifest)), indent=1) + "\n", encoding="utf-8", newline="\n")
    prereg_sha = hashlib.sha256((ROOT / "docs" / "PREREG_stage05.md").read_bytes()).hexdigest()
    import sys
    sys.path.insert(0, str(ROOT))
    from dynaicl.config.schema import load_population_config
    cfg_hash = load_population_config(ROOT / "config" / "stage05.yaml").config_hash()
    nb05 = nb_dir / "DynaICL_Stage05_Colab.ipynb"
    nb05.write_text(json.dumps(build_stage05_notebook(sha, len(manifest), prereg_sha, cfg_hash), indent=1) + chr(10),
                    encoding="utf-8", newline=chr(10))
    print(f"bundle:   {out}  ({out.stat().st_size} bytes, {len(manifest)} files, sha256 {sha})")
    print(f"notebook: {nb_path}")
    print(f"notebook: {nb05}  (prereg sha256 {prereg_sha[:16]}..., config hash {cfg_hash[:12]})")


if __name__ == "__main__":
    main()
