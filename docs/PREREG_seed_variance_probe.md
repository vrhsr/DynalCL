# Seed-variance probe: pre-registration DRAFT 0.2 (2026-11-03; 0.1 of 2026-11-01). NOT FROZEN. NOT AUTHORISED. Nothing trained. No GPU.

Changes in 0.2 (disclosure S52, made after seeing batch 7's reference-only operating characteristics): the option-B Q2 cell
set and the go / no-go tiers below; the F2 arm is trained at sequence length 81 and evaluated at n in {20, 40, 80}; its cost
is given as a range.

Status: CPU draft for the user's review (S40 decision 3: seed-variance probe first, then the memorisation transition). No seed
below is registered or used; no GPU or torch job may start without the user's explicit go-ahead. Machinery as the frozen
Stage 1A study (`dynaicl_neural/`, controls, convergence record, provenance); what changes is the purpose: **measurement, not
classification**.

## 1. Question
How much does a trained model's regret, and its distance to each reference, vary between training seeds in the family planned
for the memorisation-transition study? Every power statement of this project rests on that number (the F1 lookup: a
population-vs-context-only classification needs a between-seed sd <= 0.01 nats at 32 models per arm; a memorisation
classification tolerates 0.10, `results_stage2/f1_power_lookup/`), and no trained-model value exists for any family except a
UNIF-only proxy (0.0017 nats at 10k steps, size M; disclosure S20).

## 2. Design
* Family F1 (unknown noise scale; references frozen in Stage 1 v2; head m = 8 from the F1 head floor, S38).
* Arms (pretraining law): CONT-F1 (P_F1); LIB-8 and LIB-16 (each model its own library of K systems from P_F1). Chosen
  because the F1 map and the nearest-system limit put the library separability boundary between K = 8 and 32 (S41).
* **Plus the bivariate arm LIB-64 (F2)** (user decision S44): 16 models, each with its own library of 64 systems from P_F2.
  Its purposes: the seed spread in the family of the planned memorisation-transition study (option B), and a **measurement of
  the F2 cost per model-step** on the shared GPU, which replaces the ASSUMED 1.5x factor in that study's costing. Prerequisite:
  the F2 head floor (bivariate mixture head size; CPU, `docs/STAGE3_F2_DESIGN_CPU_SPEC.md`).
  **Sequence length 81 (contexts up to n = 80)** for this arm (0.2): option B's Q2 cells lie at n = 40 and 80, so the arm
  must be evaluated there, and its per-step cost must be measured at the length option B would train at (Stage 1A trained at
  length 20). Evaluation of the F2 arm: held-out systems, r = 1, n in {20, 40, 80}, against its own lib_64 and population
  Bayes (the F1 arms keep the cells of section 3).
* Heads (VERIFIED head floors): F1 arms m = 8 univariate components (S38); F2 arm m = 8 bivariate components with full
  covariances (S48).
* 16 models per arm, size M (as Stage 1A), budget grid {10k, 25k, 50k}; every checkpoint is evaluated (no budget selection).
* **Go / no-go rule for option B (fixed before any freeze; S49).** Statistic: for the F2 LIB-64 arm, at the checkpoint the
  memorisation study would use (the probe's own convergence record decides which; reported for all three), the between-seed
  sd of each Q2 statistic (the model's distances to lib_64 and to population Bayes on held-out systems, and their contrast)
  in each Q2 cell. Upper bound: for each cell and statistic, the larger of (a) the one-sided 95% chi-square bound for a normal
  sd with 15 degrees of freedom, s x sqrt(15 / chi2_{0.05, 15}) = 1.437 s, and (b) the 95th percentile of the seed-bootstrap
  distribution of the sd (2000 resamples of the 16 models); U = the maximum over the LIB-64 arm's Q2 cells (r = 1, n = 40 and
  80) and statistics. **Q2 cell set and tolerance (chosen in 0.2 from batch 7, `results-stage2-cpu-batch7` @ `3896f37`,
  after seeing those reference-only operating characteristics; S52):** cell set C = held-out, r = 1: K = 16 at n in
  {20, 40, 80}; K = 64 and K = 256 at n in {40, 80}; K = 1024 at n = 80. Excluded: K >= 64 at n = 20 and K = 1024 at
  n = 40, where the library and context-only references are within 0.064 / 0.021 / 0.039 and 0.028 nats and the frozen
  lookup tolerates at most 0.01 (or nothing). Pooled s*(M) on C by the frozen `lookup` rule = 0.02 nats at M = 32, 64 and
  128 (binding cells: K = 1024, n = 80 at every M; K = 256, n = 40 at M = 32 and 64). Reduced set C' = C without K = 1024
  and without K = 256 at n = 40: s*(M) = 0.02 / 0.05 / 0.05 at M = 32 / 64 / 128. **Rule:**
  (1) U <= 0.02 nats: option B is a GO with 32 models per arm, cell set C, all arms;
  (2) 0.02 < U <= 0.05: GO with 64 models per arm, cell set C', the K = 1024 arm dropped (no classifiable cell at that
  tolerance);
  (3) U > 0.05: NO-GO, reported in advance as NOT RESOLVABLE (compute), and option A (F1) is considered with the F1 arms'
  bound computed the same way.
  (1) and (2) also require that the confirmatory compute fits the GPU budget the user sets (with the per-step cost this arm
  measures); otherwise NO-GO as in (3). More models do not help beyond these tiers on the lookup's grid of seed sds
  {0.01, 0.02, 0.05, 0.1}. The point estimate is never used for this decision. (The Stage 1A pilot rule, 1.35 x the pilot
  sd <= s*(M), stays the rule for the memorisation study's own pilot.)
* **K = 2 arm:** not in C. No operating characteristics exist for K = 2 cells (batches 6 and 7 covered K >= 16); its
  library-vs-population gaps are about 0.9 nats at n >= 10 (batch 5), larger than K = 16's, so it is expected, not shown,
  to be the easiest cell. Before any freeze: either a specified CPU run adds K = 2 cells to the lookup, or the arm is
  dropped (open decision).
* **Carry-over to other library sizes: NOT assumed.** The probe measures F2 at K = 64 only. For the go / no-go decision K = 64
  is used as a screening value for K in {16, 256} (ASSUMED, stated as such); it is not used for K = 2 or 1024. The
  memorisation study's own pilot (8 models in every arm) re-estimates the sd per arm and sets M by its frozen rule before
  any confirmatory run, so a K for which the screening assumption fails is caught there.

## 3. Measurements (per arm, per cell r in {0.25, 1, 4} x n in {2, 3, 5, 10, 20, 40}, per checkpoint)
* Regret against the arm's own Bayes predictor on its own law: R = E[KL(ref_arm || model)] by y-quadrature (Stage 1A V-RB).
* On held-out systems from P_F1: G_pop = E[LS(pop) - LS(model)] and, for LIB arms, G_lib = E[LS(lib_K,own) - LS(model)].
* Primary output: the between-seed standard deviation of R, G_pop and G_lib per cell, with a seed-bootstrap 95% interval
  (2000 resamples of the 16 models); summary: the largest sd over cells, per arm and checkpoint.
* Controls as Stage 1A (C2: each arm's regret against its own reference at n = 20; causality; reproducibility of evaluation).

## 4. How the result is used (fixed now)
* No hypothesis test and no classification is made from this probe.
* The measured sd (upper interval end) is entered into the frozen lookup rule to give the number of models per arm the
  memorisation-transition study needs; if that exceeds the GPU budget the user sets, that study is reported in advance as
  NOT RESOLVABLE (compute) and not run.
* Disclosure: any later design choice that uses these numbers is recorded as made after seeing them.

## 5. Compute (estimate and basis)
* F1 arms: 3 arms x 16 models x 50 000 steps x 0.0114 s per model-step (contended J0, size M, S19) x 1.25 (safety) / 3600 =
  **9.5 GPU-hours** (measured pilot rate 0.01076 s, S26: 9.0 h). ASSUMED: the m = 8 head does not change the per-step cost
  materially (measured in the engineering smoke). F2 arm: 16 x 50 000 x 0.0114 x 1.5 (ASSUMED bivariate factor, which this
  arm measures) x f_L x 1.25 / 3600, where f_L is the cost ratio of length 81 to length 20 (the J0 rate was taken with the
  Stage 1A trainer, length 20; ASSUMED that J0 used that default): **4.8 h** if the per-step cost does not depend on length
  (an under-used GPU), **19.2 h** if it is linear in length (f_L = 81/20; attention is quadratic, so this is not an upper
  bound). **Probe total 14.2-28.7 GPU-h.** Evaluation under 1 h.
* The measured F2 cost per model-step at length 81 (wall time per step at the run's concurrency, logged with GPU utilisation
  and the other processes present) is reported and replaces 1.5 x f_L in `docs/PREREG_memorisation_transition.md` before that
  study is frozen.
* The A4000 is shared: GPU work starts only after the user confirms it is free.

## 6. Seeds (proposed, UNUSED, NOT registered; checked against every manifest when registered)
probe_train 86001, probe_eval 86101, probe_library 86201, probe_bootstrap 86999, probe_smoke 86901.

## 7. Seen before this draft
All reference maps (1A, F1, F3, F2), the theory quantities of batch 5 section E (S41), the Stage 1A pilot's budget outcome and
timing (no effect information), the UNIF-only spread read (S20). Batch 4 and the box part of batch 5 not yet returned.
For 0.2: batches 4-7 (all reference-only; batch 6's and batch 7's F2 operating characteristics, S48 and S52). No network result.

## 8. Decisions
1. Arms decided (S44): F1 CONT, LIB-8, LIB-16, plus F2 LIB-64.
2. Open: GPU budget and the go-ahead (nothing runs without it).
