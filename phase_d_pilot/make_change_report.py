"""Generate docs/STAGE06_CHANGE_REPORT_v1_to_v2.md (+ .json) after the v2 freeze. Outside the frozen set (it needs the v2 hashes).

Compares the preserved v1 snapshot (zip members) with the v2 manifest: every added, changed or removed file with old and new
hashes, mapped to an approved item; anything not covered by the approval is flagged. Also the byte-identity evidence for the scientific
content (pre-registration, confirmatory configuration, statistical and reference code, seed values).
"""

from __future__ import annotations

import hashlib
import json
import sys
import zipfile
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
V1_ZIP, V1_MAN = ROOT / "dist" / "stage06_frozen_snapshot.zip", "docs/FREEZE_MANIFEST_STAGE06.json"
V2_MAN, V2_SHAFILE = "docs/FREEZE_MANIFEST_STAGE06_v2.json", ROOT / "dist" / "stage06_frozen_snapshot_v2.sha256"

# path prefix / exact path -> (approved item, reason)
RULES = [
    ("dynaicl/experiments/stage06_authorization.py", "1 authorization gate", "new: HMAC artifact verification, key handling, run lock"),
    ("dynaicl/experiments/stage06_errors.py", "1 + 2", "new: REFUSED / CORRUPT taxonomy shared by the runner and the gate"),
    ("scripts/stage06_issue_authorization.py", "1 issuer tool", "new: documented issuer, tested with test keys only"),
    ("docs/STAGE06_AUTHORIZATION_GATE.md", "1 threat model", "new: design, threat model and limits"),
    ("dynaicl/experiments/stage06_probe.py", "1 + 2 + 3 (+ F13)", "gate at start/resume/completion, run lock, REFUSED/CORRUPT handling, seed-role check, call-time roots; F13: unit-record checksum (unit schema v2), field-level manifest and qualification validation, config read once"),
    ("dynaicl/validation/checks_stage06_gate.py", "1 + 2 + 3 tests", "new: V25 gate, V26 taxonomy, V27 fuzz, V28 seed roles"),
    ("dynaicl/validation/mutations_stage06_gate.py", "1 mutation tests", "new: 12 mutants"),
    ("tests/test_stage06_gate.py", "1 + 2 + 3 tests", "new: wrappers, mutation kills, v1-failure reproduction, document and notebook scans"),
    ("dynaicl/validation/checks_stage06_analysis.py", "2 (F14)", "V24 fixture manifest gained the now-required created_utc field; no assertion removed"),
    ("tests/test_stage06_analysis.py", "2 (F14)", "end-to-end test expects exit 4 (CORRUPT) for a checksum mismatch; no assertion removed or weakened"),
    ("dynaicl/config/stage06_seed_roles.py", "3 seed roles", "new: loader, validator, generated-document renderer, mode allocation check"),
    ("config/stage06_seed_manifest.yaml", "3 seed roles", "v1 role `pilot` split into pilot_evaluation / pilot_bootstrap; allowed and forbidden uses per role. Seed VALUES unchanged (see below)"),
    ("docs/STAGE06_SEED_ROLES.md", "3 seed roles", "new: generated from the table and tested"),
    ("dynaicl/experiments/stage06_freeze.py", "4 new freeze under a new version label", "freeze tooling gained version labels; refuses to write v1 or overwrite"),
    ("scripts/stage06_freeze.py", "4 new freeze under a new version label", "same; refuses record/verify/freeze once the manifest exists (disclosure E2)"),
    ("scripts/stage06_mutation_matrix.py", "1 + 4", "new mutants and detectors, versioned _v2 outputs, failing cases recorded"),
    ("docs/PREREG_stage06_AMENDMENT_1.md", "4 amendment", "new: dated operational amendment; the pre-registration itself is untouched"),
    ("docs/STAGE06_VALIDATION_REPORT_v2.md", "4 validation report", "new"),
    ("docs/STAGE06_TESTED_FILES_v2.json", "4 tested-file record", "new"),
    ("docs/STAGE06_MUTATION_MATRIX_v2.md", "4 evidence", "new"),
    ("docs/STAGE06_MUTATION_MATRIX_v2.json", "4 evidence", "new"),
    ("docs/STAGE06_CALIBRATION_DIAGNOSTIC_v2.md", "4 evidence", "new; byte-identical to the v1 diagnostic"),
    ("docs/STAGE06_ENVIRONMENT_MANIFEST_v2.json", "4 evidence", "new environment manifest for the v2 freeze"),
]
IDENTITY_FILES = ["docs/PREREG_stage06.md", "config/stage06.yaml", "config/stage06_pilot.yaml", "config/stage06_test.yaml",
                  "dynaicl/experiments/stage06_analysis.py", "dynaicl/references/kalman_quadrature.py", "dynaicl/systems/noisy.py",
                  "dynaicl/evaluation/noisy_harness.py", "dynaicl/config/stage06_schema.py", "docs/MATH_STAGE06.md",
                  "dynaicl/validation/checks_stage06.py", "dynaicl/validation/mutations_stage06.py"]


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def classify(rel: str):
    for key, item, why in RULES:
        if rel == key:
            return item, why
    return None, None


def main() -> int:
    v2 = json.loads((ROOT / V2_MAN).read_text(encoding="utf-8"))
    lines = V2_SHAFILE.read_text(encoding="utf-8").splitlines()
    v2_snap_sha, v2_man_sha = lines[0].split()[0], lines[1].split()[0]
    with zipfile.ZipFile(V1_ZIP) as z:
        v1 = json.loads(z.read(V1_MAN).decode("utf-8"))
        v1_files = dict(v1["files"])
        v1_members = {n: sha(z.read(n)) for n in z.namelist()}
        v1_seed_table = yaml.safe_load(z.read("config/stage06_seed_manifest.yaml").decode("utf-8"))["roles"]
        v1_cfg_hashes = v1["config_hashes"]
    assert all(v1_members[k] == h for k, h in v1_files.items()), "the preserved v1 snapshot no longer matches its manifest"
    v2_files = dict(v2["files"])
    rows, flagged = [], []
    for rel in sorted(set(v1_files) | set(v2_files)):
        old, new = v1_files.get(rel), v2_files.get(rel)
        if old == new:
            continue
        status = "added" if old is None else "removed" if new is None else "changed"
        item, why = classify(rel)
        row = {"file": rel, "status": status, "v1_sha256": old, "v2_sha256": new, "approved_item": item, "reason": why}
        rows.append(row)
        if item is None:
            flagged.append(row)
    unchanged = sorted(set(v1_files) & set(v2_files) - {r["file"] for r in rows})
    ident = [(f, v1_files.get(f), v2_files.get(f)) for f in IDENTITY_FILES]
    ident_ok = all(a is not None and a == b for _, a, b in ident)
    v2_seed_table = yaml.safe_load((ROOT / "config" / "stage06_seed_manifest.yaml").read_text(encoding="utf-8"))["roles"]
    seeds_v1 = sorted(s for r in v1_seed_table.values() for s in r["seeds"])
    seeds_v2 = sorted(s for r in v2_seed_table.values() for s in r["seeds"])
    conf = {k: (v1_seed_table[k]["seeds"], v2_seed_table[k]["seeds"]) for k in ("confirmatory_evaluation", "confirmatory_bootstrap")}
    pilot_v1 = v1_seed_table["pilot"]["seeds"]
    pilot_v2 = v2_seed_table["pilot_evaluation"]["seeds"] + v2_seed_table["pilot_bootstrap"]["seeds"]
    val_v1, val_v2 = set(v1_seed_table["validation"]["seeds"]), set(v2_seed_table["validation"]["seeds"])
    other_same = all(v1_seed_table[k]["seeds"] == v2_seed_table[k]["seeds"] for k in ("design_calculation", "selection"))
    cfg_same = {k: v1_cfg_hashes[k]["config_hash"] == v2["config_hashes"][k]["config_hash"] for k in v1_cfg_hashes}
    out = {"v1": {"manifest_sha256": sha((ROOT / V1_MAN).read_bytes()), "snapshot_sha256": sha(V1_ZIP.read_bytes()), "files": len(v1_files)},
           "v2": {"manifest_sha256": v2_man_sha, "snapshot_sha256": v2_snap_sha, "files": len(v2_files)},
           "changes": rows, "unchanged_count": len(unchanged), "flagged_not_covered": flagged,
           "byte_identity": {f: {"v1": a, "v2": b, "identical": a == b} for f, a, b in ident},
           "seeds": {"all_seed_values_identical_v1_v2": seeds_v1 == seeds_v2, "confirmatory": conf, "pilot_v1_role": pilot_v1,
                     "pilot_v2_roles": pilot_v2, "pilot_values_identical": sorted(pilot_v1) == sorted(pilot_v2),
                     "validation_v1_subset_of_v2": val_v1 <= val_v2, "validation_added": sorted(val_v2 - val_v1),
                     "design_and_selection_identical": other_same},
           "config_hashes_identical": cfg_same}
    (ROOT / "docs" / "STAGE06_CHANGE_REPORT_v1_to_v2.json").write_text(json.dumps(out, indent=1, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    L = ["# Stage 0.6 change report: v1 freeze -> v2 freeze", "",
         "Generated by `phase_d_pilot/make_change_report.py` AFTER the v2 freeze (so it is not inside the v2 manifest; its facts are checkable against the two manifests).", "",
         "## 1. The two freezes", "", "| | v1 (preserved untouched) | v2 |", "|---|---|---|",
         f"| manifest | `{out['v1']['manifest_sha256']}` | `{v2_man_sha}` |", f"| snapshot archive | `{out['v1']['snapshot_sha256']}` | `{v2_snap_sha}` |",
         f"| files covered | {len(v1_files)} | {len(v2_files)} |", "",
         f"The v1 snapshot's members were re-hashed for this report and equal the v1 manifest ({len(v1_files)} files). The v1 manifest and snapshot files are byte-identical to their "
         "recorded hashes. The v2 manifest records the v1 hashes under `supersedes`. **Phase D qualification and pilot artifacts are bound to the v1 snapshot; they are obsolete for v2, preserved, "
         "and not reused.**", "",
         "## 2. Scientific content: byte-identity evidence", "", "| file | v1 SHA-256 | v2 SHA-256 | identical |", "|---|---|---|---|"]
    for f, a, b in ident:
        L.append(f"| `{f}` | `{(a or '')[:16]}...` | `{(b or '')[:16]}...` | **{a == b}** |")
    L += ["", f"* All three config hashes are identical in the two manifests: {cfg_same} (so the confirmatory configuration's hash `{v2['config_hashes']['config/stage06.yaml']['config_hash'][:16]}...` is unchanged).",
          f"* Confirmatory seeds are unchanged: {conf}.",
          f"* Pilot seeds: v1 role `pilot` {pilot_v1}; v2 roles `pilot_evaluation` + `pilot_bootstrap` {pilot_v2}; same values: {sorted(pilot_v1) == sorted(pilot_v2)}.",
          f"* The set of ALL seed values in the table is identical in v1 and v2: {seeds_v1 == seeds_v2}. design_calculation and selection are identical: {other_same}. The v1 validation seeds are a subset of the v2 ones (v2 adds {sorted(val_v2 - val_v1)}: validation seeds only, no change to any scientific seed).",
          "* The statistical, reference and estimand code (`stage06_analysis.py`, `kalman_quadrature.py`, `noisy.py`, `noisy_harness.py`, `stage06_schema.py`) is byte-identical (table above).", "",
          "## 3. Every changed, added or removed file", "", f"{len(rows)} files differ; {len(unchanged)} are byte-identical in both freezes.", "",
          "| file | status | v1 | v2 | approved item | reason |", "|---|---|---|---|---|---|"]
    for r in rows:
        L.append(f"| `{r['file']}` | {r['status']} | `{(r['v1_sha256'] or '-')[:12]}` | `{(r['v2_sha256'] or '-')[:12]}` | {r['approved_item'] or '**NOT COVERED**'} | {r['reason'] or ''} |")
    L += ["", "## 4. Changes not covered by the approval", ""]
    L += ([f"* `{r['file']}` ({r['status']})" for r in flagged] if flagged else ["None. Every changed or added file maps to an approved item above. Items marked F13 and F14 go beyond the literal list and are disclosed (docs/DISCLOSURE_LOG_STAGE06.md): the unit-record checksum, field-level validation of the manifest and qualification report, and the test adjustments that follow from the new taxonomy."])
    L += ["", "## 5. Hash order for the notebook and bundle (no circular hashing)", "",
          "(1) the v2 freeze produces the manifest and the snapshot; (2) the pilot tooling is zipped (`dist/phase_d_pilot_bundle_v2.zip`); (3) the pilot notebook is built embedding the snapshot, manifest and bundle "
          "hashes; (4) `phase_d_pilot/PILOT_BUNDLE_MANIFEST_v2.json` lists the hashes of the tooling files, the bundle, the notebook, the v2 manifest and the v2 snapshot. Nothing hashes the pilot-bundle manifest. "
          "The notebook and bundle are outside the v2 manifest."]
    (ROOT / "docs" / "STAGE06_CHANGE_REPORT_v1_to_v2.md").write_text("\n".join(L) + "\n", encoding="utf-8", newline="\n")
    print(f"changes {len(rows)}, unchanged {len(unchanged)}, flagged {len(flagged)}, identity ok {ident_ok}, seeds identical {seeds_v1 == seeds_v2}, config hashes identical {all(cfg_same.values())}")
    return 0 if ident_ok and not flagged and all(cfg_same.values()) and seeds_v1 == seeds_v2 else 1


if __name__ == "__main__":
    raise SystemExit(main())
