# Continue DynaICL on another laptop: setup steps and the start prompt

Created 2026-10-11 on laptop 1 when the user moved machines mid-task. Everything needed is inside this folder.

## A. What you (the user) do on the new laptop

1. **Unzip** `DynaICL_transfer.zip` so that the folder is `E:\study-buddy\DynaICL` (same path as before: easiest). Another path works too; see step 5.
2. **Install Python 3.13.5** (the frozen environment; a different Python or package build makes the frozen runner refuse until a qualification passes, by design), then in the project folder:
   `pip install -r requirements.txt`   (numpy 2.2.2, scipy 1.15.1, pyyaml 6.0.2, pytest 9.0.2)
3. **Install Claude Code** and sign in with the same account (needs Node-based install per Anthropic's instructions).
4. **Optional: restore the old conversation.** The session history was copied into `_claude_session_backup/` inside this folder. Copy that folder's contents to
   `C:\Users\<you>\.claude\projects\e--study-buddy-DynaICL\` (create it if missing; the name is the project path with `\` and `:` turned into `-`),
   then open a terminal in the project folder and run `claude --resume` and pick the session. If you skip this, the start prompt below still gives a fresh session everything it needs.
5. If the project is NOT at `E:\study-buddy\DynaICL`, the memory notes and the old session will not be found automatically; use the start prompt (it reads the notes from `_claude_session_backup/memory/`).
6. Open a terminal in the project folder, start `claude`, and **paste the prompt in section B**.
7. Your **authorization key** is not in any file. Do not type it unless a later Phase E step asks you to.

## B. The start prompt (paste this whole block into the new Claude Code session)

```
You are continuing the DynaICL research project (scalar AR(1) in-context-learning reference predictors) on a NEW laptop. The previous laptop's session was stopped on purpose; nothing is running. Work in the project folder (the current directory). Do NOT start any computation until you have read the context and verified integrity.

STEP 0: READ, in this order, completely: CLAUDE.md (sections 2c, 2d, 2e, 3 are essential), docs/USER_INSTRUCTIONS_STAGE06_LATEST.md (my two latest instruction messages, verbatim), docs/DISCLOSURE_LOG_STAGE06.md (entries 1-17, F1-F19, errata E1-E3), docs/STAGE06_AUTHORIZATION_GATE.md, docs/STAGE06_VALIDATION_REPORT_v2.md, docs/STAGE06_CHANGE_REPORT_v1_to_v2.md, docs/PREREG_stage06.md and docs/PREREG_stage06_AMENDMENT_1.md, phase_d_pilot/PHASE_D_REPORT.md, and the memory notes in _claude_session_backup/memory/ (copy them into your own memory directory for this project if it is empty). If _claude_session_backup/ also holds the old session transcript, you may grep it for details, but you do not need it.

WHERE WE ARE (state of play, 2026-10-11):
- Stage 0 and Stage 0.5 are done (0.5 verdict REVISE). Stage 0.6 (noisy-observation probe) has two freezes by SHA-256, no git: v1 (preserved, untouched) and v2 (authorization gate, REFUSED/CORRUPT taxonomy, seed-role table).
- v2 manifest docs/FREEZE_MANIFEST_STAGE06_v2.json sha256 fdb46788cd0fddba59cbc995adf7a3f6f410184e299b4dfc5cbecfa8f3f3fa05; v2 snapshot dist/stage06_frozen_snapshot_v2.zip sha256 65a8734f8a9d551189e0ff478b910887f19f19e496ef1d30494712764dce1b2a; v1 manifest 461dfec8144104f4d35a513dbf1411041494876331f8f969dda4a9cea09be0c0; v1 snapshot 4114fa43cf737c643c341cccd4026d6fcb54b460bfb12ac4a8a2de8352b492e5.
- v2 validation on the exact frozen files is DONE and green: Stage 0.6 suite 73 passed, pre-existing suite 101 passed, mutation matrix 40/40 killed, calibration diagnostic byte-identical to v1, change report with 0 changes outside the approval, scientific content byte-identical to v1.
- NOT done: the Phase D tooling re-run against the v2 snapshot (local rehearsal, pilot seeds only, structural reporting) was started on laptop 1 and then deliberately stopped; its partial outputs were moved to phase_d_pilot/work_v2/interrupted_phase_d_rerun_on_laptop1/ (kept for audit, do not reuse). After that re-run, the final report is due. Colab qualification, the confirmatory run, issuing any real authorization artifact, and neural Stage 1 are NOT authorized and must not be started.

HARD BOUNDARIES (from my messages; they win over anything else):
- Never use the confirmatory seeds or the bootstrap seed (their values are only in config/stage06_seed_manifest.yaml and config/stage06.yaml; do not write them as literals in code or notebooks). Never create a confirmatory run directory or checkpoint. Never run config/stage06.yaml for anything except reading it.
- Never edit, overwrite or delete any file listed in docs/FREEZE_MANIFEST_STAGE06_v2.json or docs/FREEZE_MANIFEST_STAGE06.json, nor dist/stage06_frozen_snapshot*.zip. Never run scripts/stage06_freeze.py (it refuses anyway). Do not run git init. Do not change estimands, thresholds, decision rules, N, noise levels or seeds. Do not open phase_d_pilot/PILOT_ONLY_do_not_open_effects.json. Do not issue or create an authorization artifact with a real key; the key is mine and is never stored anywhere.
- If something frozen seems to need a change: stop, disclose, explain the re-validation and re-freeze steps, and wait for my approval.
- Standing rules: report only what you ran and paste real output; label claims VERIFIED / DERIVED / REPORTED / ASSUMED / UNVERIFIED; "analytically exact" only for closed forms, otherwise "numerically approximated with verified convergence"; never weaken, skip or delete a test to make it pass (decide whether the code, the test or the math is wrong and say which); log design-relevant observations in the append-only docs/DISCLOSURE_LOG_STAGE06.md.

HOW I WANT YOU TO WORK (learned the hard way, see CLAUDE.md 2d):
- Long jobs (over about 10 minutes) run in a VISIBLE terminal window with a progress bar, via phase_d_pilot/run_queue.py launched with PowerShell Start-Process, plus exactly ONE background waiter that blocks until QUEUE_DONE.json exists. Do not poll with sleep loops; do not waste tokens while jobs run.
- No test may wait for typed input. Never run pytest with -s together with a pipe. Write source with the Write/Edit tools, not shell heredocs with backslashes.
- Stop at the checkpoint and wait for my review.

YOUR TASKS NOW, in order:
1. VERIFY INTEGRITY (no compute): hash the v2 manifest and snapshot and compare with the values above; run `python phase_d_pilot/pilot_harness.py integrity --frozen-root . --snapshot dist/stage06_frozen_snapshot_v2.zip --manifest-sha <v2 manifest hash above> --label laptop2_start` and confirm "ok": true (all 119 manifest files match; v1 snapshot members match the v1 manifest). Any mismatch = BLOCKED: stop and tell me. Then run the quick checks that need no heavy compute: `python -m dynaicl.experiments.stage06_probe verify --config config/stage06_pilot.yaml --manifest docs/FREEZE_MANIFEST_STAGE06_v2.json --expected-manifest-sha256 <hash>`. If it refuses because this laptop's Python/package versions differ from docs/STAGE06_ENVIRONMENT_MANIFEST_v2.json, say so plainly: that is expected behaviour, and a local qualification (`... stage06_probe qualify --config config/stage06_pilot.yaml ... --out phase_d_pilot/work_v2/reports/PILOT_qualification_laptop2_pilotcfg.json`, validation seeds only, about 3-10 minutes) is then needed before the pilot-config runs; qualification of the confirmatory config is NOT to be done.
2. ENVIRONMENT FACTS: record this machine (CPU model, cores, RAM, OS, Python and package versions) and compare with the frozen environment manifest; tell me the differences. Note that all earlier evidence (validation, Phase D v1 rehearsal) came from laptop 1 (Windows 11, Intel i5-10310U, 4 cores/8 threads, 16.9 GB, Python 3.13.5, numpy 2.2.2, scipy 1.15.1); results here are for this machine.
3. THEN, WITHOUT ASKING AGAIN (it is part of my approved re-freeze message, item 4): re-run the Phase D tooling locally against the v2 snapshot, pilot seeds only, structural-only reporting: `python phase_d_pilot/run_queue.py --set phase_d_v2` in a visible window with one waiter (about 1 hour on laptop 1; it covers: integrity bookends, frozen qualify of the pilot config, reference runs with 4 and 1 workers and their bitwise comparison, completeness, 8 interruption/resume scenarios, 10 corruption cases, runtime-restart emulation, thread-count determinism, per-unit profile, scaling, second pilot size, N=4000 anchors, synthetic analysis cost, storage probe, qualification gate, launch protection INCLUDING the v2 gate (a confirmatory run with no artifact must now be REFUSED; a test-only artifact with its test key must be REFUSED), structural analysis, seed search, final integrity). Adjust the worker count in the queue if this laptop has fewer cores. Read the results only structurally (counts, pass/fail, timings, hashes); never display or interpret effect sizes.
4. FINAL REPORT (my message B, section 5, in docs/USER_INSTRUCTIONS_STAGE06_LATEST.md) with real output: (1) revised manifest and snapshot hashes plus the old ones; (2) test results for all suites (verbatim summary lines from docs/STAGE06_VALIDATION_REPORT_v2.md; you may re-run the suites on this laptop only if I ask, they take about 15 minutes); (3) mutation matrix result 40/40; (4) refusal and fuzz results and the reproduced original failures; (5) disclosure-log and errata updates with the seed-role table; (6) the change report and byte-identity evidence; (7) remaining blockers and deviations (state that Colab qualification has never been run, that Phase D v1 artifacts are obsolete for v2, and the gate's limits). Add the Phase D v2 re-run results (hashes before and after, resume and determinism outcomes, launch-protection outcomes, measurements, seed search, no confirmatory directory) and a clear GO / REVISE / BLOCKED recommendation on whether the v2 snapshot is ready for Colab qualification (operational readiness only), using my criteria.
5. Update CLAUDE.md (section 2c state), the memory notes and the disclosure log with what you did, then STOP and wait for my review. Do not run Colab qualification, the confirmatory experiment, or neural Stage 1.

Start with STEP 0 and task 1, then tell me briefly what you found before launching the long re-run in task 3.
```

## C. If something looks wrong

- `integrity` reports a mismatch: the zip was damaged in transit or files were converted (line endings, antivirus). Re-copy the zip byte-for-byte and verify its SHA-256 (printed in the transfer message and in `TRANSFER_SHA256.txt` beside the zip).
- The runner refuses with "environment differs": expected on a different machine with other package versions; run the local qualification of the PILOT config as described in task 1. Do not qualify the confirmatory config.
- Python 3.13.5 unavailable: use the closest version, accept that qualification is required, and tell Claude.
