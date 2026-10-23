"""Record the Stage 1 execution environment (PREREG_stage1 section 13) as JSON.

Usage (box): .venv-stage1/bin/python scripts/stage1_env_manifest.py --out results_stage1/env/STAGE1_ENVIRONMENT_MANIFEST.json
Reads versions only; changes nothing. Touches the GPU only to query its name and CUDA availability.
"""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import platform
import shutil
import subprocess
import sys
from pathlib import Path


def _run(cmd: list[str]) -> str:
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=60).stdout.strip()
    except Exception as exc:
        return f"unavailable: {exc}"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    out = Path(ap.parse_args(argv).out)
    out.parent.mkdir(parents=True, exist_ok=True)
    import numpy
    import pytest
    import scipy
    import torch
    import yaml
    info = {
        "python": sys.version, "implementation": platform.python_implementation(), "executable": sys.executable,
        "system": platform.system(), "machine": platform.machine(), "platform": platform.platform(),
        "numpy": numpy.__version__, "scipy": scipy.__version__, "pyyaml": yaml.__version__, "pytest": pytest.__version__,
        "torch": torch.__version__, "torch_cuda": torch.version.cuda,
        "cudnn": torch.backends.cudnn.version() if torch.backends.cudnn.is_available() else None,
        "cuda_available": torch.cuda.is_available(),
        "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
        "nvidia_smi": _run(["nvidia-smi", "--query-gpu=name,driver_version,memory.total", "--format=csv,noheader"])
        if shutil.which("nvidia-smi") else None,
        # uv-created venvs have no pip; list installed distributions directly (fixes an empty list in the first run)
        "packages": sorted(f"{d.metadata['Name']}=={d.version}" for d in importlib.metadata.distributions()),
    }
    out.write_text(json.dumps(info, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in info.items() if k != "packages"}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
