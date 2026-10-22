"""Mutation-detection matrix (Section 5.G).

    python scripts/mutation_report.py                 # every validation check under every mutation
    python scripts/mutation_report.py --pytest        # also: the whole pytest suite under each mutation

Writes runs/mutation_report_<UTC>/ with matrix.json, matrix.md and (with --pytest) per-mutation junit XML.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dynaicl.provenance import git_state, package_versions, platform_info  # noqa: E402
from dynaicl.validation.checks import ALL_CHECKS  # noqa: E402
from dynaicl.validation.mutations import MUTATIONS, detected, run_mutation_matrix  # noqa: E402


def check_matrix_markdown(matrix: dict) -> str:
    checks = list(next(iter(matrix.values())))
    lines = ["| mutation | " + " | ".join(checks) + " | detected by |", "|---|" + "---|" * (len(checks) + 1)]
    for mut, row in matrix.items():
        cells = [row[c]["status"].replace("ERROR:", "ERR:") for c in checks]
        by = [c for c in checks if detected(row[c])]
        lines.append(f"| {mut} | " + " | ".join(cells) + f" | {', '.join(by) if by else ('-' if mut == 'baseline' else 'NOT DETECTED')} |")
    return "\n".join(lines)


def failing_tests(junit: Path) -> tuple[list[str], int]:
    tree = ET.parse(junit)
    failed, total = [], 0
    for case in tree.iter("testcase"):
        total += 1
        if case.find("failure") is not None or case.find("error") is not None:
            failed.append(f"{case.get('classname')}::{case.get('name')}")
    return failed, total


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pytest", action="store_true", help="also run the full pytest suite under each mutation")
    ap.add_argument("--checks", nargs="*", default=None, help="subset of check ids (default: all)")
    ap.add_argument("--jobs", type=int, default=1, help="parallel pytest processes for the --pytest phase")
    ap.add_argument("--pytest-args", nargs="*", default=[], help="extra pytest arguments, e.g. a subset of test files")
    args = ap.parse_args()
    out = ROOT / "runs" / f"mutation_report_{dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    out.mkdir(parents=True)
    checks = {k: v for k, v in ALL_CHECKS.items() if args.checks is None or k in args.checks}
    t_start = dt.datetime.now()
    n_total = len(checks) * (len(MUTATIONS) + 1)
    done = [0]

    def progress(mutation, check, row):
        done[0] += 1
        elapsed = (dt.datetime.now() - t_start).total_seconds() / 60
        print(f"[checks {done[0]:3d}/{n_total}  {elapsed:5.1f} min] {mutation:36s} {check:3s} {row['status']:28s} "
              f"{row['seconds']:7.1f}s", flush=True)

    print(f"phase A: {len(checks)} checks x {len(MUTATIONS) + 1} runs (baseline + mutations), one process", flush=True)
    matrix = run_mutation_matrix(checks, progress=progress)
    report = {"checks": matrix, "git": git_state(ROOT), "packages": package_versions(), "platform": platform_info()}
    md = ["# Mutation-detection matrix", "", "## Validation checks (pass = not detected)", "", check_matrix_markdown(matrix)]
    if args.pytest:
        md += ["", "## Full pytest suite under each mutation", ""]
        report["pytest"] = {}
        names = ["baseline", *MUTATIONS]

        print(f"phase B: whole pytest suite under each of {len(names)} settings, {max(1, args.jobs)} at a time",
              flush=True)

        def run_suite(name):
            env = dict(os.environ, DYNAICL_MUTATION="" if name == "baseline" else name)
            t0 = dt.datetime.now()
            subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
                            f"--junitxml={out / f'junit_{name}.xml'}", *args.pytest_args],
                           cwd=ROOT, env=env, capture_output=True, text=True)
            mins = (dt.datetime.now() - t0).total_seconds() / 60
            print(f"[pytest] finished {name:36s} in {mins:5.1f} min", flush=True)

        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=max(1, args.jobs)) as pool:
            list(pool.map(run_suite, names))
        for name in names:
            junit = out / f"junit_{name}.xml"
            failed, total = failing_tests(junit)
            report["pytest"][name] = {"n_tests": total, "failed": failed}
            md.append(f"### {name}: {len(failed)} of {total} tests failed")
            md += [f"- {t}" for t in failed] + [""]
    (out / "matrix.json").write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    (out / "matrix.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md))
    print(f"\nwritten to {out}")
    undetected = [m for m in MUTATIONS if not any(detected(r) for r in matrix[m].values())]
    baseline_bad = [c for c, r in matrix["baseline"].items() if detected(r)]
    return 1 if (undetected or baseline_bad) else 0


if __name__ == "__main__":
    raise SystemExit(main())
