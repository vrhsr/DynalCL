# F3 short-context separability map: specification (committed BEFORE the map is run)

Status: DRAFT spec, 2026-10-28. Task C of the standing instruction of 2026-10-27: map, from the FROZEN Stage 0.6 Kalman
references only (no new reference mathematics, CPU, no model), where population-aware Bayes is separable from the
noise-aware stability-only (context-only) reference at SHORT contexts, and where a finite library is separable from
continuous-prior Bayes. Reference-only: it guides design and is not a confirmatory result. The Stage 0.6 confirmatory
verdict (STOP at long contexts n = 10..40; docs/STAGE06_RESULTS.md) stands and is not re-analysed here; this map uses new
systems from a new seed role and different context lengths.

## 1. Family and references (all frozen Stage 0.6 code, used read-only)
* F3 = latent AR(1) x_t = a x_{t-1} + w_t, w_t ~ N(0, 1), observed as y_t = x_t + v_t, v_t ~ N(0, q) (sigma_w = 1;
  `dynaicl.systems.noisy.NoisyObservationModel`), x_0 ~ N(0, r^2) independent of a; the likelihood is the Kalman likelihood
  conditional on the x_0 prior, exactly as Stage 0.6 (docs/MATH_STAGE06.md).
* pop = `noisy_population_reference` with the Stage 0.6 population prior P-STABLE (a ~ TN(0.4, 0.3^2) on (-0.95, 0.95));
  stab = `noise_aware_stability_predictor` (a ~ U(-0.999, 0.999)), the Stage 0.6 LOCKED comparator. Both share the Kalman
  code, the node set and the noise model and differ only in the prior (Stage 0.6 information parity).
* lib_K: uniform weights over K atoms a_k drawn from pop; posterior weights from the frozen `kalman_filter_on_nodes` evaluated
  at the atom values (the atoms play the role of nodes, with uniform prior mass), predictive mixture from the frozen
  `observation_predictive_moments` and `mixture_logpdf_cdf`. This is the library posterior given the atoms, analytically exact
  in float64 (a composition of frozen functions; TESTED against a direct per-atom Kalman evaluation before the run).
* Grid: q in {0 (control), 0.755, 2.56, 6.5} (the Stage 0.6 noise levels); r in {0.25, 1, 4}; h in {1, 5};
  n in {2, 3, 4, 5, 6, 7, 8, 9}. K in {2, 4, 16, 64}, 16 library draws per K (atoms nested across K within a draw).

## 2. Sets, sizes, seeds
* HELD: systems from pop (truth = pop). INLIB: systems are the atoms of the draw (truth = lib_K).
* Seed role `f3_map` (root 80701, config/stage2_seed_manifest.yaml; never used before). HELD systems, observation noise and
  x_0 through the frozen `generate_noisy_split` with `NamedStreams(80701)`; library atoms from stream `f3_map_library/draw{d}`;
  INLIB systems from `SeedSequence(80701, spawn_key=(sha256("f3_map_inlib"), d, K))`.
* HELD: N = 20 000 contexts per (q, r); every n and h is cut from the same trajectories (contexts only through the frozen
  `make_noisy_context`). INLIB: N = 10 000 per (q, r, K, draw). Sizes chosen so that the SE of a 0.02-nat gap is about
  0.3 / sqrt(N) <= 0.003 (Stage 0.5 item sd of score differences about 0.3; ASSUMED similar here, measured and reported).

## 3. Estimands and estimator
* Truth-matched gaps, E[LS(truth) - LS(other)] (= expected KL >= 0, DERIVED): HELD (pop, stab) [Q1-type]; HELD (lib, pop);
  INLIB (lib, pop); INLIB (lib, stab) [Q2-type].
* Estimator: paired realized log-score differences on the same contexts and targets (common random numbers); SE from the
  item sd. (No Rao-Blackwell KL here: the observation predictives are Gaussian mixtures over the node set, and realized
  targets with N >= 10 000 already give SE about 0.003.)

## 4. Decision rules (fixed here, as the Stage 1A map, docs/STAGE1_SEPARABILITY_MAP_SPEC.md section 4)
* Bound = estimate +/- 3.0 x SE per cell (two-sided per-cell level about 0.0027; the map guides design, so no global
  Bonferroni; the expected number of wrongly marked cells is reported).
* Q1-type cell (q, r, h, n): IDENTIFIABLE if the lower bound >= delta = 0.02; UNIDENTIFIABLE if the upper bound < delta;
  otherwise BORDERLINE.
* Q2-type cell (set, q, r, h, n, K, pair): per draw a bound as above; IDENTIFIABLE if >= 90% of the 16 draws have a lower bound
  >= delta; UNIDENTIFIABLE if >= 90% have an upper bound < delta; otherwise PARTIAL.
* Validity checks (any failure: the map is INVALID and is not used):
  (i) node doubling of pop and stab (frozen settings `refined(2)`) on 200 HELD contexts per (q, n): max change <= 1e-6 nats;
  (ii) the q = 0 control column of HELD (pop, stab) at h = 1, r = 1, n in {2, 3, 5} agrees with the known-sigma Stage 1A map
  cells of the same estimand (results-stage1-map-1A) within |z| <= 4 (different systems: a statistical agreement check);
  (iii) the library predictor equals a direct per-atom Kalman evaluation to 1e-10 on 50 contexts;
  (iv) disjointness: INLIB systems are library atoms, HELD systems are not; no shared noise streams between sets.
* Summary reported per (q, h): the largest n at which HELD (pop, stab) is IDENTIFIABLE, and the (K, n) cells where library vs
  continuous is IDENTIFIABLE. An honest negative (no cell separates) is a valid outcome and will be reported as such.

## 5. Compute and execution
Timing on a smoke seed (role f3_map is NOT used for timing) decides local vs box; anything over about 10 minutes runs on the
box CPU with at most 16 workers, through a relay prompt, results as small files on a `results-stage2-f3-map` branch.
Code: `dynaicl_families/stage2/f3_map.py`, runner `scripts/stage2_f3_map.py` (to be written after this spec is committed).
