# CLAUDE.md: DynaICL orientation (read this first)

This file gives a new session full context in one read. Details are in the files it points to.
Last updated: 2026-10-27. **Start with section 0 (where things stand now)**, then 2h-quater (Stage 1 pilot result). Sections are in
chronological order; older ones (1-2g, 7-8) are historical where they say "not started / not authorised / not a git repo".

## 0. Where things stand now (2026-10-27): read this first

* **Active work: Stage 1 (neural, working name IdentICL) on branch `stage1-planning`** (latest pushed commit: see `git log`).
  Never push `main` without asking; never `--force`.
* **Current freeze: Stage 1 v2** (Amendment 1, 96 GPU-h), manifest `docs/FREEZE_MANIFEST_STAGE1_v2.json` sha256 `94cf1c51...` (section 2h-ter).
* **Stage 1A pilot: DONE on the box (2026-10-24 18:28 UTC). Reported outcome: NOT RESOLVABLE (compute)** (B = 50k, cap 24 < 32 models).
  NOT YET VERIFIED here: the box has not pushed `results-stage1-pilot` yet. Details and the open decision: section 2h-quater.
* **Waiting on the user** for: (1) relaying the push prompt to the box (small pilot files only), then I verify and append disclosure S26;
  (2) the decision: accept NOT RESOLVABLE (compute) as the Stage 1A result, or a post-pilot Amendment 2 (128 GPU-h). Nothing is running.
* Finished stages: 0 (references), 0.5 (REVISE), 0.6 (confirmatory verdict STOP, section 2g). Workstream B (literature) done:
  `docs/literature/`. Workstream C (paper, `paper/`, claims-to-evidence table) NOT started. F1 neural pre-registration and F2 NOT started.
* The box: repo `/home/rama_11187/projects/dynacl`, `.venv-stage1` (torch 2.14.1+cu126), shared RTX A4000 (another user's job,
  `ts2vec_matched`, holds ~8 GB and ~100% utilisation since 2026-10-23: confirm the GPU is free before any Stage 1 GPU work).
  This session cannot message the box; the user relays prompts. Results come back as small files on a `results-*` branch.
* **UPDATE 2026-10-29 (standing instruction of 2026-10-27: all CPU-side work, no GPU, no CUDA).** Pilot VERIFIED from the pushed
  files (S26). The user chose Amendment 2 with conditions (S27), then paused it: the candidate (128 GPU-h; the gate now refuses
  TEST-ONLY keys, a real defect found in the v2 gate, S28; issuer; continuation and confirmatory wrappers; key plan) is on the
  LOCAL, UNPUSHED branch `amendment2-candidate` (`eaf4d3a`). HARD NO until the user says so: pilot full evaluation at B,
  Amendment 2 / v3 freeze, any confirmatory run or authorization, any torch/GPU job, any F1/F2 neural training.
  CPU workstreams (code outside the Stage 1 freeze globs: `dynaicl_families/stage2/`, `tests_stage2/`, `scripts/stage2_*`,
  seeds in `config/stage2_seed_manifest.yaml`; disclosures S28-S31 in docs/DISCLOSURE_LOG_STAGE1.md):
  A (F1): A2 validation PASS (`results_stage2/f1_validation/`); box CPU batch 1 (`results-stage2-cpu-batch1` @ `50a7664`,
  verified S33): F1-V9 mutation matrix PASS, F1 power lookup (Q1 0.01/0.02/0.03, Q2 0.10 at M = 32/64/128); A3 DRAFT
  `docs/PREREG_stage2_F1.md` (section 7 filled). B (F2): `docs/MATH_F2.md`, `dynaicl_families/stage2/f2_var.py`, tests; the per-item
  Monte Carlo target 2e-4 is infeasible for the context-only reference at n <= 5 (S30; user decision pending); map spec NOT written.
  C (F3): map VALID (batch 1, S33): pop vs stab identifiable only at q = 0 (n <= 7) and q = 0.755 (n = 2), h = 1; nothing at
  q >= 2.56 or h = 5; library vs continuous never on held-out systems.
  D: literature D1/D2/D4 done; GAP_AND_NOVELTY.md section 8 (2026-10-29) updated after the F1/F3 maps.
  E: branch `paper-draft`: `paper/claims.yaml` + `paper/tools/build_claims.py` (re-extracts every number from pinned commits;
  PASS 17 verified, 1 pending) and `paper/OUTLINE_track1.md` (CP4, waiting for the user before any full text).
* Rules that bite most often: never edit a frozen file or manifest; disclosure logs are append-only; never open pilot effect files
  (`results_stage1/pilot/eval/`, `phase_d_pilot/PILOT_ONLY_do_not_open_effects.json`); never ask for, store or print a key;
  compute over ~10-15 min runs on the box (detached in tmux, one background waiter, no polling loops); stop at every checkpoint.

## 1. What this project is

**DynaICL** studies in-context learning (ICL) of dynamical systems. The question for later stages: when a
model (e.g. a transformer pretrained on many systems) forecasts a new trajectory from its context, does
it behave like:
- **continuous-prior Bayes**, which generalises population knowledge,
- a **finite-library posterior**, which memorises the training systems, or
- a **context-only estimator**, which uses no population knowledge?

**Stage 0 (this repo, done):** build and validate the *reference predictors* that every later
experiment treats as ground truth, for scalar AR(1) x_t = a x_{t-1} + sigma eps_t. CPU only, no training.
A wrong reference silently invalidates the project, so correctness beats speed and features.
The original Stage 0 spec is in [docs/STAGE0_SPEC.md](docs/STAGE0_SPEC.md).

**Out of scope until asked (Stage 0 wording; neural Stage 1 is now active, see section 0):** the ~2,000-model sweep, chaotic/particle-filter posteriors, neural or
transformer pretraining, cross-model validation, any novelty or publishability claim.

## 2. Status

- Stage 0 code, docs, validation suite and pre-registered separability experiment: **complete**.
- Tests: see section 7 for the last full run and its result.
- Independent audit (a sub-agent re-derived the math and read the code): no critical defects. One major
  quadrature weakness was found and fixed (DECISIONS D-08).
- **Remote mutation matrix: DONE** (Google Colab, 2026-10-09/10; results pasted by the user; archive not saved because the Colab runtime recycled). Baseline row: 20/20 checks pass. All 5 mutations detected (see 7.1). Pipeline exit codes 0/0.
- (Historical, Stage 0.) Not a git repository at the time, so Stage 0 provenance records git as unavailable. Since 2026-10-22 the workspace IS a git repo (section 2f). Integrity evidence is SHA-256 manifests plus read-only snapshot archives.

## 2b. Stage 0.5 (decisive population-advantage experiment): DONE, decision REVISE

- Task spec: the user's Stage 0.5 message (primary Q1 = matched population-aware Bayes vs the strongest
  context-only frontier; secondary Q2 = library vs continuous). No neural training. No novelty claims.
- Step 1 review of Stage 0: `docs/STAGE0_RESULTS_REVIEW.md` (generated by `scripts/review_stage0_results.py`).
- Pre-registration: `docs/PREREG_stage05.md`, **FROZEN** (sha256 fcf7f3a5...; draft sha256 d614c247...).
  delta = 0.02 nats. Per-replicate decision interval = mean +/- 2.24 SE. A class counts only if both replicates agree.
  Decision = PROCEED / REVISE / STOP via `decide()` (P1 reliability, P2 stable across n, P3 robust across r).
- New code: `dynaicl/experiments/population_advantage.py` (resumable; `--checkpoint-dir`),
  `dynaicl/baselines/stability_prior.py` (generic-stability context-only member), schema
  `PopulationAdvantageConfig`, and `tests/test_stage05.py` (scale equivariance, rules, smoke, resume).
- Configs: `config/stage05.yaml` (confirmatory: N = 3378/replicate, seeds 52001/52002/52101/52102/52999;
  config hash 51c7621b7a8f), `config/stage05_pilot.yaml` (seeds 51001-51004), `config/stage05_smoke.yaml`.
- Pilot run: `runs/20261009T190645936218Z_stage05_pilot_16ab5a7e45`. P1 held, and it was used **only** for N
  (sd_q90 = 0.2906). Pilot effects must not be used for conclusions.
- **Confirmatory run done** (Colab, 84 min): `runs/20261010T053729455237Z_stage05_population_advantage_51c7621b7a`
  (hashes match the frozen config and pre-registration; checksums verified; the user's archive is in `colab/`).
- **Pre-registered decision: REVISE.** P1 reliability passed (0/2736 T1, 0/288 T2, quadrature 1.3e-15). P2 failed
  (h = 5 negligible). P3 failed (r = 4 inconclusive). Write-up: `docs/STAGE05_RESULTS.md`; tables:
  `docs/STAGE05_RESULTS_TABLES.md` (from `scripts/summarize_stage05.py`).
- Key findings:
  - The strongest context-only estimator was **generic-stability Bayes** in all 144 cells. It explains 47-86% of
    Stage 0's "population advantage" (r = 1, h = 1, n = 2-10).
  - The population-specific advantage is ~0.043-0.050 nats, confirmed only for h = 1, n <= 3, r <= 1. At h = 5 it is
    <= 0.014, and at r = 4 it is about half that size.
  - Library vs continuous is practically interchangeable for K >= 4 (equivalent in 70/72 E-CONT and 72/72 E-LIB cells).
    It is distinguishable only for a K = 2 library on held-out systems.
- Recommended next step (not started; the user decides): a pre-registered **Stage 0.6 identification-difficulty
  probe**, AR(1) with observation noise (Kalman reference; it must pass validation first). See STAGE05_RESULTS.md section 8.
  No Stage 1 neural experiment is supported yet.

## 2c. Stage 0.6 (noisy-observation probe): v2 FREEZE DONE (2026-10-11); confirmatory run NOT authorised, NOT started

**Question:** with latent AR(1) observed through additive Gaussian noise (q = sigma_v^2 / sigma_w^2 in {0.755, 2.56, 6.5}, control q = 0; r in {0.25, 1, 4};
h in {1, 5}; n = 2..40), does knowing the population prior (noise-aware population Bayes) give a meaningful long-context advantage (L = n 10..40) over the
LOCKED comparator (noise-aware stability-only Bayes) beyond what it gives at zero noise? Rules: `docs/PREREG_stage06.md` (v1 text, frozen, never edited)
plus `docs/PREREG_stage06_AMENDMENT_1.md` (operational changes only). Estimands, delta = 0.02, N = 4000 per replicate, two replicates, 36-contrast studentized max-|t|
cluster bootstrap (alpha 0.05 per replicate, B 20000+), GO / STOP / REVISE / BLOCKED rules, Tier-1 / Tier-2 reproduction, critical checks: all unchanged since v1.
Seeds: confirmatory R1/R2 = the two replicate roots and the bootstrap root listed in `config/stage06_seed_manifest.yaml` (UNUSED; their values live only in that table and
`config/stage06.yaml`, never as literals in code). The seed-role table is the single source of truth (`docs/STAGE06_SEED_ROLES.md` is generated from it, V28).

**History (phases).** A audit and math (`docs/MATH_STAGE06.md`, `STAGE06_AUDIT.md`); B implementation and validation V1-V19; C pre-registration, 36-contrast inference, dry run
(`STAGE06_DECISION_DRY_RUN.md`: GO and STOP reachable, 0 false GO), mutation matrix, **v1 freeze** (manifest `461dfec8...`, snapshot `4114fa43...`); D pilot / operational qualification
(local rehearsal, `phase_d_pilot/PHASE_D_REPORT.md`): everything passed except that the frozen runner had NO authorization gate, so the recommendation was REVISE; then the user approved
the gate change and a re-freeze only -> **v2 freeze**.

**Current frozen state (v2).** Created alongside v1 under `_v2` names; v1 is preserved byte-identical and must never be touched.

| | SHA-256 |
|---|---|
| v2 manifest `docs/FREEZE_MANIFEST_STAGE06_v2.json` (119 files) | `fdb46788cd0fddba59cbc995adf7a3f6f410184e299b4dfc5cbecfa8f3f3fa05` |
| v2 snapshot `dist/stage06_frozen_snapshot_v2.zip` (read-only) | `65a8734f8a9d551189e0ff478b910887f19f19e496ef1d30494712764dce1b2a` |
| v1 manifest / v1 snapshot (preserved) | `461dfec8144104f4d35a513dbf1411041494876331f8f969dda4a9cea09be0c0` / `4114fa43cf737c643c341cccd4026d6fcb54b460bfb12ac4a8a2de8352b492e5` |
| pre-registration (unchanged) | `ec42214a84b1d6999acc156f2532f9d1b745debad5dfd1138458ebcb15b92e66` |
| confirmatory config file (unchanged; config hash `8304d1ab2d37efbf...`) | `4d30069f2ec767cb2e2bb0c0eeaf89f29f56e4fe8623bfa889fd8f34f803c755` |
| pilot bundle `dist/phase_d_pilot_bundle_v2.zip` / notebook `colab/pilot/DynaICL_Stage06_PhaseD_PILOT_v2.ipynb` | `c13dbd06...` / `79f9180b...` |

The user stores the v2 manifest hash OUTSIDE the workspace; the runner takes it as `--expected-manifest-sha256`. `docs/STAGE06_CHANGE_REPORT_v1_to_v2.md` lists all 23 changed or added files (0 outside the
approval) and the byte-identity evidence for the scientific content. `dist/superseded_v2_attempt1/` holds a first v2 freeze that was set aside (disclosure F18).

**What v2 added.** (1) Authorization gate: a confirmatory `run` / `analyze` needs `--authorization A.json --snapshot S.zip` and the user's secret key (env `DYNAICL_STAGE06_AUTH_KEY` or a hidden
prompt): an HMAC-SHA256 artifact binding manifest, snapshot, config (hash and file), pre-registration, amendment, exact seed set, run id, issue time and expiry (<= 72 h); verified at start, on every
resume and at completion; one run id per checkpoint directory (`RUN_LOCK.json`); pilot / test configs take no authorization; test-only artifacts and keys can never authorize. Design and limits:
`docs/STAGE06_AUTHORIZATION_GATE.md`. Issuer for the user's Phase E: `scripts/stage06_issue_authorization.py` (never run with a real key here; no artifact exists in the workspace, V25 asserts it).
(2) Outcome taxonomy `REFUSED` (exit 3) / `CORRUPT` (exit 4) naming path and reason (`dynaicl/experiments/stage06_errors.py`); unit checkpoint schema v2 with a metadata checksum (`record_sha256`).
(3) Seed-role table with allowed / forbidden uses (pilot split into `pilot_evaluation` 62001/62101 and `pilot_bootstrap` 62999). (4) Checks V25 gate, V26 taxonomy, V27 seeded fuzz, V28 seed roles; 12 new mutants.

**v2 validation (exact frozen files, 93 tested files, record `docs/STAGE06_TESTED_FILES_v2.json`):** Stage 0.6 suite 73 passed (544 s), pre-existing suite 101 passed (320 s), mutation matrix 40/40 killed with no
survivors and no kill through an unexpected exception (`STAGE06_MUTATION_MATRIX_v2.md`), calibration diagnostic byte-identical to v1, the two v1 failures (truncated unit JSON, missing qualification path)
reproduced on the v1 snapshot and fixed. Report: `docs/STAGE06_VALIDATION_REPORT_v2.md`.

**Where things are NOT done yet (read this before acting).**
* **Phase D re-run against the v2 snapshot (local rehearsal, pilot seeds only, structural reporting) was STARTED AND STOPPED on laptop 1 (disclosure F19) and is PENDING.** The user moved to a new laptop: `NEW_LAPTOP_START_PROMPT.md` holds the setup steps and the exact start prompt (it also says what to do first: verify integrity, then run `python phase_d_pilot/run_queue.py --set phase_d_v2`, then write the final report with a GO / REVISE / BLOCKED recommendation, then stop). A copy of the old session and memory is in `_claude_session_backup/`.
* **Colab qualification has never been run** (v1 or v2). The pilot notebook is `colab/pilot/DynaICL_Stage06_PhaseD_PILOT_v2.ipynb` (no confirmatory cell, no confirmatory seed, no authorization material).
* The confirmatory run, the issuance of a real authorization artifact, and neural Stage 1 are NOT authorised. Each needs the user's separate explicit go-ahead. Never run the confirmatory config.
* Gate limits (see the gate doc): it does not stop someone who can edit and run code outside the frozen tree, or who holds the key.

**Hard rules for this stage (the user's, verbatim in spirit).** Never use confirmatory seeds or create a confirmatory run directory or checkpoint. Never edit, overwrite or delete a frozen file, the v1 snapshot or either
manifest. Do not run `git init`. Do not change estimands, thresholds, decision rules, N, noise levels or seeds. After the freeze, `scripts/stage06_freeze.py` refuses `record-tested`, `verify-tested` and `freeze`
(it once rewrote a frozen file by mistake: disclosure F1, F8, E2). Do not use pilot effect sizes for any design decision; `phase_d_pilot/PILOT_ONLY_do_not_open_effects.json` must stay unopened.
Disclosure log (`docs/DISCLOSURE_LOG_STAGE06.md`) is append-only: entries 1-17 (before the v1 freeze), F1-F18 (after), errata E1-E3.

**Phase D tooling (outside the frozen set):** `phase_d_pilot/` (harness `pilot_harness.py`, children `pilot_child.py`, helpers `pilot_common.py`, visible job queue `run_queue.py`, notebook builder
`build_phase_d_notebook.py`, `make_change_report.py`, `README_PHASE_D.md`), reports under `phase_d_pilot/work_v2/reports/` (v2) and `phase_d_pilot/work/reports/` (v1, preserved, obsolete for v2).

**Next steps, only on the user's instruction:** (a) user runs the pilot notebook on Colab and returns `phaseD_colab_results.tar.gz`; (b) a Phase E decision (qualification of the confirmatory config on Colab, the user
issues the authorization with their own key, the run, then analysis); (c) Stage 1 only after Stage 0.6 results and a separate decision.

## 2d. Working lessons from the Stage 0.6 sessions (the environment bites; remember these)

* Visible long jobs: the user wants long jobs in a visible terminal with a progress bar and does not want polling. Use `phase_d_pilot/run_queue.py` (`--set validation`, `--set phase_d_v2`,
  `--only 3,12 tag`) launched with PowerShell `Start-Process powershell -ArgumentList '-NoExit','-Command',...`, then ONE background waiter that blocks until `QUEUE_DONE.json` exists. Do not sleep-poll.
* No test may ever wait for a typed key: a hidden-prompt fallback hung a matrix run for hours (F17). Tests must run with a non-interactive stdin. Never run pytest with `-s` plus a pipe.
* Shell heredocs mangle backslashes and some quotes in this environment: write source with the Write or Edit tool (or a file in the scratchpad) instead of inline Python with escapes.
* A background `cmd &` inside a Bash call does not survive as a tracked task: run the real command with `run_in_background`. `find /` over the disk times out: scope searches.
* Windows: replacing a file another process holds open raises PermissionError; killing a process tree is `taskkill /F /T`; `os.getcwd` matters because the shell cwd can silently change to a subdirectory.
* A frozen test that passes vacuously is a trap: the notebook-scan test only ran once a notebook existed (F18). Run scans on the final artifact after building it.
* Report only what was run; label VERIFIED / DERIVED / REPORTED / ASSUMED / UNVERIFIED; never call numerical results exact; stop at every checkpoint the user sets.

## 2e. Continuing on another laptop or in a new session

* Copy the whole project folder byte-for-byte (zip or robocopy; no line-ending conversion), including `dist/`, `docs/`, `config/`, `colab/`, `phase_d_pilot/` and `runs/` (the Stage 0.5 results are needed by Tier-1 and Tier-2).
  `phase_d_pilot/work*` (scratch) and `__pycache__` may be left out. Install Python 3.13.5 and `pip install -r requirements.txt` (numpy 2.2.2, scipy 1.15.1, pyyaml 6.0.2, pytest 9.0.2).
  Verify integrity with the runner's own check: `python -m dynaicl.experiments.stage06_probe verify --config config/stage06_pilot.yaml --manifest docs/FREEZE_MANIFEST_STAGE06_v2.json --expected-manifest-sha256 <v2 manifest hash>`.
  If the environment differs from the frozen environment manifest the runner refuses until `qualify` passes there (by design).
* The Claude Code conversation history lives outside the project: `C:/Users/<user>/.claude/projects/e--study-buddy-DynaICL/` (session `.jsonl` files and `memory/`). Copy that folder to the same place on the new machine
  (the folder name encodes the project path: `E:/study-buddy/DynaICL`), then run `claude --resume` in the project directory. A fresh session without the transcript can recover everything from this file, the memory notes,
  `docs/DISCLOSURE_LOG_STAGE06.md`, `docs/STAGE06_VALIDATION_REPORT_v2.md`, `docs/STAGE06_CHANGE_REPORT_v1_to_v2.md` and `phase_d_pilot/PHASE_D_REPORT.md`.
* The user's authorization key is never stored anywhere. Running jobs and waiters do not survive a move.

## 2f. Git, the Linux box and the Phase D result (2026-10-22; read with the disclosure log F20-F25)

* The workspace IS now a git repo (user-approved `git init`), pushed to the PUBLIC repo `https://github.com/vrhsr/DynalCL` (`main`, commit `4305222`; `runs/` and `dist/` force-added; `_claude_session_backup/` and `phase_d_pilot/work*` excluded via `.git/info/exclude`, `core.autocrlf` off).
  Branches: `phase-d-linux-tooling` (non-frozen Phase D tooling fixes, `29912c9`, `0448e13`), `results-phase-d-v2-linux-20261022` (small result files from the box). Never push or edit anything that changes a frozen file.
* **Compute rule (user): anything over ~10-15 min runs on the remote box only.** The box is a Linux x86_64 machine with its own Claude Code session; this session cannot message it (not listed as a peer), so the user relays prompts. Python 3.13.5 venv via user-space `uv`; deploy key (write, one repo) added by the user; push over ssh port 443.
* On Linux the runner REFUSES until `qualify` passes (`--qualification`). The PILOT-config qualification passed on the box (V4, V6, V11, V13). The harness queue reads `PHASE_D_QUALIFICATION` for the report path.
* **Phase D v2 on the Linux box: 25/25 tasks passed (attempt 3)**; report `phase_d_pilot/PHASE_D_V2_REPORT_linux.md`: GO, scoped to the pilot config on that platform. Attempts 1-2 (15/25, 21/25) failed only in non-frozen tooling (disclosure F22-F24).
  Still NOT done and NOT authorised: Colab qualification, qualification of the confirmatory config, the confirmatory run, the authorization artifact, Stage 1. The harness rewrites `PILOT_ONLY_do_not_open_effects.json` and the pilot YAMLs on each run; restore them with `git checkout` and never open the effects file.
* Full Phase D queue runtime on the box is about 13 min (the queue's own per-task estimates, about 85 min, were far too high).

## 2g. Stage 0.6 CONFIRMATORY RESULT (2026-10-22): pre-registered verdict STOP. Read `docs/STAGE06_RESULTS.md`.

* The user authorized Phase E; it ran once on the Linux box (run id `phaseE-20261022`, 50/50 units, 3.1 min). All six critical checks PASS. **Verdict STOP:** all 18 long-context gains have an adjusted upper bound below delta = 0.02 in both replicates (largest +0.0077);
  the increment over zero noise is at most +0.0012 and negative for the larger noise levels. Files: `results_stage06_confirmatory/phaseE-20261022/` (checksums verified), disclosure log F26-F29.
* **Do not re-run the confirmatory config, issue another authorization, or re-analyse** (the runner refuses a second run for that run id; any new run would need a new, user-initiated decision and would not be pre-registered).
* The authorization key for this run was generated on the box by the user's instruction and shredded (F26); the artifact stays off-repo. Never ask for, store or print any key.
* Stage 1 (neural) is NOT started or authorised. What it should do given STOP (population advantage only at short contexts in these AR(1) families, even with observation noise) is the user's decision.

## 2h-quater. Stage 1A PILOT RESULT (2026-10-24, relayed 2026-10-27): reported NOT RESOLVABLE (compute); NOT YET VERIFIED

* Ran once on the box via `pilot_tooling/run_stage1_pilot.sh` (pilot seeds, `config/stage1_pilot.yaml`; 32 models = 8 each of CONT, UNIF,
  LIB-2, LIB-16, size M, 100k steps, checkpoints 10k/25k/50k/100k). Finished 2026-10-24 18:28 UTC; wrapper step `done`.
* REPORTED by the box (not yet checked here): all 32 models trained; controls evaluated; `pilot-decide` ran ONCE; log line
  `B=50000 M1=None M2=None cap=24 secondary=None`; status **NOT RESOLVABLE (compute)** (PREREG v3 section 8 and Amendment 1:
  the cap at 50k under 96 GPU-h is 24 < the 32-model minimum).
* Meaning (frozen rules): the convergence rule did not qualify 10k or 25k (a control failed or validation NLL at positions 0-2 still
  improved by >= 0.002 nats to the next grid point; which one is in `pilot_decision.json`) and qualified 50k. Because pass 1 stopped,
  the full evaluation at B NEVER RAN: no Q1/Q2 effect information exists. `results_stage1/pilot/eval/` holds only controls and
  validation NLL and must still never be opened or pushed.
* NOT DONE: the box did not push the results (no `results-stage1-pilot` branch on origin as of 2026-10-27). The push-only relay prompt
  (no compute) is `pilot_tooling/RELAY_push_pilot_results.md`; it also asks the box to confirm the 50k checkpoints still exist (do not delete
  weights). After the push: verify the freeze-verify line in `wrapper_log.txt`, `git_head.txt`, the training records, the timings and
  `pilot_decision.json`; then append disclosure S26 (pilot outcome); then write appendix A.
* OPEN DECISION (the user's): (1) accept NOT RESOLVABLE (compute) as the Stage 1A result (clean, pre-registered, uninformative);
  (2) RECOMMENDED if ~5-6 days of shared GPU are acceptable: post-pilot Amendment 2, budget 96 -> 128 GPU-h. Projection at B = 50k:
  2 replicates x 10 arms x 32 models x (50000 x 0.01141 + 1) s x 1.25 = 127 h -> cap 32 (M = 40 needs about 159 h). Then, on CPU with no
  retraining, the full evaluation at B on the existing pilot models and `pilot-decide` again (M forced to 32; a family whose lookup
  needs 64 becomes NOT RESOLVABLE; all secondary families dropped). Must be disclosed as made after seeing the pilot's budget choice
  (convergence information only, no effects). Requires a v3 freeze alongside v1/v2, suite + mutation matrix, and the user's
  authorization for the confirmatory run. (3) NOT recommended: recompute the cap from measured pilot timings instead of J0
  (looks like choosing the input that gives feasibility). Lowering the 32-model minimum is off the table (audit A1 power fix).

## 2h-ter. Stage 1 freeze v2 (Amendment 1: cap-rule budget 96 GPU-h), 2026-10-24: THE CURRENT FREEZE

* Manifest `docs/FREEZE_MANIFEST_STAGE1_v2.json` (57 files) sha256 `94cf1c51c80763ce3da4bc37134a4aa03e024744c4e231f2898ffd72a6bc5f75`;
  snapshot `dist/stage1_frozen_snapshot_v2.zip` sha256 `67ed86062f6f9079f719f3896f8ae7fd422dce9878eef9589cbe8a917c56d2a9`;
  freeze commit `3a29c15`; amendment `docs/PREREG_stage1_AMENDMENT_1.md`. v1 (below) preserved untouched. Caps at 96 h:
  120 / 48 / 24 at B = 10k / 25k / 50k (B = 50k still NOT RESOLVABLE (compute)). Pilot wrapper: `pilot_tooling/run_stage1_pilot.sh`
  (not frozen). Pilot DONE (section 2h-quater). Disclosure log S1-S25.

## 2h-bis. Stage 1 FROZEN before the pilot (2026-10-24)

* Manifest `docs/FREEZE_MANIFEST_STAGE1.json` (55 files) sha256 `ef3dd65e749a49ed5600e95fc613d3192d5ac62d9a902485b290fa25f7369da0`;
  snapshot `dist/stage1_frozen_snapshot.zip` sha256 `7a070c80d2444b6a94e7b7310cf40f78e376ffeb46aeefb01cf0929387139be0`; commit `f8e1dab`.
  PREREG is v3 (budget grid {10k, 25k, 50k, 100k} with a convergence criterion; min 32 models per arm; contended J0 caps 56/24/8 at
  10k/25k/50k, so only B = 10k is feasible; NOT RESOLVABLE (compute) otherwise). Never edit a frozen file; verify with
  `python scripts/stage1_freeze.py verify --manifest docs/FREEZE_MANIFEST_STAGE1.json --expected-sha256 <hash>`.
* Next, only on the user's approval: the pilot (pilot seeds; `scripts/stage1_run.py` with config/stage1_pilot.yaml), then
  pilot-decide, then the confirmatory run under the user's authorization artifact. Disclosure log S1-S23.

## 2h. Stage 1 (neural; working name IdentICL), branch `stage1-planning` (2026-10-23): at checkpoint 3, NOT frozen

* Read `docs/STAGE1_PLAN.md` (v2, approved), `docs/PREREG_stage1.md` (draft v2, proposed for freezing), `docs/DISCLOSURE_LOG_STAGE1.md`
  (S1-S17, append-only), `docs/STAGE1_INDEPENDENT_AUDIT.md`, `docs/literature/` (bibliography, gap/novelty: AR(1)-only is not main-track).
* Done: Stage 1A separability map (box, `results-stage1-map-1A`), F1 (unknown sigma) references + map (`results-stage1-step3`),
  operating characteristics v2 (bootstrap-calibrated; v1 power claims WITHDRAWN after the audit), power lookup, neural code
  (`dynaicl_neural/`), runner `scripts/stage1_run.py`, freeze tool `scripts/stage1_freeze.py`; tests_stage1 82 passed; mutation matrix 7/7.
* Box: repo `/home/rama_11187/projects/dynacl`; `.venv` (frozen Stage 0.6 stack, untouched) and `.venv-stage1` (torch 2.14.1+cu126).
  The GPU (RTX A4000) is shared; GPU jobs only after the user says it is free. Compute > 10-15 min runs on the box.
* Next (user decides): J0 + engineering smoke on the GPU (`scripts/stage1_box_j0_smoke.sh`), then the freeze BEFORE the pilot, then
  the pilot (pilot seeds only), then the confirmatory run under the authorization gate. F2 is NOT started (needs F1 approval).
* Main risk: Q1 is resolvable only if the between-seed sd of a model's regret is <= about 0.015 nats (lookup).

## 3. Working rules the user set (keep following them)

1. **Correctness first. Report only what was run.** Paste real output. Never weaken, skip or delete a test to make
   it pass. When something fails, decide whether the code, the test or the math is wrong, and say which.
2. **Label every claim** DERIVED (in docs/MATH.md), TESTED (name the test), ASSUMED, or UNVERIFIED.
3. Use "analytically exact" only for closed forms. Use "numerically approximated with verified convergence"
   (with method, resolution and measured error) for quadrature, grids and MC. Never say "numerically exact".
4. Every tolerance and threshold needs a stated justification. All thresholds are hypotheses.
5. Use meaningful names (`ConjugateGaussianAr1Predictor`, not `Model1`). Default stack only: numpy, scipy,
   pytest, pyyaml, float64. Add a dependency only with a reason.
6. **Compute policy:** run locally only jobs under ~10 minutes. Anything longer (CPU or GPU) gets
   packaged as a pipeline script with the command, expected runtime and what to send back. The user
   runs it on remote hardware and returns results.
7. Plan first for big tasks (PLAN.md), then proceed. If something blocks, state it and take the most
   conservative option.

## 4. Invariants (breaking any of these silently invalidates the references)

- **Likelihood is conditional on x_0, and x_0 is drawn independently of a.** Contexts always start at the
  trajectory's x_0, and `evaluation/harness.make_context` is the *only* place contexts are cut. Never
  burn in, never start from the stationary distribution, and never cut a mid-trajectory context
  (MATH 1.1-1.2).
- **Prior matching:** the matched Bayes reference for a condition uses exactly that condition's prior and
  likelihood, enforced by fingerprints (`references/matched.py`; one guard function,
  `check_system_distribution`). Optimality diagnostics refuse unmatched references.
- **Information access:** predictors receive only an immutable `ContextWindow` (float64; other dtypes are
  rejected). Ground truth stays in evaluator-private `GroundTruth`. Context-only predictors take
  no prior or library.
- **Randomness:** `NamedStreams` (rng.py) keys streams by SHA-256 of the name, with per-item children. Adding
  streams or items never shifts others. Results are bitwise reproducible and independent of worker count.
- **Calibration** is a pass/fail condition for the *matched* reference only. For everything else it is a
  measurement.
- **Point-only predictors** (`PointPredictor`, e.g. a future MSE-trained net) are never scored with
  log score or CRPS.
- **Overflow:** a predictive that float64 cannot represent raises `FloatingPointError`. It never returns inf/NaN.

## 5. Repository map

```
dynaicl/systems/      ar1.py (simulator, transition_pairs, Horner c_h), priors.py (P-GAUSS, P-NIG, P-STABLE),
                      context.py (ContextWindow, GroundTruth), library.py, conditions.py (E-CONT/E-LIB), splits.py
dynaicl/references/   predictive.py (Gaussian/StudentT/Mixture/Quadrature/Empirical/PointForecast), base.py,
                      conjugate.py, quadrature.py (adaptive panel placement), library.py, known.py (oracle), matched.py
dynaicl/baselines/    flat_prior.py, ols.py, kernel.py (rolling-origin/blocked/LOO), persistence.py, family.py (frontier)
dynaicl/metrics/      scoring.py (log score, CRPS, PIT/coverage, paired diffs), calibration.py
dynaicl/evaluation/   harness.py (make_context, evaluation sets, scoring, guarded optimality diagnostics)
dynaicl/validation/   oracles.py (raw-likelihood grids, truncnorm closed forms, IS), checks.py (A-F, J),
                      mutations.py (G), kernel_schemes.py (K)
dynaicl/experiments/  separability.py (the Section 7 map; CLI)
dynaicl/config/       schema.py (strict typed YAML schema + hash);  dynaicl/provenance.py (run records)
config/               separability.yaml (main), separability_pilot.yaml, smoke.yaml
scripts/              mutation_report.py, remote_validation_pipeline.sh, build_colab_bundle.py
colab/, dist/         generated Colab notebook and code bundle (rebuild with build_colab_bundle.py; dist/ is gitignored)
tests/                test_a..k + metrics, matched_guard, config_provenance (conftest: DYNAICL_MUTATION hook)
docs/                 MATH.md (derivations), DECISIONS.md (D-01..D-24), RISKS.md (R-01..R-16),
                      PREREG_separability.md (frozen), STAGE0_SPEC.md (original task spec)
runs/                 run outputs (gitignored); see section 7 for which runs are current
dynaicl/references/kalman_quadrature.py, systems/noisy.py, evaluation/noisy_harness.py   Stage 0.6 noisy-observation reference (Kalman likelihood on a shared node set)
dynaicl/experiments/stage06_{analysis,probe,authorization,errors,freeze}.py   Stage 0.6 frozen analysis, runner, authorization gate, REFUSED/CORRUPT taxonomy, freeze tooling
dynaicl/config/stage06_{schema,seed_roles}.py, config/stage06*.yaml (+ stage06_seed_manifest.yaml = seed-role table)   Stage 0.6 configs and seed roles
dynaicl/validation/checks_stage06*.py, mutations_stage06*.py   checks V1-V28 and 40 mutants; tests/test_stage06_*.py
scripts/stage06_*.py   audits, dry run, mutation matrix, calibration diagnostic, freeze, issuer; phase_d_pilot/   Phase D tooling (NOT frozen)
dist/ (snapshots, bundles), colab/ (notebooks), docs/STAGE06_*.md, docs/PREREG_stage06*.md, docs/DISCLOSURE_LOG_STAGE06.md   Stage 0.6 evidence and freezes
PLAN.md, README.md    plan and status; setup, exactness table, commands, how to add a predictor
```

## 6. Commands

```bash
python -m pytest -q                         # full suite (~6-7 min locally)
python -m pytest -q -m "not slow"           # skips F (optimality, ~2.5 min)
python -m dynaicl.experiments.separability --config config/smoke.yaml          # ~10 s
python -m dynaicl.experiments.separability --config config/separability.yaml --workers 7   # ~6 min
bash scripts/remote_validation_pipeline.sh  # REMOTE ONLY (~35-45 min on 8+ cores, ~1-1.5 h on Colab free): full mutation matrix
python -m dynaicl.experiments.stage06_probe verify --config config/stage06_pilot.yaml --manifest docs/FREEZE_MANIFEST_STAGE06_v2.json --expected-manifest-sha256 <hash>   # Stage 0.6 integrity check (no compute)
python phase_d_pilot/run_queue.py --set validation | --set phase_d_v2    # visible progress window for long Stage 0.6 jobs (see 2d)
python scripts/build_colab_bundle.py        # rebuilds dist/dynaicl_stage0_bundle.zip + colab/DynaICL_Stage0_Colab.ipynb (run after ANY code change)
python scripts/mutation_report.py --checks A6 C1 J1 --pytest --pytest-args tests/test_c_identities.py tests/test_j_leakage.py --jobs 6  # ~40 s runner smoke; exits 1 by design
DYNAICL_MUTATION=off_by_one_likelihood python -m pytest -q   # whole suite under one injected bug
```

The shell here is Windows Git Bash plus PowerShell. Long bash heredocs with nested quotes have failed in
this environment, so write patch scripts to the scratchpad and run them, or use the Edit tool.

## 7. Results to date

### 7.1 Validation (local)

- **Last full pytest run (final code, 2026-10-09):** 95 passed, 0 failed, 755.7 s. (CPU was shared with the
  experiment run; on an idle machine it takes about 6.3 min.) The slowest tests are F (optimality) and E (calibration).
- **Google Colab (Linux, Python 3.13.16, 2 vCPU, pinned stack), 2026-10-09:** baseline suite 95 passed in
  413 s. That is a second, independent platform. Its mutation matrix finished (see above).
- **How to read the remote mutation matrix:** in the pytest phase the mutation is monkeypatched only in the
  main pytest process. `test_i_same_config_and_seed_bitwise_identical...` compares workers = 1 (mutated)
  against workers = 2 ('spawn' workers, NOT mutated), so it is expected to fail under any mutation that
  changes experiment outputs. Count it as an artefact, not as meaningful detection. The meaningful
  detectors are the check matrix (phase A) and the other tests.
- Remote pipeline runner smoke-tested locally on a subset (`--checks A6 C1 J1 --pytest --pytest-args
  tests/test_c_identities.py tests/test_j_leakage.py --jobs 6`, 38 s). The machinery works. It exits 1 by
  design there, because that subset cannot detect the guard-bypassed mutation (only E/F do).
- A3 quadrature convergence: worst node-doubling error **1.7e-13 nats** over 8 regimes x h in {2, 5, 20, 50},
  including the audit's wide-posterior regimes, with no panel cap hit. The target is 1e-6 nats (MATH 5.3).
- E calibration of the matched reference: 126 tests (SBC, PIT KS, 50/80/95% coverage) across 5 conditions
  (P-GAUSS, P-NIG, P-STABLE truncnorm, P-STABLE uniform, E-LIB) and several (n, h). No failures at the Bonferroni level.
- F optimality: 190 paired comparisons, none violated.
- G mutation detection (targeted detectors inside pytest):

  | Mutation | Detected by |
  |---|---|
  | wrong prior variance | A1, C1, E (P-GAUSS) |
  | off-by-one likelihood index | A1, A6, C1 |
  | future value leaked into the context | J1, E (P-GAUSS) |
  | unmatched reference | the guard (`UnmatchedReferenceError`) in E and F |
  | unmatched reference with all guards disabled | E (E-LIB) and F (E-LIB), statistically |

  Full remote matrix (Colab): wrong_prior_variance by A1,B1,C1,C2,E,F; off_by_one by A1,A2,A5,A6,B1,B2,C1,C4,D2,E,F; future_leak by E,F,J1; unmatched_reference by E,F,J1 (guard error); guard_bypassed by E,F (statistical). Whole pytest suite under mutation: 6/12/5/6/4 of 95 tests fail respectively, baseline 0. As predicted, test_i_same_config... fails under mutations that change experiment outputs (spawned workers are unmutated): an artefact.
- Oracle findings: scipy truncnorm moments are off by ~6e-11 in deep tails (D-07). The NIG 2-D grid has
  ~1e-8 range error at n = 2 (accounted for in its tolerance).

### 7.2 Runs (runs/ is gitignored; config hash 9123175bb3 = config/separability.yaml)

| Run | Role |
|---|---|
| `runs/20261009T094047949167Z_separability_9123175bb3` | **CURRENT main result.** Final code. 60 cells x 2337 eval items. Pre-registration sha256 f3401ff0... recorded in provenance. |
| `runs/20261009T090315191651Z_separability_9123175bb3` | Superseded (pre-audit quadrature). Item-level log scores differ from the current run by <= 2e-10 nats. |
| `runs/20261009T090102869678Z_separability_pilot_4071d8a6c5` | Pilot (seed 7110, 300 items). Used only to set N = 2337 via the PREREG rule (sd_q90 = 0.2417). |

### 7.3 Separability map (current run; pre-registered rule, delta = 0.02 nats)

- **Theorem-level:** T1 0/516 violations (min z = -0.48), T2 0/60 failing cells (min p = 5.1e-3), T3 pass,
  max quadrature error at targets 1.3e-15.
- **Regimes separable for all three strategy pairs: 2 of 60.** Both are E-CONT, sigma = 1, n = 5, h in {1, 5}, K = 4.
- **E-LIB, library vs continuous-prior Bayes: "equivalent" in all 48 cells** (max |gap| 0.0085 nats).
- E-CONT, library vs continuous: separable only for K = 4 (12/12 cells; gap 0.025-0.061 nats). K >= 16 is equivalent.
- `frontier_all` = flat-prior Bayes (the sigma-informed member) in every cell. Matched vs frontier_all is separable only at n = 5.
  `frontier_strict` (mostly OLS Student-t) is separable from matched up to n = 20, and equivalent at n = 80.
- 30/60 cells have all three strategies mutually equivalent. G is ill-conditioned in 50% of cells.
- Kernel baselines fall back to persistence in 100% of n = 5, h = 5 items (only 1 analog pair).

### 7.4 Diagnostic hypotheses (observed vs pre-registered expectation)

- H1 (matched minus flat-prior shrinks with n): **as expected**, monotone in all 4 series. n = 5: 0.036-0.155 nats;
  n = 80: <= 0.001.
- H2 (small-K library overconfident on E-CONT): **as expected for K = 4** (95% coverage 0.923-0.947, z down to
  -6.0). K >= 64 is within about +/-2 SE. A ~2 SE dip at 50% coverage at n = 80 appears for *every* predictor,
  including the matched reference on the same items, so it is paired-item noise, not a library effect.
- H3 (library approaches continuous as K grows): **as expected.** |gap| decreases monotonically in K in all 12
  series (K = 4: 0.025-0.061; K = 256: <= 0.0007).
- H4 (E-LIB library advantage changes with n): the advantage is tiny everywhere (<= 0.0085 nats), largest at
  K = 4, n = 5, and it shrinks with n. **This contradicts the pre-registered expectation** that "the library
  should gain at large n". Explanation (DERIVED reasoning, not quantified): both posteriors concentrate on
  the true a, and the continuous predictor's excess predictive variance over a known-a predictor is
  about v_n x_n^2 = O(1/n). The gap is bounded by that, so it must vanish with n.
- Kernel schemes (test K): at n = 10, h = 3, rolling-origin is worse than LOO by 1.53 +/- 0.51 nats (only 3 validation
  points). At n >= 30 the schemes differ by <= ~0.03 nats.

### 7.5 Reading against the pre-registered criteria (PREREG section 8)

- PROCEED: technically met, **narrowly**. T1-T3 pass, and 2 cells are separable for all pairs, both at K = 4 and n = 5.
- REVISE signal: the library-vs-continuous distinction, which matters most for "memorisation vs generalisation",
  is within 0.0085 nats everywhere under E-LIB, and within delta for K >= 16 under E-CONT.
- STOP: not met. Matched vs frontier is separable at n = 5 (and to n = 20 against the strict frontier).
- **The decision is the user's.** It has not been made.

## 8. Next steps (candidates; the user decides)

1. **User:** run `bash scripts/remote_validation_pipeline.sh` remotely and send back the tar.gz. Then verify
   matrix.md (each mutation detected, baseline all pass) and record the result here (section 7.1).
2. **Decide PROCEED vs REVISE** for Stage 1 (section 7.5).
3. **Smallest next experiment (a candidate, not yet pre-registered):** a targeted probe of whether *any*
   AR(1) regime separates library from continuous-prior Bayes under E-LIB by >= delta. Rationale: the gap is
   bounded by parameter-uncertainty variance v_n x_n^2, so look where that is large: n in {2, 3, 5, 10},
   K in {2, 4, 8}, h in {1, 5, 10}, and a larger initial-state signal (x_0 sd 3-5 x sigma). Same code via a new
   YAML. Minutes of CPU. Pre-register it first (copy PREREG_separability.md).
4. Optional extensions (spec Section 8, not started): AR(1) with observation noise (Kalman likelihood with
   a grid over a), and VAR(1) with a matrix-normal-inverse-Wishart prior.
5. Housekeeping: `git init` and a first commit, so runs record a commit hash (R-11). Only if the user wants it.
