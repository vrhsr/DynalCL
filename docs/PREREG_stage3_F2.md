# Stage 3 (F2 neural, bivariate VAR(1)) pre-registration: DRAFT 0.1 (2026-10-31). NOT FROZEN. Nothing trained. NOT AUTHORISED.

Status: draft for the user's review (task B4). F2 neural training needs the user's explicit go-ahead (standing rule: F2 only
after F1 approval). Numbers marked PENDING come from CPU jobs not yet run. Machinery, rules and lessons as the F1 draft
(`docs/PREREG_stage2_F1.md`) and the frozen Stage 1A pre-registration; what changes is the family, the output dimension and
the cells.

## 1. Questions
* **Q1-F2.** Do transformers pretrained on P_F2 behave like population-aware Bayes or like the context-only reference C_F2
  on held-out bivariate systems, in the cells where these differ by at least delta = 0.02 nats?
* **Q2-F2.** Do transformers pretrained on K bivariate systems from P_F2 behave like the library posterior or like a
  generalising reference, and from which K on?
* Why F2 (DERIVED from the F2 map, reference-only, `results-stage2-cpu-batch23` @ `56e73a8`): unlike the scalar families,
  library vs population is IDENTIFIABLE on held-out systems for K = 2 and K = 16 in every cell and for K = 64 in 13 of 15
  cells, so a memorisation-to-generalisation transition may be observable by score at library sizes where the scalar maps
  showed nothing; population vs context-only is IDENTIFIABLE at n in {10, 20} for every r (0.07-0.34 nats).

## 2. Family and references (VERIFIED)
x_t = A x_{t-1} + e_t, e_t ~ N(0, Sigma), d = 2, x_0 ~ N(0, r^2 I) independent of (A, Sigma), h = 1 (docs/MATH_F2.md).
pop = P_F2 (MNIW: B0 = 0.4 I, V0 = 0.09 I, nu0 = 7, Psi0 = 4 I, spectral radius < 0.95); ctx = C_F2 (B0 = 0, V0 = 100 I,
nu0 = 1.5, Psi0 = 0.01 I, radius < 0.999); lib_K exact. Validation (box, `56e73a8`): F2 validation PASS (117 tests);
F2-V11 mutation matrix PASS (7/7; unmatched reference and wrong truncation caught only by the extra detectors).
Truncated predictives are Monte Carlo with per-item SE <= 0.01 nats (disclosure S34); the context-only reference is not
computable to that criterion at n <= 3 and is MC-LIMITED at n = 5 in the map.

## 3. Arms
CONT-F2 (law P_F2) | CTX-F2 (law C_F2; positive control) | LIB-K, K in {2, 16, 64, 256} (atoms from P_F2, per model seed).
Common random numbers across arms as Stage 1A.

## 4. Models
Causal transformer as Stage 1A / F1, with a bivariate output head: a mixture of m bivariate Gaussians with full covariance.
**PENDING: head floor for d = 2** (the Stage 1A rule: smallest m with mean KL floor <= 0.001 nats in every cell; needs a
two-dimensional quadrature or a Monte Carlo floor estimate with a stated error). F1 needed m = 8 for its heavy-tailed
context-only predictive; the F2 context-only predictive is also heavy-tailed at short contexts.

## 5. Cells, estimands and rules
* Q1-F2: held-out pop vs ctx at n in {10, 20} x r in {0.25, 1, 4} (6 cells, all IDENTIFIABLE in the map). n = 5 is excluded
  unless a later reference run meets the Monte Carlo criterion there (it is MC-LIMITED in the map; estimates about 1.2 nats).
  Rule `classify_q1_held` with the bootstrap critical value; PROCEED threshold 5 of 6 cells (the Stage 1A proportion,
  rounded up).
* Q2-F2: held-out lib vs pop for K in {2, 16, 64} at n in {2, 3, 5, 10, 20} (IDENTIFIABLE or PARTIAL in the map); arm-level
  gate and two-way rule `classify_memorisation` as Stage 1A; K = 256 is a generalisation control (not mapped).
* Controls C1 (CTX-F2 vs ctx on C_F2 systems, n in {10, 20}) and C2 (each arm vs its own reference at n = 20); V-RB, V-REPRO.

## 6. Operating characteristics and power (PENDING)
To be computed with the analysis's bootstrap critical value (audit A1) from the F2 map's per-cell gaps and SDs, and turned into
a power lookup with the frozen rule, before any freeze.

## 7. Seeds (proposed, UNUSED; registered at the freeze)
f2n_pilot_* 83001/83101/83201/83999; f2n_confirmatory_* 84001-84002 / 84101-84102 / 84201-84202 / 84999; f2n_head_floor 83301.

## 8. Open decisions (the user's)
1. Whether F2 neural follows F1 neural, runs in parallel, or replaces it (F2's library separability is the stronger case
   for Q2; F1's population window is the stronger case for Q1).
2. GPU budget (bivariate models and 2-D heads cost more per step; to be measured).
