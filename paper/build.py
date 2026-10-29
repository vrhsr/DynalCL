"""Build the Track 1 manuscript from a clean checkout (task E2 / E4).

Steps, each fatal on failure: (1) claims table (paper/tools/build_claims.py: every claim re-extracted from a pinned commit);
(2) number macros (tools/build_numbers.py); (3) tables (tools/make_tables.py); (4) numbers audit (tools/check_numbers.py);
(5) PDF with pdflatex + bibtex if available. Needs git history with the pinned commits (git fetch origin).

    python paper/build.py            # or: make -C paper
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

PAPER = Path(__file__).resolve().parent


def run(cmd: list[str], cwd: Path) -> None:
    print("$", " ".join(cmd), flush=True)
    rc = subprocess.run(cmd, cwd=cwd).returncode
    if rc != 0:
        raise SystemExit(f"FAILED ({rc}): {' '.join(cmd)}")


def main() -> int:
    py = sys.executable
    run([py, "tools/build_claims.py"], PAPER)
    run([py, "tools/build_numbers.py"], PAPER)
    run([py, "tools/make_tables.py"], PAPER)
    run([py, "tools/check_numbers.py"], PAPER)
    if not shutil.which("pdflatex"):
        print("pdflatex not found: claims, numbers and audit passed; PDF not built")
        return 0
    # MiKTeX refuses PATH entries that are files (seen on the authors' Windows machine); pass a cleaned PATH
    env = dict(os.environ)
    env["PATH"] = os.pathsep.join(p for p in env.get("PATH", "").split(os.pathsep) if not os.path.isfile(p))
    for cmd in (["pdflatex", "-interaction=nonstopmode", "-halt-on-error", "main.tex"], ["bibtex", "main"],
                ["pdflatex", "-interaction=nonstopmode", "-halt-on-error", "main.tex"],
                ["pdflatex", "-interaction=nonstopmode", "-halt-on-error", "main.tex"]):
        print("$", " ".join(cmd), flush=True)
        if subprocess.run(cmd, cwd=PAPER, env=env, stdout=subprocess.DEVNULL).returncode != 0:
            raise SystemExit(f"FAILED: {' '.join(cmd)} (see main.log / main.blg)")
    log = (PAPER / "main.log").read_text(encoding="latin-1")
    if "undefined" in log:
        raise SystemExit("FAILED: undefined references or citations remain (see main.log)")
    print("PDF built: paper/main.pdf")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
