"""PHASE D (PILOT) harness. NOT part of the frozen file set. Pilot seeds only; no task here can start a confirmatory run.

    python pilot_harness.py <task> --frozen-root R --snapshot Z --manifest-sha H [--work W] [--durable D] ...

Tasks: integrity, env, ref-run, interrupt-tests, corruption-tests, restart-emulation, determinism, profile-units, scaling,
anchor, size-sweep, analysis-cost, storage-probe, launch-protection, completeness, structural-analysis, seed-search,
qualification-gate.

Every task writes pilot-labelled JSON under ``<work>/reports`` and prints a short structural summary. The same harness
runs locally (Windows rehearsal) and on Colab (Linux) so the two can be compared. Pilot config: the FROZEN
``config/stage06_pilot.yaml`` (seeds 62001, 62101; bootstrap 62999) is the only config the frozen runner accepts.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import re
import shutil
import statistics
import subprocess
import sys
import time
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import pilot_common as PC  # noqa: E402

CHILD = str(HERE / "pilot_child.py")
PILOT_CFG = "config/stage06_pilot.yaml"


class Ctx:
    def __init__(self, a):
        self.root = PC.use_frozen_root(a.frozen_root)
        self.snapshot = Path(a.snapshot).resolve()
        self.sha = a.manifest_sha
        self.work = Path(a.work).resolve()
        self.durable = Path(a.durable).resolve() if getattr(a, "durable", None) else None
        self.qualification = Path(a.qualification).resolve() if getattr(a, "qualification", None) else None
        self.reports = self.work / "reports"
        self.reports.mkdir(parents=True, exist_ok=True)
        from dynaicl.config.stage06_schema import load_stage06_config
        self.cfg = load_stage06_config(self.root / PILOT_CFG)
        PC.assert_pilot_config(self.cfg)
        self.cpu = PC.cpu_model()

    def log_phase(self, name: str, **kw):
        with open(self.reports / "PILOT_phase_log.jsonl", "a", encoding="utf-8") as fh:
            fh.write(json.dumps({"utc": PC.utc_now(), "phase": name, "cpu_model": self.cpu, "host": os.uname().nodename
                                 if hasattr(os, "uname") else os.environ.get("COMPUTERNAME"), **kw}, sort_keys=True) + "\n")

    def write(self, name: str, obj) -> Path:
        p = self.reports / name
        p.write_text(json.dumps({"run_kind": PC.RUN_KIND, **obj} if isinstance(obj, dict) else obj, indent=1, sort_keys=True,
                                default=str) + "\n", encoding="utf-8")
        return p

    def runner(self, command, ckpt=None, runs=None, workers=None, extra=(), config=PILOT_CFG, qualification=None, cwd=None):
        return PC.runner_cmd(self.root, command, config, self.sha, ckpt, runs, workers, qualification or self.qualification,
                             extra)

    def run_sync(self, cmd, log: Path, threads=None, timeout=3600, env_extra=None) -> dict:
        t = time.time()
        p = PC.spawn(cmd, self.root, log, threads, env_extra)
        try:
            rc = p.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            PC.hard_kill(p)
            rc = "timeout"
        return {"rc": rc, "wall_s": round(time.time() - t, 2)}

    def units(self):
        from dynaicl.experiments import stage06_probe as P
        return P.plan_units(self.cfg), P


def tail(path: Path, n=3) -> str:
    try:
        return " | ".join(Path(path).read_text(encoding="utf-8", errors="replace").strip().splitlines()[-n:])[:400]
    except FileNotFoundError:
        return ""


# ------------------------------------------------------------------------------------------ comparison


def compare_ckpt(ctx: Ctx, ref_parent: Path, test_parent: Path) -> dict:
    """Every unit: same json (minus timings), arrays bitwise equal, same npz file bytes. Also reports leftovers."""
    import numpy as np
    units, P = ctx.units()
    ref, tst = PC.ckpt_root_for(ref_parent, ctx.cfg), PC.ckpt_root_for(test_parent, ctx.cfg)
    res = {"units_expected": len(units), "missing": [], "meta_differs": [], "arrays_differ": [], "npz_file_bytes_differ": [],
           "max_abs_diff": 0.0}
    for u in units:
        n = P.unit_name(u)
        if not (tst / f"{n}.json").is_file() or not (tst / f"{n}.npz").is_file():
            res["missing"].append(n)
            continue
        try:
            a, b = json.loads((ref / f"{n}.json").read_text()), json.loads((tst / f"{n}.json").read_text())
        except (ValueError, OSError):
            res["meta_differs"].append(f"{n}:unreadable_json")
            continue
        for d in (a, b):
            d.pop("seconds", None)
        if a != b:
            res["meta_differs"].append(n)
        if (ref / f"{n}.npz").read_bytes() != (tst / f"{n}.npz").read_bytes():
            res["npz_file_bytes_differ"].append(n)
        try:
            with np.load(ref / f"{n}.npz") as za, np.load(tst / f"{n}.npz") as zb:
                if set(za.files) != set(zb.files):
                    res["arrays_differ"].append(n)
                    continue
                for k in za.files:
                    if za[k].tobytes() != zb[k].tobytes():
                        res["arrays_differ"].append(f"{n}:{k}")
                        res["max_abs_diff"] = max(res["max_abs_diff"], float(np.max(np.abs(za[k].astype(float) - zb[k].astype(float)))))
        except Exception as exc:        # any read error of a corrupted file (BadZipFile, EOFError, ...) is a difference, not a crash of the checker
            res["arrays_differ"].append(f"{n}:unreadable({type(exc).__name__})")
    files = sorted(f.name for f in tst.glob("*")) if tst.exists() else []
    res["json_files"] = sum(f.endswith(".json") for f in files)
    res["npz_files"] = sum(f.endswith(".npz") for f in files)
    res["leftover_tmp_files"] = [f for f in files if f.endswith(".tmp")]
    res["unexpected_files"] = [f for f in files if not f.endswith((".json", ".npz", ".tmp"))]
    res["identical_to_reference"] = not (res["missing"] or res["meta_differs"] or res["arrays_differ"]
                                         or res["npz_file_bytes_differ"] or res["json_files"] != len(units))
    return res


def saved_lines(*logs: Path) -> list[str]:
    names = []
    for lg in logs:
        if lg.exists():
            names += re.findall(r"units?,\s*[\d.]+ min\] (\S+) \(", lg.read_text(encoding="utf-8", errors="replace"))
    return names


# ------------------------------------------------------------------------------------------ tasks


def t_integrity(ctx: Ctx, a):
    r = PC.integrity_snapshot(ctx.root, ctx.snapshot, ctx.sha, a.label, ctx.reports / "PILOT_integrity_log.jsonl")
    print(json.dumps({k: r[k] for k in ("label", "manifest_sha256", "snapshot_sha256", "prereg_sha256",
                                       "config_confirmatory_sha256", "config_pilot_sha256", "amendment_sha256", "manifest_files",
                                       "workspace_file_mismatches", "snapshot_member_mismatches", "ok")}, indent=1))
    return 0 if r["ok"] else 2


def t_env(ctx: Ctx, a):
    r = PC.environment_report(ctx.root, ctx.durable)
    p = ctx.write(f"PILOT_environment_{a.tag}.json", r)
    print(f"environment report -> {p}")
    print(json.dumps({k: r[k] for k in ("environment_fingerprint", "fingerprint_differences", "cpu_model", "cpu_count_logical",
                                        "ram_total_gb", "gpu")}, indent=1, default=str))
    return 0


def t_ref_run(ctx: Ctx, a):
    base = ctx.work / a.tag
    if base.exists():
        raise SystemExit(f"{base} exists; choose a new --tag")
    ctx.log_phase(f"ref-run:{a.tag}:start", workers=a.workers, threads=a.threads)
    cmd = ctx.runner("run", base / "ckpt", base / "runs", a.workers, qualification=a.qualification)
    r = ctx.run_sync(cmd, base / "log.txt", a.threads)
    ctx.log_phase(f"ref-run:{a.tag}:end", **r)
    print(a.tag, r, tail(base / "log.txt"))
    return 0 if r["rc"] == 0 else 1


def t_interrupt_tests(ctx: Ctx, a):
    ref = Path(a.ref_parent)
    rng = random.Random(20261010)
    scen = [("clean_max_new_units", "cli", dict(workers=1, first_extra=["--max-new-units", "12"])),
            ("clean_keyboardinterrupt_mid_unit", "crash", dict(point="interrupt_mid_unit", after=9, workers=1)),
            ("hard_kill_external_w1", "kill", dict(workers=1, min_done=6, resume_workers=4)),
            ("hard_kill_external_w4", "kill", dict(workers=4, min_done=16, resume_workers=1)),
            ("hard_kill_external_late", "kill", dict(workers=4, min_done=40, resume_workers=2)),
            ("selfkill_savez_partial", "crash", dict(point="savez_partial", after=7, workers=1)),
            ("selfkill_before_npz_replace", "crash", dict(point="before_npz_replace", after=8, workers=1)),
            ("selfkill_before_json_replace", "crash", dict(point="before_json_replace", after=9, workers=1))]
    if a.only:
        scen = [s for s in scen if s[0] in a.only]
    results = {}
    for name, kind, kw in scen:
        base = ctx.work / "interrupt" / name
        if base.exists():
            shutil.rmtree(base)
        ck, runs, l1, l2 = base / "ckpt", base / "runs", base / "phase1.log", base / "phase2.log"
        ctx.log_phase(f"interrupt:{name}:phase1")
        info = {"kind": kind, **{k: v for k, v in kw.items()}}
        if kind == "cli":
            r1 = ctx.run_sync(ctx.runner("run", ck, runs, kw["workers"], extra=kw["first_extra"]), l1, 1)
        elif kind == "crash":
            cmd = [sys.executable, CHILD, "crash-run", "--frozen-root", str(ctx.root), "--point", kw["point"], "--after",
                   str(kw["after"]), "--", *ctx.runner("run", ck, runs, kw["workers"])[3:]]
            r1 = ctx.run_sync(cmd, l1, 1)
        else:
            cmd = ctx.runner("run", ck, runs, kw["workers"])
            p = PC.spawn(cmd, ctx.root, l1, 1)
            t0 = time.time()
            root = PC.ckpt_root_for(ck, ctx.cfg)
            while p.poll() is None and PC.count_done(root) < kw["min_done"] and time.time() - t0 < 1500:
                time.sleep(0.2)
            time.sleep(rng.uniform(0.0, 2.5))
            alive = p.poll() is None
            PC.hard_kill(p)
            r1 = {"rc": "killed" if alive else p.returncode, "wall_s": round(time.time() - t0, 2), "was_alive_at_kill": alive}
        root = PC.ckpt_root_for(ck, ctx.cfg)
        info["phase1"] = r1
        info["units_done_after_phase1"] = PC.count_done(root)
        info["files_after_phase1"] = sorted(f.name for f in root.glob("*") if f.suffix in (".tmp",)) if root.exists() else []
        info["npz_without_json"] = sorted(f.stem for f in root.glob("*.npz") if not (root / f"{f.stem}.json").exists()) if root.exists() else []
        ctx.log_phase(f"interrupt:{name}:phase2")
        w2 = kw.get("resume_workers", 1)
        r2 = ctx.run_sync(ctx.runner("run", ck, runs, w2), l2, 1)
        info["phase2"] = {**r2, "workers": w2}
        info["phase1_tail"] = tail(l1)
        info["phase2_tail"] = tail(l2)
        cmpd = compare_ckpt(ctx, ref, ck)
        names = saved_lines(l1, l2)
        dup = sorted({n for n in names if names.count(n) > 1})
        info.update({"comparison_with_uninterrupted_reference": cmpd, "units_printed_more_than_once": dup,
                     "units_missing_at_end": cmpd["missing"],
                     "result_dirs_written": len(list(runs.glob("*"))) if runs.exists() else 0})
        results[name] = info
        print(f"{name}: phase1 {r1} done={info['units_done_after_phase1']}; resume rc={r2['rc']}; identical="
              f"{cmpd['identical_to_reference']}; dup={dup}; leftovers={cmpd['leftover_tmp_files']}", flush=True)
    ctx.write(f"PILOT_interrupt_tests_{a.tag}.json", {"results": results})
    return 0 if all(r["comparison_with_uninterrupted_reference"]["identical_to_reference"] and r["phase2"]["rc"] == 0
                    for r in results.values()) else 1


def corrupt_cases():
    """(name, mutator(root, unit_names) -> unit name affected, expectation text)."""
    import numpy as np

    def truncate_npz(root, names):
        f = root / f"{names[3]}.npz"
        f.write_bytes(f.read_bytes()[: f.stat().st_size // 2])
        return names[3]

    def flip_byte(root, names):
        f = root / f"{names[4]}.npz"
        b = bytearray(f.read_bytes())
        b[len(b) // 2] ^= 0xFF
        f.write_bytes(bytes(b))
        return names[4]

    def truncate_json(root, names):
        f = root / f"{names[5]}.json"
        f.write_bytes(f.read_bytes()[: int(f.stat().st_size * 0.6)])
        return names[5]

    def delete_json(root, names):
        (root / f"{names[6]}.json").unlink()
        return names[6]

    def delete_npz(root, names):
        (root / f"{names[7]}.npz").unlink()
        return names[7]

    def swap_npz(root, names):
        a, b = root / f"{names[8]}.npz", root / f"{names[9]}.npz"
        da, db = a.read_bytes(), b.read_bytes()
        a.write_bytes(db)
        b.write_bytes(da)
        return names[8]

    def zero_npz(root, names):
        (root / f"{names[10]}.npz").write_bytes(b"")
        return names[10]

    def leftover_tmp(root, names):
        (root / f"{names[11]}.npz.tmp").write_bytes(b"partial")
        (root / f"{names[11]}.json.tmp").write_bytes(b"{")
        return names[11]

    def edit_config_hash(root, names):
        f = root / f"{names[12]}.json"
        d = json.loads(f.read_text())
        d["config_hash"] = "0" * 64
        f.write_text(json.dumps(d))
        return names[12]

    def wrong_shape_valid_checksum(root, names):
        import hashlib
        f = root / f"{names[13]}.json"
        d = json.loads(f.read_text())
        npz = root / f"{names[13]}.npz"
        with open(npz, "wb") as fh:
            np.savez(fh, pop_logscore=np.zeros((1, 1, 1)), stab_logscore=np.zeros((1, 1, 1)),
                     pop_pit=np.zeros((1, 1, 1), dtype="float32"), stab_pit=np.zeros((1, 1, 1), dtype="float32"))
        d["npz_sha256"] = hashlib.sha256(npz.read_bytes()).hexdigest()
        f.write_text(json.dumps(d))
        return names[13]

    return [("truncated_npz", truncate_npz), ("single_bit_flip_npz", flip_byte), ("truncated_json", truncate_json),
            ("json_missing_npz_present", delete_json), ("npz_missing_json_present", delete_npz),
            ("npz_swapped_between_units", swap_npz), ("zero_length_npz", zero_npz), ("leftover_tmp_files_only", leftover_tmp),
            ("json_wrong_config_hash", edit_config_hash), ("valid_checksum_wrong_array_shape", wrong_shape_valid_checksum)]


def t_corruption_tests(ctx: Ctx, a):
    units, P = ctx.units()
    names = [P.unit_name(u) for u in units]
    ref = Path(a.ref_parent)
    results = {}
    for name, mut in corrupt_cases():
        base = ctx.work / "corruption" / name
        if base.exists():
            shutil.rmtree(base)
        shutil.copytree(ref, base / "ckpt")                    # corruption is applied to a COPY only
        root = PC.ckpt_root_for(base / "ckpt", ctx.cfg)
        before = {f.name: PC.sha256_file(f) for f in PC.ckpt_root_for(ref, ctx.cfg).glob("*")}
        hit = mut(root, names)
        info = {"unit_corrupted": hit}
        r1 = ctx.run_sync(ctx.runner("run", base / "ckpt", base / "runs", 1), base / "resume1.log", 1)
        txt = (base / "resume1.log").read_text(encoding="utf-8", errors="replace")
        info.update({"first_resume_rc": r1["rc"], "first_resume_tail": tail(base / "resume1.log", 2),
                     "refused_cleanly": "REFUSED:" in txt, "uncaught_exception": "Traceback" in txt,
                     "finished_without_error": r1["rc"] == 0})
        cm = compare_ckpt(ctx, ref, base / "ckpt")
        info["identical_after_first_resume"] = cm["identical_to_reference"]
        if r1["rc"] != 0:
            # the frozen logic never repairs a bad checkpoint: the operator removes the unit's files and resumes
            for ext in (".json", ".npz", ".npz.tmp", ".json.tmp"):
                (root / f"{hit}{ext}").unlink(missing_ok=True)
            for other in ("npz_swapped_between_units",):
                if name == other:
                    (root / f"{names[9]}.json").unlink(missing_ok=True)
                    (root / f"{names[9]}.npz").unlink(missing_ok=True)
            r2 = ctx.run_sync(ctx.runner("run", base / "ckpt", base / "runs2", 1), base / "resume2.log", 1)
            cm2 = compare_ckpt(ctx, ref, base / "ckpt")
            info.update({"remediation": "operator deleted the affected unit file(s); resumed", "second_resume_rc": r2["rc"],
                         "identical_after_remediation": cm2["identical_to_reference"]})
        info["silently_skipped"] = bool(r1["rc"] == 0 and not info["identical_after_first_resume"])
        results[name] = info
        print(f"{name}: rc={r1['rc']} clean_refusal={info['refused_cleanly']} traceback={info['uncaught_exception']} "
              f"identical_first={info['identical_after_first_resume']} identical_after_remediation="
              f"{info.get('identical_after_remediation')} silently_skipped={info['silently_skipped']}", flush=True)
    ctx.write(f"PILOT_corruption_tests_{a.tag}.json", {"results": results})
    ok = all(not r["silently_skipped"] and (r["identical_after_first_resume"] or r.get("identical_after_remediation"))
             for r in results.values())
    return 0 if ok else 1


def t_restart_emulation(ctx: Ctx, a):
    """LOCAL EMULATION of a runtime restart: kill everything mid-run, throw away the extracted code tree and every local
    process, re-extract the frozen snapshot into a NEW directory, and resume using only the checkpoint directory."""
    base = ctx.work / "restart"
    if base.exists():
        shutil.rmtree(base)
    durable = base / "durable"
    cmd = ctx.runner("run", durable, base / "runs_a", 4)
    p = PC.spawn(cmd, ctx.root, base / "a.log", 1)
    root_a = PC.ckpt_root_for(durable, ctx.cfg)
    t0 = time.time()
    while p.poll() is None and PC.count_done(root_a) < 20 and time.time() - t0 < 1500:
        time.sleep(0.2)
    PC.hard_kill(p)
    done_a = PC.count_done(root_a)
    fresh = base / "fresh_root"
    with zipfile.ZipFile(ctx.snapshot) as z:
        z.extractall(fresh)
    a2 = argparse.Namespace(frozen_root=str(fresh), snapshot=str(ctx.snapshot), manifest_sha=ctx.sha, work=str(base / "work2"),
                            durable=None)
    ctx2 = Ctx(a2)
    ctx2.log_phase("restart-emulation:resume_from_fresh_extraction", cpu_note="same machine (emulation)")
    r = ctx2.run_sync(ctx2.runner("run", durable, base / "runs_b", 2), base / "b.log", 1)
    cm = compare_ckpt(ctx, Path(a.ref_parent), durable)
    out = {"emulation_only": True, "units_done_before_kill": done_a, "resume_rc": r["rc"], "fresh_root": str(fresh),
           "comparison_with_uninterrupted_reference": cm, "resume_tail": tail(base / "b.log")}
    ctx.write("PILOT_restart_emulation.json", out)
    print(f"restart emulation: done_before_kill={done_a}; resume rc={r['rc']}; identical={cm['identical_to_reference']}")
    shutil.rmtree(fresh, ignore_errors=True)                     # an extracted snapshot (frozen docs mention the seeds)
    return 0 if r["rc"] == 0 and cm["identical_to_reference"] else 1


def child_profile(ctx: Ctx, cfg_path: Path, unit: str, out: Path, threads=None, save_ckpt=None, timeout=3600):
    cmd = [sys.executable, CHILD, "profile-unit", "--frozen-root", str(ctx.root), "--config", str(cfg_path), "--unit", unit,
           "--out", str(out)] + (["--save-ckpt", str(save_ckpt)] if save_ckpt else [])
    r = ctx.run_sync(cmd, out.with_suffix(".log"), threads, timeout)
    return json.loads(out.read_text()) if out.exists() else {"error": r, "tail": tail(out.with_suffix(".log"))}


def t_determinism(ctx: Ctx, a):
    nproc = os.cpu_count() or 1
    unit_set = ["primary,0,0,2", "primary,1,3,0", "naive,0,3,2"]
    threads = [1, 1, 2, 4, nproc]
    res = {}
    base = ctx.work / "determinism"
    for u in unit_set:
        rows = []
        for i, th in enumerate(threads):
            o = base / f"{u.replace(',', '_')}_T{th}_{i}.json"
            rows.append({"threads": th, **child_profile(ctx, ctx.root / PILOT_CFG, u, o, th)})
        ref_h = rows[0]["array_sha256"]
        res[u] = {"rows": [{k: r.get(k) for k in ("threads", "wall_s", "cpu_s")} for r in rows],
                  "all_arrays_bitwise_equal_to_first_run": all(r["array_sha256"] == ref_h and r["meta_json_sha256"] == rows[0]["meta_json_sha256"]
                                                               for r in rows)}
        # against the stored reference checkpoint
        if a.ref_parent:
            import numpy as np
            units, P = ctx.units()
            n = P.unit_name(tuple([u.split(",")[0], *map(int, u.split(",")[1:])]))
            with np.load(PC.ckpt_root_for(Path(a.ref_parent), ctx.cfg) / f"{n}.npz") as z:
                from pilot_child import array_hash
                res[u]["bitwise_equal_to_reference_checkpoint"] = all(array_hash(z[k]) == ref_h[k] for k in z.files)
        print(u, res[u]["all_arrays_bitwise_equal_to_first_run"], res[u].get("bitwise_equal_to_reference_checkpoint"), flush=True)
    # analysis pipeline (bootstrap matmul uses BLAS): synthetic data, fixed seed, different thread counts
    ana = []
    for th in (1, 1, 2, nproc):
        o = base / f"analysis_T{th}_{len(ana)}.json"
        cmd = [sys.executable, CHILD, "det-analysis", "--frozen-root", str(ctx.root), "--out", str(o), "--n-systems", "4000"]
        ctx.run_sync(cmd, o.with_suffix(".log"), th)
        ana.append({"threads": th, **(json.loads(o.read_text()) if o.exists() else {"error": tail(o.with_suffix('.log'))})})
    res["analysis_synthetic"] = {"rows": [{k: r.get(k) for k in ("threads", "seconds", "ok", "draws", "result_sha256")} for r in ana],
                                 "bitwise_equal_across_threads": len({r.get("result_sha256") for r in ana}) == 1}
    print("analysis (synthetic) bitwise equal across threads:", res["analysis_synthetic"]["bitwise_equal_across_threads"])
    ctx.write(f"PILOT_determinism_{a.tag}.json", {"thread_counts": threads, "results": res})
    return 0


def t_profile_units(ctx: Ctx, a):
    units, P = ctx.units()
    base = ctx.work / "profile"
    rows = []
    for u in units:
        s = ",".join(map(str, u))
        o = base / f"{s.replace(',', '_')}.json"
        rows.append(child_profile(ctx, ctx.root / PILOT_CFG, s, o, 1))
        r = rows[-1]
        print(f"{s}: wall {r.get('wall_s', float('nan')):.1f}s cpu {r.get('cpu_s', float('nan')):.1f}s rss {r.get('peak_rss_mb', 0):.0f}MB", flush=True)
    ctx.write(f"PILOT_unit_profile_{a.tag}.json", {"config": PILOT_CFG, "threads": 1, "rows": rows})
    return 0


def variant_cfg(ctx: Ctx, name: str, n: int, naive: int, mode="pilot") -> Path:
    import yaml
    d = yaml.safe_load((ctx.root / PILOT_CFG).read_text(encoding="utf-8"))
    d["grid"]["n_systems"], d["secondary"]["naive_n_systems"] = n, naive
    d["experiment"]["name"], d["experiment"]["mode"] = f"stage06_phase_d_{name}", mode
    p = HERE / "config" / f"PILOT_{name}.yaml"
    p.parent.mkdir(exist_ok=True)
    p.write_text(yaml.safe_dump(d, sort_keys=False), encoding="utf-8")
    return p


def t_scaling(ctx: Ctx, a):
    base = ctx.work / "scaling"
    cells_p = ["primary,0,0,2", "primary,0,1,0", "primary,0,2,1", "primary,0,3,2"]
    cells_n = ["naive,0,0,2", "naive,0,3,0"]
    rows = []
    for tag, n, k in (("N50", 50, 50), ("N100", 100, 100), ("N200", 200, 50), ("N400", 400, 400)):
        cfgp = ctx.root / PILOT_CFG if tag == "N200" else variant_cfg(ctx, tag, n, k)
        for u in cells_p + cells_n:
            o = base / f"{tag}_{u.replace(',', '_')}.json"
            r = child_profile(ctx, cfgp, u, o, 1)
            rows.append({"size": tag, "n_systems": n, "naive_n": k, **{x: r.get(x) for x in ("unit", "wall_s", "cpu_s", "peak_rss_mb",
                                                                                          "n_forecasts", "wall_s_per_forecast")}})
            print(tag, u, f"{r.get('wall_s', float('nan')):.2f}s", flush=True)
    ctx.write(f"PILOT_scaling_{a.tag}.json", {"rows": rows})
    return 0


def t_anchor(ctx: Ctx, a):
    """Real units at the CONFIRMATORY SIZE (N = 4000) on PILOT seeds only; checkpoint write/load timed and sized."""
    base = ctx.work / "anchor"
    cfgp = variant_cfg(ctx, "N4000", 4000, 4000)
    rows = []
    for u in a.units:
        o = base / f"{u.replace(',', '_')}.json"
        r = child_profile(ctx, cfgp, u, o, 1, save_ckpt=base / "ckpt", timeout=7200)
        rows.append(r)
        print(u, {k: r.get(k) for k in ("wall_s", "cpu_s", "peak_rss_mb", "ckpt_write_s", "ckpt_bytes", "ckpt_load_verify_s")}, flush=True)
    ctx.write(f"PILOT_anchor_N4000_{a.tag}.json", {"rows": rows})
    return 0


def t_size_sweep(ctx: Ctx, a):
    """Second pilot size: ALL 50 units at N = 50, through the frozen run_units() on a pilot-labelled variant config
    (the frozen CLI refuses configs that are not frozen, so the frozen function is called directly)."""
    cfgp = variant_cfg(ctx, "N50", 50, 50)
    from dynaicl.config.stage06_schema import load_stage06_config
    from dynaicl.experiments import stage06_probe as P
    cfg = load_stage06_config(cfgp)
    PC.assert_pilot_config(cfg)
    ck = ctx.work / "size_sweep_N50" / "ckpt"
    t = time.time()
    done = P.run_units(cfg, P.checkpoint_root(ck, cfg), None, a.workers)
    res = P.analyze(cfg, done)
    out = {"n_units_done": len(done), "n_units_expected": len(P.plan_units(cfg)), "wall_s": round(time.time() - t, 1),
           "analyze_pilot_mode_keys": sorted(res), "critical_check_flags": res["critical_checks"]}
    ctx.write(f"PILOT_size_sweep_N50_{a.tag}.json", out)
    print(out)
    return 0


def t_analysis_cost(ctx: Ctx, a):
    import yaml
    d = yaml.safe_load((ctx.root / PILOT_CFG).read_text(encoding="utf-8"))
    d["grid"]["n_systems"], d["secondary"]["naive_n_systems"] = 4000, 4000
    d["experiment"]["name"], d["experiment"]["mode"] = "stage06_phase_d_analysis_cost_synthetic", "test"
    p = HERE / "config" / "PILOT_analysis_cost_N4000_mode_test.yaml"
    p.write_text(yaml.safe_dump(d, sort_keys=False), encoding="utf-8")
    o = ctx.reports / f"PILOT_analysis_cost_synthetic_{a.tag}.json"
    tmp = ctx.work / "analysis_cost_tmp"
    if tmp.exists():
        shutil.rmtree(tmp)
    cmd = [sys.executable, CHILD, "analysis-cost", "--frozen-root", str(ctx.root), "--config", str(p), "--out", str(o),
           "--tmp-dir", str(tmp)]
    r = ctx.run_sync(cmd, o.with_suffix(".log"), 1, timeout=7200)
    print(r, tail(o.with_suffix(".log")))
    if o.exists():
        print(json.loads(o.read_text()))
    return 0 if o.exists() else 1


def t_storage_probe(ctx: Ctx, a):
    """Atomic-replace and throughput probe of a storage directory (e.g. a mounted Google Drive)."""
    import hashlib
    import multiprocessing as mp
    import numpy as np
    d = Path(a.dir) / f"PILOT_storage_probe_{int(time.time())}"
    d.mkdir(parents=True)
    out = {"dir": str(d)}
    rng = np.random.default_rng(62001)
    payload = [rng.random(7_490_000 // 8).tobytes() for _ in range(2)]
    digs = {hashlib.sha256(p).hexdigest() for p in payload}
    target = d / "target.bin"
    # throughput: write tmp + fsync + replace; read + sha256
    w, rd, fs, rp = [], [], [], []
    for i in range(a.repeats):
        tmp = d / "target.bin.tmp"
        t = time.perf_counter()
        with open(tmp, "wb") as fh:
            fh.write(payload[i % 2])
            fh.flush()
            t1 = time.perf_counter()
            try:
                os.fsync(fh.fileno())
                fs.append(time.perf_counter() - t1)
            except OSError as exc:
                out["fsync_error"] = repr(exc)
        t2 = time.perf_counter()
        os.replace(tmp, target)
        rp.append(time.perf_counter() - t2)
        w.append(time.perf_counter() - t)
        t = time.perf_counter()
        got = hashlib.sha256(target.read_bytes()).hexdigest()
        rd.append(time.perf_counter() - t)
        if got not in digs:
            out.setdefault("read_after_replace_mismatches", 0)
            out["read_after_replace_mismatches"] += 1
    out["throughput"] = {"payload_mb": 7.49, "write_total_s_median": statistics.median(w), "fsync_s_median": statistics.median(fs) if fs else None,
                         "replace_s_median": statistics.median(rp), "read_verify_s_median": statistics.median(rd),
                         "write_mb_per_s": 7.49 / statistics.median(w), "read_mb_per_s": 7.49 / statistics.median(rd)}
    try:
        fd = os.open(d, os.O_RDONLY)
        os.fsync(fd)
        os.close(fd)
        out["directory_fsync"] = "ok"
    except OSError as exc:
        out["directory_fsync"] = f"unsupported or failed: {exc!r}"
    # torn-read probe: a separate process reads while this process replaces the file repeatedly
    stop = mp.Event()
    q = mp.Queue()
    pr = mp.Process(target=_reader, args=(str(target), list(digs), stop, q), daemon=True)   # never outlives a crashed parent
    pr.start()
    denied = 0
    for i in range(a.repeats * 5):
        tmp = d / "target.bin.tmp"
        with open(tmp, "wb") as fh:
            fh.write(payload[i % 2])
            fh.flush()
            try:
                os.fsync(fh.fileno())
            except OSError:
                pass
        for attempt in range(2000):          # Windows refuses to replace a file another process holds open
            try:
                os.replace(tmp, target)
                break
            except PermissionError:
                denied += 1
                time.sleep(0.002)
        else:
            out["replace_gave_up"] = True
    stop.set()
    reads, torn, missing = q.get()
    pr.join()
    out["concurrent_reader"] = {"reads": reads, "torn_reads": torn, "file_missing_during_replace": missing,
                                "replacements": a.repeats * 5, "replace_denied_attempts_while_reader_open": denied}
    shutil.rmtree(d, ignore_errors=True)
    ctx.write(f"PILOT_storage_probe_{a.tag}.json", out)
    print(json.dumps(out, indent=1))
    return 0


def _reader(path, digs, stop, q):
    import hashlib
    reads = torn = missing = 0
    while not stop.is_set():
        try:
            b = Path(path).read_bytes()
        except (FileNotFoundError, PermissionError, OSError):
            missing += 1
            continue
        reads += 1
        if hashlib.sha256(b).hexdigest() not in digs:
            torn += 1
    q.put((reads, torn, missing))


def mask_seeds(text: str) -> str:
    return PC.confirmatory_seed_pattern().sub("<confirmatory-seed>", text)


def extract_copy(ctx: Ctx, name: str) -> Path:
    d = ctx.work / "throwaway" / name
    if d.exists():
        shutil.rmtree(d)
    with zipfile.ZipFile(ctx.snapshot) as z:
        z.extractall(d)
    return d


def rebuild_manifest(copy: Path) -> str:
    """Throwaway copies only: re-hash the copy's manifest so a deliberate edit passes the manifest gate and reaches the gate
    under test. NEVER used on the workspace."""
    workspace = PC._ROOT[0] or PC.HERE.parent
    if Path(copy).resolve() == Path(workspace).resolve():
        raise RuntimeError("rebuild_manifest refuses to touch the frozen workspace")
    # v2: build_manifest takes the freeze Version, the copy already holds the v2 manifest (write_manifest never overwrites, so the
    # COPY's file is removed first), and v2 hashes the v1 manifest and v1 snapshot ("supersedes"), which a snapshot extraction
    # does not contain: they are copied from the workspace into the copy's dist/ and docs/ (read-only use).
    for rel in ("dist/stage06_frozen_snapshot.zip", "docs/FREEZE_MANIFEST_STAGE06.json"):
        src, dst = Path(workspace) / rel, Path(copy) / rel
        if src.is_file() and not dst.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, dst)
    code = ("import sys; sys.path.insert(0, sys.argv[1]); from pathlib import Path; "
            "from dynaicl.experiments import stage06_freeze as F; from dynaicl.config.stage06_schema import load_stage06_config; "
            "r=Path(sys.argv[1]); v=F.VERSIONS['v2']; "
            "m=F.build_manifest(r, load_stage06_config(r/'config/stage06.yaml').tier2.stage05_run, v); "
            "(r/v.manifest).unlink(missing_ok=True); print(F.write_manifest(r, m, v.manifest)[1])")
    out = subprocess.run([sys.executable, "-c", code, str(copy)], cwd=copy, capture_output=True, text=True,
                         env=PC.child_env(copy))
    if out.returncode:
        raise RuntimeError(out.stderr)
    return out.stdout.strip().splitlines()[-1]


def stub_cmd(copy: Path, sha: str, command: str, cfg: str, ckpt: Path, runs: Path, extra=()):
    return [sys.executable, CHILD, "stub-run", "--frozen-root", str(copy), "--", command, "--config", cfg, "--manifest",
            PC.MANIFEST_REL, "--expected-manifest-sha256", sha, "--checkpoint-dir", str(ckpt), "--runs-dir", str(runs), *extra]


def t_launch_protection(ctx: Ctx, a):
    """All tests run on THROWAWAY copies with the evaluation entry points stubbed (they raise STUB_REACHED), temporary output
    directories, and the workspace untouched. This tests the guards, not the full computation path."""
    res, tmp = {}, ctx.work / "launch_protection"
    if tmp.exists():
        shutil.rmtree(tmp)
    tmp.mkdir(parents=True)

    def run(case, copy, sha, command, cfg, extra=(), ckpt=None):
        ck = ckpt or tmp / case / "ckpt"
        cmd = stub_cmd(copy, sha, command, cfg, ck, tmp / case / "runs", extra)
        r = ctx.run_sync(cmd, tmp / case / "log.txt", 1, 600)
        txt = (tmp / case / "log.txt").read_text(encoding="utf-8", errors="replace")
        outcome = ("REACHED_EVALUATION_ENTRY_POINT" if "STUB_REACHED" in txt else
                   "REFUSED" if "REFUSED:" in txt else "ERROR")
        res[case] = {"rc": r["rc"], "outcome": outcome, "message": mask_seeds(next((l for l in txt.splitlines() if "REFUSED" in l), tail(tmp / case / "log.txt", 1))[:220])}
        print(case, res[case]["outcome"], "-", res[case]["message"][:120], flush=True)

    c1 = extract_copy(ctx, "lp_base")
    # A. confirmatory `run`, correct manifest, no authorization artifact of any kind (v2: must be REFUSED before any evaluation)
    run("A_confirmatory_run_no_authorization_artifact", c1, ctx.sha, "run", "config/stage06.yaml", ("--workers", "1"))
    # A2/A3. a TEST-ONLY artifact created in the throwaway copy with the copy's own issuer and a test key. The command-line path
    # must refuse it (test-only artifact, and test key) even though it is signed correctly under that key.
    test_key = "TEST-ONLY-phase-d-throwaway-key-0001"
    art = tmp / "A2" / "test_only_artifact.json"
    art.parent.mkdir(parents=True, exist_ok=True)
    issue = [sys.executable, str(c1 / "scripts/stage06_issue_authorization.py"), "--manifest", str(c1 / PC.MANIFEST_REL), "--snapshot",
             str(ctx.snapshot), "--config", str(c1 / "config/stage06.yaml"), "--run-id", "TEST-PHASE-D-0001", "--out", str(art), "--test-only"]
    ri = subprocess.run(issue, cwd=c1, capture_output=True, text=True, env={**PC.child_env(c1), "DYNAICL_STAGE06_AUTH_KEY": test_key})
    res["A2_test_only_artifact_issued_in_throwaway_copy"] = {"rc": ri.returncode, "outcome": "ok" if ri.returncode == 0 else "ERROR",
                                                            "message": mask_seeds((ri.stdout + ri.stderr).strip().splitlines()[-1][:160])}
    for case, key in (("A2_test_only_artifact_with_its_matching_test_key", test_key), ("A3_test_only_artifact_with_another_key", "another-key-0123456789abcdefghij")):
        cmd = stub_cmd(c1, ctx.sha, "run", "config/stage06.yaml", tmp / case / "ckpt", tmp / case / "runs",
                       ("--workers", "1", "--authorization", str(art), "--snapshot", str(ctx.snapshot)))
        r = ctx.run_sync(cmd, tmp / f"{case}.log", 1, 600, env_extra={"DYNAICL_STAGE06_AUTH_KEY": key})
        txt = (tmp / f"{case}.log").read_text(encoding="utf-8", errors="replace")
        res[case] = {"rc": r["rc"], "outcome": "REACHED_EVALUATION_ENTRY_POINT" if "STUB_REACHED" in txt else ("REFUSED" if "REFUSED:" in txt else "ERROR"),
                     "message": mask_seeds(next((l for l in txt.splitlines() if "REFUSED" in l), tail(tmp / f"{case}.log", 1))[:200])}
        print(case, res[case]["outcome"], "-", res[case]["message"][:110], flush=True)
    art.unlink()
    # B. confirmatory `analyze` given PILOT output: pilot checkpoints copied under the confirmatory config-hash directory
    from dynaicl.config.stage06_schema import load_stage06_config
    conf = load_stage06_config(ctx.root / "config/stage06.yaml")
    pilot_ck = PC.ckpt_root_for(Path(a.ref_parent), ctx.cfg)
    ckB = tmp / "B_analyze_pilot_output_as_confirmatory" / "ckpt"
    shutil.copytree(pilot_ck, ckB / conf.config_hash()[:16])
    run("B_confirmatory_analyze_given_pilot_checkpoints", c1, ctx.sha, "analyze", "config/stage06.yaml", (), ckpt=ckB)
    n_copied = len(list(ckB.rglob("*.npz")))
    shutil.rmtree(ckB)                       # the 50 copied pilot files are inputs, not outputs of any guard case
    # B2. same, pilot checkpoint parent passed unchanged (confirmatory hash dir absent)
    run("B2_confirmatory_analyze_pilot_checkpoint_parent", c1, ctx.sha, "analyze", "config/stage06.yaml", (), ckpt=Path(a.ref_parent))
    # C. pilot mode with confirmatory seeds (copy edited; manifest re-hashed so the frozen-config gate passes)
    c2 = extract_copy(ctx, "lp_pilot_with_confirmatory_seeds")
    p = c2 / "config/stage06_pilot.yaml"
    roles = PC.seed_roles()
    pe, pb = roles["pilot_evaluation"]["seeds"], roles["pilot_bootstrap"]["seeds"][0]
    ce, cb = roles["confirmatory_evaluation"]["seeds"], roles["confirmatory_bootstrap"]["seeds"][0]
    p.write_text(p.read_text(encoding="utf-8").replace(f"evaluation: {pe}".replace("'", ""), f"evaluation: {ce}").replace(
        f"bootstrap: {pb}", f"bootstrap: {cb}"), encoding="utf-8")
    run("C_pilot_mode_with_confirmatory_seeds", c2, rebuild_manifest(c2), "run", "config/stage06_pilot.yaml", ("--workers", "1"))
    # D. confirmatory mode with pilot seeds
    c3 = extract_copy(ctx, "lp_confirmatory_with_pilot_seeds")
    p = c3 / "config/stage06.yaml"
    p.write_text(p.read_text(encoding="utf-8").replace(f"evaluation: {ce}", f"evaluation: {pe}").replace(
        f"bootstrap: {cb}", f"bootstrap: {pb}"), encoding="utf-8")
    run("D_confirmatory_mode_with_pilot_seeds", c3, rebuild_manifest(c3), "run", "config/stage06.yaml", ("--workers", "1"))
    # E. confirmatory run without manifest arguments
    cmd = [sys.executable, CHILD, "stub-run", "--frozen-root", str(c1), "--", "run", "--config", "config/stage06.yaml",
           "--checkpoint-dir", str(tmp / "E" / "ckpt"), "--runs-dir", str(tmp / "E" / "runs")]
    r = ctx.run_sync(cmd, tmp / "E.log", 1, 600)
    txt = (tmp / "E.log").read_text(encoding="utf-8", errors="replace")
    res["E_confirmatory_run_without_manifest_arguments"] = {"rc": r["rc"], "outcome": "REFUSED" if "REFUSED" in txt else
                                                           ("REACHED_EVALUATION_ENTRY_POINT" if "STUB_REACHED" in txt else "ERROR"),
                                                           "message": mask_seeds(tail(tmp / "E.log", 1)[:200])}
    print("E", res["E_confirmatory_run_without_manifest_arguments"]["outcome"])
    # F. entry-point audit (static)
    probe = (c1 / "dynaicl/experiments/stage06_probe.py").read_text(encoding="utf-8")
    audit = {"argparse_flags": sorted(set(re.findall(r'add_argument\("(--[a-z0-9-]+)"', probe))),
             "os_environ_reads": re.findall(r"os\.environ[^\n]*", probe),
             "mentions_authorization": bool(re.search(r"authori[sz]", probe, re.I)),
             "run_kind_field_in_checkpoints": '"run_kind"' in probe,
             "checkpoints_bound_to": ["config_hash (differs between pilot and confirmatory: mode is part of the config)",
                                      "manifest_sha256", "unit identity", "schema version", "array shapes/dtypes", "npz SHA-256"]}
    res["F_entry_point_audit"] = audit
    # confirm no real data was produced by any case
    produced = [str(p) for p in tmp.rglob("*.npz")]
    res["no_unit_checkpoints_written_by_any_case"] = not produced
    res["pilot_checkpoint_files_copied_as_input_to_case_B"] = n_copied
    ctx.write("PILOT_launch_protection.json", {"results": res, "note": "guards tested on throwaway copies with stubbed evaluation; "
                                               "this does not test the full computation path"})
    print("npz written by guard tests:", produced)
    shutil.rmtree(tmp, ignore_errors=True)                       # stub logs and edited copies contain seed numbers by design
    shutil.rmtree(ctx.work / "throwaway", ignore_errors=True)
    return 0


def t_qualification_gate(ctx: Ctx, a):
    """On a throwaway copy whose frozen environment manifest is edited to differ from this machine (manifest re-hashed in the
    COPY), run the frozen `qualify` for real, then test acceptance and refusals of the qualification mechanism."""
    base = ctx.work / "qualification_gate"
    if base.exists():
        shutil.rmtree(base)
    copy = extract_copy(ctx, "qg")
    envp = copy / "docs/STAGE06_ENVIRONMENT_MANIFEST.json"
    j = json.loads(envp.read_text(encoding="utf-8"))
    j["environment"]["numpy"] = "0.0.0-simulated-difference"
    envp.write_text(json.dumps(j), encoding="utf-8")
    sha = rebuild_manifest(copy)
    res = {"note": "copy-only: simulated environment difference; the real checks inside `qualify` are executed"}

    def runner(cfg, qual=None, command="verify"):
        cmd = PC.runner_cmd(copy, command, cfg, sha, qualification=qual)
        r = subprocess.run(cmd, cwd=copy, capture_output=True, text=True, env=PC.child_env(copy))
        txt = r.stdout + r.stderr
        return {"rc": r.returncode, "outcome": "accepted" if r.returncode == 0 else ("REFUSED" if "REFUSED" in txt else "ERROR"),
                "message": next((l for l in txt.splitlines() if "REFUSED" in l or "pre-flight" in l), txt.strip()[-160:])[:230]}
    res["no_report"] = runner("config/stage06_pilot.yaml")
    q = base / "qual_pilot.json"
    t = time.time()
    cmd = PC.runner_cmd(copy, "qualify", "config/stage06_pilot.yaml", sha, extra=["--out", str(q)])
    subprocess.run(cmd, cwd=copy, capture_output=True, text=True, env=PC.child_env(copy))
    res["qualify_seconds"] = round(time.time() - t, 1)
    rep = json.loads(q.read_text())
    res["report_passed"] = rep["passed"]
    res["valid_report"] = runner("config/stage06_pilot.yaml", q)
    other_cfg = runner("config/stage06.yaml", q)                       # report bound to the pilot config, used for the other config
    res["report_for_other_config_stale"] = other_cfg
    stale = dict(rep, manifest_sha256="1" * 64)
    (base / "stale_manifest.json").write_text(json.dumps(stale))
    res["report_bound_to_other_manifest"] = runner("config/stage06_pilot.yaml", base / "stale_manifest.json")
    other_env = dict(rep, environment={**rep["environment"], "machine": "other-machine"})
    (base / "other_env.json").write_text(json.dumps(other_env))
    res["report_bound_to_other_environment"] = runner("config/stage06_pilot.yaml", base / "other_env.json")
    failed = dict(rep, passed=False)
    (base / "failed.json").write_text(json.dumps(failed))
    res["report_failed"] = runner("config/stage06_pilot.yaml", base / "failed.json")
    res["report_missing_path"] = runner("config/stage06_pilot.yaml", base / "does_not_exist.json")
    ctx.write("PILOT_qualification_gate.json", res)
    for k, v in res.items():
        if isinstance(v, dict) and "outcome" in v:
            print(k, v["outcome"], "-", v["message"][:110])
    shutil.rmtree(base, ignore_errors=True)
    shutil.rmtree(ctx.work / "throwaway", ignore_errors=True)
    return 0


def t_completeness(ctx: Ctx, a):
    import numpy as np
    units, P = ctx.units()
    cfg = ctx.cfg
    ck = PC.ckpt_root_for(Path(a.ref_parent), cfg)
    H, ns, N = len(cfg.grid.horizons), len(cfg.grid.context_lengths), cfg.grid.n_systems
    exp = {"units": 2 + 24 + 24, "primary_units": 24, "naive_units": 24,
           "primary_items_per_array": H * ns * N, "naive_items_per_array": len(P.naive_members(cfg)) * H * len(cfg.secondary.naive_context_lengths) * cfg.secondary.naive_n_systems}
    got = {"unit_json": len(list(ck.glob("*.json"))), "unit_npz": len(list(ck.glob("*.npz")))}
    bad, nonfinite, total, pit_out = [], 0, 0, 0
    names = [P.unit_name(u) for u in units]
    dup_names = len(names) - len(set(names))
    for u in units:
        try:
            rec, arrays = P.load_unit(ck, u, cfg, PC.integrity_snapshot(ctx.root, ctx.snapshot, ctx.sha, "x", None)["manifest_sha256"])
        except Exception as exc:
            bad.append((P.unit_name(u), repr(exc)[:120]))
            continue
        for k, v in arrays.items():
            total += v.size
            nonfinite += int((~np.isfinite(v)).sum())
            if k.endswith("pit"):
                pit_out += int(((v < 0) | (v > 1)).sum())
    cells_seen = {(u[1], u[2], u[3]) for u in units if u[0] == "primary"}
    cells_expected = {(rep, qi, ri) for rep in range(2) for qi in range(len(cfg.model.noise_ratios))
                      for ri in range(len(cfg.model.initial_state_ratios))}
    out = {"expected": exp, "found": got, "units_failed_frozen_load_verify": bad, "duplicate_unit_names": dup_names,
           "array_elements_checked": total, "non_finite_elements": nonfinite, "pit_outside_0_1": pit_out,
           "primary_cells_present": sorted(cells_seen) == sorted(cells_expected),
           "context_lengths": [cfg.grid.context_lengths[0], cfg.grid.context_lengths[-1], len(cfg.grid.context_lengths)],
           "horizons": list(cfg.grid.horizons), "noise_ratios": list(cfg.model.noise_ratios),
           "initial_state_ratios": list(cfg.model.initial_state_ratios)}
    out["complete"] = (got["unit_json"] == exp["units"] and got["unit_npz"] == exp["units"] and not bad and dup_names == 0
                       and nonfinite == 0 and pit_out == 0 and out["primary_cells_present"])
    ctx.write(f"PILOT_completeness_{a.tag}.json", out)
    print({k: out[k] for k in ("found", "duplicate_unit_names", "array_elements_checked", "non_finite_elements", "pit_outside_0_1",
                               "primary_cells_present", "complete")}, "units failing frozen load/verify:", len(bad))
    return 0 if out["complete"] else 1


def t_structural_analysis(ctx: Ctx, a):
    """The FROZEN analysis pipeline (P.analyze, full non-pilot branch) on the PILOT per-item outputs, bootstrap seed 62999.
    The config variant has mode 'test' only so analyze() takes the full branch; seeds are the pilot seeds. Gain estimates,
    intervals and labels go to a pilot-labelled file that this script never prints or summarises."""
    import yaml
    from dynaicl.config.stage06_schema import load_stage06_config
    from dynaicl.experiments import stage06_probe as P
    d = yaml.safe_load((ctx.root / PILOT_CFG).read_text(encoding="utf-8"))
    d["experiment"]["mode"], d["experiment"]["name"] = "test", "stage06_phase_d_structural_analysis"
    p = HERE / "config" / "PILOT_structural_analysis_mode_test.yaml"
    p.write_text(yaml.safe_dump(d, sort_keys=False), encoding="utf-8")
    cfg = load_stage06_config(p)
    PC.assert_pilot_config(cfg)
    assert cfg.seeds.bootstrap == 62999
    pilot_cfg = ctx.cfg
    ck = PC.ckpt_root_for(Path(a.ref_parent), pilot_cfg)
    done = {u: P.load_unit(ck, u, pilot_cfg, PC.integrity_snapshot(ctx.root, ctx.snapshot, ctx.sha, "x", None)["manifest_sha256"])
            for u in P.plan_units(pilot_cfg)}
    t = time.perf_counter()
    status, err = "success", None
    try:
        res = P.analyze(cfg, done)
    except Exception as exc:                 # reported structurally; no data-dependent detail is printed
        status, err, res = "exception", type(exc).__name__, {}
    secs = time.perf_counter() - t
    ef = HERE / "PILOT_ONLY_do_not_open_effects.json"
    ef.write_text(json.dumps({"run_kind": PC.RUN_KIND, "WARNING": "pilot effect estimates; never use for design decisions",
                              "analysis": res}, default=str), encoding="utf-8")
    reps = res.get("replicates", [])
    contrasts = [c for r in reps for c in r.get("contrasts", [])]
    finite = sum(all(map(lambda x: x == x and abs(x) != float("inf"), (c["estimate"], c["se"], c["lo"], c["hi"]))) for c in contrasts)
    struct = {"execution": status, "exception_type": err, "seconds": round(secs, 2), "replicates": len(reps),
              "replicates_with_ok_flag": sum(bool(r.get("ok")) for r in reps), "contrast_rows": len(contrasts),
              "contrast_rows_all_finite": finite, "has_decision_block": "decision" in res, "has_tier2_block": "tier2" in res,
              "n_curve_rows": len(res.get("n_curves", [])), "naive_secondary_rows": len(res.get("naive_secondary", [])),
              "bootstrap_seed_used": cfg.seeds.bootstrap, "effects_written_to": str(ef.name)}
    ctx.write(f"PILOT_structural_analysis_{a.tag}.json", struct)
    print(json.dumps(struct, indent=1))
    return 0


def t_seed_search(ctx: Ctx, a):
    seeds = tuple(str(x) for x in PC.confirmatory_seeds())
    pat = PC.confirmatory_seed_pattern()
    hits, scanned = [], 0
    for d in a.dirs:
        for f in Path(d).rglob("*"):
            if not f.is_file():
                continue
            scanned += 1
            if f.suffix == ".npz":
                try:
                    with zipfile.ZipFile(f) as z:
                        members = z.namelist()
                    if any(pat.search(m) for m in members):
                        hits.append(str(f))
                except zipfile.BadZipFile:                     # deliberately corrupted copies: scan the raw bytes instead
                    if pat.search(f.read_bytes().decode("latin-1")):
                        hits.append(str(f))
                continue
            try:
                txt = f.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            if pat.search(txt) or pat.search(f.name):
                hits.append(str(f))
    ctx.write(f"PILOT_seed_search_{a.tag}.json", {"seeds_searched": seeds, "dirs": list(a.dirs), "files_scanned": scanned,
                                                  "files_with_a_whole_token_match": hits})
    print(f"files scanned: {scanned}; whole-token matches for {seeds}: {len(hits)}", hits[:5])
    return 0 if not hits else 3


def t_restart_part_a(ctx: Ctx, a):
    """COLAB runtime-restart test, part A: start the frozen pilot run on DURABLE storage and wait until >= 20 units are saved.
    Then the USER disconnects/deletes the runtime (or restarts the session) while this cell is still running."""
    base = (ctx.durable or ctx.work) / "restart_colab"
    if base.exists():
        raise SystemExit(f"{base} exists; remove it to repeat the test")
    durable = base / "durable"
    ctx.log_phase("restart-colab:part_a_start", workers=a.workers)
    p = PC.spawn(ctx.runner("run", durable, base / "runs_a", a.workers), ctx.root, base / "a.log", 1)
    root = PC.ckpt_root_for(durable, ctx.cfg)
    t0 = time.time()
    while p.poll() is None and time.time() - t0 < 3000:
        n = PC.count_done(root)
        if n != getattr(t_restart_part_a, "_last", -1):
            t_restart_part_a._last = n
            print(f"units saved to durable storage: {n}/50", flush=True)
        if n >= 20:
            print("READY: now do Runtime -> Disconnect and delete runtime (or restart the session). "
                  "This cell will not finish by itself.", flush=True)
            time.sleep(1500)
            break
        time.sleep(1)
    return 0


def t_restart_part_b(ctx: Ctx, a):
    """COLAB runtime-restart test, part B: after the restart, resume from durable storage only and compare."""
    base = (ctx.durable or ctx.work) / "restart_colab"
    durable = base / "durable"
    root = PC.ckpt_root_for(durable, ctx.cfg)
    before = PC.count_done(root)
    leftovers = sorted(f.name for f in root.glob("*.tmp")) if root.exists() else []
    ctx.log_phase("restart-colab:part_b_resume", units_found=before)
    r = ctx.run_sync(ctx.runner("run", durable, base / "runs_b", a.workers), base / "b.log", 1)
    cm = compare_ckpt(ctx, Path(a.ref_parent), durable)
    out = {"units_found_after_restart": before, "stale_tmp_files_found": leftovers, "resume_rc": r["rc"],
           "comparison_with_uninterrupted_reference": cm, "resume_tail": tail(base / "b.log")}
    ctx.write(f"PILOT_restart_colab_{a.tag}.json", out)
    print(f"found {before}/50 units after the restart; resume rc={r['rc']}; identical to the uninterrupted reference: "
          f"{cm['identical_to_reference']}")
    return 0 if r["rc"] == 0 and cm["identical_to_reference"] else 1


def t_compare_refs(ctx: Ctx, a):
    """Worker-count / execution-order independence: two completed uninterrupted runs must be bitwise identical."""
    r = compare_ckpt(ctx, Path(a.ref_parent), Path(a.other_parent))
    ctx.write(f"PILOT_worker_count_independence_{a.tag}.json", {"reference_vs_other": r})
    print({k: (v if not isinstance(v, list) or len(v) < 4 else f"{len(v)} items") for k, v in r.items()})
    return 0 if r["identical_to_reference"] else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("task")
    ap.add_argument("--frozen-root", required=True)
    ap.add_argument("--snapshot", required=True)
    ap.add_argument("--manifest-sha", required=True)
    ap.add_argument("--work", default=str(HERE / PC.WORK_NAME))
    ap.add_argument("--durable")
    ap.add_argument("--tag", default="local")
    ap.add_argument("--label", default="check")
    ap.add_argument("--workers", type=int, default=1)
    ap.add_argument("--threads", type=int, default=1)
    ap.add_argument("--qualification")
    ap.add_argument("--ref-parent")
    ap.add_argument("--other-parent")
    ap.add_argument("--only", nargs="*")
    ap.add_argument("--units", nargs="*", default=["primary,0,0,2", "primary,0,3,0"])
    ap.add_argument("--dir")
    ap.add_argument("--dirs", nargs="*")
    ap.add_argument("--repeats", type=int, default=20)
    a = ap.parse_args()
    ctx = Ctx(a)
    fn = {"integrity": t_integrity, "env": t_env, "ref-run": t_ref_run, "interrupt-tests": t_interrupt_tests,
          "corruption-tests": t_corruption_tests, "restart-emulation": t_restart_emulation, "determinism": t_determinism,
          "profile-units": t_profile_units, "scaling": t_scaling, "anchor": t_anchor, "size-sweep": t_size_sweep,
          "analysis-cost": t_analysis_cost, "storage-probe": t_storage_probe, "launch-protection": t_launch_protection,
          "qualification-gate": t_qualification_gate, "completeness": t_completeness,
          "structural-analysis": t_structural_analysis, "seed-search": t_seed_search,
          "restart-part-a": t_restart_part_a, "restart-part-b": t_restart_part_b,
          "compare-refs": t_compare_refs}[a.task]
    return fn(ctx, a)


if __name__ == "__main__":
    raise SystemExit(main())
