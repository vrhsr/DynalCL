# Phase D v2 local rehearsal on Linux (pilot seeds only): report

Run: `python phase_d_pilot/run_queue.py --set phase_d_v2` in tmux `dynaicl_d`, venv Python 3.13.5 (numpy 2.2.2, scipy 1.15.1, pyyaml 6.0.2, pytest 9.0.2).
Host: Linux x86_64 (frozen env was Windows AMD64). Queue exit 1; QUEUE_DONE.json total 264.5 s. Per-task logs: phase_d_pilot/work_v2/queue_phase_d_v2/logs/.
Prior steps (VERIFIED, run this session): verify without qualification -> REFUSED exit 3 (system/machine differ); `qualify` (pilot config) PASSED exit 0 (V4, V6, V11, V13);
verify with --qualification -> pre-flight OK exit 0. Integrity bookends 0-5 all rc 0.

## Per-task result (25 tasks)
PASS (15): bookend0; frozen qualify (22 s); bookend1-5; per-unit profile (67 s); scaling (40 s); size sweep N=50 (8 s); anchors N=4000 (67 s);
analysis cost synthetic (3 s); storage probe (1 s); structural analysis (13 s).
FAIL (10):
| # | task | rc | cause (from log) | class |
|---|---|---|---|---|
| 3 | ref run 4 workers | 1 (child rc 3) | REFUSED: env differs; run qualify and pass --qualification. The harness does not pass --qualification | environment gate, by design; harness has no option for it |
| 4 | ref run 1 worker | 1 | same | same |
| 5 | compare refs bitwise | 1 | 50 units missing (no ref runs) | cascade of 3/4 |
| 6 | completeness | 1 | 0 of 50 units found | cascade |
| 8 | interrupt/resume (8) | 1 | ProcessLookupError in pilot_common.hard_kill (os.killpg on exited pid) | POSIX port bug in pilot tooling (Windows-written) |
| 10 | corruption tests | 1 | ref_w4/ckpt missing | cascade |
| 11 | restart emulation | 1 | same ProcessLookupError in hard_kill | POSIX port bug |
| 13 | determinism | 1 | ref_w4 npz missing | cascade |
| 20 | qualification gate (throwaway copy) | 1 | rebuild_manifest calls stage06_freeze.build_manifest without required `version` arg (pilot_harness.py:644) | tooling/frozen-API mismatch, not OS-related |
| 22 | launch protection | 1 | ref_w4/ckpt/<hash> missing | cascade |
| 24 | seed search | 3 | matches of the listed forbidden seed tokens, only inside work_v2/throwaway/lp_base copies (docs, seed manifest, stage06.yaml); none in pilot outputs | check scans throwaway copies of frozen docs; needs interpretation |

Runtimes of failed tasks: 0.3-14 s each (they failed fast). Nothing was patched; no task was re-run.

## Side effects to know about (VERIFIED by git status)
Tracked files modified by the queue: phase_d_pilot/config/PILOT_{N50,N100,N400,N4000,analysis_cost_N4000_mode_test,structural_analysis_mode_test}.yaml
(930/930 lines; `git diff --ignore-space-at-eol` shows no content change, so line-ending rewrite only) and phase_d_pilot/PILOT_ONLY_do_not_open_effects.json
(1 line changed per numstat; I did not open or diff it, and the harness rewrote it). None are in docs/FREEZE_MANIFEST_STAGE06_v2.json (grep count 0).
Not reverted; not staged. Decision on discarding or keeping them is yours.

## Recommendation: BLOCKED (for a Linux-local Phase D result); NOT GO
- No scientific result was produced for reference-run reproducibility, bitwise worker independence, resume, corruption, determinism or launch protection: 10/25 tasks failed and 8 of the 10 depend on the reference run or on process-kill.
- It is not a REVISE of the frozen code. Causes sit in non-frozen pilot tooling (hard_kill, rebuild_manifest call, no --qualification pass-through) and the by-design environment gate.
- Fixing needs code changes in phase_d_pilot/ (non-frozen), which I was told to stop and ask about. Alternative: run Phase D on the frozen Windows environment or Colab as the notebook intends.
- The timing tasks (profile, scaling, size sweep, anchors) passed but are Linux timings; they do not replace the Windows or Colab ones.
Labels: all above VERIFIED from logs, except the cause of the effects-file change (ASSUMED harness rewrite) and the seed-search interpretation (UNVERIFIED).
