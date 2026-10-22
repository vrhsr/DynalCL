"""PHASE D (PILOT) job queue with a live terminal dashboard. NOT part of the frozen file set. Pilot seeds only.

    python -u phase_d_pilot/run_queue.py

Runs the remaining Phase D tasks one after another (timing tasks must not overlap), shows an overall progress bar, a task table
and the tail of the running task's output, and writes machine-readable status so an assistant can wait for ONE completion marker
instead of polling:

    phase_d_pilot/work/queue/queue_status.json   updated every second
    phase_d_pilot/work/queue/QUEUE_DONE.json     written once, at the end (also when some tasks failed)
    phase_d_pilot/work/queue/logs/<task>.log     full output per task

No task here can start a confirmatory run (the harness refuses non-pilot seeds and has no confirmatory mode).
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
WORK = HERE / "work_v2"
QDIR = WORK / "queue"
LOGS = QDIR / "logs"
SNAP_SHA_FILE = ROOT / "dist" / "stage06_frozen_snapshot_v2.sha256"
SHA = SNAP_SHA_FILE.read_text(encoding="utf-8").splitlines()[1].split()[0] if SNAP_SHA_FILE.exists() else "NOT-FROZEN-YET"
BASE = ["--frozen-root", str(ROOT), "--snapshot", str(ROOT / "dist/stage06_frozen_snapshot_v2.zip"), "--manifest-sha", SHA]
REF = str(WORK / "ref_w4" / "ckpt")
H = [sys.executable, "-u", str(HERE / "pilot_harness.py")]


def task(name, minutes, args):
    return {"name": name, "est_min": minutes, "cmd": H + [args[0], *BASE, *args[1:]]}


TASKS = [
    {"name": "wait: interrupt tests (running in background)", "est_min": 14, "cmd": None, "wait_for": WORK / "reports/PILOT_interrupt_tests_local.json"},
    task("integrity bookend 2 (after interrupt tests)", 0.3, ["integrity", "--label", "bookend_2_after_interrupt_tests"]),
    task("corruption / truncation tests", 10, ["corruption-tests", "--tag", "local", "--ref-parent", REF]),
    task("runtime-restart emulation", 4, ["restart-emulation", "--ref-parent", REF]),
    task("integrity bookend 3 (after resume tests)", 0.3, ["integrity", "--label", "bookend_3_after_resume_tests"]),
    task("determinism: thread counts + analysis", 12, ["determinism", "--tag", "local", "--ref-parent", REF]),
    task("per-unit profile (50 units, serial)", 9, ["profile-units", "--tag", "local"]),
    task("scaling at N = 50/100/200/400", 11, ["scaling", "--tag", "local"]),
    task("second pilot size: all 50 units at N = 50", 2, ["size-sweep", "--tag", "local", "--workers", "4"]),
    task("anchors at N = 4000 (2 primary + 1 naive)", 14, ["anchor", "--tag", "local", "--units", "primary,0,0,2", "primary,0,3,0", "naive,0,0,2"]),
    task("analysis cost at confirmatory scale (synthetic)", 6, ["analysis-cost", "--tag", "local"]),
    task("storage probe (local disk)", 1, ["storage-probe", "--tag", "local_windows_disk", "--dir", str(WORK)]),
    task("qualification gate (throwaway copy)", 4, ["qualification-gate"]),
    task("integrity bookend 4 (after timing tasks)", 0.3, ["integrity", "--label", "bookend_4_after_timing_tasks"]),
    task("launch protection (stubbed copies)", 2, ["launch-protection", "--tag", "local", "--ref-parent", REF]),
    task("completeness (reference run)", 0.3, ["completeness", "--tag", "ref_w4", "--ref-parent", REF]),
    task("structural analysis on pilot output", 1, ["structural-analysis", "--tag", "local", "--ref-parent", REF]),
    task("seed search (pilot outputs)", 0.5, ["seed-search", "--tag", "local", "--dirs", str(WORK), str(HERE / "config")]),
    task("integrity bookend 5 (end of Phase D)", 0.3, ["integrity", "--label", "bookend_5_end_of_phase_d"]),
    # 20-24: re-measurement after fixing the Windows peak-memory probe (it returned 0 in the first pass)
    task("memory re-measure: anchors N = 4000 incl. integrity/tier1", 7, ["anchor", "--tag", "local_memfix", "--units", "primary,0,0,2", "primary,0,3,0", "naive,0,0,2", "integrity", "tier1"]),
    task("memory re-measure: synthetic analysis cost", 0.5, ["analysis-cost", "--tag", "local_memfix"]),
    task("memory re-measure: scaling N = 50..400", 5, ["scaling", "--tag", "local_memfix"]),
    task("memory re-measure: per-unit profile (50 units)", 9, ["profile-units", "--tag", "local_memfix"]),
    task("integrity bookend 6 (final)", 0.3, ["integrity", "--label", "bookend_6_final"]),
]


def cmd_task(name, minutes, cmd):
    return {"name": name, "est_min": minutes, "cmd": cmd}


PY = [sys.executable, "-u"]
S06 = ["tests/test_stage06_reference.py", "tests/test_stage06_analysis.py", "tests/test_stage06_gate.py", "tests/test_stage06_mutations.py"]
VALIDATION_TASKS = [
    cmd_task("record tested-file hashes (v2)", 0.2, PY + ["scripts/stage06_freeze.py", "--version", "v2", "record-tested"]),
    cmd_task("Stage 0.6 test suite (incl. slow V4/V9/V10, gate, mutations)", 14,
             PY + ["-m", "pytest", "-p", "no:cacheprovider", "-v", "--durations=8", *S06]),
    cmd_task("pre-existing Stage 0 / 0.5 suite (101 tests)", 10,
             PY + ["-m", "pytest", "-p", "no:cacheprovider", "-v", "--durations=5", *[f"--ignore={x}" for x in S06], "tests"]),
    cmd_task("mutation matrix v2 on a copy (40 mutants)", 8, PY + ["scripts/stage06_mutation_matrix.py", "--workers", "6", "--copy-dir",
                                                                    str(HERE / "work_v2" / "mutation_copy_v2")]),
    cmd_task("calibration diagnostic (pre-specified protocol) on a copy", 3, PY + ["phase_d_pilot/run_calibration_copy.py"]),
    cmd_task("verify the tested files are unchanged (once)", 0.2, PY + ["scripts/stage06_freeze.py", "--version", "v2", "verify-tested"]),
]

W2 = str(WORK) 
REF2 = str(WORK / "ref_w4" / "ckpt")
FROZEN_CLI = ["-m", "dynaicl.experiments.stage06_probe"]
PHASE_D_V2 = [
    task("integrity bookend 0 (start)", 0.3, ["integrity", "--label", "v2_bookend_0_start"]),
    cmd_task("frozen qualify (pilot config, local)", 3, PY + FROZEN_CLI + ["qualify", "--config", "config/stage06_pilot.yaml", "--manifest",
             "docs/FREEZE_MANIFEST_STAGE06_v2.json", "--expected-manifest-sha256", SHA, "--out", str(WORK / "reports" / "PILOT_qualification_local_windows_pilotcfg.json")]),
    task("reference run, 4 workers", 4, ["ref-run", "--tag", "ref_w4", "--workers", "4", "--threads", "1"]),
    task("reference run, 1 worker (order/worker independence)", 8, ["ref-run", "--tag", "ref_w1", "--workers", "1", "--threads", "1"]),
    task("compare the two reference runs bitwise", 0.2, ["compare-refs", "--tag", "ref_w4_vs_w1", "--ref-parent", REF2, "--other-parent", str(WORK / "ref_w1" / "ckpt")]),
    task("completeness of the reference run", 0.3, ["completeness", "--tag", "ref_w4", "--ref-parent", REF2]),
    task("integrity bookend 1 (after reference runs)", 0.3, ["integrity", "--label", "v2_bookend_1_after_reference_runs"]),
    task("interruption / resume scenarios (8)", 24, ["interrupt-tests", "--tag", "local", "--ref-parent", REF2]),
    task("integrity bookend 2 (after interrupt tests)", 0.3, ["integrity", "--label", "v2_bookend_2_after_interrupt_tests"]),
    task("corruption / truncation tests (10 cases)", 4, ["corruption-tests", "--tag", "local", "--ref-parent", REF2]),
    task("runtime-restart emulation", 4, ["restart-emulation", "--ref-parent", REF2]),
    task("integrity bookend 3 (after resume tests)", 0.3, ["integrity", "--label", "v2_bookend_3_after_resume_tests"]),
    task("determinism: thread counts + analysis", 4, ["determinism", "--tag", "local", "--ref-parent", REF2]),
    task("per-unit profile (50 units, serial)", 8, ["profile-units", "--tag", "local"]),
    task("scaling at N = 50/100/200/400", 5, ["scaling", "--tag", "local"]),
    task("second pilot size: all 50 units at N = 50", 2, ["size-sweep", "--tag", "local", "--workers", "4"]),
    task("anchors at N = 4000", 8, ["anchor", "--tag", "local", "--units", "primary,0,0,2", "primary,0,3,0", "naive,0,0,2", "integrity", "tier1"]),
    task("analysis cost at confirmatory scale (synthetic)", 1, ["analysis-cost", "--tag", "local"]),
    task("storage probe (local disk)", 1, ["storage-probe", "--tag", "local_windows_disk", "--dir", W2]),
    task("qualification gate (throwaway copy)", 3, ["qualification-gate"]),
    task("integrity bookend 4 (after timing tasks)", 0.3, ["integrity", "--label", "v2_bookend_4_after_timing_tasks"]),
    task("launch protection incl. the v2 gate (stubbed copies)", 2, ["launch-protection", "--tag", "local", "--ref-parent", REF2]),
    task("structural analysis on pilot output", 1, ["structural-analysis", "--tag", "local", "--ref-parent", REF2]),
    task("seed search (pilot outputs)", 0.5, ["seed-search", "--tag", "local", "--dirs", W2, str(HERE / "config")]),
    task("integrity bookend 5 (end)", 0.3, ["integrity", "--label", "v2_bookend_5_end_of_phase_d"]),
]


def bar(frac: float, width=46) -> str:
    n = int(round(frac * width))
    return "[" + "#" * n + "-" * (width - n) + f"] {100 * frac:5.1f}%"


def fmt(sec: float) -> str:
    sec = int(max(sec, 0))
    return f"{sec // 3600}:{sec % 3600 // 60:02d}:{sec % 60:02d}"


def read_tail(path: Path, n=7) -> list[str]:
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").replace("\r", "\n").splitlines()
        return [l[:118] for l in lines if l.strip()][-n:]
    except OSError:
        return []


def interrupt_view() -> list[str]:
    d = WORK / "interrupt"
    if not d.exists():
        return ["(interrupt tests not started yet)"]
    rows = []
    for s in sorted(d.iterdir(), key=lambda p: p.stat().st_mtime)[-4:]:
        done = len(list(s.glob("ckpt/*/*.json")))
        rows.append(f"{s.name}: {done}/50 units saved")
    return rows


def render(state, current_lines):
    total_w = sum(t["est_min"] for t in TASKS)
    done_w = sum(t["est_min"] for t, s in zip(TASKS, state["status"]) if s in ("done", "FAILED"))
    cur = state["current"]
    elapsed_cur = time.time() - state["task_start"] if cur is not None else 0
    if cur is not None:
        done_w += min(TASKS[cur]["est_min"], elapsed_cur / 60) * 0.95
    frac = min(done_w / total_w, 0.999 if cur is not None else 1.0)
    elapsed = time.time() - state["start"]
    eta = elapsed * (1 - frac) / frac if frac > 0.02 else None
    out = ["\033[H\033[J", "PHASE D (PILOT)  -  Stage 0.6 operational qualification   (pilot seeds only; no confirmatory run exists here)",
           f"started {time.strftime('%H:%M:%S', time.localtime(state['start']))}   elapsed {fmt(elapsed)}   "
           f"approx. remaining {fmt(eta) if eta is not None else '...'}   (estimate from task weights)", "",
           "OVERALL  " + bar(frac), ""]
    for i, (t, s) in enumerate(zip(TASKS, state["status"])):
        mark = {"pending": " ", "running": ">", "done": "x", "FAILED": "!"}[s]
        dur = f"{state['secs'][i]:6.0f}s" if state["secs"][i] is not None else ("   ...  " if s == "running" else "        ")
        out.append(f" [{mark}] {i + 1:2d}. {t['name'][:58]:58s} {dur}  (~{t['est_min']:g} min)")
    out += ["", "CURRENT TASK OUTPUT:"]
    out += ["   " + l for l in current_lines[-8:]]
    out.append("")
    out.append("Status file for the assistant: phase_d_pilot/work/queue/queue_status.json (it waits for QUEUE_DONE.json)")
    sys.stdout.write("\n".join(out) + "\n")
    sys.stdout.flush()


def write_status(state, finished=False):
    obj = {"updated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "tasks": [
        {"name": t["name"], "status": s, "seconds": sec, "rc": rc} for t, s, sec, rc in
        zip(TASKS, state["status"], state["secs"], state["rc"])], "current": state["current"], "finished": finished}
    (QDIR / "queue_status.json").write_text(json.dumps(obj, indent=1), encoding="utf-8")
    return obj


def main() -> int:
    global TASKS, QDIR, LOGS
    if len(sys.argv) > 2 and sys.argv[1] == "--set" and sys.argv[2] == "validation":
        TASKS = VALIDATION_TASKS
        QDIR = WORK / "queue_validation"
        LOGS = QDIR / "logs"
    elif len(sys.argv) > 2 and sys.argv[1] == "--set" and sys.argv[2] == "phase_d_v2":
        TASKS = PHASE_D_V2
        QDIR = WORK / "queue_phase_d_v2"
        LOGS = QDIR / "logs"
    elif len(sys.argv) > 2 and sys.argv[1] == "--only":      # python run_queue.py --only 3,12  (re-run chosen tasks)
        keep = {int(x) for x in sys.argv[2].split(",")}
        TASKS = [t for i, t in enumerate(TASKS, 1) if i in keep]
        QDIR = WORK / ("queue_rerun_" + sys.argv[3] if len(sys.argv) > 3 else "queue_rerun")
        LOGS = QDIR / "logs"
    os.system("")                         # enable ANSI escape sequences in the Windows console
    QDIR.mkdir(parents=True, exist_ok=True)
    LOGS.mkdir(parents=True, exist_ok=True)
    for f in (QDIR / "QUEUE_DONE.json",):
        f.unlink(missing_ok=True)
    state = {"start": time.time(), "status": ["pending"] * len(TASKS), "secs": [None] * len(TASKS), "rc": [None] * len(TASKS),
             "current": None, "task_start": time.time()}
    env = {**os.environ, "PYTHONUNBUFFERED": "1", "PYTHONPATH": str(ROOT)}
    for i, t in enumerate(TASKS):
        state.update(current=i, task_start=time.time())
        state["status"][i] = "running"
        log = LOGS / f"{i + 1:02d}.log"
        if t["cmd"] is None:                                  # wait for a background job's result file
            while not t["wait_for"].exists() and time.time() - state["task_start"] < 3 * 3600:
                render(state, interrupt_view())
                write_status(state)
                time.sleep(1)
            state["rc"][i] = 0 if t["wait_for"].exists() else "timeout"
        else:
            with open(log, "wb") as fh:
                p = subprocess.Popen(t["cmd"], cwd=ROOT, env=env, stdout=fh, stderr=subprocess.STDOUT)
                while p.poll() is None:
                    render(state, read_tail(log))
                    write_status(state)
                    time.sleep(1)
            state["rc"][i] = p.returncode
        state["secs"][i] = round(time.time() - state["task_start"], 1)
        state["status"][i] = "done" if state["rc"][i] == 0 else "FAILED"
        write_status(state)
    state["current"] = None
    render(state, ["ALL TASKS FINISHED"])
    obj = write_status(state, finished=True)
    (QDIR / "QUEUE_DONE.json").write_text(json.dumps({**obj, "total_seconds": round(time.time() - state["start"], 1)}, indent=1),
                                          encoding="utf-8")
    print("DONE. Results: phase_d_pilot/work/reports/. You can close this window.")
    return 0 if all(r == 0 for r in state["rc"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
