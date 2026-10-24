# Stage 1 mutation matrix

Overall: PASS

| mutation | exit | detected by | assertion failures | summary |
|---|---|---|---|---|
| baseline | 0 | - | 0 | 16 passed in 7.16s |
| wrong_prior_cont | 1 | test_cont_arm_draws_the_population_prior | 2 | 1 failed, 15 passed in 6.60s |
| unpaired_seeds | 1 | test_common_random_numbers_across_arms | 1 | 1 failed, 15 passed in 6.74s |
| library_not_nested | 1 | test_library_atoms_nested_and_used | 1 | 1 failed, 15 passed in 6.71s |
| missing_causal_mask | 1 | test_causality_cut_context_equals_full_sequence[S], test_causality_cut_context_equals_full_sequence[DW-deep] | 4 | 2 failed, 14 passed in 8.37s |
| target_in_input | 1 | test_causality_cut_context_equals_full_sequence[S], test_causality_cut_context_equals_full_sequence[GRU], test_causality_cut_context_equals_full_sequence[SSM], test_causality_cut_context_equals_full_sequence[DW-deep] | 8 | 4 failed, 12 passed in 6.68s |
| off_by_one_position | 1 | test_causality_cut_context_equals_full_sequence[S], test_causality_cut_context_equals_full_sequence[GRU], test_causality_cut_context_equals_full_sequence[SSM], test_causality_cut_context_equals_full_sequence[DW-deep] | 8 | 4 failed, 12 passed in 6.72s |
| wrong_reference | 1 | test_q1_statistics_use_the_population_reference | 1 | 1 failed, 15 passed in 6.45s |
