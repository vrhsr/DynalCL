"""Stage 1 mutation matrix: run tests_stage1/test_neural.py once per mutation (env STAGE1_MUTATION) and once clean.

Pass condition: the clean run passes, and every mutation makes at least one test fail with an assertion (a crash through
an unexpected exception type is reported separately). Writes <out>/mutation_matrix.json and .md.
Usage: python scripts/stage1_mutation_matrix.py --out results_stage1/mutation_matrix
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dynaicl_neural.mutations import KNOWN  # noqa: E402

TESTS = "tests_stage1/test_neural.py"


def run(mutation: str | None) -> dict:
    env = dict(os.environ)
    env.pop("STAGE1_MUTATION", None)
    if mutation:
        env["STAGE1_MUTATION"] = mutation
    t0 = time.time()
    p = subprocess.run([sys.executable, "-m", "pytest", TESTS, "-q", "-rf", "-p", "no:cacheprovider"], cwd=ROOT,
                       env=env, capture_output=True, text=True, stdin=subprocess.DEVNULL, timeout=900)
    failed = re.findall(r"^FAILED (\S+)", p.stdout, flags=re.M)
    summary = (p.stdout.strip().splitlines() or [""])[-1]
    return {"mutation": mutation or "baseline", "exit_code": p.returncode, "failed_tests": failed,
            "summary": summary, "seconds": round(time.time() - t0, 1),
            "assertion_failures": p.stdout.count("AssertionError")}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    out = Path(ap.parse_args(argv).out)
    out.mkdir(parents=True, exist_ok=True)
    rows = [run(None)] + [run(m) for m in KNOWN]
    ok = rows[0]["exit_code"] == 0 and all(r["exit_code"] != 0 and r["failed_tests"] for r in rows[1:])
    (out / "mutation_matrix.json").write_text(json.dumps({"pass": ok, "rows": rows}, indent=1), encoding="utf-8")
    lines = ["# Stage 1 mutation matrix", "", f"Overall: {'PASS' if ok else 'FAIL'}", "",
             "| mutation | exit | detected by | assertion failures | summary |", "|---|---|---|---|---|"]
    for r in rows:
        det = ", ".join(t.split("::")[-1] for t in r["failed_tests"]) or "-"
        lines.append(f"| {r['mutation']} | {r['exit_code']} | {det} | {r['assertion_failures']} | {r['summary']} |")
    (out / "mutation_matrix.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
