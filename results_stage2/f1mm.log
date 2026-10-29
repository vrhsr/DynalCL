# F1-V9 mutation matrix

Overall: PASS (baseline passes)

| mutation | frozen F1 tests failing | extra detectors failing | crashes | pytest summary |
|---|---|---|---|---|
| baseline | - | - | - | 19 passed in 415.06s (0:06:55) |
| wrong_prior | test_v5_calibration_pit_of_population_reference | calibration_n20_r0.25, calibration_n2_r1.0, calibration_n5_r4.0, matched_guard, optimality_n10_r1.0, optimality_n2_r1.0 | - | 1 failed, 18 passed in 405.83s (0:06:45) |
| off_by_one_likelihood | test_v3_grid_oracle[20-0.25-pop], test_v3_grid_oracle[20-0.25-ctx], test_v8_library_matches_brute_force | known_sigma_limit | test_v3_grid_oracle[2-1.0-pop] (A), test_v3_grid_oracle[2-1.0-ctx] (A), test_v3_grid_oracle[3-4.0-pop] (A), test_v3_grid_oracle[3-4.0-ctx] (A), test_v7_known_sigma_limit (Assert) | 8 failed, 11 passed in 415.18s (0:06:55) |
| leaked_target | test_v5_calibration_pit_of_population_reference | calibration_n20_r0.25, calibration_n2_r1.0, calibration_n5_r4.0, leakage, optimality_n2_r1.0 | - | 1 failed, 18 passed in 405.41s (0:06:45) |
| unmatched_reference | - | calibration_n20_r0.25, calibration_n2_r1.0, calibration_n5_r4.0, matched_guard, optimality_n10_r1.0, optimality_n2_r1.0 | - | 19 passed in 406.03s (0:06:46) |
| wrong_truncation | - | matched_guard | - | 19 passed in 408.14s (0:06:48) |
| wrong_sigma_integration | test_v1_sigma_marginal_closed_form_matches_quad[scale0], test_v2_inverse_gamma_predictive_given_a_is_student_t, test_v3_grid_oracle[20-0.25-pop], test_v4_node_doubling_and_normalisation[pop], test_v6_population_reference_is_optimal_on_population_systems, test_v5_calibration_pit_of_population_reference | known_sigma_limit, optimality_n10_r1.0, optimality_n2_r1.0 | test_v3_grid_oracle[2-1.0-pop] (A), test_v3_grid_oracle[3-4.0-pop] (A), test_v7_known_sigma_limit (Assert) | 9 failed, 10 passed in 387.05s (0:06:27) |
