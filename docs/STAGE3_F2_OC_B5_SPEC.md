# F2 Q2 operating characteristics on the extended F2 library map (specification)

Status: spec, 2026-11-02, committed BEFORE the seed role below is used. CPU only, synthetic models (no network, no GPU).
Follows `docs/STAGE3_F2_DESIGN_CPU_SPEC.md` section B, whose last bullet foresaw this re-run once batch 5 extended the F2
library map. User request of 2026-11-02 (disclosure S48).

**Seen before this spec:** batch 6's lookup on the batch 2-3 cells (Q2 s* = 0.01 / 0.01 / 0.02 at M = 32 / 64 / 128; every
shortfall an INCONCLUSIVE for a LIB-LIKE truth in the cell r = 1, n = 10, K = 16, where the library and context-only
references differ by only 0.045 nats; S48) and batch 5's F2 library and split results (S46).

## Design
* Simulation model, grid, rules and lookup exactly as section B of the earlier spec (F1 Q2 functions `q2_replicate`,
  `q2_classify` and the frozen `lookup` rule, all unchanged; Bonferroni-t critical value, family size 480 ASSUMED; two
  replicates must agree; pi in {0, 1}, e in {0, 0.01}, s in {0.01, 0.02, 0.05, 0.1}, M in {16, 32, 64, 128}; 300 studies).
* Cells (held-out, r = 1) from batch 5 (`results-stage2-cpu-batch5` @ `e08eee8`, read with `git show`, sha256 recorded):
  n in {20, 40, 80} x K in {16, 64, 256, 1024} (12 cells): s_lp = the library-vs-population mean gap over draws
  (`f2_library.csv`, mean_estimate), s_ps = the total population-vs-context-only gap (`split.csv`, part T),
  s_ls = |s_ps - s_lp| (paired identity on the same items).
* Output: `results_stage2/f2_oc_b5/` (oc_q2_f2.csv, f2_power_lookup.json with per-cell lookups as well as the pooled one,
  provenance). The batch 6 result (`results_stage2/f2_oc/`) is kept unchanged; both are reported.
* Seed role `f2_oc_b5` (83402), never used before this commit; smoke on `f2_tests`.
* Expected time: under a minute at 16 workers (batch 6 ran 256 settings in 15 s); a box relay because the user asked for one.
