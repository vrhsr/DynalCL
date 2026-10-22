# Stage 0.6 validation report, v2 freeze (authorization gate, refusal handling, seed roles)

Scope: the operational changes of `docs/PREREG_stage06_AMENDMENT_1.md`. The estimands, thresholds, decision rules, N, noise levels and seeds are
unchanged, and the statistical code (`stage06_analysis.py`) and the reference code are byte-identical to v1. The v1 report
(`docs/STAGE06_VALIDATION_REPORT.md`) and its evidence are preserved untouched. **No confirmatory seed was used and no confirmatory run directory,
checkpoint or per-item output exists.** No real authorization artifact exists; the issuer was exercised only with test-only keys in temporary directories.

## 1. Procedure and the exact files tested

Order followed: finalize code -> `stage06_freeze.py --version v2 record-tested` (93 files, `docs/STAGE06_TESTED_FILES_v2.json`) -> full validation ->
`verify-tested` (**93 files unchanged since the record**, VERIFIED) -> this report -> manifest. The tested file hashes are in
`STAGE06_TESTED_FILES_v2.json`; the freeze command refuses unless the manifest's hashes equal them. Two earlier attempts are NOT reported as final: the first was aborted and restarted after a test-robustness fix (a hidden key prompt hung a check run from a terminal, disclosure F17); the second
validated and froze files that were then changed because the notebook-scan test turned out to be defective (disclosure F18). That first v2 freeze is preserved, set aside, in `dist/superseded_v2_attempt1/`.
Only the third, complete run on the final files is reported here.

## 2. Test suites (verbatim summary lines, final files; Windows 11, Python 3.13.5, numpy 2.2.2, scipy 1.15.1, pytest 9.0.2)

```
Stage 0.6 suite (tests/test_stage06_reference.py, test_stage06_analysis.py, test_stage06_gate.py, test_stage06_mutations.py; incl. slow V4, V9, V10):
======================= 73 passed in 544.35s (0:09:04) ========================
Pre-existing Stage 0 / 0.5 suite (tests/ minus the four files above):
======================= 101 passed in 320.15s (0:05:20) =======================
```

The Stage 0.6 count rose from 53 (v1) to 73: 20 new tests in `tests/test_stage06_gate.py` (V25-V28, 12 mutation kills, the seed-role document test, the reproduction of the
two v1 failures, the notebook scan, the mutation-plan coverage test). The V24 fixture gained the now-required manifest field `created_utc`, and the end-to-end runner test
now expects exit code 4 (CORRUPT) for a checksum mismatch (disclosure F14); no previous refusal assertion was removed or weakened.

## 3. New checks (all VERIFIED by execution)

| ID | Check | Result | Key diagnostic |
|---|---|---|---|
| V25 | Authorization gate | PASS | 107 cases: every bound field altered individually (15 fields, signature kept) -> REFUSED; every bound hash mismatched with a valid signature -> REFUSED naming the field; seed set as subset, superset, other bootstrap, bootstrap/replicate swapped -> REFUSED; replicate order reversed is accepted (set equality); mode, purpose, schema, malformed run id, validity over 72 h, expiry before issue, issued before the freeze, not yet valid, expired, qualification binding -> REFUSED; wrong key, test key on the production path, test-only artifact on the production path -> REFUSED; 9 malformed shapes and 9 truncation points -> CORRUPT; missing file -> REFUSED; run lock: first start, resume with the same run id, second run id refused, other manifest refused, damaged lock CORRUPT, completed run id refused, other run's results directory refused; pilot and test configs with an authorization refused; confirmatory artifact against pilot and test configs refused; resume after expiry refused; completion refused when a frozen file changed; swap between check and use does not change the bound run id; the CLI refuses a launch without an artifact (exit 3) and has no flag `--no-auth`, `--allow-test-only` or `--skip-authorization`; five environment variables set to 1 change nothing; the CLI refuses a test-only artifact even with its matching test key; API guards on `run_units`, `analyze`, `write_results`; key removed from the environment after reading, no key in messages, lock or gate; issuer: test-only artifact verifies on the test path and is marked test-only, real artifact with a test key, test-only with a real-looking key, short key, no key, hours over 72, overwrite, pilot config all refused; **no authorization artifact file remains in the workspace** |
| V26 | Refusal and corruption taxonomy | PASS | 75 cases. Unit metadata: empty, whitespace, non-object, scalar, 19 truncation points, every field missing (9), every field wrong-typed (9), edited without recomputing the checksum, duplicate unit id under another name, truncated, empty or missing arrays, unexpected file in the checkpoint directory -> CORRUPT; wrong schema version, other config hash -> REFUSED; stale `.tmp` file tolerated. Qualification report: missing path -> REFUSED; empty, malformed, not an object, each field missing, wrong type -> CORRUPT; stale (other manifest or environment), failed -> REFUSED. Manifest empty or missing fields -> CORRUPT. Config file missing -> REFUSED, malformed YAML -> CORRUPT, schema violation -> REFUSED. CLI: truncated unit JSON exits 4, missing config exits 3, missing qualification path exits 3, and no partial output is written |
| V27 | Seeded checkpoint fuzz | PASS | 400 trials, seed 61021; 8 operations (truncate, bit flip, zero-fill, delete a range, insert garbage, replace with random bytes, swap with another unit's file, empty) on the unit JSON, the arrays file, or both. Outcomes: 392 CORRUPT, 0 REFUSED, 8 loads that returned exactly the original record and arrays (the operation was a no-op), **0 tracebacks, 0 silent skips, 0 loads with changed content** |
| V28 | Seed roles | PASS | 18 cases: exactly the required roles; pilot and confirmatory seed roles equal the configurations; every seed in exactly one role; every role states allowed and forbidden uses; the generated document equals the table; each config's seeds match its mode's role; pilot runs with the bootstrap seed as evaluation, swapped replicates, a selection seed, a validation seed, confirmatory seeds or the bootstrap seed as a second evaluation seed are REFUSED; a cross-role collision is refused; **no confirmatory seed appears as a literal in any Python file or v2 notebook** |
| V14 | Seed isolation (existing, re-run) | PASS | manifest seeds disjoint from every other seed literal in the repository |
| V9 | Calibration (full, existing, unchanged thresholds) | PASS | 243 tests; min p 1.18e-4 (level 4.1e-6) |
| V4 | Tier-1 (full) | PASS | 243,216 items, max abs diff 9.3e-15 |
| V10 | Optimality (counts only) | PASS | 0 / 198 violations |

**Calibration diagnostic** (the same pre-specified protocol, thresholds unchanged, `scripts/stage06_calibration_diagnostic.py` run unchanged on a copy of the tested files):
`docs/STAGE06_CALIBRATION_DIAGNOSTIC_v2.md` is byte-identical to the v1 file (SHA-256 `18024843...` for both): worst test SBC at q = 0.755, r = 1, n = 2,
p = 1.18e-4; the fresh-seed rerun (61020, 5000 items) gave p = 0.87, not replicated.

## 4. Reproduction of the two v1 failures (the new tests can detect the problem)

Run by `test_original_v1_failures_are_reproduced_on_the_old_snapshot_and_fixed_now` on a copy of the preserved v1 snapshot and on the revised tree:

```
v1 snapshot:  {'truncated_unit_json': 'JSONDecodeError', 'missing_qualification_path': 'FileNotFoundError'}
revised tree: {'truncated_unit_json': 'Corrupt',         'missing_qualification_path': 'Refusal'}
```

## 5. Mutation matrix (VERIFIED; on a copy; in-memory mutations; `STAGE06_MUTATION_MATRIX_v2.md/json`)

* 40 mutations: 28 from v1 plus 12 new gate, refusal and seed-role mutants. **Unmutated baseline: all 13 detectors pass** (V2, V7, V11, V12, V20-V28).
* **40/40 killed** by a clean assertion-level FAIL of the primary intended detector; **survivors: none**; no kill rests only on an unexpected exception.
* New mutants and the cases that kill them: `skip_hash_comparison` (altered and mismatched hash cases), `ignore_mode` (`mode_pilot`), `accept_subset_of_seeds`
  (`seeds_subset`), `accept_expired` (`expired`, `resume_after_expiry_refused`), `accept_test_keys` (`test_only_artifact_refused_on_production_path`,
  `test_key_refused_on_production_path`), `skip_reverification_on_resume` (`resume_after_expiry_refused`), `reread_artifact_after_check`
  (`swap_after_check_does_not_change_the_bound_run_id`), `run_lock_not_enforced` (replay and resume cases), `env_var_disables_gate` (the CLI launch cases),
  `unit_json_error_uncaught` (28 V26 cases), `unit_record_checksum_skipped` (`unit_json_valid_but_edited_without_recomputing_the_checksum`; V27 also fails),
  `seed_roles_not_enforced` (six V28 cases).
* The matrix workspace hashes were unchanged after the run (93 files) and the copy was unchanged.

## 6. Deviations and remaining uncertainties

1. Disclosure F13-F17: the unit record checksum (schema v2) and field-level validation of the manifest and qualification report are additions beyond the listed approval, justified by the fuzz
   requirement; tests were adjusted for the new taxonomy; a test hung on a hidden key prompt when run from a terminal and was fixed.
2. The gate stops accidental, automated or agent-initiated launches through the frozen runner; it does not stop someone who can edit and run arbitrary code outside the frozen tree or who holds the key
   (`docs/STAGE06_AUTHORIZATION_GATE.md` section 1). A second run under a new run id in a different checkpoint and results directory is not prevented by the lock.
3. The artifact mechanism was tested end to end only with test-only keys (a real artifact cannot be created without the user's key); the success path through the command-line entry point is therefore covered
   at the function level with an internal `allow_test_only` parameter that no command-line flag, environment variable or config key can reach.
4. Phase D qualification and pilot artifacts are bound to the v1 snapshot; the Phase D tooling is re-run against v2 after the freeze (outside the manifest). Colab qualification has not been run.
