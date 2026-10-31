# Stage 2 (F1 neural) pre-registration: DRAFT 0.1 (2026-10-28). NOT FROZEN. Nothing trained.

Status: draft for the user's review (task A3). Not authorised to run; F1 or F2 neural training waits for the user. Every number
marked PENDING comes from a CPU job that has not returned yet. This draft reuses the frozen Stage 1A machinery
(`dynaicl_neural/`, decision rules, bootstrap critical value, two replicates, controls, pilot and cap logic); it changes the
family, the arms, the cells and the seeds. Where Stage 1A taught a lesson, the lesson is applied (audit A1: bootstrap critical
value in the operating characteristics; S21: convergence criterion; S28: the gate refuses test keys).

## 1. Questions
* **Q1-F1 (primary).** Do transformers pretrained on the F1 population P_F1 (unknown, varying noise scale) behave like
  population-aware Bayes (pop) or like the context-only reference (ctx) on held-out systems, in the cells where these two
  references differ by at least delta = 0.02 nats?
* **Q2-F1 (primary).** Do transformers pretrained on a library of K systems (a_k, sigma_k) from P_F1 behave like the K-atom
  library posterior or like a generalising reference, and from which K on?
* Why F1 at all (DERIVED from the maps, reference-only): in Stage 1A (sigma known) pop and stab differ by only 0.023-0.054 nats
  and only for n <= 5; in F1 the held-out pop vs ctx gap is 0.03-0.32 nats and IDENTIFIABLE up to n = 10 at every r
  (results_stage1/map_F1, `results-stage1-step3` @ `66c5846`), because the population also carries noise-scale information.

## 2. Family and references (VERIFIED or PENDING as marked)
* x_t = a x_{t-1} + sigma e_t, x_0 ~ N(0, r^2) independent of (a, sigma), h = 1, n >= 2 (MATH_F1 section 3).
* pop: a ~ TN(0.4, 0.3^2; +/-0.95), sigma^2 ~ IG(3, 2), independent. ctx: a ~ U(+/-0.999), log sigma ~ U(log 0.01, log 100).
  lib_K: uniform over the model's own K atoms (a_k, sigma_k) from pop. Implementation `dynaicl_families/ar1_unknown_sigma.py`
  (frozen in Stage 1 v2).
* Validation (VERIFIED): F1-V1..V8 frozen tests 19/19; Stage-0-scale calibration / SBC / coverage / optimality / known-sigma
  limit PASS (`results_stage2/f1_validation/`, 180 tests); F1-V9 mutation matrix PASS on the box (all 6 mutations detected,
  clean baseline 19/19; `results-stage2-cpu-batch1` @ `50a7664`). Wrong truncation is detected only by the structural matched
  guard (disclosure S33).

## 3. Arms (they differ only in the law of (a, sigma) during pretraining)
| Arm | Law of (a, sigma) | Its Bayes predictor | Role |
|---|---|---|---|
| CONT-F1 | P_F1 | pop | Q1 test arm |
| CTX-F1 | ctx law | ctx | Q1 positive control; capability control C1 |
| LIB-K, K in {1, 2, 4, 8, 16, 32, 64, 256} (the F1 map's K values) | uniform over K atoms from P_F1 (per model seed) | lib_K | Q2 |
* x_0 ~ N(0, r^2), r uniform on {0.25, 1, 4} per sequence. Common random numbers across arms as Stage 1A (same initialisation,
  data order, x_0 and innovations per seed index; (a, sigma) by each arm's inverse CDF from shared uniforms).
* **Design risk (ASSUMED manageable, to be checked in the engineering smoke):** the CTX-F1 arm spans four orders of magnitude of
  sigma; a network without input normalisation may fail its control C1 for reasons unrelated to the question. A per-sequence
  scale normalisation would change what "context-only" means for the network and is NOT adopted without a decision.

## 4. Models and training
* As Stage 1A (causal transformer size M, AdamW, batch 256, warmup and cosine schedule, float32, deterministic algorithms), so
  that the F1 and Stage 1A results are comparable. Output head: Gaussian mixture with m components.
* **Head: m = 8 Gaussian components (VERIFIED, `results-stage2-cpu-batch23` @ `56e73a8`, `results_stage2/f1_head_floor/`).**
  The Stage 1A rule (smallest m in {1, 2, 4, 8} whose mean KL floor is <= 0.001 nats in every cell) applied to the F1
  references (pop, ctx, lib_2/16/256; HELD and each arm's own law; n in {2, 3, 5, 10, 20} x r in {0.25, 1, 4}; 100 contexts per
  cell; whole-line quadrature, max mass error 4.8e-10) selects m = 8: the hardest cell is the context-only reference at
  r = 4, n = 2 (mean floor 0.0039 at m = 4; 0.00080 at m = 8, worst single context 0.0019). Stage 1A used m = 2. Consequence
  (DERIVED): the heavy-tailed context-only predictive at the shortest contexts sits close to the floor even at m = 8, so the
  CTX-F1 arm's control C1 at n = 2 carries a representational component of up to about 0.001 nats on average.
* Budget grid {10k, 25k, 50k, 100k} with the Stage 1A convergence criterion (validation NLL at positions 0-2 improves by < 0.002
  nats to the next grid point; the last point cannot qualify). Cap rule as Stage 1A with the budget the user sets (PENDING the
  Stage 1A Amendment 2 decision, which sets the precedent).

## 5. Evaluation
Contexts only through the frozen `harness.make_context`. Sets per replicate: HELD (P_F1) 40 000 systems; PROBE, OOS-A
(|a| in (0.95, 0.999)) and OOS-SIGMA (sigma outside the bulk of IG(3, 2)) 10 000 each; CTX systems 4 000 for the controls.
Per-context KL(X || model) by y-quadrature (the F1 predictives are closed form given the a-quadrature).

## 6. Estimands, families and classification rules (as Stage 1A, cells from the F1 map)
### 6.1 Q1-F1 (per replicate; alpha = 0.025)
12 cells: r in {0.25, 1, 4} x n in {2, 3, 5, 10} (all HELD pop|ctx cells marked IDENTIFIABLE in the F1 map; n >= 20 is
UNIDENTIFIABLE there). Statistics R_pop = E[KL(pop || CONT_i)], G = E[KL(pop || CTX_i) - KL(pop || CONT_i)],
Delta = E[KL(pop || ctx)] from the map. 24 statistics, band estimate +/- c x SE (two-level SE), c from the hierarchical
bootstrap (4000 draws). Rule `classify_q1_held` (epsilon 0.01). Confirmed only if both replicates agree.
**Q1-F1 answer:** POP-LIKE in >= 9 of 12 cells and CTX-LIKE in none -> "behaves like population Bayes"; the mirror image ->
"behaves like the context-only reference"; otherwise "mixed or inconclusive". (9 of 12 = the Stage 1A proportion 7 of 10,
rounded up; justification: the same evidential bar per cell.)
### 6.2 Q2-F1 (per replicate; alpha = 0.025)
Cells per K: the designed-set cells (PROBE, OOS-A, OOS-SIGMA) x r in {0.25, 1} x n in {5, 10, 20} marked IDENTIFIABLE or PARTIAL
in the F1 map, plus HELD lib|pop for K <= 4 (IDENTIFIABLE there). Arm-level gate, statistics and the two-way rule
`classify_memorisation` exactly as Stage 1A section 6.2. **Caveat carried from Stage 1A:** on out-of-support sets the library's
penalty partly reflects coverage of the support edge, not only memorisation.
### 6.3 Controls and critical checks (any failure -> BLOCKED)
C1: CTX-F1's regret against ctx on CTX systems, r in {0.25, 1, 4}, n in {2, 3}: upper band < 0.01. C2: every arm's regret against
its own reference on its own distribution at n = 20: upper band < 0.01. V-RB, V-REF, V-CAUSAL, V-REPRO (1e-4) as Stage 1A.

## 7. Operating characteristics and sample size (VERIFIED 2026-10-29; box CPU batch 1, commit `50a7664`)
`scripts/stage2_f1_operating_characteristics.py` on the box (provenance commit `f10dc8c`): the Stage 1A v2 simulation model and
grid with the 12 F1 Q1 cells (Delta and per-context sd from the F1 map) and three designed-set Q2 cells; **critical value =
the analysis's own hierarchical bootstrap** (audit A1), alpha 0.025, two replicates must agree. 360 Q1 settings x 200 studies;
192 Q2 settings x 300 studies. Largest P_wrong over every setting: 0.0.
Power lookup built with the frozen rule of `scripts/stage1_power_lookup.py` (P_correct >= 0.8 for both pi = 0 and pi = 1,
e <= 0.005, both rho_cell; min 32 models): `results_stage2/f1_power_lookup/f1_power_lookup.json`.
| M | Q1 s*(M) F1 (Stage 1A) | Q2 s*(M) F1 (Stage 1A) |
|---|---|---|
| 32 | 0.01 (0.01) | 0.10 (0.02) |
| 64 | 0.02 (0.01) | 0.10 (0.05) |
| 128 | 0.03 (0.02) | 0.10 (0.05) |
Reading (DERIVED from the table, not a result about networks): F1's larger gaps buy tolerance for noisier seeds at M >= 64 (Q1)
and at every M (Q2); at M = 32 the Q1 tolerance equals Stage 1A's. The UNIF-only spread read of Stage 1A (between-seed sd 0.0017
at 10k, S20) suggests seed sds of this order are plausible, but no F1 network has been trained (UNVERIFIED for F1).

## 8. Program verdict
BLOCKED / NOT RESOLVABLE (capability or compute) / PROCEED / REVISE, in that order, with the Stage 1A definitions.

## 9. Seeds (to be registered in config/stage2_seed_manifest.yaml at the freeze; proposed, UNUSED)
f1n_pilot_train 81001, f1n_pilot_eval 81101, f1n_pilot_library 81201, f1n_pilot_bootstrap 81999; f1n_confirmatory_train
82001/82002, _eval 82101/82102, _library 82201/82202, _bootstrap 82999; f1n_head_floor 81301; f1n_engineering_smoke 81901.
(Checked against all existing tables by tests_stage2/test_seed_roles.py when registered.)

## 10. What has been seen before this draft
The F1 map (reference-only), the F1 reference validation, the Stage 1A pilot's budget outcome (training convergence on
Stage 1A arms; no effect information). No F1 neural model exists.

## 11. Open decisions (the user's)
1. Whether to pursue F1 neural at all, and whether before or after the Stage 1A Amendment 2 decision.
2. (Resolved 2026-10-31: the head floor selects m = 8 Gaussian components; no change of head family needed.)
3. Input normalisation for the CTX-F1 arm (affects what "context-only" means for the network).
4. GPU budget for F1 (sets the cap).
