"""PHASE D (PILOT) helpers. NOT part of the frozen file set. Pilot seeds only.

Everything here imports the FROZEN package from ``--frozen-root`` (the workspace, or a directory extracted from the frozen
snapshot, e.g. on Colab) and never edits it. No confirmatory seed (the values live only in the seed-role table) may be used by any pilot tool:
``assert_pilot_config`` refuses a config whose seeds are not exactly the pilot allocation.
"""

from __future__ import annotations

import hashlib
import json
import os
import platform
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

RUN_KIND = "PILOT"
PILOT_EVAL = (62001, 62101)
PILOT_BOOT = 62999
_ROOT = [None]
FREEZE_VERSION = "v2"
MANIFEST_REL = "docs/FREEZE_MANIFEST_STAGE06_v2.json"
SNAPSHOT_NAME = "stage06_frozen_snapshot_v2.zip"
WORK_NAME = "work_v2"
HERE = Path(__file__).resolve().parent


def seed_roles() -> dict:
    """The seed-role table of the frozen tree (single source of truth)."""
    import yaml
    root = _ROOT[0] or HERE.parent
    return yaml.safe_load((root / "config" / "stage06_seed_manifest.yaml").read_text(encoding="utf-8"))["roles"]


def confirmatory_seeds() -> tuple:
    r = seed_roles()
    return tuple(r["confirmatory_evaluation"]["seeds"]) + tuple(r["confirmatory_bootstrap"]["seeds"])


def confirmatory_seed_pattern():
    import re
    return re.compile(r"(?<![\d.])(?:" + "|".join(str(x) for x in confirmatory_seeds()) + r")(?![\d])")


def sha256_file(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def use_frozen_root(root) -> Path:
    root = Path(root).resolve()
    _ROOT[0] = root
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    return root


def assert_pilot_config(cfg) -> None:
    """Refuse anything that is not a pilot-seeded config. Called by every harness entry that builds data."""
    seeds = list(cfg.seeds.evaluation) + [cfg.seeds.bootstrap]
    if set(seeds) & set(confirmatory_seeds()):
        raise SystemExit(f"REFUSED: confirmatory seed in {seeds}")
    if tuple(cfg.seeds.evaluation) != PILOT_EVAL or cfg.seeds.bootstrap != PILOT_BOOT:
        raise SystemExit(f"REFUSED: seeds {seeds} are not the pilot allocation {PILOT_EVAL}, {PILOT_BOOT}")


# ------------------------------------------------------------------------------------------ integrity


def integrity_snapshot(root: Path, snapshot: Path, expected_manifest_sha: str, label: str, log: Path | None) -> dict:
    """SHA-256 of the frozen manifest, snapshot archive, pre-registration and confirmatory/pilot configs; all manifest
    files re-hashed; snapshot members compared with the manifest. ok = every comparison equals."""
    import zipfile
    man_path = root / MANIFEST_REL
    man = json.loads(man_path.read_text(encoding="utf-8"))
    out = {"label": label, "utc": utc_now(), "manifest_sha256": sha256_file(man_path),
           "manifest_matches_expected": sha256_file(man_path) == expected_manifest_sha,
           "snapshot_sha256": sha256_file(snapshot), "prereg_sha256": sha256_file(root / "docs/PREREG_stage06.md"),
           "config_confirmatory_sha256": sha256_file(root / "config/stage06.yaml"),
           "config_pilot_sha256": sha256_file(root / "config/stage06_pilot.yaml"),
           "amendment_sha256": sha256_file(root / "docs/PREREG_stage06_AMENDMENT_1.md")}
    bad = [k for k, v in man["files"].items() if not (root / k).is_file() or sha256_file(root / k) != v]
    with zipfile.ZipFile(snapshot) as z:
        badz = [k for k, v in man["files"].items() if hashlib.sha256(z.read(k)).hexdigest() != v]
        zip_ok = z.testzip() is None
    out.update({"manifest_files": len(man["files"]), "workspace_file_mismatches": bad, "snapshot_member_mismatches": badz,
                "snapshot_zip_ok": zip_ok})
    out["ok"] = bool(out["manifest_matches_expected"] and not bad and not badz and zip_ok)
    if log is not None:
        log.parent.mkdir(parents=True, exist_ok=True)
        with open(log, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(out, sort_keys=True) + "\n")
    return out


# ------------------------------------------------------------------------------------------ environment


def cpu_model() -> str:
    try:
        if os.name == "nt":
            out = subprocess.run(["powershell", "-NoProfile", "-Command",
                                  "(Get-CimInstance Win32_Processor | Select-Object -First 1).Name"],
                                 capture_output=True, text=True, timeout=30).stdout.strip()
            return out or platform.processor()
        for line in Path("/proc/cpuinfo").read_text().splitlines():
            if line.lower().startswith("model name"):
                return line.split(":", 1)[1].strip()
    except Exception as exc:  # recorded, not fatal
        return f"unavailable: {exc}"
    return platform.processor()


def total_ram_bytes() -> int | None:
    try:
        if os.name == "nt":
            import ctypes

            class MEMSTAT(ctypes.Structure):
                _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                            ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                            ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                            ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                            ("sullAvailExtendedVirtual", ctypes.c_ulonglong)]
            m = MEMSTAT()
            m.dwLength = ctypes.sizeof(MEMSTAT)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
            return int(m.ullTotalPhys)
        for line in Path("/proc/meminfo").read_text().splitlines():
            if line.startswith("MemTotal"):
                return int(line.split()[1]) * 1024
    except Exception:
        return None
    return None


def available_ram_bytes() -> int | None:
    try:
        if os.name == "nt":
            import ctypes

            class MEMSTAT(ctypes.Structure):
                _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                            ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                            ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                            ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                            ("sullAvailExtendedVirtual", ctypes.c_ulonglong)]
            m = MEMSTAT()
            m.dwLength = ctypes.sizeof(MEMSTAT)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
            return int(m.ullAvailPhys)
        for line in Path("/proc/meminfo").read_text().splitlines():
            if line.startswith("MemAvailable"):
                return int(line.split()[1]) * 1024
    except Exception:
        return None
    return None


def peak_rss_bytes() -> int | None:
    """Peak resident set of THIS process (Linux: ru_maxrss; Windows: PeakWorkingSetSize)."""
    try:
        if os.name == "nt":
            import ctypes
            from ctypes import wintypes

            class PMC(ctypes.Structure):
                _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD),
                            ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
                            ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
                            ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                            ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t)]
            pmc = PMC()
            pmc.cb = ctypes.sizeof(PMC)
            k32 = ctypes.WinDLL("kernel32")
            psapi = ctypes.WinDLL("psapi")
            k32.GetCurrentProcess.restype = wintypes.HANDLE
            psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(PMC), wintypes.DWORD]
            psapi.GetProcessMemoryInfo.restype = wintypes.BOOL
            if not psapi.GetProcessMemoryInfo(k32.GetCurrentProcess(), ctypes.byref(pmc), pmc.cb):
                return None
            return int(pmc.PeakWorkingSetSize)
        import resource
        return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss) * 1024
    except Exception:
        return None


def gpu_present() -> dict:
    found = {"nvidia_smi_on_path": shutil.which("nvidia-smi") is not None, "proc_nvidia": Path("/proc/driver/nvidia").exists(),
             "dev_nvidia0": Path("/dev/nvidia0").exists(), "CUDA_VISIBLE_DEVICES": os.environ.get("CUDA_VISIBLE_DEVICES")}
    found["any_gpu_detected"] = bool(found["nvidia_smi_on_path"] or found["proc_nvidia"] or found["dev_nvidia0"])
    return found


def blas_info() -> dict:
    import numpy as np
    import scipy
    info = {}
    for name, mod in (("numpy", np), ("scipy", scipy)):
        try:
            cfg = mod.show_config(mode="dicts")
            info[name] = {"blas": cfg.get("Build Dependencies", {}).get("blas", {}),
                          "lapack": cfg.get("Build Dependencies", {}).get("lapack", {}),
                          "simd": cfg.get("SIMD Extensions", {})}
        except Exception as exc:
            info[name] = f"unavailable: {exc}"
    info["thread_env"] = {k: os.environ.get(k) for k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
                                                         "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS")}
    # loaded native libraries (runtime thread pools), best effort without extra dependencies
    libs = []
    try:
        if os.name == "nt":
            import ctypes
            from ctypes import wintypes
            psapi = ctypes.windll.psapi
            arr = (wintypes.HMODULE * 1024)()
            need = wintypes.DWORD()
            psapi.EnumProcessModules(ctypes.windll.kernel32.GetCurrentProcess(), arr, ctypes.sizeof(arr), ctypes.byref(need))
            buf = ctypes.create_unicode_buffer(512)
            for i in range(need.value // ctypes.sizeof(wintypes.HMODULE)):
                psapi.GetModuleFileNameExW(ctypes.windll.kernel32.GetCurrentProcess(), arr[i], buf, 512)
                if any(t in buf.value.lower() for t in ("blas", "lapack", "mkl", "omp")):
                    libs.append(buf.value)
        else:
            for line in Path("/proc/self/maps").read_text().splitlines():
                p = line.split()[-1]
                if any(t in p.lower() for t in ("blas", "lapack", "mkl", "gomp", "omp")) and p not in libs:
                    libs.append(p)
    except Exception as exc:
        libs.append(f"unavailable: {exc}")
    info["loaded_native_math_libraries"] = libs
    return info


def environment_report(root: Path, durable_dir: Path | None = None) -> dict:
    import numpy as np
    from importlib import metadata
    frozen = json.loads((root / "docs/STAGE06_ENVIRONMENT_MANIFEST.json").read_text(encoding="utf-8"))
    sys.path.insert(0, str(root))
    from dynaicl.experiments.stage06_probe import current_environment, ENV_KEYS
    cur = current_environment()
    diffs = {k: [frozen["environment"].get(k), cur.get(k)] for k in ENV_KEYS if frozen["environment"].get(k) != cur.get(k)}
    pins = {}
    for line in (root / "requirements.txt").read_text().splitlines():
        if "==" in line:
            n, v = line.strip().split("==")
            try:
                got = metadata.version(n)
            except metadata.PackageNotFoundError:
                got = None
            pins[n] = {"pinned": v, "installed": got, "match": got == v}
    cur_pip = subprocess.run([sys.executable, "-m", "pip", "freeze"], capture_output=True, text=True, timeout=180)
    cur_set = set(cur_pip.stdout.split()) if cur_pip.returncode == 0 else set()
    frozen_set = set(frozen.get("pip_freeze") or [])
    fz = {x.split("==")[0].lower(): x for x in frozen_set if "==" in x}
    cr = {x.split("==")[0].lower(): x for x in cur_set if "==" in x}
    pip_diff = {"only_in_frozen_manifest": sorted(fz[k] for k in fz.keys() - cr.keys()),
                "only_in_current": sorted(cr[k] for k in cr.keys() - fz.keys()),
                "version_differs": sorted(f"{fz[k]} -> {cr[k]}" for k in fz.keys() & cr.keys() if fz[k] != cr[k])}
    disk = {}
    for name, p in (("repo", root), ("durable", durable_dir)):
        if p is not None and Path(p).exists():
            u = shutil.disk_usage(p)
            disk[name] = {"path": str(p), "total_gb": round(u.total / 1e9, 2), "free_gb": round(u.free / 1e9, 2)}
    return {"run_kind": RUN_KIND, "utc": utc_now(), "environment_fingerprint": cur,
            "frozen_environment_fingerprint": frozen["environment"], "fingerprint_differences": diffs,
            "requirements_pins": pins, "pip_freeze_differences": {k: len(v) for k, v in pip_diff.items()},
            "pip_freeze_difference_detail": pip_diff, "python_full": sys.version, "platform": platform.platform(),
            "os": {"system": platform.system(), "release": platform.release(), "machine": platform.machine()},
            "cpu_model": cpu_model(), "cpu_count_logical": os.cpu_count(),
            "cpu_count_affinity": len(os.sched_getaffinity(0)) if hasattr(os, "sched_getaffinity") else None,
            "ram_total_gb": round((total_ram_bytes() or 0) / 1e9, 2), "ram_available_gb": round((available_ram_bytes() or 0) / 1e9, 2),
            "disk": disk, "gpu": gpu_present(), "blas": blas_info(),
            "float64": {"numpy_default_float": str(np.zeros(1).dtype), "numpy_finfo_eps": float(np.finfo(float).eps)}}


# ------------------------------------------------------------------------------------------ processes


def runner_cmd(root: Path, command: str, config: str, manifest_sha: str, ckpt: Path | None = None, runs: Path | None = None,
               workers: int | None = None, qualification: Path | None = None, extra=()) -> list[str]:
    cmd = [sys.executable, "-m", "dynaicl.experiments.stage06_probe", command, "--config", config, "--manifest", MANIFEST_REL,
           "--expected-manifest-sha256", manifest_sha]
    if qualification:
        cmd += ["--qualification", str(qualification)]
    if ckpt is not None:
        cmd += ["--checkpoint-dir", str(ckpt)]
    if runs is not None:
        cmd += ["--runs-dir", str(runs)]
    if workers is not None:
        cmd += ["--workers", str(workers)]
    return cmd + list(extra)


def child_env(root: Path, threads: int | None = None) -> dict:
    env = {**os.environ, "PYTHONPATH": str(root)}
    if threads is not None:
        for k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
            env[k] = str(threads)
    return env


def spawn(cmd, root: Path, log: Path, threads: int | None = None, env_extra: dict | None = None) -> subprocess.Popen:
    log.parent.mkdir(parents=True, exist_ok=True)
    kw = {"start_new_session": True} if os.name != "nt" else {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP}
    env = child_env(root, threads)
    env.update(env_extra or {})
    return subprocess.Popen(cmd, cwd=root, env=env, stdout=open(log, "ab"), stderr=subprocess.STDOUT, **kw)


def hard_kill(proc: subprocess.Popen) -> None:
    """SIGKILL analogue for the whole process tree (Linux: SIGKILL to the process group; Windows: taskkill /F /T)."""
    if os.name == "nt":
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)], capture_output=True)
    else:
        os.killpg(proc.pid, signal.SIGKILL)
    proc.wait()


def count_done(ckpt_root: Path) -> int:
    return len(list(Path(ckpt_root).glob("*.json"))) if Path(ckpt_root).exists() else 0


def ckpt_root_for(ckpt_parent: Path, cfg) -> Path:
    return Path(ckpt_parent) / cfg.config_hash()[:16]
