# Statistical audit (Phase 5)

Labels: VERIFIED (read or run here; source named), DERIVED (math shown or located), REPORTED, ASSUMED, UNVERIFIED. Scratch
scripts (not in the repo, audit seed 20261031 which is not a project seed role):
`C:\Users\Ramana\AppData\Local\Temp\claude\e--study-buddy-DynaICL\bd3df7a4-8736-46d2-9c91-75fbaf70608c\scratchpad\audit\kl_budget.py`,
`...\audit\table_checks.py`, `...\audit\nearest_atom.py`.

## 1. Design of each map and study

| Study / map | Unit of replication | Items per cell | SE | Dependence | Rule |
|---|---|---|---|---|---|
| Stage 0.5 (pre-reg.) | item (system + context + target), two replicates | 3378 per replicate | paired item sd / sqrt(N) | CRN across predictors and n; replicates independent | mean +/- 2.24 SE per replicate, both replicates agree |
| Stage 0.6 (pre-reg.) | system cluster, two replicates | 4000 per replicate | studentised max-abs-t cluster bootstrap over 36 contrasts (B >= 20000) | handled by the bootstrap | family-wise 0.05 per replicate |
| 1A map, held-out pop vs stab | context (independent systems) | 40 000 | sd of per-context Rao-Blackwellised KL / sqrt(N) | same systems across r? no, per r; same trajectories across n (CRN) | lo = est - 3 SE >= delta |
| 1A map, library | context within one library draw; 32 draws (16 at K = 256) | 20 000 realised (HELD, INLIB), 2000 KL | per draw | atoms nested across K within a draw | >= 90% of draws agree, else PARTIAL |
| F1 map | context | 20 000 per set | per cell (file stores lo/hi, no se column) | CRN | as 1A, two-sided |
| F3 map | context | HELD 20 000 per (q, r), every n and h cut from the same trajectories; INLIB 10 000 | item sd of realised log-score differences | strong CRN across n, h | as 1A; 16 draws |
| F2 map | context | HELD 4000, INLIB 1000; 8 draws | sqrt(SE_items^2 + SE_MC^2) | CRN | as 1A; MC-LIMITED if SE_MC > delta/100 or > 1% items with per-item SE > 0.01 |

Items within a cell are independent draws (system, x_0, innovations from separate streams; VERIFIED by reading
`dynaicl_families/sampling.py` and `f2_map.py`), so the item-level SE is valid for the per-cell mean. Cells are dependent through
common random numbers (stated in the paper).

## 2. Per-cell error rate of the 3-SE rule, and multiplicity

* Per cell, with a correct normal SE, P(mark IDENTIFIABLE | true gap < delta) <= Phi(-3) = 0.00135, the same for UNIDENTIFIABLE
  (DERIVED). The 1A spec promised "the expected number of wrongly marked cells is reported with the map" (VERIFIED,
  `docs/STAGE1_SEPARABILITY_MAP_SPEC.md` section 4); **it was never reported** (pre-registration deviation, to be disclosed).
* Upper bounds on the expected number of wrong marks among the headline cells (VERIFIED by `table_checks.py`): 1A held-out
  pop vs stab 0.032 (24 cells); F1 0.024 (18); F3 0.130 (96); F2 0.012 (9). Only 8 of 72 (1A) and 36 of 192 (F3) cells with an se
  column lie within 6 SE of delta, where a wrong mark is possible at all. **Conclusion:** multiplicity is not a material problem
  for the headline windows; a family-wise version (Bonferroni or Holm over the headline cells) would change at most the
  boundary cells. It should be shown as a sensitivity table (cheap, CPU, from the existing files) and the expected count
  reported, which also closes the spec deviation.
* Library cells: the "9 in 10 draws" rule is a quantile rule over libraries, not an error-controlled test. With 8 draws (F2) it
  means 8 of 8; with 16 (F3) 15 of 16; with 32 (1A/F1) 29 of 32. The per-draw percentages in Table 3 carry binomial uncertainty
  over draws (e.g. F2 K = 64: 97% from 8 draws x 15 cells, draws shared across cells) that is not shown.

## 3. Estimators and their validity

* 1A held-out: per-context Rao-Blackwellised KL (lower variance than realised targets); validity check (i) realised vs RB on every
  truth-matched held-out cell (max |z| 3.82 vs Bonferroni 5.17; REPORTED disclosure S9).
* F3: realised targets only (the observation predictives are mixtures over the node set); SE 3.9x the 1A SE at matched n
  (VERIFIED: median SE 0.00144 vs 0.00037). This is the whole reason F3 is "underpowered" at q = 0.755. Batch 4 (N = 200 000)
  addresses it; its results are not in.
* F2: Monte Carlo log-density with per-item SE; log of an unbiased density estimate is biased downward by about SE^2 / 2
  (DERIVED, MATH_F2 section 5). For the context-only reference this **inflates** pop - ctx. Bounded by 5e-5 per item at the
  0.01 target; items above the target are flagged. Non-finite items are dropped (<= 1% in a classified cell): a small selection
  effect toward easier contexts, direction unknown, at most about 1% of the cell mean (DERIVED, crude).
* F2 MC-LIMITED at n = 5: estimates 1.20-1.28 nats with SE_items about 0.036 and SE_MC up to 0.00096 (VERIFIED, f2 map file).
  The cell-level criterion SE_MC <= delta/100 is not a statistical-validity criterion (SE_MC is 3% of SE_items); the binding
  reason is the share of items with per-item SE > 0.01 (up to 422/4000, REPORTED S38), whose downward log bias could inflate the
  gap. A bias bound (sum of SE_i^2 / 2N over flagged items) would very likely show n = 5 is far above delta, but the pre-specified
  rule says MC-LIMITED and that must stand; a bias-bounded re-statement can be added as a labelled post-hoc sensitivity.
* The MC-LIMITED rule tightens as N falls (stated in the paper, S38).

## 4. Effect sizes and practical meaning; delta

* delta = 0.02 nats per forecast; the Stage 0 pre-registration justifies it as a likelihood ratio of exp(0.02) per step "which
  compounds to about 7x over 100 predictions" (VERIFIED, PREREG_separability.md section 4). That justification is itself a
  **pooled, sequence-level** argument: by the same logic a 0.005-nat per-step gap compounds to 1.6x over 100 predictions and to
  150x over 1000. The per-cell margin is therefore a convention, not a detectability limit; detectability for a trained model is
  set by evaluation size and seed variance (Section 5 of the paper reports the F1 lookup: seed sd <= 0.01 nats at 32 models).
* tab_delta (VERIFIED, generated): the windows move with delta as expected (1A r = 1: n <= 10 / 5 / 2 at delta = 0.01 / 0.02 / 0.04).
  Two caveats: (a) values equal to a grid maximum are right-censored (F3 "9", F2 "20"); (b) coarse grids hide crossings
  (Reviewer 1 interpolates the delta = 0.02 crossing at n about 7 for 1A and 14 for F1 at r = 1, a factor of two, DERIVED by R1).

## 5. Sensitivity to the comparator and the prior

Not yet available (batch 4 not returned). Batch 4 covers 1A and F1 comparator frontiers (including a sigma-agnostic comparator
for 1A and three noise-prior widths for F1) and prior concentration (tau, alpha0). **Not covered:** F2 comparator dependence
(context-only IW(1.5, 0.01 I), V0 = 100 I) and a **noise-matched** context-only reference in F1/F2 (ctx given the true sigma /
Sigma, so that the gap isolates dynamics knowledge). These are the analyses that decide whether the F1/F2 "wider window"
statements survive (section 6.1).

## 6. Two closed-form accounts of the maps (DERIVED; numerically checked)

### 6.1 Population vs context-only: a conserved budget

For held-out systems (theta ~ P) and x_0 independent of theta, with g_n the expected h = 1 gap at context length n:
sum_{n=0}^{N-1} g_n = KL(m_P(x_{1:N} | x_0) || m_Q(x_{1:N} | x_0)) <= KL(P || Q) (chain rule of KL, then data processing), and the
left side tends to KL(P || Q) when theta is consistently estimable (Clarke and Barron 1990 asymptotics; see LITERATURE_REVIEW.md).

| Family | KL(P or Q) on the system prior (VERIFIED, `kl_budget.py`) | Summed map gaps |
|---|---|---|
| 1A known sigma | 0.582 nats (a only) | n = 1..80 (log-log interpolated, no n = 0, no tail): 0.517 / 0.469 / 0.277 at r = 0.25 / 1 / 4 (VERIFIED here). With the n = 0 term and a 1/n^2 tail: 0.566 / 0.567 / 0.571 (Reviewer 1, DERIVED/computed; not re-run here) |
| F1 unknown sigma | 0.582 (a) + 1.989 (log sigma: IG(3,2) vs log-uniform [0.01, 100]) = 2.570 | n = 2..40 only: 1.17-1.23 (the n = 0, 1 terms, where most of the sigma budget is spent, are not mapped) |
| F3 (same a priors, observation noise) | 0.582 at every q | n = 2..9 only |
| F2 | about 17.4 nats (Reviewer 2, Monte Carlo; not re-run here) | n = 10, 20 only |

Consequences (DERIVED):
1. The 1A window is predictable before any map: a budget of 0.58 nats, decaying roughly like 1/n^2 at large n, with r deciding
   how early it is spent (large r front-loads it at n = 0, which is why the r = 4 window is shortest). The map is a numerical
   confirmation of this (an independent validity check of the reference code, to about 3%).
2. Observation noise does not reduce the budget (same priors over a); it spreads it over more context steps, so each per-step
   gap falls below delta. "Observation noise shrinks population knowledge" should read "shrinks the per-forecast gap".
3. The F1 budget is 4.4x the 1A budget, and 77% of it is the noise-scale prior, whose size is set by the arbitrary width of the
   context-only log-uniform range (narrowing it to [0.1, 10] removes log 2 = 0.69 nats; Reviewer 1). Reviewer 3 computed the
   gap due to the noise scale alone (iid data, IG(3,2) vs Jeffreys): 0.19 / 0.11 / 0.056 / 0.019 nats at n = 2 / 3 / 5 / 10,
   against the F1 map's 0.25-0.32 / 0.16-0.18 / 0.087-0.094 / 0.032-0.040. **So most of the F1 "window" is noise-scale knowledge.**
   Reviewer 2 then computed it directly with independent code (r = 1, realised targets; scratch, not pre-specified): F1 gap
   0.2845 / 0.1763 / 0.0920 / 0.0344 at n = 2 / 3 / 5 / 10 (map 0.2892 / 0.1715 / 0.0936 / 0.0382, |z| <= 1.2); with the
   context-only reference given the population noise prior IG(3, 2): **0.037 / 0.032 / 0.027 / 0.015**, i.e. the window shrinks to
   n <= 5, as in the known-scale family; the sigma-only part is 57-79% of the gap. F2 prior KL (R2, Monte Carlo 4e5 draws):
   about 17.4 nats (5.7 with the population inverse-Wishart given to the comparator).
   These scratch numbers must be confirmed by a pre-specified run (new spec and seed role) before the paper says it; the spec
   will be written after these numbers were seen, which the disclosure entry must say.

### 6.2 Library vs population on held-out systems: nearest-atom limit

As n grows the population predictive tends to the true law and the library posterior concentrates on the KL-nearest atom, so
g_n(K) tends to E[min_k KL_stationary(theta || theta_k)] (DERIVED). Computed by Monte Carlo (VERIFIED, `nearest_atom.py`;
2000 systems x 32 libraries scalar, 400 x 8 bivariate):

| K | 1 | 2 | 4 | 8 | 16 | 32 | 64 | 256 | 1024 |
|---|---|---|---|---|---|---|---|---|---|
| known sigma | 0.140 | 0.074 | 0.027 | 0.0094 | 0.0040 | 0.0015 | 0.0004 | 0.0000 | - |
| unknown sigma | 0.422 | 0.230 | 0.130 | 0.066 | 0.037 | 0.022 | 0.012 | 0.0027 | - |
| bivariate VAR(1) | - | 1.08 | - | - | 0.52 | - | 0.25 | 0.165 | 0.108 |

Reading: the limit crosses delta = 0.02 between K = 4 and 8 (known sigma), near K = 32 (unknown sigma), and not even at K = 1024
in the bivariate family, whose atoms have 7 free parameters (A: 4, Sigma: 3), not 4 as the paper says. Reviewer 2 confirms the
unknown-sigma limits independently (K = 16: 0.037 nats, every draw >= delta; K = 32: 0.020, 36% of draws) and shows the F1 map's
per-draw share rising with n (K = 8: 0.43 at n = 5 to 0.88 at n = 40), so "separable libraries become rare beyond eight
systems" holds only for the mapped n range. The scalar maps (n <= 20 for 1A libraries)
show less separability than these limits (posteriors not yet concentrated; Reviewer 1's importance-sampling argument covers
that regime). The paper's "plausible reason (not tested)" is therefore derivable, and it makes a sharp prediction for the
neural Q2 study: in F2 the library reference stays distinguishable from population Bayes far beyond K = 64, so a memorisation
transition K* is observable by score there and not in the scalar families. This prediction should be checked against an
extended F2 library map (CPU) before any neural F2 study.

## 7. BORDERLINE and MC-LIMITED cells: what they imply

* BORDERLINE (F3: 21 held-out cells, 14 with estimate >= delta): simulation precision, not a property of the references. Batch 4
  at 10x N resolves most of them. A reference map can always be made more precise; "underpowered" means "not yet computed
  precisely enough", which the paper should say.
* MC-LIMITED (F2: 3 held-out, 16 in-library): numerical method limits; see section 3.

## 8. Is "separable in expected log score" testable for a trained model?

Per-cell separability at delta is neither necessary nor sufficient for classifying a model (paper Sec. 5 says not sufficient;
DERIVED here that it is not necessary either: a pooled test over cells or a cumulative log-likelihood ratio over a sequence can
discriminate references whose per-step gaps are below delta, at a rate set by the budget in 6.1). The decisive quantity for a
neural study is the model's between-seed sd of regret relative to the gap; the F1 lookup gives the requirement (<= 0.01 nats at
M = 32 for Q1) but no trained-model sd exists for any family except the Stage 1A UNIF-only proxy (0.0017 at 10k steps;
REPORTED S20).

## 9. Recommendations (all CPU)

1. Put the two closed-form accounts (6.1, 6.2) in the paper as the organising theory, with the maps as their numerical check.
2. Report gap-versus-n curves with bands (figures), not only thresholded windows; mark grid-censored values.
3. Pre-specify and run: noise-matched context-only comparators (F1, F2), an F2 comparator sweep, the F2 library map at
   K in {256, 1024} and n up to 40, and dense n grids where the window ends (1A n = 5..10, F1 n = 10..20).
4. Report the expected number of wrong marks (closes the 1A spec deviation) and a Holm-adjusted version of Table 1.
5. Rename "identifiable" (STATISTICAL meaning differs; Reviewer 1 and 3).
