# Stage 0.6 Phase A audit

Labels: VERIFIED (inspected artifact or named passing test), DERIVED (MATH_STAGE06.md), REPORTED, ASSUMED, UNVERIFIED.

## 1. Stage 0.5 artifacts and the reported findings

| Item | Status | Evidence |
|---|---|---|
| Stage 0.5 run `runs/20261010T053729455237Z_stage05_population_advantage_51c7621b7a` | VERIFIED | All 13 output checksums match. The `runs/` copy is byte-identical to the members of the user's archive `colab/<same>.tar.gz`. |
| It used the frozen config and pre-registration | VERIFIED | provenance config_hash 51c7621b7a8f; pre-registration sha256 fcf7f3a5..., which equals the current `docs/PREREG_stage05.md`. |
| Reference reliable and calibrated in all cells | VERIFIED | summary.json: T1 0/2736, T2 0/288, quadrature error <= 1.3e-15. |
| Stability-only predictor strongest in all 144 cells | VERIFIED | frontier_selection.json: frontier_ctx = stability_prior_bayes in 144/144. |
| Verdict REVISE; P2 (h = 5) and P3 (r = 4) failed; delta = 0.02 | VERIFIED | summary.json decision; run config.yaml (`practical_effect_nats: 0.02`). |
| Library and continuous interchangeable for K >= 4 | VERIFIED | STAGE05_RESULTS_TABLES.md section 3, generated from contrasts.csv by `scripts/summarize_stage05.py`. |
| Git provenance | **Not available** | The workspace is not a git repository (provenance: "fatal: not a git repository"). This affects the Phase C freeze (section 6). |

No discrepancy was found between the REPORTED Stage 0.5 findings and the artifacts.

## 2. The current implementation (VERIFIED by reading the code)

1. **Generative process.** `systems/ar1.simulate_ar1`: x_0 = given; x_t = a x_{t-1} + sigma eps_t. `systems/splits.generate_split`:
   x_0 = mean + sd z_0 with sd = r (sigma = 1 in Stage 0.5), drawn independently of a. Population prior (E-CONT):
   P-STABLE truncated normal, mu0 0.4, tau0 0.3 on (-0.95, 0.95) (`systems/priors.StableCoefficientPrior`). sigma is known.
2. **Observation noise.** There is none: the context *is* the latent path. **Indexing:** `harness.make_context` cuts x_0..x_n,
   so n counts transitions (n + 1 values), and the target is `traj[n + h]`.
3. **Likelihood.** Conditional on x_0. The quadrature uses the exact completed square in a
   (`references/quadrature.py`: `loglik = -0.5 (S_xx/sigma^2)(a - a_hat)^2`), and node windows are derived from that quadratic form
   (`quadratic_window`). **This does not carry over to noisy observations**, because the Kalman log-likelihood is not quadratic in a.
4. **Stability-only predictor.** `baselines/stability_prior.StabilityPriorBayesPredictor` = uniform prior on (-0.999, 0.999), known
   sigma, the same quadrature as the population reference.
5. **Frontier selection.** Per cell, on a separate selection split (seed root 52002, 1000 items), by mean log score, then frozen for
   both replicates (`population_advantage.run_unit`).
6. **Two-replicate rule.** Per replicate, mean +/- 2.24 SE vs delta. A class is confirmed only if both replicates agree. The SE is iid over
   items **within a cell**, which is valid there because each item is an independent system and no averaging over n was done. The
   bootstrap resampled items independently (`bootstrap_interval`). **Assumption to revisit:** cells at different n share trajectories
   (common random numbers, DECISIONS D-24). Stage 0.6 averages over n, so it needs a cluster bootstrap over systems.
7. **Fingerprints, checkpoints, reports.** `RunRecorder` (config hash, pre-registration sha256, packages, platform, seeds, checksums);
   unit checkpoints keyed by config hash with atomic replace (`run_units`); resume tested (`test_checkpoint_resume_gives_identical_results`).
8. **CPU cap and Colab.** User policy: local jobs under 10 min. `scripts/build_colab_bundle.py` builds a zip with a SHA-256 manifest
   and notebooks; the Stage 0.5 notebook checkpoints to Google Drive.
9. **Stored per-item data.** Stage 0.5 stored `item_contrasts.npy` (720 x 3378): per-item `matched_minus_frontier_ctx` (= matched -
   stability, because the frontier was always stability) and library-minus-continuous. **Raw per-predictor log scores were not
   stored.** Tier-1 regression (zero-noise reproduction) can therefore target the stored per-item primary contrast exactly.

## 3. Reusable without change

Priors (`StableCoefficientPrior`), seeds (`NamedStreams`), splits and leakage assertions, `ContextWindow` (it carries the observed
values only), the `Predictive` classes (Gaussian mixtures), scoring (log score, PIT, coverage), `RunRecorder`, checkpointing,
the Colab builder, the Stage 0.5 context-only family (as the **noise-naive** secondary baselines), and the Stage 0.5
two-replicate classification functions (with a cluster bootstrap added).

## 4. Necessary changes (proposed; no code changed in Phase A)

1. **Simulator:** latent path plus noisy observations y_t = x_t + sigma_v nu_t, with nu drawn from a **new, separate named stream**
   so that the latent path for a given seed is unchanged by adding noise. GroundTruth gains the latent path; predictors never see it.
2. **New reference module** (e.g. `references/kalman_quadrature.py`): a Kalman likelihood and predictive given a, vectorised over quadrature
   nodes, with the shared filtering prefix across n; composite Gauss-Legendre over the **full bounded prior support** (both priors
   are bounded), with resolution set by convergence tests. `NoisyObservationBayesPredictor(prior, sigma_w, sigma_v, x0_sd)` covers
   both the population-aware reference and the noise-aware stability-only comparator, which differ only in prior.
3. **Zero-noise branch:** sigma_v = 0 routes to the validated Stage 0.5 code path. The Kalman path is separately tested for
   regression at sigma_v = 0 (well-defined because r > 0) and for continuity as sigma_v -> 0.
4. **Independent validation code:** Cholesky joint-Gaussian oracle, a separately implemented integration over a, Monte Carlo, and the
   new mutations (sigma_v omitted from the predictive, wrong sigma_v, prior mismatch, latent state passed to a predictor).
5. **New experiment runner** with a cluster bootstrap, long-context aggregation, the zero-noise control contrast, Tier-2 reproduction,
   frozen-fingerprint verification at start-up, and a GO/REVISE/STOP/BLOCKED decision function.
6. **New Colab notebook** `colab/DynaICL_Stage06_Colab.ipynb`.

## 5. Workload (rough, from Stage 0.5 per-prediction timings: VERIFIED earlier profiling, this machine)

Per (system, q, r), with n = 2..40 and h in {1, 5} there are 78 contexts.
* Noise-aware predictors with a shared-prefix Kalman pass over about 1024 nodes: about 10-20 ms (ASSUMED, to be measured).
* **Noise-naive Stage 0.5 family (8 members, about 4.5 ms per context): about 0.35 s. This is the dominant cost.**

For example, 2000 systems x 2 replicates x 4 q x 3 r gives about 4.7 CPU-hours, roughly 2.3 h on Colab's 2 vCPU. Option to decide in
Phase C: evaluate the noise-naive (secondary, non-decisional) baselines only on a subset of n. The primary comparison never needs them.

## 6. Unresolved items that need the user's decision

1. **Initial state.** Proposed: x_0 latent with a known prior N(0, (r sigma_w)^2), shared by all noise-aware predictors. This is required
   for the population reference to be the exact Bayes predictor of the generative process, and it recovers Stage 0.5 exactly at
   sigma_v = 0. Alternatives: a diffuse x_0, or x_0 observed noise-free (MATH_STAGE06 section 2.2).
2. **Primary comparator set.** Under information parity, the only noise-aware context-only predictor proposed is stability-only Bayes, so
   "selection" of the *primary* comparator is trivial. Noise-naive members are selected and reported as secondary. Should
   further noise-aware context-only candidates be added?
3. **Noise levels.** Proposed: a-independent q = sigma_v^2/sigma_w^2 in {0, q1, q2, q3}. The positive levels are fixed in Phase C from a
   prior-predictive information-loss diagnostic on pilot seeds (posterior-variance inflation of a at n in {10, 20, 40}). Candidate
   starting point: {0.25, 1, 4}, *not yet justified*.
4. **Context indexing.** Proposed: keep Stage 0.5's convention (n = transitions, n + 1 noisy observations y_0..y_n).
5. **Git.** The Phase C freeze asks for "a commit and tag". The workspace is not a git repository. Options: (a) the user approves `git init`
   and a first commit of the current tree (`runs/`, `dist/` and archives excluded by `.gitignore`); (b) freeze by SHA-256 manifest only
   (already supported) without git. Nothing git-related will be done without approval.
