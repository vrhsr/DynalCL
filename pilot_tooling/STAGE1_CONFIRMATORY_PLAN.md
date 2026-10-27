# Stage 1A after Amendment 2: continuation, authorization and confirmatory run (plan; nothing started)

Not frozen. Written 2026-10-27 for the user's condition 5. Every step below needs the user's explicit go-ahead; the
confirmatory phases additionally need the user's approval in the box session (as in Stage 0.6) and an authorization
artifact under the user's key. `<H3>` = the v3 manifest hash the user stores; `<R>` = the run id the user chooses
(proposed: `stage1A-confirm-20261101`, letters, digits, `.`, `_`, `-`, 8-64 characters).

## Sequence
1. **v3 freeze** (laptop; done when the user has the hash). Nothing else may run before it.
2. **Pilot continuation** (box, CPU, pilot phase: no authorization needed, but the user's go-ahead): relay A. Produces
   `results_stage1/pilot/pilot_decision_v3_final.json` (B = 50k, M1, M2 from the frozen lookup with cap 32).
3. Laptop: verify the pushed small files; report status, M1, M2, secondary kept; disclosure entry. STOP for the user.
4. **Confirmatory training** (box, GPU, about 4-5 days): relay B, under artifact 1 (valid <= 72 h; the gate is checked
   when `train` starts; training then runs to completion). A restart after the window needs a new artifact, same run id.
5. **Confirmatory evaluation and analysis** (box): relay C, under artifact 2 (a fresh key and window, same run id).
6. Laptop: verify, write the results, disclosure entries. The original NOT RESOLVABLE (compute) stays the primary record.

## Key and artifact handling (box)
* **Who decides:** the user, in the box session, for each artifact separately. The box session must state the run id,
  the phase, the v3 manifest hash, the decision file's sha256 and the validity window, then WAIT for the user's typed
  approval. Without it, nothing is generated or launched.
* **Generate** (never displayed; the key's value never appears on a command line, in history, a log or the chat):
  `umask 077; mkdir -p ~/.dynaicl_auth; .venv-stage1/bin/python -c "import secrets; print(secrets.token_urlsafe(48))" > ~/.dynaicl_auth/key`
* **Issue** (the key enters only this process's environment):
  `DYNAICL_STAGE1_AUTH_KEY="$(cat ~/.dynaicl_auth/key)" .venv-stage1/bin/python scripts/stage1_issue_authorization.py --config config/stage1.yaml --manifest docs/FREEZE_MANIFEST_STAGE1_v3.json --expected-manifest-sha256 <H3> --snapshot dist/stage1_frozen_snapshot_v3.zip --decision results_stage1/pilot/pilot_decision_v3_final.json --run-id <R> --hours 72 --out ~/.dynaicl_auth/A_<phase>.json`
  The issuer verifies the freeze, refuses a path inside the repository, writes the artifact with mode 600 and prints the
  payload (no secret) and the artifact's sha256.
* **Launch:** the wrapper `pilot_tooling/run_stage1_confirmatory.sh` reads the key file into its own environment and
  shreds the file before anything else runs; the running processes hold the key only in memory.
* **After each phase:** `ls -la ~/.dynaicl_auth` must show no `key` file (only artifacts). Artifacts hold no secret but stay
  off the repository (as in Stage 0.6); their sha256 is in `wrapper_log.txt`. A refused gate (exit 3) means: report the
  run log line and stop; never retry with a different key or artifact without the user.
* Never: print, echo, cat, paste, commit or log the key; pass it as an argument; use a `TEST-ONLY-` key (the v3 gate refuses
  it); issue a second artifact for a different run id or decision file.

## Relay A: pilot continuation (only after the user approves; CPU; no authorization)
```
Task: Stage 1A pilot continuation under Amendment 2 (freeze v3). CPU only. Stop and report if anything fails, a check refuses, or a permission is denied.
Never open, print, summarise or push anything under results_stage1/pilot/eval/ or any model weights.
1. cd /home/rama_11187/projects/dynacl && git status --porcelain --untracked-files=no   (must print nothing)
   git fetch origin && git checkout stage1-planning && git pull --ff-only && git log --oneline -1
2. tmux new -d -s s1cont "bash pilot_tooling/run_stage1_pilot_continuation.sh <H3>"
3. Wait with ONE background waiter until results_stage1/pilot/CONTINUATION_DONE.json exists (do not poll in a loop).
   On-demand progress only: cat results_stage1/pilot/CURRENT_STEP; tail -3 results_stage1/pilot/continuation_log.txt
4. When it exists:
   git checkout results-stage1-pilot
   git add -f results_stage1/pilot/*.json results_stage1/pilot/*.txt results_stage1/pilot/CURRENT_STEP
   git diff --cached --name-only | grep -E "/eval/|\.pt$" && echo "STOP: forbidden file staged"   (must print nothing)
   find results_stage1/pilot -maxdepth 1 -type f -size +2M   (must print nothing)
   git commit -m "Stage 1A pilot continuation under Amendment 2 (v3): decisions and logs; no eval arrays, no weights" && git push origin results-stage1-pilot   (never main, never --force)
   git checkout stage1-planning
5. Report: CONTINUATION_DONE.json, continuation_log.txt, the "status", "B", "cap", "M1", "M2", "secondary_kept" fields of pilot_decision_v3_final.json, the last 3 lines of run_log.txt, and the commit hash.
```

## Relay B: confirmatory training (only after step 3 and the user's authorization; GPU)
```
Task: Stage 1A confirmatory TRAINING, run id <R>. This needs my explicit approval in this session before step 3. Stop and report if anything fails, the gate refuses, or a permission is denied.
Never print, echo or cat the key; never commit the key or the artifact; never use a TEST-ONLY key.
1. cd /home/rama_11187/projects/dynacl && git status --porcelain --untracked-files=no   (must print nothing)
   git fetch origin && git checkout stage1-planning && git pull --ff-only && git log --oneline -1
   .venv-stage1/bin/python scripts/stage1_freeze.py verify --manifest docs/FREEZE_MANIFEST_STAGE1_v3.json --expected-sha256 <H3>
   sha256sum results_stage1/pilot/pilot_decision_v3_final.json   (must equal the hash in my approval message)
   nvidia-smi   (report the processes and free memory; W = <workers> concurrent trainings need about 0.5 GB each)
   test ! -e results_stage1/confirmatory/<R> || echo "STOP: run directory exists"
2. Tell me: run id <R>, phase train, v3 manifest hash, decision sha256, validity 72 h from issue. WAIT for my typed approval.
3. After my approval only:
   umask 077; mkdir -p ~/.dynaicl_auth; .venv-stage1/bin/python -c "import secrets; print(secrets.token_urlsafe(48))" > ~/.dynaicl_auth/key
   DYNAICL_STAGE1_AUTH_KEY="$(cat ~/.dynaicl_auth/key)" .venv-stage1/bin/python scripts/stage1_issue_authorization.py --config config/stage1.yaml --manifest docs/FREEZE_MANIFEST_STAGE1_v3.json --expected-manifest-sha256 <H3> --snapshot dist/stage1_frozen_snapshot_v3.zip --decision results_stage1/pilot/pilot_decision_v3_final.json --run-id <R> --hours 72 --out ~/.dynaicl_auth/A_train.json
   tmux new -d -s s1conf "bash pilot_tooling/run_stage1_confirmatory.sh train <H3> <R> $HOME/.dynaicl_auth/A_train.json $HOME/.dynaicl_auth/key <workers>"
   sleep 60; ls -la ~/.dynaicl_auth   (no "key" file may remain); tail -3 results_stage1/confirmatory/<R>/run_log.txt   (must not say REFUSED)
4. Wait with ONE background waiter until results_stage1/confirmatory/<R>/DONE_train.json exists (days; do not poll in a loop).
   On-demand progress only: tail -2 results_stage1/confirmatory/<R>/run_log.txt
5. When it exists: git checkout -b results-stage1-confirmatory-<R>
   git add -f results_stage1/confirmatory/<R>/*.json results_stage1/confirmatory/<R>/*.txt results_stage1/confirmatory/<R>/CURRENT_STEP
   find results_stage1/confirmatory/<R>/models -name train_record.json -print0 | xargs -0 git add -f
   git diff --cached --name-only | grep -E "\.pt$|/eval/|dynaicl_auth" && echo "STOP: forbidden file staged"   (must print nothing)
   git commit -m "Stage 1A confirmatory training <R> (logs, training records; no weights)" && git push -u origin results-stage1-confirmatory-<R>   (never main, never --force)
   git checkout stage1-planning
6. Report: DONE_train.json, the wrapper_log.txt line with the artifact sha256, the last 3 lines of run_log.txt, first and last lines of gpu_telemetry.txt, ls -la ~/.dynaicl_auth, and the commit hash.
```

## Relay C: confirmatory evaluation and analysis (after relay B is verified; a NEW key and artifact, same run id)
Same as relay B with these differences: step 1 also checks that `DONE_train.json` has rc 0 and that 640 (or the planned
number of) `train_record.json` files exist; step 2 names phase `evaluate-analyze`; step 3 issues `A_eval.json` with a fresh
key and launches `bash pilot_tooling/run_stage1_confirmatory.sh evaluate-analyze <H3> <R> $HOME/.dynaicl_auth/A_eval.json
$HOME/.dynaicl_auth/key <workers> cpu`; the waiter waits for `DONE_evaluate-analyze.json`; step 5 pushes
`results.json`, the logs and the JSON files on the same results branch (never `eval/` arrays or weights); step 6 reports
DONE_evaluate-analyze.json, the run_log line starting "verdict:", and the commit hash. If evaluation outlasts the 72 h window
before `analyze` starts, the gate refuses `analyze`: stop and ask the user for a third artifact (same run id).

## Expected durations (projections, not rules)
* Continuation: full evaluation at B for 32 pilot models on CPU, unmeasured; the controls pass took 3 min for 4 checkpoints.
* Training: 640 models x 50k steps; about 96 h at the measured pilot rate with 8 workers (benchmark may change W and the
  estimate); the cap rule's own projection is 127 h with its safety factor.
* Evaluation of 640 models on CPU: estimated from the continuation's measured time x 20.
