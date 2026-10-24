# Stage 1A pre-registration (v3, as frozen before the pilot)

Status: **v3, the version frozen before the pilot** (section 15). No model of the study exists; no pilot or confirmatory
seed has been used. v1 (checkpoint 2) and v2 (checkpoint 3) are in git history (`stage1-planning`, commits `21fd209`, `a774477`).
This document, the code, the configs, the seed-role table, the power lookup and the J0, engineering-smoke and UNIF-spread result
files are frozen by a Stage 1 manifest **before the pilot** (section 15); the pilot outcome is then recorded as an appendix and the confirmatory run uses the
pilot-determined budget and model counts under the frozen rules. Labels: VERIFIED (read or recomputed from a named result
file), DERIVED (reasoning stated here or in a cited doc), ASSUMED (a planning guess), UNVERIFIED. Every threshold is a
hypothesis with a stated justification. Working project name: IdentICL.

**Changes since v1 (checkpoint 2), all before any model:** (a) the independent audit (docs/STAGE1_INDEPENDENT_AUDIT.md;
disclosure S15) found that v1's operating characteristics used a Gaussian critical value while the analysis uses the
bootstrap, so v1's power statements and target SEs are **withdrawn** (sections 7, 12); (b) the sample-size rule is now an
OC-calibrated lookup; minimum 16 models per arm; (c) the per-arm cap is set by a frozen rule from J0 (section 7);
(d) the Q2 per-model gate became an arm-level gate (section 6.2; reason: bootstrap validity); (e) secondary families are
implemented with a frozen drop rule (section 9); (f) two numerical defects found by the audit were fixed with regression tests.

**Changes in v3 (user decisions at checkpoint 3b, disclosure S21), all before any model of the study.** The first two were made
AFTER seeing UNIF-only capability evidence (engineering smoke and the 8-seed UNIF spread read; UNIF is outside the hypothesis):
(g) budget grid {10k, 25k, 50k, 100k} (was {25k, 50k, 100k, 200k}); (h) a convergence criterion added to the budget rule
(training-distribution validation NLL at positions 0-2 must improve by < 0.002 nats to the next grid point, for every pilot
model), because C2 is evaluated at n = 20, where pop and stab nearly coincide, so an under-trained CONT could pass C2 and be
spuriously STAB-LIKE at n <= 3; (i) NOT RESOLVABLE also when the cap rule makes the primary experiment infeasible (cap < minimum
models); (j) minimum 32 models per arm (was 16) and the lookup restricted to M >= 32; (k) V-REPRO tolerance fixed at 1e-4 nats
(the measured 0 came from one short run; a tolerance far below the classification margin would risk a false BLOCKED);
(l) the contended J0 timings are the cap rule's input.

## 1. Questions
* **Q1 (primary).** Do transformers pretrained on the population prior P behave like population-aware Bayes (pop) or like
  the context-only comparator (stab) on held-out systems, in the cells where these two references differ by at least delta?
* **Q2 (primary).** Do transformers pretrained on a library of K systems drawn from P behave like the K-atom library
  posterior (memorising) or like a generalising reference (pop or stab), and from which K on (the transition K*)?
* Everything else is secondary (section 9) or EXPLORATORY (section 10).

## 2. Family, references and what the map established (VERIFIED)
* Scalar AR(1), x_t = a x_{t-1} + eps_t, eps ~ N(0, 1) (sigma = 1 known), x_0 ~ N(0, r^2) independent of a, h = 1.
* References: pop = truncated normal (0.4, 0.3) on (-0.95, 0.95); stab = U(-0.999, 0.999); lib_K = uniform over the model's own
  K atoms. Batch forms equal the frozen Stage 0 / 0.5 references within 1e-9 nats, including the stored Stage 0.5 items
  (tests_stage1/test_ar1_batch_references.py; the audit re-derived them and found TN predictive errors <= 2.8e-13).
* Separability map `results_stage1/map_1A/` (branch `results-stage1-map-1A`, `a499874`; spec committed before the run; VALID):
  * Q1 held-out: IDENTIFIABLE at r in {0.25, 1}, n in {1, 2, 3, 5} and at r = 4, n in {1, 2} (Delta = 0.023-0.054 nats);
    UNIDENTIFIABLE for n >= 10.
  * Q2 held-out / in-library: library vs pop identifiable only for K = 1 (held-out, n >= 5); K = 2, 4 PARTIAL; K >= 8
    UNIDENTIFIABLE at r <= 1. **Memorisation is not visible by score on natural evaluation sets for K >= 4 in this family.**
  * Q2 designed sets: IDENTIFIABLE or PARTIAL for every K up to 256 on the probe grid and out-of-support systems (n in {5, 10, 20}).
    **Caveat (kept for the paper):** on out-of-support systems (|a| in (0.95, 0.999)) both the library and pop are misspecified;
    their separation largely reflects how close the library's extreme atom is to the support edge (coverage), not only memorisation.
  * Common random numbers (audit A6): all cells and r share the same systems; Q2 cells and library draws share their evaluation
    systems. Per-cell estimates are valid; patterns across cells or draws are not independent and are interpreted as such.

## 3. Arms (they differ only in the law of a)
| Arm | Law of a during pretraining | Its Bayes predictor | Role |
|---|---|---|---|
| CONT | P | pop | Q1 test arm |
| UNIF | U(-0.999, 0.999) | stab | Q1 positive control (context-only); capability control C1 |
| LIB-K, K in {1, 2, 4, 8, 16, 32, 64, 256} | uniform over K atoms drawn from P (per model seed) | lib_K | Q2 |
* x_0 ~ N(0, r^2), r uniform on {0.25, 1, 4} per sequence (DERIVED: the Bayes predictor does not depend on the x_0 law).
* Common random numbers: seed index i has the same initialisation, data order, x_0 and innovations in every arm; a is drawn by each
  arm's inverse CDF from the same uniforms; library atoms of seed i are nested across K (TESTED: test_neural.py; mutation matrix).

## 4. Models and training (primary configuration in bold)
* Causal transformer (explicit masked attention, fixed sinusoidal positions, pre-LayerNorm, GELU MLP 4d, no dropout); output a
  2-component Gaussian mixture for x_{t+1}.
* Parameter counts (VERIFIED from the code): S 25 734; **M 200 582**; L 1 587 462; depth/width variants 224 646 (2 layers, d 96)
  and 226 662 (8 layers, d 48); GRU 199 174; diagonal linear SSM 166 918.
* Loss: mean NLL over positions t = 0..19; AdamW lr 1e-3, weight decay 0.01, warmup min(1000, steps/10), cosine to 0, batch 256,
  gradient clip 1.0, float32; deterministic algorithms on (tested bitwise on CPU; GPU tolerance V-REPRO).
* Step budget B from the pilot (section 7) in {10k, 25k, 50k} (100k can never qualify: it has no next grid point for the
  convergence check). **Classification checkpoint: the final step of B.**
* Head size **m = 2**: smallest m with mean KL floor <= 0.001 nats in every cell (results_stage1/head_floor; worst cell mean 4.8e-5,
  worst single context 7.9e-4; m = 1 fails at 1.9e-3).

## 5. Evaluation (contexts only through `harness.make_context`)
* Sets per replicate: HELD (P) 40 000 systems; PROBE (39-point grid of a) 10 000; OOS (|a| ~ U(0.95, 0.999)) 10 000; UNIF systems
  4000 (controls). Systems shared by all models and cells of a replicate.
* Model input: the cut context cast to float32; output wrapped as float64 `GaussianMixturePredictive`. Causality TESTED (cut
  context = full sequence at position n; detects a missing mask, target leakage and an off-by-one read).
* Estimators: per-context KL(X || model) by y-quadrature (window mass checked to 1e-8). On HELD, KL(pop || model) is the
  expected regret against pop (DERIVED; audit re-derived). Realized-target regret is computed for check V-RB.

## 6. Estimands, families and classification rules
### 6.1 Q1 family (per replicate; alpha = 0.025)
10 cells: (r, n) in {0.25, 1} x {1, 2, 3, 5} plus (4, 1), (4, 2). Per cell, CONT and UNIF models paired by seed index:
R_pop = E[KL(pop || CONT_i)], G = E[KL(pop || UNIF_i) - KL(pop || CONT_i)], Delta = E[KL(pop || stab)] (reference-only, treated
as known). 20 statistics; band estimate +/- c x SE, two-level SE, **c from the hierarchical bootstrap** (4000 draws; models and
systems resampled; studentized max). Rule `classify_q1_held` (epsilon 0.01): POP-LIKE, STAB-LIKE, WORSE-THAN-STAB, INCONCLUSIVE.
Confirmed only if both replicates agree. **Q1 answer:** POP-LIKE in >= 7 of 10 cells and STAB-LIKE in none -> "behaves like
population Bayes"; the mirror image -> "behaves like the context-only comparator"; otherwise "mixed or inconclusive".
* Why the bootstrap (VERIFIED, coverage comparison in disclosure S15; 200 studies per row, seed-dominated regime): familywise
  coverage Gaussian 0.70-0.93, multivariate t 0.86-0.97, bootstrap 0.935-0.995 (0.995 at M = 8, about 0.95 at M >= 16).
### 6.2 Q2 family (per replicate; alpha = 0.025)
Cells per K: set in {PROBE, OOS} x r in {0.25, 1} x n in {5, 10, 20} (all IDENTIFIABLE or PARTIAL in the map).
* **Arm-level gate (changed from v1's per-model exclusion):** a (K, cell) is analysed only if >= 90% of the arm's models have both
  library separations (min of the two directional KLs, lib vs pop and lib vs stab, on the cell's systems) >= delta; otherwise it is
  reported GATED OUT. All of the arm's models enter a kept cell. Reason: excluding single models gives statistics with different
  model sets, and bootstrap draws that put no weight on enough of a statistic's models make its SE undefined, which the frozen
  rule would treat as an invalid analysis.
* Statistics per kept (K, cell): D_lib, D_pop, D_stab and the contrasts D_pop - D_lib, D_stab - D_lib (up to 480), one bootstrap
  band. Rule `classify_memorisation` (two-way): LIB-LIKE / GENERALISING / NEITHER / INCONCLUSIVE. Two replicates must agree.
* K's class: the class confirmed in >= 70% of its kept cells, else MIXED. **Q2 answer:** K* = the smallest K classified
  GENERALISING with no larger K LIB-LIKE; all LIB-LIKE -> "no transition up to K = 256"; otherwise "no clean transition".
### 6.3 Controls and critical checks (any failure -> BLOCKED)
* C1: UNIF arm's regret against stab on UNIF systems at r in {0.25, 1, 4}, n in {1, 2, 3}: upper band < 0.01.
* C2: every arm's regret against its own Bayes reference on its own distribution at n = 20 (CONT on HELD, UNIF on UNIF systems,
  LIB-K on its own atoms): upper band < 0.01. Bands: two-level SE with Bonferroni z over all control statistics at 0.05.
* V-RB: realized-target minus Rao-Blackwell regret, |z| <= Bonferroni critical value (familywise 0.001) in every Q1 cell and arm.
* V-REF (box rerun of tests_stage1: 78 passed in the box environment at step 3; repeated at the freeze), V-CAUSAL (tests),
  V-REPRO (one model per arm retrained from its seed; evaluation statistics must agree within **1e-4 nats**; the engineering
  smoke measured 0.0 on the box GPU for one 5k-step UNIF model).

## 7. Pilot, cap and sample size (pilot seeds only)
* Pilot arms CONT, UNIF, LIB-2, LIB-16; 8 models each (the pilot only estimates sds and capability; no inference); size M; trained
  to 100k with checkpoints 10k / 25k / 50k / 100k.
* **B** = the smallest grid checkpoint at which (a) every pilot arm passes C2 and UNIF passes C1, AND (b) for EVERY pilot model the
  training-distribution validation NLL averaged over positions 0-2 improves by less than 0.002 nats between this checkpoint and
  the next one (`pipeline.choose_budget`; 20 000 validation sequences per model from its own arm law, the same sequences at every
  checkpoint; no reference and no other arm enters). The last checkpoint (100k) cannot qualify. None -> NOT RESOLVABLE (capability).
* If the cap at B (below) is smaller than the minimum of 32 models per arm -> NOT RESOLVABLE (compute). **With the accepted
  contended J0 timings the cap is 56 at B = 10k, 24 at 25k and 8 at 50k (computed with `cap_from_j0`), so only B = 10k leaves the
  primary experiment feasible within 48 GPU-hours; B = 25k or 50k gives NOT RESOLVABLE (compute).**
* **Cap (frozen rule, user decision at checkpoint 2):** the largest M (multiple of 8, <= 128) such that the projected primary
  experiment (2 replicates x 10 arms x M models x (B x J0 effective seconds per model-step + evaluation seconds per model) x 1.25)
  fits in 48 GPU-hours (`pipeline.cap_from_j0`). J0 effective seconds come from `results_stage1/j0/j0.json` (best concurrency, wall
  time including start-up), evaluation seconds from the engineering smoke. Both files are produced before the freeze and frozen.
* **Model counts (frozen lookup, `config/stage1_power_lookup.json`, built by `scripts/stage1_power_lookup.py` from the v2
  operating characteristics):** s1 = the largest between-seed sd over the 20 Q1 statistics at B; s2 = the largest over the Q2
  statistics of LIB-2 and LIB-16 (ASSUMED representative of all K). M = the smallest M in {32, 64, 128} (>= 32, <= cap)
  whose supported sd s*(M) >= 1.35 x s (80% upper confidence factor for an sd from 8 models, computed). None -> that family
  is NOT RESOLVABLE.
  | M | Q1 s*(M) | Q2 s*(M) |
  |---|---|---|
  | 32 | 0.01 | 0.02 |
  | 64 | 0.01 | 0.05 |
  | 128 | 0.02 | 0.05 |
  s*(M) = the largest grid seed sd at which P(correct class per cell) >= 0.8 for both reference positions, e <= 0.005 (Q1) or
  e in {0, 0.01} (Q2), and every cell correlation of the seed effect (0 and 0.9).
* **Operating characteristics v2 (VERIFIED, `results-stage1-step3`, `66c5846`, `results_stage1/oc_1A_v2/`):** bootstrap critical
  value at alpha 0.025 (median c 4.16 / 3.46 / 3.29 / 3.21 at M = 16 / 32 / 64 / 128); P(wrong class) 0 in all 192 non-boundary
  Q1 settings and all 144 Q2 settings (200 and 300 two-replicate studies); P(PROCEED) 0 at every boundary truth (96 settings).
  **Operating characteristics at M >= 32 (the v3 range; min over pi in {0, 1}, e <= 0.005 and rho in {0, 0.9}):**
  | seed sd s | Q1 P(correct), M = 32 / 64 / 128 | Q1 P(PROCEED), M = 32 / 64 / 128 |
  |---|---|---|
  | 0.005 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 |
  | 0.01 | 0.88 / 0.99 / 1.00 | 0.98 / 1.00 / 1.00 |
  | 0.02 | 0.21 / 0.67 / 0.92 | 0.00 / 0.61 / 1.00 |
  | 0.03 | 0.00 / 0.21 / 0.63 | 0.00 / 0.00 / 0.39 |
  Q2 P(correct) (min over the three cells, pi in {0, 1}, e in {0, 0.01}): 1.00 at s <= 0.02 for M = 32 / 64 / 128; at s = 0.05:
  0.76 / 1.00 / 1.00. With the cap of 56 at B = 10k the usable counts are 32 (Q1 resolvable if 1.35 s1 <= 0.01, i.e. s1 <= 0.0074).
  Pre-freeze UNIF-only evidence (outside the hypothesis; disclosure S20): the largest UNIF between-seed sd over the Q1-shaped cells
  was 0.0017 at 10k (0.0063 at 5k, 0.00068 at 25k, 0.00019 at 50k). If CONT spreads similarly (ASSUMED), 32 models suffice.
* The pilot writes only sds, pass flags, counts, the cap, the projection and the retained secondary families
  (`pilot_decision.json`); no pilot means or classes are computed into any file.

## 8. Program verdict (order: BLOCKED, NOT RESOLVABLE, PROCEED, REVISE)
BLOCKED if a control or critical check fails; NOT RESOLVABLE (capability) if the pilot finds no budget meeting the controls and
the convergence criterion; NOT RESOLVABLE (compute) if the cap at B is below 32; NOT RESOLVABLE for a family whose lookup count
exceeds the cap (both families -> the study);
PROCEED (to the F1 neural stage, on a new decision) if the Q1 answer is decisive or Q2 yields K*; REVISE otherwise. The answers
of section 6 are reported with effect sizes and bands whatever the verdict.

## 9. Secondary families (alpha 0.05 / 7 per replicate each; variants split their family's level; two replicates)
| Family | Variants (arm, size, budget) | Purpose |
|---|---|---|
| Q1-behavioural | primary CONT and UNIF models on PROBE / OOS cells (`classify_behavioural`, pop vs stab) | prior use where held-out gaps are small; OOS is the sharpest test |
| training-length-4B | CONT, UNIF, size M, 4B | transience of the class |
| size-S, size-L | CONT, UNIF | capacity |
| depth-width | CONT, UNIF at (2 x 96) and (8 x 48) | depth for in-context estimation vs prior use |
| architecture | CONT, UNIF as GRU and as diagonal linear SSM | attention-specific? |
| Q2-size-L | LIB-4, LIB-16, LIB-64 at size L | capacity and K* |
M_sec = min(M1, 32) (Q2-size-L: min(M2, 32)). **Drop rule (frozen):** projected GPU hours (J0-scaled per size) of primary plus
retained secondary families must fit 48 h; families are dropped in the order architecture, depth-width, Q2-size-L, size-S,
size-L, training-length-4B; the primary families are never reduced (TESTED: test_pipeline_e2e.py).

## 10. EXPLORATORY (excluded from headline claims)
Context lengths beyond training; training trajectories at B/4, B/2; mixture-weight fits; per-r breakdowns; anything else.

## 11. Seeds (`config/stage1_seed_manifest.yaml` is the single source of truth)
Used: map 70001; OC 70101, 70102; head floor 70201; F1 map 70301; engineering smoke 70901; J0 70902; UNIF spread 70903;
smoke and timing 69999, 12345. Unused until their step: pilot 71001 / 71101 / 71201 / 71999; confirmatory 72001-72002 /
72101-72102 / 72201-72202 / 72999. Test-only roles 691xx (pytest end-to-end test; never decisions). Torch seeds derive from (train root, "stage1_init", seed index).

## 12. Compute plan (J0 measured on the shared GPU, contended: 0.0114 s per model-step at the best concurrency)
| Job | Where | Estimate |
|---|---|---|
| Pilot: 32 models x 100k steps (8 concurrent) + two evaluation passes | box GPU (shared) | about 8.5 h training (from the UNIF spread throughput: 8 models x 50k in 3827 s) + evaluation |
| Confirmatory primary + retained secondary | box GPU | <= 48 GPU-h by the frozen rules |
| Evaluation and analysis (KL quadrature, bootstrap) | box CPU | about 2-4 h (ASSUMED) |

## 13. Implementation and validation status (VERIFIED at the freeze; numbers in disclosure S21)
`dynaicl_neural/` (seeds, data, models, train, adapter, evaluate, analysis, config, pipeline, authorization), `scripts/stage1_run.py`,
`scripts/stage1_freeze.py`. Stage 1 suite and mutation matrix re-run on the frozen code (results in disclosure S21); end-to-end
pipeline tests at toy scale, budget-rule and compute-infeasibility tests; one real defect was found by the end-to-end test and fixed
(the bootstrap seed was indexed per replicate).

## 14. What was seen before freezing
Stage 0.5 per-item contrasts; the Stage 1A and F1 separability maps (reference-only); operating characteristics v1 (withdrawn)
and v2 (synthetic); smoke-seed reference numbers; the head floor; the audit; J0 timings (GPU shared); the engineering smoke (UNIF,
2 models, 5k steps: capability numbers and exact retraining reproducibility); the 8-seed UNIF spread read (UNIF-only between-seed
sds and capability by checkpoint). UNIF is outside the hypothesis; no CONT or LIB model of the study has been trained; no pilot or
confirmatory seed has been used.

## 14b. Status of every audit finding (docs/STAGE1_INDEPENDENT_AUDIT.md)
| Item | Severity | Status |
|---|---|---|
| A1 Gaussian vs bootstrap critical value in the OC | MAJOR | **Fixed**: OC v2 uses the bootstrap critical value (median of 5 x 1000-draw replicates per setting); v1 power withdrawn; min 16 models (raised to 32 in v3); lookup. Residual, disclosed: the per-setting c varied across the 5 replicates (median range 0.21, max 2.53), so OC power is evaluated at the median c, while the real analysis computes c once per study with 4000 draws. |
| A2 model effect shared across cells | MINOR | **Fixed and bounded**: OC v2 simulates one model-level effect with cell correlation rho in {0, 0.9}; the lookup takes the minimum power over both. VERIFIED from oc_q1_v2.csv: per-cell power at rho = 0.9 is >= power at rho = 0 in 96 of 96 setting pairs (smallest difference -0.001, Monte Carlo noise) and the bootstrap c is smaller at rho = 0.9 in 96 of 96 (mean 3.23 vs 3.65). DERIVED: sharing does not change a cell's marginal distribution, only the correlation across cells, which lowers the max-statistic quantile (Slepian-type argument), so per-cell power can only rise with non-negative sharing; the lookup (rho = 0) is therefore conservative for any rho in [0, 1]. |
| A3 G without system variance in the OC | MINOR | **Fixed**: G's system component is pi d_j (grows with pi). |
| A4 F1 quadrature at the support edge | MINOR | **Fixed** with regression test (fails on old code, passes now). |
| A5 window gap near the support edge | NOTE | **Fixed** with regression test. |
| A6 common random numbers across cells and draws | NOTE | **Disclosed** in section 2; patterns across cells / draws are not treated as independent evidence. |
| A7 F1 KL window | NOTE | **Not applicable**: the F1 map uses score gaps, not KL (spec section 3). |
| A8 log-uniform marginal underflow at (n = 81, R = 1e-12) | NOTE | **Deferred, unreachable** (R >= R_min ~ sigma^2 chi^2_79 at n = 80); raises loudly if ever hit. |
| A9 Q2 OC critical value and independent distances | NOTE | **Fixed**: Bonferroni-t value with M - 1 df over 480 statistics (conservative) and per-system distances correlated 0.5. |
| A10 WORSE outcomes not counted as wrong | NOTE | **Fixed**: WORSE counts as wrong for a POP truth; for STAB truths P_WORSE was 0 in all 96 settings (VERIFIED). |
| A11 Q2 OC seed derived arithmetically | NOTE | **Fixed**: OC v2 takes both seeds from the seed-role table (role stage1_oc: 70101, 70102). |

## 15. Freeze (step 5)
`scripts/stage1_freeze.py build` writes `docs/FREEZE_MANIFEST_STAGE1.json` (SHA-256 of every file in the frozen set: this document,
the map specs, MATH_F1, the audit, configs, seed table, power lookup, requirements-stage1.txt, dynaicl_families/, dynaicl_neural/,
tests_stage1/, scripts/stage1_*, and the result files results_stage1/j0/j0.json, results_stage1/eng_smoke/eng_smoke.json and
results_stage1/unif_spread/unif_spread.json) and a read-only snapshot. You
store the manifest hash outside the workspace. Pilot and confirmatory runs verify it; the confirmatory run additionally needs your
authorization artifact (HMAC-SHA256 under your key, binding manifest, snapshot, config, this document, the pilot decision and the
seed set; one run id per output directory). Appendix A (after the pilot) will record the pilot decision.
