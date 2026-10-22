# Stage 0.6 Phase B validation report

Scope: the implementation and independent validation of the noisy-observation reference. **No confirmatory evaluation was
run and no Stage 0.6 effect size was inspected** (DISCLOSURE_LOG_STAGE06.md entries 1-8). Seeds: validation roots
61001-61017; design calculations 61901-61902; selection 63001 (audit only). The confirmatory roots 64101/64102/64999 are
allocated in `config/stage06_seed_manifest.yaml` and unused.

## 1. Implementation (new files)

| File | Purpose |
|---|---|
| `dynaicl/systems/noisy.py` | Noisy-observation model, condition (fingerprint covers prior + noise + x_0 prior), split generator (observation noise from a separate named stream) |
| `dynaicl/references/kalman_quadrature.py` | Kalman filter vectorised over nodes and systems with a shared prefix; observation predictive; shared node set; reference, comparator and secondary noise-aware candidates |
| `dynaicl/evaluation/noisy_harness.py` | The single context cutter (y only), the target index n + h, batch and per-context scoring |
| `dynaicl/validation/noisy_oracles.py` | Independent oracles: explicit joint covariance + Cholesky, scipy.quad over a, Monte Carlo, finite-n Fisher information (analytic, finite-difference, MC score) |
| `dynaicl/validation/checks_stage06.py`, `mutations_stage06.py` | Checks V1-V17 and seven mutations |
| `tests/test_stage06_reference.py`, `tests/test_stage06_mutations.py` | pytest wrappers |
| `scripts/stage06_noise_level_verification.py`, `scripts/stage06_selection_audit.py` | Design calculations and the selection audit |
| `config/stage06_seed_manifest.yaml` | Seed roles |

Changed shared code: `PredictorDescription` gains `observation_model` (default "noise-free", so Stage 0/0.5 behaviour is unchanged;
the full pre-existing suite was re-run, see section 6).

## 2. Validation checks (all VERIFIED by execution; numbers are the measured diagnostics)

| ID | Check | Result | Key diagnostic |
|---|---|---|---|
| V1 | Kalman vs joint-Gaussian Cholesky, fixed a (log-likelihood; observed and latent targets; h = 1, 5; all q, r; n in {0, 1, 2, 5, 20, 40}; a up to 0.998) | PASS | 3240 comparisons; worst error 0.005 x tolerance (tolerance 50 eps kappa(Sigma)) |
| V2 | The observed-target variance exceeds the latent-target variance by exactly sigma_v^2 | PASS | worst 0.07 x the rounding tolerance |
| V3 | q = 0 Kalman path vs the Stage 0.5 code path (both priors) | PASS | 720 comparisons; worst 1.3e-4 x tolerance |
| V4 | **Tier-1:** stored Stage 0.5 per-item contrasts reproduced on the Stage 0.5 seeds | PASS | **243,216 items; max abs diff 9.3e-15** (tolerance 1e-9, fixed in advance) |
| V5 | Continuity as sigma_v -> 0 | PASS | slope 1.999 for fixed data (expected 2); 0.994 for consistent data (expected 1); monotone |
| V6 | Quadrature convergence (8 hard cases x 2 horizons; broad, concentrated and boundary) | PASS | worst paired-gain error at the default 1040 nodes vs 4x: **6e-15** (requirement 2e-5; budget 2e-4) |
| V7 | Independent integration oracle (Cholesky + scipy.quad), reference AND comparator | PASS | 160 comparisons; worst 1.6e-6 x tolerance |
| V8 | Monte Carlo (prior importance sampling + exact conditional draws) | PASS | max abs z 2.94 (z_crit 3.99) |
| V9 | Calibration of the population reference: SBC of a, PIT and 50/80/95% coverage (q in 3 levels x r in 3 x n in {2, 10, 40} x h in {1, 5}) | PASS | 243 tests, min p 1.2e-4 (Bonferroni level 4.1e-6) |
| V10 | Bayes optimality vs every context-only predictor (noise-aware and noise-naive) | PASS | **0 violations / 198** comparisons (counts only, by rule) |
| V11 | Parity null (the population class with the stability prior equals the comparator) | PASS | 936 per-context comparisons, bitwise, plus the batch path |
| V12 | Information access: latent-path invariance, future invariance, interface rejection, off-by-one with a positive control | PASS | all sub-checks True |
| V13 | Shared-prefix batch path equals the per-context path (n = 2..40, all q, r, h) | PASS | max abs diff 8e-15 |
| V14 | Seed isolation: latent path unchanged by q; observation noise disjoint; manifest disjoint from repo seeds | PASS | 24 seeds, 0 collisions |
| V15 | Analytic special cases | PASS | narrow prior -> Kalman 2.7e-8; high-noise -> prior predictive, monotone (2.0e-4, 4.5e-5, 2.6e-6); Riccati 6e-16; chain rule h = 2: 7e-14 |
| V16 | Failure surfacing (NaN/inf inputs, impossible configurations, non-finite scores raise) | PASS | all sub-checks True |
| V17 | Noise-naive baselines match their stated definitions | PASS | flat-prior mean = S_xy/S_xx of y |

Theorem-level (bugs if violated): V1, V3, V4, V5, V6, V7, V8, V11, V12, V13, V15, V16, the calibration (V9) and
non-negative expected gain (V10). All hold. Calibration is not treated as proof of correctness: V1, V4 and V7 are
independent analytic and numerical confirmations.

## 3. Mutation tests (VERIFIED)

Matrix over 13 fast checks (V9s = reduced calibration; baseline row all pass). "FAIL" = clean detection; the
"(guard)" entry is the harness's designed consistency assertion.

| Mutation | Detected by |
|---|---|
| omit_target_noise_variance (mandatory) | V1, V2, V7, V8, V15, V9s |
| wrong_sigma_v_in_reference | V7, V8, V11, V15, V9s |
| prior_mismatch_in_reference | V7, V8, V11, V9s |
| latent_state_passed_to_predictor | V12 (latent_invariance), V9s |
| off_by_one_context_length | V12 (indexing + harness guard), V13 (guard), V9s (guard) |
| off_by_one_target_index | V12 (indexing, targets_at_n_plus_h), V13/V9s (explicit "too short" error) |
| noise_naive_mislabeled_as_noise_aware | V7, V11 (behavioural mismatch), V12 (future/batch API) |

pytest `test_stage06_mutations.py` requires a **clean FAIL** (an exception alone is not accepted) for every mutation.
The full matrix over every check, including the slow V4/V9/V10, exceeds the 10-minute local budget and belongs to the
Phase D remote pipeline.

## 4. Noise levels and the selection-data audit

See `STAGE06_NOISE_LEVEL_VERIFICATION.md` and `STAGE06_SELECTION_AUDIT.md`. In summary:
* The asymptotic rule holds by construction. At finite n (10..40, r <= 1) the Phase A retention is 0.47-0.50 / 0.22-0.24 /
  0.09-0.12. r = 4 retains more. Short n retains much less. Bayesian information gain beyond the prior is lower still.
  Finite-n calibrated alternatives (q = 0.721/2.363/5.714 at n = 20; 0.738/2.462/6.109 at n = 40) are within 4-14% of the
  proposal.
* No valid noise-aware context-only alternative beats stability-only (0/240 cells), and no noise-naive predictor does
  (0/576).

## 5. Remaining uncertainties (UNVERIFIED or open)

1. **Far tails.** Accuracy is verified at predictive quantiles 1e-3..1-1e-3, at targets, and by the oracle at 3 points per
   context. Far-tail log densities are not separately verified.
2. **Fixed node set.** Convergence is verified for the posteriors in the planned grid (n <= 40, r <= 4, q in {0, 0.755,
   2.56, 6.5}). Larger n or r would need re-verification.
3. **V9 min p = 1.2e-4** is low for 243 tests (about a 3% chance under correct code) but above the pre-set level.
4. **Full mutation matrix** over the slow checks is not yet run (Phase D, remote).
5. **Precision planning** depends on the estimand definition and on L (Phase C). The Stage 0.5 per-n sd at n = 10..20 is
   0.07-0.18 (zero noise).
6. **No version control** (user decision): the integrity evidence will be SHA-256 manifests plus a snapshot archive.

## 6. Test runs

See section 7.

## 7. Test runs (verbatim summary lines)

**Stage 0.6 tests** (`pytest -v tests/test_stage06_reference.py tests/test_stage06_mutations.py`):

```
============================= test session starts =============================
platform win32 -- Python 3.13.5, pytest-9.0.2, pluggy-1.6.0 -- C:\Users\Ramana\AppData\Local\Programs\Python\Python313\python.exe
DYNAICL_MUTATION=<none>
rootdir: E:\study-buddy\DynaICL
configfile: pyproject.toml
plugins: langsmith-0.7.22, anyio-4.8.0, cov-7.1.0, mock-3.15.1
collecting ... collected 23 items

tests/test_stage06_reference.py::test_stage06_numerical_reference[V1] PASSED [  4%]
tests/test_stage06_reference.py::test_stage06_numerical_reference[V2] PASSED [  8%]
tests/test_stage06_reference.py::test_stage06_numerical_reference[V3] PASSED [ 13%]
tests/test_stage06_reference.py::test_stage06_numerical_reference[V5] PASSED [ 17%]
tests/test_stage06_reference.py::test_stage06_numerical_reference[V6] PASSED [ 21%]
tests/test_stage06_reference.py::test_stage06_numerical_reference[V7] PASSED [ 26%]
tests/test_stage06_reference.py::test_stage06_numerical_reference[V8] PASSED [ 30%]
tests/test_stage06_reference.py::test_stage06_numerical_reference[V13] PASSED [ 34%]
tests/test_stage06_reference.py::test_stage06_numerical_reference[V15] PASSED [ 39%]
tests/test_stage06_reference.py::test_stage06_numerical_reference[V16] PASSED [ 43%]
tests/test_stage06_reference.py::test_stage06_numerical_reference[V17] PASSED [ 47%]
tests/test_stage06_reference.py::test_stage06_parity_null_and_access PASSED [ 52%]
tests/test_stage06_reference.py::test_stage06_tier1_regression_against_stored_stage05_items PASSED [ 56%]
tests/test_stage06_reference.py::test_stage06_calibration_of_population_reference PASSED [ 60%]
tests/test_stage06_reference.py::test_stage06_bayes_optimality_counts_only PASSED [ 65%]
tests/test_stage06_mutations.py::test_stage06_detectors_pass_without_mutation PASSED [ 69%]
tests/test_stage06_mutations.py::test_stage06_mutation_detected_by_clean_failure[latent_state_passed_to_predictor] PASSED [ 73%]
tests/test_stage06_mutations.py::test_stage06_mutation_detected_by_clean_failure[noise_naive_mislabeled_as_noise_aware] PASSED [ 78%]
tests/test_stage06_mutations.py::test_stage06_mutation_detected_by_clean_failure[off_by_one_context_length] PASSED [ 82%]
tests/test_stage06_mutations.py::test_stage06_mutation_detected_by_clean_failure[off_by_one_target_index] PASSED [ 86%]
tests/test_stage06_mutations.py::test_stage06_mutation_detected_by_clean_failure[omit_target_noise_variance] PASSED [ 91%]
tests/test_stage06_mutations.py::test_stage06_mutation_detected_by_clean_failure[prior_mismatch_in_reference] PASSED [ 95%]
tests/test_stage06_mutations.py::test_stage06_mutation_detected_by_clean_failure[wrong_sigma_v_in_reference] PASSED [100%]

=================================== PASSES ====================================
____________________ test_stage06_numerical_reference[V1] _____________________
---------------------------- Captured stdout call -----------------------------

V1_kalman_vs_cholesky: {'n_comparisons': 3240, 'worst_err_over_tol': np.float64(0.004960014112287394)}
____________________ test_stage06_numerical_reference[V2] _____________________
---------------------------- Captured stdout call -----------------------------

V2_target_noise_variance: {'worst_err_over_tol': 0.06666373245352426}
____________________ test_stage06_numerical_reference[V3] _____________________
---------------------------- Captured stdout call -----------------------------

V3_zero_noise_matches_stage05_path: {'n_comparisons': 720, 'worst_err_over_tol': np.float64(0.00013177886308022934)}
____________________ test_stage06_numerical_reference[V5] _____________________
---------------------------- Captured stdout call -----------------------------

V5_continuity_sigma_v_to_zero: {'fixed_data': {'errors': [0.007526136945011697, 7.60160593960002e-05, 7.602366385306425e-07, 7.602373397475048e-09], 'slope': 1.9986825316093662}, 'consistent_data': {'errors': [0.1355134197173422, 0.014106224955336977, 0.001415469647638723, 0.00014159489152287819], 'slope': 0.994131440381647}}
____________________ test_stage06_numerical_reference[V6] _____________________
---------------------------- Captured stdout call -----------------------------

V6_quadrature_convergence: {'worst_gain_err': 4.440892098500626e-15, 'worst_case': 'boundary: q=0 n=40 r=4 a=0.998', 'budget': 0.0002}
____________________ test_stage06_numerical_reference[V7] _____________________
---------------------------- Captured stdout call -----------------------------

V7_independent_integration_oracle: {'n_comparisons': 160, 'worst_err_over_tol': 1.6071426307984127e-06}
____________________ test_stage06_numerical_reference[V8] _____________________
---------------------------- Captured stdout call -----------------------------

V8_monte_carlo_noisy: {'z_crit': 3.9878789366069176, 'max_abs_z': 2.939776887364797}
____________________ test_stage06_numerical_reference[V13] ____________________
---------------------------- Captured stdout call -----------------------------

V13_batch_equals_per_context: {'max_abs_diff': 7.993605777301127e-15}
____________________ test_stage06_numerical_reference[V15] ____________________
---------------------------- Captured stdout call -----------------------------

V15_analytic_special_cases: {'narrow_prior_max_err': 2.710386848292501e-08, 'high_noise_errors': [0.00019643153737147756, 4.468158476633732e-05, 2.574127742960286e-06], 'riccati_rel_err': 5.893577711639953e-16, 'chain_rule_rel_err': 6.538920506292747e-14}
____________________ test_stage06_numerical_reference[V16] ____________________
---------------------------- Captured stdout call -----------------------------

V16_failure_surfacing: {'nan_context_rejected': True, 'inf_observation_raises': True, 'support_not_on_cut_points_raises': True, 'nan_target_raises': True, 'singular_model_rejected': True}
____________________ test_stage06_numerical_reference[V17] ____________________
---------------------------- Captured stdout call -----------------------------

V17_noise_naive_definitions: {'flat_prior_mean_matches_definition': True}
_____________________ test_stage06_parity_null_and_access _____________________
---------------------------- Captured stdout call -----------------------------

V11_parity_null: {'n_comparisons': 936}

V12_information_access: {'indexing': True, 'harness_guard_ok': True, 'targets_at_n_plus_h': True, 'latent_invariance': True, 'future_invariance': True, 'interface': True}

V14_seed_isolation: {'stage06_seeds': 24, 'collisions_with_repo_literals': []}
_________ test_stage06_tier1_regression_against_stored_stage05_items __________
---------------------------- Captured stdout call -----------------------------

V4_tier1_regression_stage05: {'items_compared': 243216, 'max_abs_diff': 9.325873406851315e-15, 'tolerance': 1e-09}
______________ test_stage06_calibration_of_population_reference _______________
---------------------------- Captured stdout call -----------------------------

V9_noisy_calibration: n_tests=243 min_p=1.18e-04 level=4.1e-06
__________________ test_stage06_bayes_optimality_counts_only __________________
---------------------------- Captured stdout call -----------------------------

V10_noisy_optimality: {'n_comparisons': 198, 'n_violations': 0, 'z_crit': 4.414999762884038}
_ test_stage06_mutation_detected_by_clean_failure[latent_state_passed_to_predictor] _
---------------------------- Captured stdout call -----------------------------

latent_state_passed_to_predictor: V12=FAIL
_ test_stage06_mutation_detected_by_clean_failure[noise_naive_mislabeled_as_noise_aware] _
---------------------------- Captured stdout call -----------------------------

noise_naive_mislabeled_as_noise_aware: V7=FAIL, V11=FAIL
_ test_stage06_mutation_detected_by_clean_failure[off_by_one_context_length] __
---------------------------- Captured stdout call -----------------------------

off_by_one_context_length: V12=FAIL
__ test_stage06_mutation_detected_by_clean_failure[off_by_one_target_index] ___
---------------------------- Captured stdout call -----------------------------

off_by_one_target_index: V12=FAIL
_ test_stage06_mutation_detected_by_clean_failure[omit_target_noise_variance] _
---------------------------- Captured stdout call -----------------------------

omit_target_noise_variance: V2=FAIL, V7=FAIL
_ test_stage06_mutation_detected_by_clean_failure[prior_mismatch_in_reference] _
---------------------------- Captured stdout call -----------------------------

prior_mismatch_in_reference: V7=FAIL, V11=FAIL
_ test_stage06_mutation_detected_by_clean_failure[wrong_sigma_v_in_reference] _
---------------------------- Captured stdout call -----------------------------

wrong_sigma_v_in_reference: V7=FAIL, V11=FAIL
============================= slowest 8 durations =============================
10084.00s call     tests/test_stage06_reference.py::test_stage06_calibration_of_population_reference
4952.68s call     tests/test_stage06_reference.py::test_stage06_bayes_optimality_counts_only
114.65s call     tests/test_stage06_reference.py::test_stage06_tier1_regression_against_stored_stage05_items
30.84s call     tests/test_stage06_mutations.py::test_stage06_detectors_pass_without_mutation
18.29s call     tests/test_stage06_mutations.py::test_stage06_mutation_detected_by_clean_failure[prior_mismatch_in_reference]
16.88s call     tests/test_stage06_mutations.py::test_stage06_mutation_detected_by_clean_failure[noise_naive_mislabeled_as_noise_aware]
13.76s call     tests/test_stage06_reference.py::test_stage06_numerical_reference[V13]
12.72s call     tests/test_stage06_mutations.py::test_stage06_mutation_detected_by_clean_failure[wrong_sigma_v_in_reference]
===========================
====================== 23 passed in 15279.55s (4:14:39) =======================
```

**Full pre-existing suite** (Stage 0 + 0.5; `pytest -q --ignore` the two Stage 0.6 files):

```
============================= slowest 5 durations =============================
15046.61s call     tests/test_f_optimality.py::test_f_matched_reference_is_optimal_under_its_own_condition
65.00s call     tests/test_g_mutations.py::test_g_mutation_is_detected[unmatched_reference_guard_bypassed]
62.98s call     tests/test_e_calibration.py::test_e_matched_reference_sbc_pit_and_coverage
62.52s call     tests/test_g_mutations.py::test_g_detector_variants_pass_without_mutation
16.07s call     tests/test_a_algebra.py::test_a5_nig_matches_2d_numerical_integration
101 passed in 15328.29s (4:15:28)
exit=0
101 passed in 15328.29s (4:15:28)
```

**Wall-time anomaly (disclosure entry 9):** both concurrent runs show a single test absorbing about 15,000 s (Stage 0.6
calibration + optimality: 10,084 + 4,953 s; Stage 0 F: 15,047 s). Without that pause, the runs took about 4.7 and 5.5 min, as
expected. Windows logged a system-time-change event at 18:27:44 IST, which is typical on resume from sleep. The most likely cause is
system sleep or suspension (UNVERIFIED). No test result depends on wall time. The fast checks were also run individually
earlier (V1-V17 timings 0.1-87 s each).

---

# Phase C addendum (final validation on the files to be frozen)

Order followed: finalize code -> `scripts/stage06_freeze.py record-tested` (86 files, `docs/STAGE06_TESTED_FILES.json`) ->
full validation -> `verify-tested` (**86 files unchanged since the record**, VERIFIED by execution) -> this report -> manifest.
The tested file hashes are in `STAGE06_TESTED_FILES.json`; the freeze command refuses unless the manifest hashes equal them.

## 8. New and extended checks (all VERIFIED by execution, final run)

| ID | Check | Result | Key diagnostic |
|---|---|---|---|
| V18 | Far-tail log density at +/-6, 10, 15 sd vs a log-shifted high-precision oracle; narrow-prior analytic reference at up to 40 sd | PASS | 108 comparisons; max abs error vs oracle 1.7e-13 (tolerance 1e-6); analytic sub-check 0.0017 x tolerance |
| V19 | Design audit: same a, x_0 draw, process noise and observation noise across all q and r; reference matched; items independent of the item count | PASS | all six sub-checks True |
| V20 | L-estimand and the 36-contrast table vs explicit loops; frozen contrast order; missing-cell handling | PASS | max abs error 0.0 |
| V21 | Cluster bootstrap: shared indices across contrasts, system-level SE, critical value vs Sidak / identical columns, simultaneous coverage, failure surfacing | PASS | shared-index error 9e-16; SE relative error 5e-16; bootstrap SD / SE 0.98-1.01; c = 3.209 vs Sidak 3.190; identical columns 1.935 vs 1.960; coverage 0.923 (300 datasets, inside the 3.29 SE tolerance); every failure mode raises |
| V22 | Decision rule truth table (14 hand-derived cases) and flag definitions | PASS | every verdict as derived; G+ without I+ is not SUPPORTED |
| V23 | Tier-2 criterion | PASS | z_crit 3.3415; max combined SE 0.004781; PASS / PASS / FAIL / UNINFORMATIVE as constructed |
| V24 | Runner refusals on temporary copies (22 cases, accepts and refusals) | PASS | all as expected |
| V4 | Tier-1 (full, 3378 items x 2 replicates) | PASS | 243,216 items; max abs diff 9.3e-15 |
| V9 | Calibration (full) | PASS | 243 tests; min p 1.18e-4 (level 4.1e-6) |
| V10 | Optimality (counts only) | PASS | 0 / 198 violations |

V9 diagnostic (`STAGE06_CALIBRATION_DIAGNOSTIC.md`, pre-specified protocol): the rerun reproduces V9 exactly. Observed p-values
below 1e-3 / 1e-2 / 0.05: 3 / 12 / 25, against 0.24 / 2.4 / 12.2 expected for independent tests. The worst test (SBC,
q = 0.755, r = 1, n = 2, p = 1.2e-4) did **not** replicate on fresh seed 61020 with 5000 items (p = 0.87). 20 of the 27 SBC tests
have p <= 0.05, and all V9 cells share the same held-out a-values. That shared sample is itself mildly non-uniform under the
prior (chi-square p = 0.011, KS p = 0.005; fresh sample KS p = 0.77). So the cluster is one chance event in the shared sample,
not a predictor defect. The KL-bound on the available log-score change from recalibration is 0 (bias-corrected). UNVERIFIED:
that is a statistical interpretation, not a proof; V1, V4 and V7 remain the independent correctness evidence.

Coverage study of the frozen band (scratch script, synthetic; disclosure entry 15): simultaneous coverage 0.952 (N = 300, B = 1000),
0.951 (B = 4000), 0.965 (N = 4000, B = 2000, 600 datasets; same with t5 tails).

## 9. Full mutation matrix (VERIFIED; on a copy; `STAGE06_MUTATION_MATRIX.md/.json`)

* 28 mutations (7 reference/harness, 21 analysis/decision/Tier-2/runner), each an in-memory patch inside a subprocess that imports
  a copy of the 86 files. **Unmutated baseline: all nine detectors pass.**
* **28/28 killed by a clean FAIL of the primary intended detector** (an exception would not count); survivors: none.
* Workspace hashes unchanged after the run: True; copy unchanged: True.
* History (disclosure entry 16): a trial run killed 26/28. `bootstrap_failures_dropped` crashed (code hardened: a degenerate critical
  value raises) and `go_ignores_increment` survived (test gap: V22 gained a G+-without-I+ case). Neither fix weakened a test.

## 10. Test runs (verbatim summary lines, final code)

```
Stage 0.6 suite (tests/test_stage06_reference.py, test_stage06_mutations.py, test_stage06_analysis.py; Python 3.13.5, pytest 9.0.2, win32):
======================= 53 passed in 745.21s (0:12:25) ========================
Pre-existing Stage 0 / 0.5 suite:
101 passed in 538.35s (0:08:58)
```

The two suites ran concurrently on one machine (so each took longer than alone). The new tests include the end-to-end runner test in
test mode (partial run, resume, analysis outputs, corrupted-checkpoint refusal).

## 11. Remaining uncertainties after Phase C

1. **Planning assumptions.** The noise inflation of the spread (kappa) and the correlation across noise levels (rho_q) cannot be
   estimated from Stage 0.5. Half-widths were computed for kappa in {1, 2}. If noise inflates the spread more than that, the
   half-widths grow in proportion, and STOP becomes harder to reach (REVISE would result).
2. **STOP at sub-threshold gains** is unlikely under the noise-inflated planning spread (2-3 of 100 at gains delta/2, kappa 2).
3. **Environment.** Qualification (V4, V6, V11, V13) is required if the execution environment differs from the frozen environment
   manifest. A different BLAS may change results at rounding level only (UNVERIFIED on Colab until qualification is run there).
4. **Runtime on Colab** is estimated from local timing, not measured there.
5. No version control (user decision): SHA-256 manifest plus a read-only snapshot, printed manifest hash stored outside the workspace.
