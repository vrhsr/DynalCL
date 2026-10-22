# Phase D (v2 freeze) operational rehearsal on a Linux box: final report

Written 2026-10-22. Scope: PILOT config and pilot seeds only. No confirmatory seed, config, run directory or authorization artifact was used or created.
Evidence: GitHub branch `results-phase-d-v2-linux-20261022` (commit `5a9e5a6`; reports under `phase_d_pilot/work_v2/reports/`, `results_linux/`).
Labels: VERIFIED = read by me in a report file or in code; REPORTED = the box's account, not independently checked; DERIVED = my reading of code.
I did not open `PILOT_ONLY_do_not_open_effects.json` (it is not on the results branch) and did not use any pilot effect size.

## 1. Environment
Linux x86_64 (32 logical CPUs), venv Python 3.13.5, numpy 2.2.2, scipy 1.15.1, pyyaml 6.0.2, pytest 9.0.2 (VERIFIED, qualification report). The frozen environment is Windows AMD64, so the runner REFUSED
until `qualify` passed here (VERIFIED, exit 3, then pass). `qualify` ran the frozen qualification checks V4, V6, V11, V13 on the pilot config: all PASS in about 22 s. The report is bound to this
environment, this manifest and this config. Manifest checked against `fdb46788cd0fddba59cbc995adf7a3f6f410184e299b4dfc5cbecfa8f3f3fa05` (typed by the user; matches the laptop file).

## 2. Result: attempt 3, 25 of 25 tasks passed (VERIFIED, `QUEUE_DONE.json`, 777.9 s)
| Question | Evidence | Result |
|---|---|---|
| Reference run completeness | `PILOT_completeness_ref_w4` | 50/50 units, 1,689,600 array elements, 0 non-finite, 0 PIT outside [0,1], 0 duplicates, 0 failed frozen load-verify |
| Worker-count independence (4 vs 1 worker) | `PILOT_worker_count_independence_ref_w4_vs_w1` | all 50 units identical, `max_abs_diff` 0.0, npz file bytes identical |
| Interruption and resume (8 scenarios, incl. 3 external hard kills and 3 self-kills mid-write) | `PILOT_interrupt_tests_local` | every resume rc 0; `arrays_differ` and `npz_file_bytes_differ` empty in all 8; no duplicate or missing units; the one npz-without-json state (`selfkill_before_json_replace`) was recomputed to an identical result |
| Corruption (10 cases) | `PILOT_corruption_tests_local` | 8 refused with `CORRUPT:` exit 4 (wrong config hash, missing npz, swapped npz, single bit flip, truncated json, truncated npz, wrong array shape, zero-length npz); the 2 rc 0 cases (leftover tmp files; json missing with npz present) were handled correctly and identical; no traceback; `silently_skipped` False everywhere; after remediation all identical |
| Restart from a fresh extraction | `PILOT_restart_emulation` | 20 units done before kill, resume rc 0, 50/50 identical to the reference (emulation only, same machine) |
| Determinism across thread counts (1, 1, 2, 4, 32) | `PILOT_determinism_local` | 3 units: arrays bitwise equal across thread counts and to the reference checkpoint; synthetic analysis result bitwise equal |
| Qualification gate | `PILOT_qualification_gate` | 6 refusal cases REFUSED (no report, other environment, other manifest or config, failed report, missing path), valid report accepted |
| Launch protection incl. the v2 authorization gate (stubbed copies) | `PILOT_launch_protection` | confirmatory run without authorization, test-only artifact with matching or other key, confirmatory analyze on pilot checkpoints, mode and seed mismatches, run without manifest arguments: all REFUSED rc 3; no checkpoint written by any case |
| Seed search | `PILOT_seed_search_local` | 2,723 files scanned; no whole-token match for the confirmatory seeds in any pilot output |
| Structural analysis on pilot output | `PILOT_structural_analysis_local` | frozen `analyze()` ran to success; 72 contrast rows all finite, decision and tier-2 blocks present, 2 replicates ok |
Timing, scaling, size-sweep, anchor and per-unit-profile tasks also completed (rc 0). I did NOT analyse their contents here: they are Linux timings, and this report makes no sizing or design claim from pilot output.

## 3. How we got here (all three Linux attempts; details in the disclosure log, F20-F25)
* Attempt 1: 15 of 25. Cause was the Windows-written, non-frozen Phase D tooling: no `--qualification` pass-through, `hard_kill` raising on an already-exited process, `rebuild_manifest` not updated for v2 (it would have failed on Windows too), and seed-search hits only in the leftover throwaway copies (a knock-on of the crash, since cleanup runs at the end of those tasks).
* Attempt 2 (after fixes 1-3): 21 of 25. The 4 failures were comparison and wording problems in the tooling (the v2 unit record's `record_sha256` includes timings; corruption now reports `CORRUPT:` exit 4, not `REFUSED:`; the restart emulation did not receive the qualification report). The arrays were byte-identical throughout.
* Attempt 3 (after fixes 4-6): 25 of 25.
Every fix is in a file outside the frozen manifest (`phase_d_pilot/pilot_common.py`, `pilot_harness.py`, `run_queue.py`; branch `phase-d-linux-tooling`, commits `29912c9`, `0448e13`). No frozen file changed (`verify` passed after every attempt: REPORTED by the box; I did not independently re-hash the frozen files on the box. The three changed files are not in the manifest: DERIVED from `code_files()` in `stage06_freeze.py`, which lists only `dynaicl/`, `tests/`, `scripts/stage06_*.py`, the configs, the seed manifest and the dependency specs).
The comparison fix is not a loosening for real differences: each record's own checksum is verified first, then `seconds` and `record_sha256` (a function of `seconds`) are ignored; I tested it on synthetic records (identical, changed meta field, wrong checksum).

## 4. Recommendation: GO, scoped (not a clearance for anything else)
GO for this: the frozen v2 runner, with the pilot config, on Linux x86_64 after a passing environment qualification, completes the pilot, resumes exactly after interruption, refuses corrupt or stale inputs and all unauthorized confirmatory launches, and gives bitwise-identical arrays across worker and thread counts. I found no evidence of a defect in the frozen code.
This is NOT: authorization of the confirmatory run, a statement about the confirmatory config on this or any other platform, or evidence about the science (no pilot effect size was used).

## 5. What is not covered
* The qualification covers 4 checks on the PILOT config. The confirmatory config would need its own qualification where it is run; I have not verified exactly what the runner requires (UNVERIFIED).
* Colab (the platform the notebook targets) has never been run. A Windows v2 Phase D run was started and stopped (disclosure F19) and not repeated.
* The restart test is an emulation on the same machine, not a real runtime loss.
* The corruption and interruption tests ran against the pilot config's checkpoints only.
* Timings measured here do not transfer to Colab or the laptop.

## 6. Decisions that remain with the user
(a) Whether to also run Phase D on Colab or Windows. (b) Whether to start Phase E: qualification of the confirmatory config, issuing the authorization with the user's own key, the run, the analysis. (c) Stage 1.
