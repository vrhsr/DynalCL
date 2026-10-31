# Sensitivity analyses requested by internal review 1: specification (committed BEFORE the runs)

Status: spec, 2026-10-31. Reference-only CPU analyses answering the review's open items M5/M6 (precision of the noisy map),
M7 (comparator dependence) and M9 (prior dependence) (`paper/REVIEW_RESPONSE_1.md` on `paper-draft`). Code
`dynaicl_families/stage2/sensitivity.py`, runner `scripts/stage2_sensitivity.py`. They do not change any earlier map; they
report how the earlier windows move.

## 1. Common design
Held-out systems only (truth = the population reference of the study), h = 1, r in {0.25, 1, 4}, delta = 0.02. Paired
realised log-score differences on the same contexts and targets (common random numbers); gap = E[LS(pop) - LS(other)]
(an expected KL, since pop is the truth). Cell rule as the maps: IDENTIFIABLE if estimate - 3 SE >= delta, UNIDENTIFIABLE if
estimate + 3 SE < delta, else BORDERLINE. Contexts through the frozen `make_context`; systems through the frozen
`generate_split` / `generate_noisy_split`.

## 2. Comparator frontier (review M7)
* Known noise scale (data from the Stage 1A population, TN(0.4, 0.3^2; +/-0.95), sigma = 1): context-only comparators
  (a) uniform on (-0.999, 0.999) with sigma known (the locked comparator); (b) uniform on (-0.95, 0.95) with sigma known (knows
  the population's support); (c) uniform on (-0.9999, 0.9999) with sigma known; (d) sigma-agnostic: the F1 context-only
  reference (a uniform on (-0.999, 0.999), log sigma uniform on [log 0.01, log 100]); (e) the frozen OLS Student-t plug-in
  (`OlsPlugInPredictor("student_t", min_transitions=2)`, non-Bayesian). n in {2, 3, 5, 10, 20}; N = 20 000 per (r, n).
* Unknown noise scale (data from P_F1): context-only comparators with a uniform on (-0.999, 0.999) and log-uniform noise
  priors over [0.1, 10], [0.01, 100] (the map's), [0.001, 1000]; and the OLS Student-t plug-in. Same n, r, N.

## 3. Prior dependence (review M9)
* Known noise scale: population TN(0.4, tau^2; +/-0.95) for tau in {0.15, 0.3, 0.6}, data drawn from the same prior (each pop is
  matched to its data), comparator (a).
* Unknown noise scale: tau in {0.15, 0.3, 0.6} with sigma^2 ~ IG(3, 2), and the noise-prior concentration alpha0 in {2, 3, 10}
  with IG(alpha0, alpha0 - 1) (mean 1) at tau = 0.3; comparator: the F1 map's context-only reference.
* Same n, r, N.

## 4. Noisy observations at higher precision (review M5/M6)
F3 pop vs stab (frozen Stage 0.6 references), q in {0, 0.755, 2.56, 6.5}, r in {0.25, 1, 4}, h in {1, 5}, n = 2..9, with
N = 200 000 per (q, r) (ten times the map's 20 000; SE about 1/sqrt(10) of the map's), scored in chunks of 10 000 (memory).

## 5. Seeds and outputs
New seed roles in `config/stage2_seed_manifest.yaml`: `sensitivity` (81501) for sections 2-3 and `f3_precision` (81601) for
section 4, never used before this spec's commit; smoke runs use `f3_tests`. Outputs: one CSV of cells (analysis, family,
variant, r, n, h, estimate, se, decision), a report, provenance; small files on a results branch. Box CPU, at most 16 workers.

## 6. Not done here (still open)
Per-draw library distributions are tabulated from the existing map files (no new runs); a sequence-level test is not attempted.
