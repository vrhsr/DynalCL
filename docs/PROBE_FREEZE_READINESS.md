# Seed-variance probe: what remains before it can be frozen (prepared 2026-11-02; nothing frozen or run)

User instruction (S48): prepare the probe (`docs/PREREG_seed_variance_probe.md`) for freezing: pre-registration, freeze and
authorization steps; do not freeze or run anything; the GPU go-ahead comes separately. Template: the Stage 1A path
(`docs/PREREG_stage1.md`, `scripts/stage1_freeze.py`, `scripts/stage1_run.py`, disclosures S14-S25) and
`paper/research_audit/GPU_EXECUTION_CHECKLIST.md`.

## 1. Decided
Arms F1 CONT, LIB-8, LIB-16 and F2 LIB-64 (S44); 16 models per arm; size M; checkpoints 10k / 25k / 50k; heads m = 8 (F1,
univariate; F2, bivariate full covariance); measurement only (between-seed sd with seed-bootstrap intervals; no
classification); the F2 arm also measures the F2 cost per model-step; decision threshold for option B written in the draft.

## 2. Code that does not exist yet (VERIFIED by reading `dynaicl_neural/`, 2026-11-02)
The frozen Stage 1A neural code covers only the known-scale scalar AR(1): `data.SequenceSampler` draws a with sigma = 1;
`models.ModelSpec` is univariate (scalar input, univariate mixture head, m = 2 by default); `evaluate` scores against the
known-scale references through `ContextStats`. Needed, outside the frozen Stage 1 globs (new modules, so the frozen files stay
untouched):
1. F1 sampler: per-sequence (a, sigma) from P_F1 (CONT) or from the model's own K atoms (LIB-K), sigma varying, x_0 ~
   N(0, r^2), r uniform on {0.25, 1, 4}; common random numbers across arms as Stage 1A.
2. F1 evaluation: per-context KL(reference || model) against `UnknownScaleReference` / `ScaleLibrary` on a whole-line
   tan-substitution grid (as the F1 head floor), regret R, G_pop, G_lib; seed-bootstrap sd per cell.
3. F2 model: bivariate input tokens and a bivariate mixture head (m = 8, Cholesky-parametrised covariances).
4. F2 sampler: (A, Sigma) from the truncated MNIW (exact rejection, as `f2_var.sample_truncated_prior`), per-model library of
   64 atoms; bivariate trajectories.
5. F2 evaluation: realised log scores against lib_64 (exact) and population Bayes (Monte Carlo, per-item SE as the F2 map);
   regret against the model's own library by a 2-D quadrature or by realised scores on in-library systems.
6. Per-step cost logging (wall time per step at the run's concurrency, GPU utilisation and other processes), both families.
7. Runner and probe config (seed roles registered in `config/stage2_seed_manifest.yaml`: 86001 / 86101 / 86201 / 86901 /
   86999 as proposed), provenance, resumable checkpoints.
8. Tests: unit tests of 1-6 (shapes, causality, sampler laws against the references' priors, head normalisation, evaluation
   against a closed-form case), an end-to-end CPU test with a tiny model, and a mutation matrix adapted from Stage 1A.

**Blocker for implementation:** items 1-8 can be written now, but testing them needs torch on CPU, which the standing rule
excludes until the user's go-ahead ("no torch jobs"). Estimated effort once allowed: 1-2 days of code and tests.

## 3. Freeze and authorization steps (in order; each waits for the user where marked)
1. [USER] Allow CPU torch for unit tests (or wait for the GPU go and do it then).
2. Implement and test section 2; adapted mutation matrix; record tested files.
3. [USER, GPU go] J0 timing and an engineering smoke on the box (test seed role); confirm the GPU is free first.
4. Finalise the draft: compute from the measured timing, the F2 threshold from batch 7, everything seen so far (S40-S48).
   (S52: the F2 threshold from batch 7 is in draft 0.2: cell set C / C', tiers U <= 0.02 -> 32 models, U <= 0.05 -> 64
   models without K = 1024. Also needed now: the F2 arm trains at length 81, so J0 / the smoke must time the F2 model at
   length 81 as well as the F1 models at length 20; open: K = 2 operating characteristics or drop the arm.)
5. Freeze with a generalised freeze tool (new manifest next to the Stage 1 v1 / v2 manifests, which stay untouched),
   read-only snapshot, `verify`; [USER] stores the manifest hash outside the workspace.
6. Authorization: a measurement-only probe makes no confirmatory decision, so the keyed gate is not strictly required;
   recommended anyway for consistency, with the gate fix from `amendment2-candidate` (refuse TEST-ONLY keys; S28) included in
   the frozen code. [USER] issues the artifact on the box with their own key.
7. [USER] Relay the run (detached; one waiter); results to a `results-*` branch; verification and disclosure here.

## 4. Decisions (user, 2026-11-02, S49)
1. CPU torch ALLOWED, narrowly: unit tests and smoke runs of a few steps only, CPU only, test seed roles only, no production
   seeds, nothing frozen, no GPU / CUDA.
2. The probe uses the authorization gate, with the S28 test-key fix ported from `amendment2-candidate` (`eaf4d3a`) into the
   probe's new runner and tested (the gate test must fail on the v2 behaviour and pass on the fixed one).
3. Go / no-go rule for option B fixed in the draft (upper confidence bound of the F2 seed sd; no carry-over assumed beyond a
   stated screening use).
