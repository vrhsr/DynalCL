# F1 separability map: specification (written and committed BEFORE the map is run)

Family F1: scalar AR(1) with unknown noise scale (docs/MATH_F1.md), h = 1. References only; CPU only; no model.
Code: `dynaicl_families/f1_separability.py`, runner and summariser `scripts/stage1_f1_map.py`. References validated by
`tests_stage1/test_f1_references.py` (F1-V1..V8; the F1 mutation matrix F1-V9 is still to do and is not a precondition for
this reference-only map).

## 1. References and sets
* pop_F1: a ~ TN(0.4, 0.3^2; +/-0.95), sigma^2 ~ IG(3, 2), independent. ctx_F1: a ~ U(-0.999, 0.999), log sigma ~ U(log 0.01,
  log 100). lib_K: uniform over K atoms (a_k, sigma_k) drawn from P_F1; atoms of draw d nested across K (first K of 256).
* Sets: HELD (systems from P_F1; truth = pop_F1), INLIB (the library's atoms; truth = lib_K), PROBE ((a, sigma) uniform over
  the grid a in {-0.9, -0.75, ..., 0.9} x sigma in {0.3, 0.5, 1, 2, 3}), OOS-A (|a| ~ U(0.95, 0.999), random sign, sigma^2 from
  IG(3, 2)), OOS-SIGMA (a from P_F1's a-prior, sigma ~ U(2.5, 5); P(sigma > 2.5) = 0.0043 under IG(3, 2)).
* x_0 ~ N(0, r^2) independent of (a, sigma), r in {0.25, 1, 4}; n in {2, 3, 5, 10, 20, 40} (n = 1 excluded, MATH_F1 section 3).
* K in {1, 2, 4, 8, 16, 32, 64, 256}; 32 library draws for K <= 64, 16 for K = 256.

## 2. Sizes and seeds
Root seed from the seed-role table, role `f1_map` (70001-series: **70301**; never used before). Q1: 20 000 systems per set and
r. Q2 per draw: the first 5000 systems of each Q1 set (same systems; pop and ctx scores reused) plus 10 000 fresh in-library
systems (seed derived from (70301, "stage1_f1_inlib", draw, K)).

## 3. Estimator
Realized-target score gaps E_D[LS(A) - LS(B)] per (set, r, n, pair[, K, draw]), mean and SE over systems. Behavioural KL
(used in Stage 1A) is NOT used: the ctx_F1 predictive has polynomial tails (|y|^-(n+1)), so KL from it into a Gaussian
library is infinite at n = 2 (DERIVED). For HELD (pop, ctx) and INLIB pairs the gap equals an expected KL and is >= 0 in
expectation; for the other sets it can have either sign.

## 4. Decision rules (frozen here)
* Bound: estimate +/- 3.0 SE for HELD (pop, ctx) (one-sided meaning: lower bound vs delta); for every other (set, pair) the
  bound is |estimate| +/- 3.0 SE (two-sided separation in either direction). delta = 0.02.
* Q1 cell: IDENTIFIABLE if lower >= delta; UNIDENTIFIABLE if upper < delta; else BORDERLINE.
* Q2 cell (per draw as above): IDENTIFIABLE if >= 90% of draws have lower >= delta; UNIDENTIFIABLE if >= 90% have upper < delta;
  else PARTIAL.
* Validity (else INVALID and unused): node doubling of pop_F1 and ctx_F1 on the first 50 contexts of every Q1 (set, r, n),
  max |difference| <= 1e-6 nats (checked at run time; the run aborts above the limit); KL is not used, so there is no
  Rao-Blackwell check; disjointness assertions between sets pass.
* The map guides the design of a separate F1 neural pre-registration (not written yet). No F1 network is trained before
  that pre-registration is frozen.

## 5. Compute
Laptop timing at one tenth of the sizes (smoke seed): Q1 per r 85 s; Q2 per unit and r about 9-10 s. Full map (ASSUMED
linear): Q1 about 45 CPU-min, Q2 about 240 units x 300 s = 20 CPU-hours: box CPU in tmux, about 1.5 h with 20 workers.
Results pushed: report, decisions, checks, provenance, checksums (rows file and caches stay on the box if > 2 MB).
