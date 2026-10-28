"""F1-V9 mutation matrix (docs/MATH_F1.md section 6; task A1).

For the clean code and each mutation in dynaicl_families/stage2/f1_mutations.KNOWN, in separate processes:
  (i) the FROZEN F1 tests (tests_stage1/test_f1_references.py, unedited) under the pytest plugin that injects the mutation;
  (ii) the extra detectors (python -m dynaicl_families.stage2.f1_detect).
Pass condition: the clean row passes everything; every mutation is detected by at least one assertion-style failure (a
failed test or a failed detector without an exception); detections only through crashes are reported separately.
Writes <out>/f1_mutation_matrix.json and .md, and <out>/provenance.json (source hashes, versions, command).

Usage: python scripts/stage2_f1_mutation_matrix.py --out results_stage2/f1_mutation_matrix --jobs 2
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dynaicl_families.stage2.f1_mutations import ENV, KNOWN  # noqa: E402

FROZEN_TESTS = "tests_stage1/test_f1_references.py"
SOURCES = ["dynaicl_families/ar1_unknown_sigma.py", "dynaicl_families/sampling.py", "dynaicl_families/ar1_known_sigma.py",
           FROZEN_TESTS, "dynaicl_families/stage2/f1_mutations.py", "dynaicl_families/stage2/f1_plugin.py",
           "dynaicl_families/stage2/f1_checks.py", "dynaicl_families/stage2/f1_detect.py",
           "config/stage2_seed_manifest.yaml", "scripts/stage2_f1_mutation_matrix.py"]


def _env(mutation: str | None) -> dict:
    env = dict(os.environ)
    env.pop(ENV, None)
    if mutation:
        env[ENV] = mutation
    for k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
        env[k] = "1"                                   # one core per process; rows run in parallel
    return env


def run_row(mutation: str | None) -> dict:
    t0 = time.time()
    p = subprocess.run([sys.executable, "-m", "pytest", FROZEN_TESTS, "-q", "-rf", "-p", "no:cacheprovider",
                        "-p", "dynaicl_families.stage2.f1_plugin"], cwd=ROOT, env=_env(mutation),
                       capture_output=True, text=True, stdin=subprocess.DEVNULL, timeout=3600)
    # "-rf" short summary lines read "FAILED <id> - <ExceptionType>: <message>"; only AssertionError counts as a
    # detection (a MemoryError from running rows in parallel once made the clean row fail: disclosure S29)
    fails = re.findall(r"^FAILED (\S+)(?: - (\w+))?", p.stdout, flags=re.M)
    failed = [f for f, kind in fails if kind in ("AssertionError", "assert", "")]
    failed_other = [f"{f.split('::')[-1]} ({kind})" for f, kind in fails if kind not in ("AssertionError", "assert", "")]
    errors = re.findall(r"^ERROR (\S+)", p.stdout, flags=re.M)
    summary = (p.stdout.strip().splitlines() or [""])[-1]
    d = subprocess.run([sys.executable, "-m", "dynaicl_families.stage2.f1_detect"], cwd=ROOT, env=_env(mutation),
                       capture_output=True, text=True, stdin=subprocess.DEVNULL, timeout=3600)
    try:
        det = json.loads(d.stdout.strip().splitlines()[-1])
    except Exception:
        det = {"checks": {"detector_run": {"pass": False, "exception": d.stderr[-2000:]}}}
    det_fail = sorted(k for k, v in det["checks"].items() if not v["pass"] and "exception" not in v)
    det_crash = sorted(k for k, v in det["checks"].items() if not v["pass"] and "exception" in v)
    return {"mutation": mutation or "baseline", "pytest_exit": p.returncode, "pytest_summary": summary,
            "failed_tests": [f.split("::")[-1] for f in failed], "failed_other_exception": failed_other,
            "errored_tests": [e.split("::")[-1] for e in errors],
            "assertion_failures_in_pytest": p.stdout.count("AssertionError"),
            "detector_failures": det_fail, "detector_crashes": det_crash, "detectors": det,
            "seconds": round(time.time() - t0, 1)}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--jobs", type=int, default=2)    # memory: the frozen F1-V3 grid oracle needs about 1-2 GB a process
    args = ap.parse_args(argv)
    out = ROOT / args.out
    out.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=args.jobs) as ex:
        rows = list(ex.map(run_row, [None, *KNOWN]))
    base = rows[0]
    base_ok = (base["pytest_exit"] == 0 and not base["detector_failures"] and not base["detector_crashes"]
               and not base["failed_other_exception"])
    for r in rows[1:]:
        r["detected_by_assertion"] = bool(r["failed_tests"] and r["assertion_failures_in_pytest"]) or bool(
            r["detector_failures"])
    ok = base_ok and all(r["detected_by_assertion"] for r in rows[1:])
    (out / "f1_mutation_matrix.json").write_text(json.dumps({"pass": ok, "baseline_pass": base_ok, "rows": rows},
                                                            indent=1, default=float), encoding="utf-8")
    lines = ["# F1-V9 mutation matrix", "", f"Overall: {'PASS' if ok else 'FAIL'} (baseline {'passes' if base_ok else 'FAILS'})",
             "", "| mutation | frozen F1 tests failing | extra detectors failing | crashes | pytest summary |",
             "|---|---|---|---|---|"]
    for r in rows:
        crashes = ", ".join(r["detector_crashes"] + r["errored_tests"] + r["failed_other_exception"]) or "-"
        lines.append(f"| {r['mutation']} | {', '.join(r['failed_tests']) or '-'} | "
                     f"{', '.join(r['detector_failures']) or '-'} | {crashes} | {r['pytest_summary']} |")
    (out / "f1_mutation_matrix.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    prov = {"command": " ".join([Path(sys.executable).name, *sys.argv]), "python": platform.python_version(),
            "platform": platform.platform(), "seconds": round(time.time() - t0, 1),
            "sources_sha256": {s: hashlib.sha256((ROOT / s).read_bytes()).hexdigest() for s in SOURCES}}
    try:
        import numpy, scipy  # noqa: E401
        prov["numpy"], prov["scipy"] = numpy.__version__, scipy.__version__
        prov["git_head"] = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True,
                                          text=True).stdout.strip()
        prov["git_dirty_tracked"] = bool(subprocess.run(["git", "status", "--porcelain", "--untracked-files=no"],
                                                        cwd=ROOT, capture_output=True, text=True).stdout.strip())
    except Exception as exc:
        prov["error"] = str(exc)
    (out / "provenance.json").write_text(json.dumps(prov, indent=1), encoding="utf-8")
    print("\n".join(lines))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
