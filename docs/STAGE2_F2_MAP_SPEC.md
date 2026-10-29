# F2 separability map: specification (committed BEFORE the map is run)

Status: spec, 2026-10-29 (task B3). Reference-only map for F2 = bivariate VAR(1) with a stability-truncated
matrix-normal-inverse-Wishart prior (docs/MATH_F2.md); guides design, not a confirmatory result. Code
`dynaicl_families/stage2/f2_map.py`, runner `scripts/stage2_f2_map.py`, references `dynaicl_families/stage2/f2_var.py`.

## 1. References, sets, grid
* pop = P_F2 (B0 = 0.4 I, V0 = 0.09 I, nu0 = 7, Psi0 = 4 I, rho(A) < 0.95); ctx = C_F2 (B0 = 0, V0 = 100 I, nu0 = 1.5,
  Psi0 = 0.01 I, rho(A) < 0.999); lib_K = uniform over K atoms (A_k, Sigma_k) drawn from pop (exact).
* HELD: systems from pop (truth = pop). INLIB: systems are the K atoms (truth = lib_K). x_0 ~ N(0, r^2 I), r in {0.25, 1, 4};
  h = 1 only (the Rao-Blackwellised estimator and the control variate exist only for h = 1, MATH_F2 section 6).
* n in {2, 3, 5, 10, 20} for pairs without ctx (pop-lib, lib-pop); **n in {5, 10, 20} for pairs with ctx (pop-ctx, lib-ctx).**
  Reason (measured before this spec, f2_tests seed, 40 items per n, disclosure S35): at n = 2 and 3 the ctx reference capped at
  2^22 draws for 23/40 and 22/40 items (RMS per-item SE 0.046 and 0.45, some non-positive estimates); at n = 5 3/40 capped;
  n >= 10 none. DERIVED explanation: with d = 2 the ctx model has 7 parameters while n transitions give 2n observed numbers, so
  under its very vague prior the predictive is barely constrained for n <= 3. Those cells are reported as NOT COMPUTABLE.
* K in {2, 16, 64}; 8 library draws per K (atoms nested across K within a draw).

## 2. Sizes and seeds
Seed role `f2_map` (root 80601, config/stage2_seed_manifest.yaml; never used before this spec's commit). HELD systems from
`NamedStreams(80601)` (stream code 11); library atoms from stream `f2_map_library/draw{d}`; INLIB systems from
`SeedSequence(80601, spawn_key=(sha256("f2_map_inlib"), d, K))` (stream code 12); each Monte Carlo item has its own child
stream. HELD: N = 4000 per (r, n); INLIB: N = 1000 per (r, K, draw).

## 3. Estimator and Monte Carlo criterion (user decision S34)
Paired realised log-score differences (common random numbers). pop and ctx are Monte Carlo estimates (MATH_F2 section 5,
production estimator C or R, two-phase choice) with per-item target SE(log p) <= 0.01 nats and at least 1000 accepted draws,
cap 2^22 draws. Each gap carries SE = sqrt(SE_items^2 + SE_MC^2) with SE_MC = sqrt(sum_i se_i^2) / N. A cell is **MC-LIMITED**
(reported, not classified) if SE_MC > delta / 100 = 2e-4 or more than 1% of its items have a per-item SE > 0.01 or a
non-finite estimate.

## 4. Decision rules (as the Stage 1A and F3 maps)
Bound = mean +/- 3 SE. pop-ctx cell (r, n): IDENTIFIABLE if lower >= delta = 0.02; UNIDENTIFIABLE if upper < delta; else
BORDERLINE. Library cells: per draw as above; IDENTIFIABLE / UNIDENTIFIABLE if >= 90% of the 8 draws agree; MC-LIMITED if more
than 10% of draws are; else PARTIAL.
Validity (any failure: map INVALID): (i) radius-50 truncation equals the closed-form untruncated predictive to 1e-12 on 20
contexts; (ii) the interval Rao-Blackwell estimator (independent algorithm, MATH_F2 5b) agrees with the production estimator on
10 HELD items at n = 10 for pop and ctx, |z| <= 4 each; (iii) the library predictor equals per-atom scipy evaluation to 1e-10 on
20 contexts; (iv) disjointness: no HELD system equals a library atom; INLIB systems are atoms.

## 5. Compute
Timing (f2_tests seed): pop 5-13 ms per item; ctx 6 ms (n = 20), 27 ms (n = 10), about 0.8 s (n = 5) per item. Estimated about
20-25 CPU-hours; box CPU with 16 workers, relay `pilot_tooling/RELAY_stage2_cpu_batch2.md`, small result files on
`results-stage2-cpu-batch2`.
