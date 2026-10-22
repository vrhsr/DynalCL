# Stage 1A separability map: specification (written and committed BEFORE the map is run)

Purpose: decide, from the Bayes references alone (CPU, no model), in which cells a trained model could be classified as
population-like, context-only-like or library-like, because the references themselves differ there by at least
delta = 0.02 nats. Plan v2 section 2. Code: `dynaicl_families/separability.py`; runner `scripts/stage1_separability_map.py`;
summary and decisions `scripts/stage1_separability_summarize.py`.

## 1. Family, references, sets
* Scalar AR(1), sigma = 1 known, h = 1. References (batch closed forms, equal to the frozen references within 1e-9 nats,
  TESTED in `tests_stage1/test_ar1_batch_references.py` including the stored Stage 0.5 items):
  pop = truncated normal (mean 0.4, sd 0.3) on (-0.95, 0.95); stab = uniform on (-0.999, 0.999); lib_K = uniform over K atoms drawn from pop.
* Evaluation sets: HELD (systems from pop; truth = pop), INLIB (systems = the library's atoms; truth = lib_K), PROBE (a uniform
  over the 39-point grid -0.95, -0.90, ..., 0.95), OOS (|a| ~ U(0.95, 0.999), random sign: outside pop's support).
* x_0 ~ N(0, r^2), r in {0.25, 1, 4}. Q1 context lengths n in {1, 2, 3, 5, 10, 20, 40, 80}; Q2 n in {1, 2, 3, 5, 10, 20}.
* K in {1, 2, 4, 8, 16, 32, 64, 256}; library draws: 32 per K for K <= 64, 16 for K = 256. Atoms of draw d are nested across K.

## 2. Sizes and seeds
* Root seed **70001** (new role `stage1_map`; never used before; distinct from the planned pilot 710xx and confirmatory 720xx roots).
  Held-out, probe and out-of-support systems come from `NamedStreams(70001)` through the frozen `generate_split`
  (stream codes 0, 2, 3); library atoms from stream `stage1_map_library/draw{d}`; in-library systems from a seed derived by
  `SeedSequence(70001, spawn_key=(sha256("stage1_map_inlib"), d, K))`.
* Q1: HELD N = 40 000; PROBE and OOS N = 10 000. Q2 per draw: HELD and INLIB realized N = 20 000; KL estimates N = 2 000.

## 3. Estimators
* Truth-matched pairs: HELD (pop, stab), HELD (lib, pop), INLIB (lib, pop), INLIB (lib, stab). Gap = E[LS(truth) - LS(other)].
  * HELD pairs: primary = per-context KL(truth || other) (Rao-Blackwellised); check = realized targets.
  * INLIB pairs: realized targets only (primary).
* Other pairs (no reference is the truth): HELD (lib, stab), PROBE and OOS (pop, stab), (lib, pop), (lib, stab).
  Behavioural separation = min(E[KL(A || B)], E[KL(B || A)]).
* KL integrals: composite Gauss-Legendre in y, panels <= sigma/2, window mass checked at run time (|mass - 1| <= 1e-8 or the
  run aborts).

## 4. Decision rules (all frozen here)
* Bound = estimate +/- 3.0 x SE (per cell; two-sided per-cell level about 0.0027). A global Bonferroni over thousands of map
  cells would make the map uninformative, and the map only guides design. Every model-level classification is re-gated at
  analysis time on the confirmatory evaluation systems, inside that analysis's simultaneous band (PREREG_stage1). The
  expected number of wrongly marked cells is reported with the map.
* **Q1 cell** (set, r, n): IDENTIFIABLE if the lower bound >= delta; UNIDENTIFIABLE if the upper bound < delta; otherwise BORDERLINE.
* **Q2 cell** (set, r, n, K, pair): per draw d a bound as above. IDENTIFIABLE if >= 90% of draws have a lower bound >= delta;
  UNIDENTIFIABLE if >= 90% of draws have an upper bound < delta; otherwise PARTIAL. Library draws differ, so the neural analysis
  gates each model on its own library; PARTIAL cells are classified only for models whose library passes there.
* **Validity checks (any failure: the map is INVALID and is not used):** (i) realized vs Rao-Blackwell agreement on every HELD
  truth-matched cell: |z| <= z_C, with z_C the two-sided Bonferroni critical value for familywise 0.001 over all such comparisons;
  (ii) every KL window mass check passes; (iii) disjointness assertions pass (held-out systems are not library atoms;
  no shared trajectories or noise between sets).
* Mechanical selection for the pre-registration: Q1 neural cells = HELD cells marked IDENTIFIABLE. Q2 neural cells = the (set, K)
  combinations marked IDENTIFIABLE or PARTIAL for at least one n. Out-of-support and probe sets serve the pre-registered
  out-of-support ablation and Q2 only where marked.

## 5. Compute
Measured on the laptop with one tenth of the sizes: Q1 (r = 1) 23 s; Q2 unit K = 8: 16 s; K = 64: 66 s. Extrapolated full map
(ASSUMED linear): about 27 CPU-hours, dominated by K = 256. It runs on the box CPU (no GPU), in tmux, with about 24 workers:
about 1-1.5 h wall. Results: small CSVs (< 2 MB) on a results branch.
