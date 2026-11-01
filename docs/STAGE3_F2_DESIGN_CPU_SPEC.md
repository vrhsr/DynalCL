# F2 neural design, CPU part: bivariate head floor and Q2 operating characteristics (specification)

Status: spec, 2026-11-01, committed BEFORE the seed roles below are used. CPU only (no network, no GPU, no torch). User decision
S44: the memorisation-transition study uses F2 (option B) after the seed-variance probe; its CPU prerequisites start now.
Drafts it serves: `docs/PREREG_memorisation_transition.md`, `docs/PREREG_seed_variance_probe.md` (F2 arm LIB-64).
**Seen before this spec:** the F2 map (S38), the theory quantities (S41), the paper audit (S40); not batch 4 or batch 5.

## A. Bivariate head floor (role `f2n_head_floor`, 83301)
Question: how many components m must a network's output head (a mixture of m bivariate Gaussians with full covariance) have so
that it can represent each reference predictive it is compared with, to within the Stage 1A floor of epsilon / 10 = 0.001 nats?
* References: pop (P_F2; the CONT-F2 arm's own law = held-out law) and lib_K for K in {2, 16, 64, 256, 1024} (the LIB-K arms),
  each on HELD systems (from P_F2) and, for lib_K, on OWN systems (the library's atoms, uniformly). Library atoms: exact draws
  from P_F2 (as the F2 map), one library per K for this purpose.
* Cells: n in {2, 3, 5, 10, 20} x r in {0.25, 1, 4}; C = 40 contexts per cell (contexts cut by the frozen `make_context`).
* Representation of the reference predictive per context: lib_K is an exact Gaussian mixture; pop is represented as the
  mixture of the Rao-Blackwellised Student-t predictives of J = 2000 accepted draws from its untruncated posterior (the
  production estimator R's mixture; MATH_F2 sections 4-5), which can be sampled and evaluated exactly.
* Floor estimate per context and m in {1, 2, 4, 8} (the F1 grid): as the F1 head floor (weighted EM on quadrature nodes of
  p), in two dimensions: a 96 x 96 tan-substitution Gauss-Legendre grid on coordinates whitened by p's moments; mass error
  |sum w p - 1| checked per context (abort above 1e-5); q_m maximises sum_i a_i log q(y_i), a_i = w_i p(y_i) normalised
  (full covariances; two starts; up to 300 iterations; relative tolerance 1e-8; covariance floor 1e-9 times the scale), which
  minimises the quadrature KL(p || q_m) = sum_i a_i (log p - log q_m); the floor for m is the minimum over m' <= m (nested
  families; local optima make each value an upper bound). If no m <= 8 qualifies, the rule reports none and m = 16 is a
  follow-up.
* **Amendment before any production seed was used (2026-11-01):** the first version of this section fitted q_m by EM to
  100 000 samples and estimated the KL on 20 000 independent samples. The smoke on the `f2_tests` role showed about 270 s per
  context (impractical), and reducing the sample size would bring the fitting bias (about parameters / (2 S)) close to the
  0.001 threshold. Quadrature has no sampling bias and follows the F1 precedent; on one smoke context it agreed with the
  sample-based estimate at m = 2 (1.6e-3 vs 1.5e-3 nats), with a mass error of about 1e-13 at a 128-point grid and 4e-12 at
  96. Disclosed (S44).
* Decision rule (as Stage 1A and F1): the head uses the smallest m whose mean floor is <= 0.001 nats in every cell; a cell
  whose mean-floor SE exceeds 2e-4 is flagged and reported.

## B. Q2 operating characteristics and power lookup (role `f2_oc`, 83401)
* Simulation model, grid and rules exactly as the F1 Q2 operating characteristics (`scripts/stage2_f1_operating_characteristics.py`,
  functions `q2_replicate`, `q2_classify` imported unchanged; synthetic "models"; Bonferroni-t critical value with the same
  ASSUMED family size 480 until the F2 family is fixed; two replicates must agree). Grid: pi in {0, 1}, e in {0, 0.01},
  s in {0.01, 0.02, 0.05, 0.1}, M in {16, 32, 64, 128}; 300 studies per setting.
* Cells: held-out F2 map (`results-stage2-cpu-batch23` @ `56e73a8`, `results_stage2/f2_map/map_rows.csv.gz`, read with
  `git show`, sha256 recorded): r = 1, n in {10, 20}, K in {16, 64}; separations s_lp = mean over library draws of the
  pop-lib gap, s_ps = the pop-ctx gap, s_ls = |s_ps - s_lp| (the paired identity gap(lib, ctx) = gap(pop, ctx) -
  gap(pop, lib) on the same items).
* Power lookup by the frozen rule (`scripts/stage1_power_lookup.py`, function `lookup`, unchanged; P_correct >= 0.8, minimum
  32 models): Q2 s*(M).
* When batch 5 extends the F2 library map (K up to 1024, n up to 80), the cells are re-chosen from it and B is re-run under the
  same role with a new output folder; the change is disclosed and both versions are kept.

## C. Outputs and compute
* A: `results_stage2/f2_head_floor/` (per-cell CSV, summary with the chosen m, provenance). Estimated from the smoke: see the
  relay; over 10 minutes, so it runs on the box after batches 4 and 5.
* B: `results_stage2/f2_oc/` (oc_q2_f2.csv, f2_power_lookup.json, input sha256, provenance). Runs locally if under about 10
  minutes, otherwise on the box.
* Smoke runs use the `f2_tests` role (never results). Nothing here changes a map, a frozen file or a decision.
