# Batch 5: splitting the population gap, longer contexts, larger libraries, cumulative gaps (specification)

Status: spec, 2026-11-01, committed BEFORE any seed of the roles below is used. Reference-only CPU analyses (no network, no
GPU). Decision of the user at checkpoint 1 of the paper audit (disclosure S40). Batch 4 (`docs/STAGE2_SENSITIVITY_SPEC.md`)
is separate and unchanged. Code `dynaicl_families/stage2/batch5.py`, runner `scripts/stage2_batch5.py`.

**Seen before this spec (S40).** Prior KL budgets (1A 0.582, F1 2.570 nats, F2 about 17.4 by a reviewer's Monte Carlo); large-n
nearest-atom limits of the held-out library gap; a reviewer's scratch F1 computation with the context-only reference given the
population noise prior (0.037 / 0.032 / 0.027 / 0.015 nats at n = 2 / 3 / 5 / 10, r = 1, against the map's 0.29 / 0.17 / 0.09 /
0.04); the F1 per-draw library share rising with n. These are why the analyses below were chosen; no scratch number is used as
a result.

**Purpose and framing.** (A, B) split the held-out population-vs-context-only gap into a part due to knowing the population's
noise level and a part due to knowing its dynamics; this does not replace the earlier maps, it decomposes their gaps.
(B, C) map library separability at longer contexts and larger libraries. (D) estimate the cumulative (sequence-level) gap
directly, the quantity bounded by the prior KL. (E) compute the closed-form and Monte Carlo theory quantities (prior KL budgets,
nearest-atom limits) as pinned files for the paper.

**Terminology.** A cell is SEPARABLE if estimate - 3 SE >= delta, NOT SEPARABLE if estimate + 3 SE < delta, BORDERLINE
otherwise (identical to the IDENTIFIABLE / UNIDENTIFIABLE / BORDERLINE rule of the earlier maps); delta = 0.02 nats; library
cells: per draw, then SEPARABLE / NOT SEPARABLE if >= 90% of draws agree, else PARTIAL (as the maps). Decisions are made only
for truth-matched pairs (the truth is the population reference on held-out systems); other differences are reported as
estimates with SE, without a decision.

## A. F1 (unknown noise scale): split of the gap
* Held-out systems from P_F1 (MATH_F1 section 1), r in {0.25, 1, 4}, N = 20 000 per r; every n is cut from the same
  trajectories with the frozen `harness.make_context`; realised targets, h = 1.
* n in {2, 3, 5, 10, 12, 14, 16, 18, 20, 25, 30, 40} (the map's grid plus points where its window closes).
* References (all `UnknownScaleReference`, frozen F1 code): pop = P_F1; ctx = C_F1 (the map's: a ~ U(+/-0.999), log sigma ~
  U(log 0.01, log 100)); ctx_nm = a ~ U(+/-0.999), sigma^2 ~ IG(3, 2) (knows the population noise prior, not its dynamics);
  ctx_dm = a ~ TN(0.4, 0.3^2; +/-0.95), log sigma ~ U(log 0.01, log 100) (knows the population dynamics prior, not its noise
  level).
* Estimands (paired, same items): total T = E[LS(pop) - LS(ctx)]. Path 1: dynamics part D1 = E[LS(pop) - LS(ctx_nm)], noise
  part N1 = E[LS(ctx_nm) - LS(ctx)]. Path 2: noise part N2 = E[LS(pop) - LS(ctx_dm)], dynamics part D2 = E[LS(ctx_dm) -
  LS(ctx)]. T = D1 + N1 = N2 + D2 exactly (item by item). The two paths can differ (interaction); the symmetric split
  D = (D1 + D2) / 2, N = (N1 + N2) / 2 is reported with its item-level SE. Decisions for pop vs ctx, pop vs ctx_nm, pop vs ctx_dm.

## B. F2 (bivariate VAR(1)): split, longer contexts, larger libraries
* Held-out systems from P_F2 (MATH_F2 section 2), r in {0.25, 1, 4}, N = 4000 per r, n in {2, 3, 5, 10, 20, 40, 80}, contexts
  by the frozen `make_context` coordinate by coordinate (as the F2 map), h = 1.
* References: pop = P_F2; ctx = C_F2 (the map's); ctx_nm = MNIW(B0 = 0, V0 = 100 I, nu0 = 7, Psi0 = 4 I, c = 0.999) (the
  population's noise prior, vague coefficients); ctx_dm = MNIW(B0 = 0.4 I, V0 = 0.09 I, nu0 = 1.5, Psi0 = 0.01 I, c = 0.95)
  (the population's coefficient prior and truncation, vague noise). Limitation stated in advance: in a conjugate MNIW prior the
  coefficient prior scales with Sigma, so ctx_dm's coefficient prior is not the population's marginal coefficient prior; the
  split is exact arithmetic but its "dynamics" and "noise" labels are approximate in F2.
* Context-only variants are scored at n in {10, 20, 40, 80} only (at n <= 5 the context-only Monte Carlo is capped for many
  items; the map's n = 5 result stands as MC-LIMITED). Monte Carlo estimator, per-item SE target 0.01, cap 2^22 draws, and the
  MC-LIMITED rule exactly as the F2 map (`f2_map.truncated_scores`, `gap`, `classify`, unchanged).
* Libraries: K in {2, 16, 64, 256, 1024}, 8 draws (atoms nested across K within a draw, drawn exactly from P_F2), lib vs pop at
  every n; evaluated in chunks of items (memory). Library atoms come from new streams (`b5_f2_library/draw{d}`).
* Estimands: as A for the split (T, D1, N1, N2, D2, D, N), with Monte Carlo SE included as in the F2 map; library gaps per draw.

## C. F1 libraries at long contexts
* Held-out systems from P_F1, r in {0.25, 1, 4}, N = 20 000 per r, n in {20, 40, 80, 160}, K in {4, 8, 16, 32, 64}, 32 draws
  (64 atoms per draw from P_F1, nested; streams `b5_f1_library/draw{d}`), exact `ScaleLibrary` predictive; lib vs pop per draw;
  cell rule as the maps.

## D. Cumulative gaps (sequence level)
* For held-out systems, sum over context lengths of the per-step paired log-score differences, item by item; its mean estimates
  KL(m_pop(x_{1:N} | x_0) || m_other(x_{1:N} | x_0)), bounded by KL(prior_pop || prior_other) (chain rule; data processing).
  Item-level SE of the sum (exact for the cumulative statistic).
* 1A (known sigma, frozen batch references): pop vs stab (U(+/-0.999)), r in {0.25, 1, 4}, N = 40 000 per r, every n = 1..160;
  plus the n = 0 term (prediction of x_1 from x_0 alone) by composite Gauss-Legendre over a (64 panels x 16 nodes; node doubling
  reported). Per-n rows for every n (a dense 1A curve) and cumulative rows.
* F1: pop vs ctx and pop vs ctx_nm, r in {0.25, 1, 4}, N = 20 000 per r, n = 2..160 (n = 0, 1 excluded: MATH_F1 section 3);
  cumulative from n = 2.
* F3 (frozen Stage 0.6 Kalman references): pop vs stab, q in {0, 0.755, 2.56, 6.5}, r in {0.25, 1, 4}, N = 20 000 per (q, r),
  n = 2..40, h = 1, scored in chunks; cumulative from n = 2.

## E. Theory quantities (run locally; seconds to minutes)
* Prior KL budgets: 1A KL(TN(0.4, 0.3^2; +/-0.95) || U(+/-b)) for b in {0.95, 0.999, 0.9999} by adaptive quadrature; F1 sigma
  part for log-uniform ranges [0.1, 10], [0.01, 100], [0.001, 1000] and the noise-matched case (0); F2 KL(P_F2 || Q) for Q in
  {C_F2, ctx_nm, ctx_dm} by Monte Carlo (draws from the truncated P_F2; truncation normalisers by acceptance fractions;
  2 x 10^5 draws; SE reported).
* Large-n nearest-atom limits of the held-out library gap: E[min_k KL_stationary(theta || theta_k)] for known sigma (K in {1,
  2, 4, 8, 16, 32, 64, 256}), unknown sigma (same K) and F2 (K in {2, 16, 64, 256, 1024}); Monte Carlo over systems and library
  draws with SE.
* These are DERIVED quantities computed numerically; they make predictions that sections A-D test.

## Seeds, outputs, compute
* New roles in `config/stage2_seed_manifest.yaml`, never used before this commit: `b5_f1_split` 85001 (A and C), `b5_f2` 85101
  (B), `b5_cumulative` 85201 (D), `b5_theory` 85301 (E), `b5_tests` 85901 (smoke and unit tests only, never results). Unit seeds
  are derived from the role seed by `SeedSequence(role, spawn_key=(sha256(unit name)[:4], ...))`.
* Outputs: `results_stage2/batch5/` with `split.csv`, `f2_library.csv`, `f1_library_long.csv`, `cumulative.csv`, `theory.json`
  (E, from the local run), `BATCH5_REPORT.md`, `provenance.json` (source hashes, git head, clean-tree flag), `BATCH5_DONE.json`;
  units under `units/` stay on the box. Box CPU, at most 16 workers; resumable.
* No earlier map, decision or frozen file changes. Any result of this batch enters the paper only through `claims.yaml` /
  `numbers.yaml` pinned to the results commit, after verification and a disclosure entry.
