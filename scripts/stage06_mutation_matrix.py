"""Stage 0.6 full mutation matrix on a COPY of the implementation (user decision 11c).

    python scripts/stage06_mutation_matrix.py [--workers 8] [--copy-dir DIR]  -> docs/STAGE06_MUTATION_MATRIX_v2.md (+ .json)
    (v2 freeze: versioned outputs, so the v1 matrix evidence is preserved untouched)

1. SHA-256 of every code / test / config file in the workspace (the set that will be frozen).
2. A copy of the repository is made in a scratch directory; every job runs with that copy first on sys.path and as its
   working directory. Mutations are in-memory patches of module attributes inside the job's process; no file is edited.
3. Baseline job: every intended detector must PASS without mutation.
4. One job per mutation: the PRIMARY intended detector must return a clean FAIL (the check ran and reported
   passed = False). An exception (ERROR) does not count as a kill. Auxiliary detectors are reported, not required.
5. Afterwards the hashes of the workspace files and of the copy are recomputed and must equal step 1.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dynaicl.experiments.stage06_freeze import code_files  # noqa: E402
from dynaicl.provenance import sha256_file  # noqa: E402

# mutation -> (primary detector, auxiliary detectors). Detector keys: V* of checks_stage06 or checks_stage06_analysis.
PLAN = {
    "omit_target_noise_variance": ("V2", ("V7",)),
    "wrong_sigma_v_in_reference": ("V7", ("V11",)),
    "prior_mismatch_in_reference": ("V7", ("V11",)),
    "latent_state_passed_to_predictor": ("V12", ()),
    "off_by_one_context_length": ("V12", ()),
    "off_by_one_target_index": ("V12", ()),
    "noise_naive_mislabeled_as_noise_aware": ("V11", ("V7",)),
    "l_region_off_by_one": ("V20", ("V21",)),
    "increment_wrong_baseline": ("V20", ()),
    "items_as_independent_units": ("V21", ()),
    "independent_indices_per_contrast": ("V21", ()),
    "pointwise_critical_value": ("V21", ()),
    "unstudentized_max_statistic": ("V21", ()),
    "bootstrap_failures_dropped": ("V21", ()),
    "go_single_replicate": ("V22", ()),
    "go_non_adjacent_pairs": ("V22", ()),
    "go_ignores_increment": ("V22", ()),
    "go_one_scale": ("V22", ()),
    "stop_single_replicate": ("V22", ()),
    "negative_gain_not_blocked": ("V22", ()),
    "missing_cell_not_blocked": ("V22", ()),
    "gain_flag_uses_upper_bound": ("V22", ()),
    "tier2_unadjusted_cutoff": ("V23", ()),
    "tier2_uninformative_as_pass": ("V23", ()),
    "manifest_file_hashes_not_checked": ("V24", ()),
    "checkpoint_checksum_not_checked": ("V24", ()),
    "seed_collision_not_checked": ("V24", ()),
    "environment_difference_ignored": ("V24", ()),
    # v2 freeze: authorization gate, refusal handling, seed roles
    "skip_hash_comparison": ("V25", ()), "ignore_mode": ("V25", ()), "accept_subset_of_seeds": ("V25", ()),
    "accept_expired": ("V25", ()), "accept_test_keys": ("V25", ()), "skip_reverification_on_resume": ("V25", ()),
    "reread_artifact_after_check": ("V25", ()), "run_lock_not_enforced": ("V25", ()), "env_var_disables_gate": ("V25", ()),
    "unit_json_error_uncaught": ("V26", ("V27",)), "unit_record_checksum_skipped": ("V26", ("V27",)),
    "seed_roles_not_enforced": ("V28", ()),
}

JOB = r"""
import json, sys, time, traceback
sys.path.insert(0, {copy!r})
from dynaicl.validation import checks_stage06 as C, checks_stage06_analysis as CA, checks_stage06_gate as CG
from dynaicl.validation.mutations_stage06 import MUTATIONS_STAGE06
from dynaicl.validation.mutations_stage06_analysis import MUTATIONS_STAGE06_ANALYSIS
from dynaicl.validation.mutations_stage06_gate import MUTATIONS_STAGE06_GATE
import dynaicl
assert dynaicl.__file__.startswith({copy!r}), dynaicl.__file__
checks = {{**C.ALL_CHECKS_STAGE06, **CA.ALL_CHECKS_STAGE06_ANALYSIS, **CG.ALL_CHECKS_STAGE06_GATE}}
muts = {{**MUTATIONS_STAGE06, **MUTATIONS_STAGE06_ANALYSIS, **MUTATIONS_STAGE06_GATE}}
name, keys = {name!r}, {keys!r}

def safe(check):
    t0 = time.time()
    try:
        r = check()
        status = "pass" if r.passed else "FAIL"
        failed = list(r.details.get("failed") or [])[:10] if not r.passed else []
        if not r.passed and not failed and "n_failures" in r.details:
            failed = [f"fuzz: {{r.details['n_failures']}} failing trials"]
        return {{"status": status, "failed_cases": failed, "seconds": round(time.time() - t0, 2)}}
    except Exception as exc:
        return {{"status": "ERROR:" + type(exc).__name__, "failed_cases": [], "detail": str(exc)[:200], "seconds": round(time.time() - t0, 2)}}

if name == "baseline":
    res = {{k: safe(checks[k]) for k in keys}}
else:
    with muts[name]():
        res = {{k: safe(checks[k]) for k in keys}}
print("RESULT" + json.dumps(res))
"""


def run_job(copy: Path, name: str, keys: list[str]) -> dict:
    t0 = time.time()
    p = subprocess.run([sys.executable, "-c", JOB.format(copy=str(copy), name=name, keys=keys)], cwd=copy,
                       capture_output=True, text=True, timeout=1800)
    line = next((x for x in p.stdout.splitlines() if x.startswith("RESULT")), None)
    if line is None:
        return {"job_error": (p.stderr or p.stdout)[-1500:], "seconds": round(time.time() - t0, 1)}
    return {"checks": json.loads(line[6:]), "seconds": round(time.time() - t0, 1)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--copy-dir", default=None)
    args = ap.parse_args()
    t0 = time.time()
    before = {rel: sha256_file(ROOT / rel) for rel in code_files(ROOT)}
    base = Path(args.copy_dir or tempfile.mkdtemp(prefix="stage06_mutation_copy_"))
    copy = base / "repo"
    if copy.exists():
        raise FileExistsError(copy)
    for rel in before:
        (copy / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / rel, copy / rel)
    for rel in ("docs/PREREG_stage06.md", "docs/PREREG_stage06_AMENDMENT_1.md", "docs/STAGE06_SEED_ROLES.md"):
        (copy / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / rel, copy / rel)
    s05 = "runs/20261010T053729455237Z_stage05_population_advantage_51c7621b7a"
    for rel in ("results/item_contrasts.npy", "results/item_contrasts_index.csv", "checksums.json", "config.yaml"):
        (copy / s05 / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / s05 / rel, copy / s05 / rel)
    copy_before = {rel: sha256_file(copy / rel) for rel in before}
    assert copy_before == before, "copy differs from the workspace"
    from dynaicl.validation.mutations_stage06 import MUTATIONS_STAGE06
    from dynaicl.validation.mutations_stage06_analysis import MUTATIONS_STAGE06_ANALYSIS
    from dynaicl.validation.mutations_stage06_gate import MUTATIONS_STAGE06_GATE
    registered = set(MUTATIONS_STAGE06) | set(MUTATIONS_STAGE06_ANALYSIS) | set(MUTATIONS_STAGE06_GATE)
    if registered != set(PLAN):
        raise SystemExit(f"PLAN and the mutation registries disagree: {sorted(registered ^ set(PLAN))}")
    detectors = sorted({d for p, aux in PLAN.values() for d in (p, *aux)}, key=lambda k: int(k[1:]))
    jobs = [("baseline", detectors)] + [(m, [p, *aux]) for m, (p, aux) in PLAN.items()]
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futs = {name: pool.submit(run_job, copy, name, keys) for name, keys in jobs}
        results = {}
        for name, _ in jobs:
            results[name] = futs[name].result()
            print(f"{name}: " + (", ".join(f"{k}={v['status']}" for k, v in results[name]["checks"].items())
                                 if "checks" in results[name] else "JOB ERROR"), flush=True)
    after = {rel: sha256_file(ROOT / rel) for rel in before}
    copy_after = {rel: sha256_file(copy / rel) for rel in before}
    base_ok = "checks" in results["baseline"] and all(v["status"] == "pass" for v in results["baseline"]["checks"].values())
    rows = []
    for m, (prim, aux) in PLAN.items():
        r = results[m]
        st = r.get("checks", {})
        killed = st.get(prim, {}).get("status") == "FAIL"
        cases = st.get(prim, {}).get("failed_cases", [])
        exc_only = bool(cases) and all(str(c).startswith("UNEXPECTED") for c in cases)
        rows.append({"mutation": m, "primary": prim, "primary_status": st.get(prim, {}).get("status", "JOB ERROR"),
                     "aux": {a: st.get(a, {}).get("status") for a in aux}, "killed": killed and not exc_only,
                     "killed_only_through_an_unexpected_exception": exc_only, "failing_cases": cases[:6], "seconds": r["seconds"],
                     "detail": st.get(prim, {}).get("detail", r.get("job_error", ""))[:200]})
    out = {"baseline_all_pass": base_ok, "baseline": results["baseline"], "rows": rows,
           "killed": sum(r["killed"] for r in rows), "total": len(rows),
           "survivors": [r["mutation"] for r in rows if not r["killed"]],
           "workspace_hashes_unchanged": after == before, "copy_hashes_unchanged": copy_after == before,
           "files_tested": before, "copy_dir": str(copy), "seconds": round(time.time() - t0, 1)}
    (ROOT / "docs" / "STAGE06_MUTATION_MATRIX_v2.json").write_text(json.dumps(out, indent=1, sort_keys=True) + "\n",
                                                                encoding="utf-8", newline="\n")
    L = ["# Stage 0.6 mutation matrix (on a copy; in-memory mutations)", "",
         f"Generated by `scripts/stage06_mutation_matrix.py` in {out['seconds']} s. Copy: `{copy}`.", "",
         f"- Unmutated baseline, every detector PASS: **{base_ok}** "
         + "(" + ", ".join(f"{k} {v['status']}" for k, v in results['baseline'].get('checks', {}).items()) + ")",
         f"- Killed by a clean FAIL of the primary intended detector: **{out['killed']}/{out['total']}**; survivors: "
         f"{out['survivors'] or 'none'}",
         f"- Workspace file hashes unchanged after the run: **{out['workspace_hashes_unchanged']}**; copy unchanged: "
         f"**{out['copy_hashes_unchanged']}** ({len(before)} files; hashes in STAGE06_MUTATION_MATRIX_v2.json)", "",
         "| mutation | primary detector | primary status | auxiliary | killed | failing cases (first) | seconds |", "|---|---|---|---|---|---|---|"]
    for r in rows:
        L.append(f"| {r['mutation']} | {r['primary']} | {r['primary_status']} | "
                 f"{', '.join(f'{k}={v}' for k, v in r['aux'].items()) or '-'} | {'yes' if r['killed'] else '**NO**'} | "
                 f"{', '.join(str(c) for c in r['failing_cases'][:3])[:110]} | {r['seconds']} |")
    L += ["", "Status meanings: FAIL = the check ran and reported passed = False (a kill); ERROR:<type> = the check raised "
          "(NOT a kill); pass = not detected."]
    (ROOT / "docs" / "STAGE06_MUTATION_MATRIX_v2.md").write_text("\n".join(L) + "\n", encoding="utf-8", newline="\n")
    print(f"killed {out['killed']}/{out['total']}; survivors {out['survivors']}; baseline {base_ok}; "
          f"workspace unchanged {out['workspace_hashes_unchanged']}; copy unchanged {out['copy_hashes_unchanged']}")


if __name__ == "__main__":
    main()
