# Stage 1A pre-registration (DRAFT for review at checkpoint 2; NOT frozen)

Status: **DRAFT.** Nothing in this document has been frozen, no model exists, no Stage 1 training, pilot or confirmatory
seed has been used. After your review it is frozen together with the code, configs and seed-role table by a Stage 1
manifest (section 15). Labels: VERIFIED (read or recomputed from a result file named here), DERIVED (reasoning stated
here or in a cited doc), ASSUMED (a planning guess), UNVERIFIED. Every threshold is a hypothesis with a stated
justification. Plan: `docs/STAGE1_PLAN.md` v2 (approved at checkpoint 1). Working project name: IdentICL.

## 1. Questions

* **Q1 (primary).** Do transformers pretrained on the population prior P behave like population-aware Bayes (the pop
  reference) or like the context-only comparator (the stab reference) on held-out systems, in the cells where these two
  references differ by at least delta?
* **Q2 (primary).** Do transformers pretrained on a library of K systems drawn from P behave like the K-atom library
  posterior (memorising) or like a generalising reference (pop or stab), and from which K on (the transition K*)?
* Everything else in this document is secondary (section 9) or EXPLORATORY (section 10).

## 2. Family, references and what the map established (VERIFIED)

* Scalar AR(1), x_t = a x_{t-1} + eps_t, eps ~ N(0, 1) (sigma = 1 known), x_0 ~ N(0, r^2) independent of a, h = 1.
* References (frozen Stage 0 / 0.5 code, batch forms equal within 1e-9 nats, tests_stage1/test_ar1_batch_references.py):
  pop = truncated normal (0.4, 0.3) on (-0.95, 0.95); stab = U(-0.999, 0.999); lib_K = uniform over the model's own K atoms.
* Separability map `results_stage1/map_1A/` (branch `results-stage1-map-1A`, commit `a499874`; spec
  `docs/STAGE1_SEPARABILITY_MAP_SPEC.md`, committed before the run; VALID, 4344 agreement checks, max |z| 3.82 vs 5.17):
  * Q1 on held-out systems: IDENTIFIABLE at r in {0.25, 1}, n in {1, 2, 3, 5} and at r = 4, n in {1, 2}
    (Delta = 0.023-0.054 nats); UNIDENTIFIABLE for n >= 10 (and r = 4, n >= 3).
  * Q2 on held-out and in-library systems: library vs pop identifiable only for K = 1 (held-out, n >= 5); K = 2, 4
    PARTIAL; K >= 8 UNIDENTIFIABLE at r <= 1. **Memorisation is not visible by score on natural evaluation sets for
    K >= 4 in this family.**
  * Q2 on designed sets: library vs pop IDENTIFIABLE or PARTIAL for every K in {1, ..., 256} on the probe grid and on
    out-of-support systems at n in {5, 10, 20}. Caveat (DERIVED): on out-of-support systems (|a| in (0.95, 0.999)) both the
    library and pop are misspecified; their separation largely reflects how close the library's extreme atom is to the
    support edge (coverage), not only memorisation. Results on that set are reported as such.

## 3. Arms (pretraining distributions; they differ only in the law of a)

| Arm | Law of a during pretraining | Its Bayes predictor | Role |
|---|---|---|---|
| CONT | P | pop | Q1 test arm; Q2 generalising control |
| UNIF | U(-0.999, 0.999) | stab | Q1 positive control (context-only); capability control C1 |
| LIB-K, K in {1, 2, 4, 8, 16, 32, 64, 256} | uniform over K atoms drawn from P (per model seed) | lib_K | Q2 |

* x_0 ~ N(0, r^2) with r uniform on {0.25, 1, 4} per sequence (DERIVED: the Bayes predictor does not depend on the x_0
  law, because the likelihood is conditional on x_0 and x_0 is independent of a). Sequences x_0..x_20, fresh every step.
* Common random numbers: model seed index i uses the same initialisation, data order, x_0 and noise in every arm; a is
  drawn by each arm's inverse CDF from the same uniforms (LIB-K: atom index from the same uniforms). Library atoms of
  seed i are nested across K (the first K atoms of the 256-atom draw).

## 4. Models and training (primary configuration in bold)

* Causal decoder-only transformer: linear embedding of the scalar input, fixed sinusoidal positions, pre-LayerNorm,
  GELU MLP (4d), no dropout. Output: a Gaussian-mixture density for x_{t+1} with m components (head floor rule below).
* Sizes: S (2 layers, d 32, 2 heads, about 25k parameters), **M (4 layers, d 64, 4 heads, about 200k)**, L (8 layers,
  d 128, 8 heads, about 1.6M). Parameter counts DERIVED as 12 d^2 per layer, to be confirmed by the code.
* Loss: mean negative log likelihood over positions t = 0..19 (predict x_{t+1} from x_0..x_t). AdamW, lr 1e-3, weight
  decay 0.01, 1000 warmup steps then cosine decay to 0, batch 256 sequences, gradient-norm clip 1.0, float32.
* Step budget B: chosen in the pilot (section 7) from {25k, 50k, **B**, 4B}; checkpoints at B/4, B/2, B, (4B for the
  training-length factor). **The classification checkpoint is the final step of B.**
* Head size m: the smallest m in {1, 2, 4, 8} whose mean KL floor (best m-mixture vs each reference predictive, pop, stab and
  libraries K in {2, 8, 32, 256}) is <= epsilon/10 = 0.001 nats in every evaluated cell
  (`scripts/stage1_head_floor.py`, seed 70201, `results_stage1/head_floor/head_floor.csv`; 60 contexts per cell, sets HELD /
  PROBE / OOS, r in {0.25, 1, 4}, n in {1, 3, 5, 20}; VERIFIED). **m = 2.** m = 1 fails (worst cell mean 1.9e-3 nats, mostly
  the stab reference, whose truncation at 0.999 skews the predictive); with m = 2 the worst cell mean is 4.8e-5, the worst
  95th percentile 3.1e-4 and the worst single context 7.9e-4. The fitted floors are upper bounds (EM; local optima).
* Every model seed randomises initialisation, data order and data (and library atoms for LIB-K).

## 5. Evaluation (contexts only through `dynaicl.evaluation.harness.make_context`)

* Sets: HELD (systems from P), PROBE (a uniform on the 39-point grid -0.95..0.95), OOS (|a| ~ U(0.95, 0.999), random
  sign). N = 40 000 systems per replicate for HELD; 10 000 each for PROBE and OOS. Systems are shared by all models and
  cells of a replicate (common random numbers).
* The model sees `make_context(trajectory, n).values` cast to float32 and returns mixture parameters, cast to float64 and
  wrapped as the frozen `GaussianMixturePredictive`. A test asserts that the output at the last position of a cut context
  equals the output at position n of the full sequence (causality check; catches future leakage).
* **Estimators (Rao-Blackwellised):** for each model and context, KL(X || model) by y-quadrature for each reference X
  (`dynaicl_families/kl.py`, window mass checked to 1e-8). On HELD, KL(pop || model) is the model's expected regret
  against pop (DERIVED: pop is Bayes on HELD). The realized-target log-score regret is computed too and must agree
  (validity check V-RB below).

## 6. Estimands, families and classification rules

### 6.1 Q1 family (per replicate; alpha = 0.025)
Cells C1: (r, n) in {0.25, 1} x {1, 2, 3, 5} plus (4, 1), (4, 2): 10 cells (the map's IDENTIFIABLE held-out cells).
Per cell, over the CONT and UNIF models (paired by seed index):
* R_pop = E[KL(pop || CONT_i)]; G = E[KL(pop || UNIF_i) - KL(pop || CONT_i)] (DERIVED: = E[LS(CONT_i) - LS(UNIF_i)] on HELD);
  Delta = E[KL(pop || stab)] on the same systems (reference-only; its SE is about 0.0004 and it is treated as known).
* 20 statistics (10 R_pop + 10 G). Simultaneous band: estimate +/- c x SE (two-level SE; c from the hierarchical bootstrap,
  4000 draws, studentized max over the 20; `dynaicl_neural/analysis.py`).
* Rule `classify_q1_held` (epsilon = 0.01): POP-LIKE if hi(R_pop) < Delta/2 and lo(G) > Delta/2; STAB-LIKE if lo(R_pop) > Delta/2
  and |G| < Delta/2 at both band ends; WORSE-THAN-STAB if lo(R_pop) > Delta + epsilon; INCONCLUSIVE otherwise.
* A cell's class is confirmed only if both replicates give it (otherwise DISCORDANT, counted as INCONCLUSIVE).
* **Q1 answer:** "CONT behaves like population Bayes" if POP-LIKE is confirmed in >= 7 of the 10 cells and STAB-LIKE in none;
  "CONT behaves like the context-only comparator" if STAB-LIKE is confirmed in >= 7 and POP-LIKE in none; otherwise
  "mixed or inconclusive", reported with every cell's estimates and bands.

### 6.2 Q2 family (per replicate; alpha = 0.025)
Cells C2(K): set in {PROBE, OOS} x r in {0.25, 1} x n in {5, 10, 20}: 12 cells for every K (all IDENTIFIABLE or PARTIAL in the
map). Per model, cells where the model's own library is not separable from pop or stab at >= delta (gate: the reference
separation computed on the replicate's systems) are excluded for that model and reported.
* Statistics per (K, cell): D_lib, D_pop, D_stab (D_X = E[KL(X || model)]) and the contrasts D_pop - D_lib, D_stab - D_lib:
  5 x 12 x 8 = 480 statistics; one studentized-max band over them.
* Rule `classify_memorisation`: LIB-LIKE / GENERALISING / NEITHER / INCONCLUSIVE (separations from the replicate's own
  reference computations). Two replicates must agree.
* K's class: the class confirmed in >= 70% of its gated cells (8 of 12 when none are gated out); otherwise MIXED.
* **Q2 answer:** K* = the smallest K classified GENERALISING such that no larger K is LIB-LIKE. If every K is LIB-LIKE:
  "no transition up to K = 256". If the pattern is non-monotone or mostly MIXED: "no clean transition", reported per K.
* Secondary (not decision-driving): which generalising reference is nearer (`classify_behavioural`, pop vs stab).

### 6.3 Controls and critical checks (any failure: verdict BLOCKED for the affected family)
* C1: every UNIF model's regret against stab on its own distribution (U systems) at n in {1, 2, 3}, upper band < epsilon = 0.01.
* C2: every arm's arm-mean regret against its own Bayes reference on its own distribution at n = 20, upper band < epsilon.
* V-RB: realized-target vs Rao-Blackwell regret agree on HELD (|z| <= Bonferroni critical value at familywise 0.001).
* V-REF: the batch references reproduce the frozen references (rerun of tests_stage1 on the box environment) and the KL
  window mass checks pass.
* V-CAUSAL: cut-context output equals full-sequence output for 1000 random contexts per model family (<= 1e-6 in float32).
* V-REPRO: one model per arm is retrained from its seed; its evaluation statistics agree with the original to <= 1e-4 nats
  (GPU nondeterminism tolerance; ASSUMED; measured in the pilot and fixed before the confirmatory run).
* Bootstrap validity: no non-finite or zero per-draw SE (as Stage 0.6).

## 7. Pilot and sample size (pilot seeds only; pilot effects are written to a file that is not opened)

* Pilot arms: CONT, UNIF, LIB-2, LIB-16; 8 models each; size M; trained to 200k steps with checkpoints at 25k, 50k, 100k, 200k.
* **Budget B** = the smallest checkpoint at which every pilot model passes C1 and C2 on training-distribution validation
  systems (pilot evaluation seed). None passes: Stage 1A verdict NOT RESOLVABLE (capability), no confirmatory run.
* **Number of models** per arm and replicate, from the between-seed sd s of the per-model statistics at budget B:
  * Q1: s1 = the largest between-seed sd over the 20 Q1 statistics (CONT, UNIF pilots); M1 = max(8, ceil((1.35 s1)^2 / 0.002^2)).
  * Q2: s2 = the largest over the Q2 statistics of LIB-2 and LIB-16 (ASSUMED representative of all K); M2 = max(8, ceil((1.35 s2)^2 / 0.008^2)).
  * 1.35 = sqrt(7 / chi2_{0.20, 7}), the 80% upper confidence factor for an sd from 8 models (computed).
  * Cap 64 per arm per replicate. If M1 > 64: Q1 NOT RESOLVABLE at delta (no confirmatory Q1 run); likewise Q2.
* Justification of the targets (VERIFIED, `results_stage1/oc_1A/oc_q1_a025.csv`, `oc_q2_c405.csv`): at the
  pre-registered family sizes, for models at either reference (pi in {0, 1}):
  * Q1 (alpha 0.025): P(correct class per cell) 0.90-0.98 at s = 0.01, M = 32 when the approximation error e <= 0.005
    (0.58-0.95 at e = 0.01); 0.71-0.82 at s = 0.02, M = 64 (e <= 0.005). The target SE 0.002 (delta/10) is the
    s/sqrt(M) at which per-cell power is about 0.9 or more for e <= 0.005. With the cap of 64, Q1 is resolvable for
    s up to about 0.016 (UCL-adjusted).
  * Q2 (c = 4.05, the Bonferroni value for 480 statistics at 0.025): P(correct) >= 0.88 at s = 0.05, M = 32 (0.30 at M = 16).
  * P(wrong class) was 0 in every non-boundary setting: 352 Q1 settings and 144 Q2 settings, 300 two-replicate studies each.
  * Models half-way between references (pi = 0.25, 0.5, 0.75) are mostly INCONCLUSIVE: the design does not resolve
    intermediate positions, by construction of the margins.
* Pilot statistics used: only between-seed sds, C1/C2 pass flags and timing. Pilot means and classes are never computed
  into any file that is opened (`results_stage1/pilot/PILOT_ONLY_do_not_open_effects.json`).

## 8. Program verdict (in the order BLOCKED, NOT RESOLVABLE, PROCEED, REVISE)

* BLOCKED: a critical check or control fails (reported as a capability or validity failure, not a scientific result).
* NOT RESOLVABLE: the pilot rule says no budget passes C1/C2, or M1 > 64 and M2 > 64.
* PROCEED (to the F1 neural stage, on a new decision): the Q1 answer is decisive (POP-LIKE or STAB-LIKE) or Q2 yields K*.
* REVISE: otherwise.
* The scientific answers (section 6) are reported with effect sizes and bands whatever the verdict.

## 9. Secondary families (each alpha = 0.05 / 6 per replicate; two replicates; CONT and UNIF arms unless stated)

| Family | Purpose | Models |
|---|---|---|
| Q1 behavioural on PROBE and OOS (cells IDENTIFIABLE in the map, n <= 20; rule `classify_behavioural` with pop, stab) | Prior use where held-out gaps are small; OOS is the sharpest test (pop cannot reach abs(a) > 0.95) | the primary CONT/UNIF models |
| Size S and L | Does capacity change the Q1 class? | M_sec per arm and size |
| Training length 4B (classification at 4B) | Is the class stable after longer training (transience)? | M_sec |
| Depth vs width at equal parameters: (2 layers, d 96) vs (8 layers, d 48), both 221 184 parameters by 12 d^2 per layer | Depth for in-context estimation (Cole et al.) vs use of the prior | M_sec each |
| Architecture: GRU (2 x 128) and a diagonal linear recurrent state-space model (4 layers, d 64), plain PyTorch | Is the behaviour attention-specific? | M_sec each |
| Q2 with size L | Does capacity move K*? | M_sec for LIB-K at K in {4, 16, 64} |

M_sec = min(M1, 32). If the J0-projected total exceeds 48 GPU-hours (your instruction: 1-2 days), secondary families are
dropped in this order until it fits: architectures, depth/width, Q2-size-L, size S, size L, training length. The primary
families are never reduced.

## 10. EXPLORATORY (no confirmatory alpha; excluded from headline claims)
Context lengths beyond training (n = 40, 80); the training trajectory of each statistic at B/4 and B/2; mixture-weight fits
between library and continuous predictors; per-r breakdowns beyond the cells above; anything not listed in sections 6 and 9.

## 11. Seeds (single source of truth after the freeze: `config/stage1_seed_manifest.yaml`)

| Role | Seed | Status |
|---|---|---|
| stage1_map | 70001 | used (map) |
| stage1_oc | 70101, 70102 | used (operating characteristics) |
| stage1_head_floor | 70201 | used (head floor) |
| smoke / timing (never decisions) | 69999, 12345 | used |
| engineering smoke (UNIF only, before the freeze) | 70901 | unused |
| pilot train / eval / library / bootstrap | 71001 / 71101 / 71201 / 71999 | unused |
| confirmatory R1 / R2 train | 72001 / 72002 | unused |
| confirmatory R1 / R2 eval | 72101 / 72102 | unused |
| confirmatory R1 / R2 library | 72201 / 72202 | unused |
| confirmatory bootstrap | 72999 | unused |
Torch seeds derive from `NamedStreams(root).seed_sequence(name, arm, seed_index)` (stable across arms and model counts).

## 12. Compute plan (ASSUMED until J0; one shared RTX A4000, wall-clock limited)

| Job | Where | Estimate |
|---|---|---|
| Unit tests, mutation matrix, J0 benchmark (300 steps per size, random data) | laptop then box | minutes |
| Engineering smoke (UNIF, 2 models, 5k steps, seed 70901) | box GPU | < 15 min |
| Pilot: 32 models x 200k steps (size M) + evaluation | box GPU | ASSUMED 5 min per model if batched 8-16 per GPU: about 1-2 h |
| Confirmatory primary: CONT + UNIF (M1 each) + 8 LIB arms (M2 each), 2 replicates, size M | box GPU | at M1 = M2 = 64: 1280 models; at ASSUMED 150 models per GPU-hour about 9 h |
| Secondary families | box GPU | up to about 1500 more models; trimmed by the rule in section 9 |
| Evaluation (KL quadrature for every model and cell) | box CPU + GPU | about 1-2 h |

## 13. Implementation and validation before the freeze (step 3)
`dynaicl_neural/` data (arm samplers with CRN), models (transformer, GRU, linear SSM), training (deterministic settings,
checkpointing, GPU temperature and utilisation logged per job), evaluation adapter, analysis (exists). Tests: sampler laws
(KS), CRN coupling, library atoms, causality (V-CAUSAL), oracle "models" (pop / stab / lib wrapped as models must be
classified POP-LIKE / STAB-LIKE / LIB-LIKE with zero regret), training determinism on CPU, bootstrap vs Gaussian agreement.
Mutation matrix: wrong prior in an arm, unpaired seeds, missing causal mask, target leaked into the input, wrong reference
in the analysis, off-by-one position, library atoms not nested. No test waits for input.

## 14. What was seen before this draft
Stage 0.5 per-item contrasts (planning spreads); the full separability map (reference-only); operating characteristics
(synthetic); smoke-seed reference numbers; the head-floor smoke. No model, no neural result, no Stage 1 pilot or
confirmatory seed.

## 15. Freeze (step 5, after your approval)
A Stage 1 manifest (`docs/FREEZE_MANIFEST_STAGE1.json`) over this document, the configs, the seed manifest, `dynaicl_families/`,
`dynaicl_neural/`, the scripts and tests; a read-only snapshot; an authorization gate for the confirmatory run (you issue it with
your own key, as in Stage 0.6); one confirmatory run per decision; append-only disclosure log `docs/DISCLOSURE_LOG_STAGE1.md`.
