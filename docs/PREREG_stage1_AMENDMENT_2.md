# Stage 1A pre-registration, Amendment 2 (POST-PILOT follow-up; clearly labelled)

Status: part of the Stage 1 freeze v3 (`docs/FREEZE_MANIFEST_STAGE1_v3.json`). `docs/PREREG_stage1.md` (v3) and
`docs/PREREG_stage1_AMENDMENT_1.md` stay in force except where this amendment overrides them. Freezes v1 and v2 (manifests
`ef3dd65e...`, `94cf1c51...`, and their snapshots) are preserved untouched; both manifests are listed in the v3 manifest.

## 1. The original pre-registered outcome stands
The pilot ran once under freeze v2 (2026-10-24; disclosure S26). Its pre-registered verdict is
**NOT RESOLVABLE (compute)**: the frozen budget rule chose B = 50 000 steps, where the frozen cap rule allows 24 models per arm
within 96 GPU-hours, below the minimum of 32. That verdict is the result of the pre-registered study. It stays in the record
and is reported in any paper as the primary outcome. The original decision files are frozen in this freeze
(`results_stage1/pilot_outcome_v2/`, byte copies of the pushed files on branch `results-stage1-pilot`, commit `e260526`).

Everything this amendment enables is a **post-pilot amended follow-up**. It must be reported under that label, next to the
original verdict and with this document, never as the pre-registered result.

## 2. What was known when this amendment was made
Made on 2026-10-27, AFTER seeing the pilot's budget outcome and BEFORE any effect-bearing evaluation:
* Seen: the pilot decision record (control pass flags at each checkpoint, the largest validation-NLL improvement to the next
  checkpoint, B, cap, the J0 and evaluation-time inputs), training wall-clock and GPU telemetry, the per-model training
  records (wall time; the training-loss trajectory of one record, CONT seed 0, own-arm training loss with no reference, was
  displayed while checking the record format), and the concurrency benchmark (section 4).
* Not seen, and not computed: no Q1/Q2 statistic of any pilot model exists. The full evaluation at B never ran (the wrapper
  log goes verify, train, evaluate_controls, decide_1, done; no `step50000.npz` exists, checked on the box by file name only).
  Nothing under `results_stage1/pilot/eval/` has been opened.

Why B = 50k (frozen rule): at 10k the UNIF control C1 (r = 4, n = 1) failed and the validation NLL still improved by 0.00522
to 25k; at 25k all controls passed but the largest improvement to 50k was 0.002146 (tolerance 0.002, a narrow miss that is
reported, not re-adjudicated); at 50k all controls passed and the improvement to 100k was 0.00126.

## 3. What changes
1. **Cap-rule budget: 96 -> 128 GPU-hours** (`config/stage1.yaml`, `cap_rule.gpu_hours_limit`). The cap rule itself is
   unchanged: same formula, same contended J0 input (0.011413 s per model-step), same evaluation input (1.446 s per model,
   from the frozen engineering smoke) and the same 1.25 safety factor. At B = 50k the cap becomes 32
   (2 x 10 x 32 x (50 000 x 0.011413 + 1.446) x 1.25 / 3600 = 127.13 h <= 128). The drop rule for secondary families reads
   the same field and uses 128 h; with M = 32 the primary experiment alone projects to 127.13 h, so in practice every secondary
   family that needs training is dropped (Q1-behavioural reuses the primary models and needs none).
2. **The pilot continues from its existing models; nothing is retrained.** Under freeze v3, and only after it is verified:
   copy the original decision aside (it must be byte-identical to the frozen copy), run `pilot-decide` (status NEEDS FULL
   EVALUATION AT B), run the frozen full evaluation at B = 50k on the 32 pilot models (CPU), run `pilot-decide` again. The
   frozen lookup then picks M per family from {32, 64, 128} with M <= cap = 32: a family needs M = 32 (Q1: 1.35 x s1 <= 0.01;
   Q2: 1.35 x s2 <= 0.02) or it is NOT RESOLVABLE. Wrapper: `pilot_tooling/run_stage1_pilot_continuation.sh` (not frozen).
3. **Authorization gate hardening and issuer (procedural; no computation changes; disclosure S28).** The v2 gate accepted a
   self-made TEST-ONLY key with a matching test artifact for the frozen confirmatory config (demonstrated on temporary
   folders: the v2 runner wrote `RUN_LOCK.json`; it never happened on a real run). `scripts/stage1_run.py` now refuses any
   TEST-ONLY key before anything else. New `scripts/stage1_issue_authorization.py` builds the artifact from the same
   `binding_for` function the gate uses. New tests: `tests_stage1/test_issue_authorization.py`.

## 4. Projections (both stated; budget set openly)
Primary experiment at B = 50k, 32 models per arm, 2 replicates x 10 arms = 640 models; evaluation 1.446 s per model.

| Throughput source | s per model-step | with safety 1.25 | without |
|---|---|---|---|
| Contended J0 (frozen cap-rule input; 300-step runs at 16 processes, start-up included) | 0.011413 | 127.13 h | 101.71 h |
| Measured pilot (32 x 100k steps, 8 processes, GPU shared with two other jobs) | 0.010760 | 119.87 h | 95.90 h |
| Concurrency benchmark (frozen J0 script, size M, 1500 steps; 8 / 12 / 16 processes) | [filled after the benchmark] | | |

**Budget: 128 GPU-hours** (proposed; [user's confirmation after the benchmark, date]), the smallest round number at which the frozen cap rule with its
frozen J0 input allows the 32-model minimum at B = 50k. The measured and benchmark rates are reported to set expectations
for wall-clock time and the number of concurrent workers; they do not enter any rule. Considered and not chosen: 256 h
(cap 64; it would matter only if a family's seed sd needed M = 64; real wall-clock up to about 8 days on the shared GPU).

## 5. Unchanged
Estimands, families, arms, alpha, classification rules, the budget grid and convergence criterion, the 32-model minimum, the
power lookup, the controls and critical checks, V-REPRO 1e-4, seeds and seed roles, verdict rules, the secondary families and
their drop order, and the gate's binding (manifest, snapshot, config, pre-registration, pilot decision file, seed set, run id,
validity <= 72 h).

## 6. Execution of the confirmatory run (unchanged rules, stated for clarity)
The confirmatory run needs the user's authorization through the gate, approved by the user in the box session. The gate is
checked when each runner subcommand starts; an artifact is valid for at most 72 h, so training (about 4-5 days) is launched
under one artifact, and evaluation and analysis (and any restart after expiry) need a new artifact for the same run id.
Key and artifact handling: `pilot_tooling/STAGE1_CONFIRMATORY_PLAN.md`.
