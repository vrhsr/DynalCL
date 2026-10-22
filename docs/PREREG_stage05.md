# Pre-registration: Stage 0.5, decisive population-advantage experiment

Status: **FROZEN before the confirmatory run.** The draft was written before the pilot and before any Stage 0.5
evaluation data existed (draft sha256 d614c247...). Section 5 (N) was filled in from the pilot by the rule stated there. The document is then frozen, and its SHA-256 is
recorded in the confirmatory run's provenance. Config: `config/stage05.yaml`.
Implementation: `dynaicl/experiments/population_advantage.py`.

## 1. Questions

* **Primary (Q1).** Does the matched population-aware Bayesian reference beat the **strongest context-only
  estimator** by a practically meaningful amount?
* **Secondary (Q2).** Can the finite-library and continuous-prior predictors be distinguished reliably?

The two are decided separately. Q1 remains viable even if Q2 fails. All three strategies do not
need to be mutually distinguishable.

## 2. What Stage 0 showed, and why this design (no new data were used to choose it)

Source: `docs/STAGE0_RESULTS_REVIEW.md`, generated from the Stage 0 run files.
- Matched vs the Stage 0 frontier (flat-prior Bayes) was meaningful only at n = 5 (0.036-0.157 nats). At
  n = 20 it was 0.005-0.017, and at n = 80 it was <= 0.005.
- Library vs continuous differed materially only for K = 4 under E-CONT.
- G was ill-conditioned wherever the frontier gap was below delta (all n = 80 rows, half the n = 20 rows).

This motivates short contexts and small libraries. Because Stage 0 results guided these choices, the
confirmatory evaluation uses **only fresh seeds**: no library, selection or evaluation item from
Stage 0 or the pilot is reused.

**Two design changes, each justified before any Stage 0.5 data:**
1. **The context-only family gains a generic-stability Bayes member** (uniform prior on (-0.999, 0.999),
   known sigma; `baselines/stability_prior.py`). It uses no population information, only the structural
   fact that the systems are stable, so it is context-only under the Stage 0 definition. Leaving it out
   would credit generic stability knowledge to "population knowledge" and overstate Q1. The primary
   comparator is therefore the frontier over 8 members (`frontier_ctx`). The Stage 0 frontier (7 members)
   is reported for continuity.
2. **sigma is fixed at 1 and the initial-state-to-noise ratio r = sd(x_0)/sigma is varied.** Log-score
   differences are invariant to a common rescaling of (x, sigma) (docs/MATH.md section 11; TESTED), so r is
   the only scale that matters. Stage 0 covered r in {1, 4} under the labels sigma = 1 and sigma = 0.25.
   (Terminology: this AR(1) has *innovation* noise sigma. There is no separate observation noise.)

## 3. Design (`config/stage05.yaml`)

| Factor | Levels | Justification |
|---|---|---|
| Prior | P-STABLE truncated normal (mu0 0.4, tau0 0.3, rho 0.95) | Unchanged from Stage 0. Fixed before any result. Conclusions are conditional on this population. |
| r = sd(x_0)/sigma | 0.25, 1, 4 | r = 1 is roughly a stationary-scale start (stationary sd 1/sqrt(1 - a^2) ≈ 1.1 at the prior mean). 0.25 is a start near rest. 4 is a large initial transient. |
| Context length n | 1, 2, 3, 5, 10, 20 | Short contexts, where Stage 0 showed effects. n = 20 is an anchor overlapping Stage 0. |
| Horizon h | 1, 5 | As in Stage 0. |
| Condition | E-CONT; E-LIB with K in {2, 4, 8} | Held-out vs in-library. Each uses its own matched reference. |
| Library atoms | iid from the prior, uniform weights, nested in K | As in Stage 0 (fresh library seed). |

Cells: E-CONT 3 x 6 x 2 = 36; E-LIB 3 x 3 x 6 x 2 = 108. Predictors per cell: the matched reference; continuous-prior
Bayes (E-LIB); libraries K in {2, 4, 8} (E-CONT); the 8 context-only members.

**Seeds (fresh; none appear anywhere in Stage 0 code or configs, checked by grep):**
library 52001, selection 52002, evaluation replicates R1 = 52101 and R2 = 52102, bootstrap 52999.
The pilot uses 51001-51004. Each role has its own `NamedStreams` root, so the replicates are fully independent.

**Frontier selection:** `frontier_ctx`, `frontier_stage0` (7 members) and `frontier_strict` (no sigma-informed
member) are chosen by mean log score on the selection split (1000 items per cell), **once**, and then frozen
for both evaluation replicates. Selection never sees evaluation data.

## 4. Metric, effect threshold, uncertainty

* **Primary metric:** paired mean log-score difference D = S(matched) - S(frontier_ctx), in nats per forecast,
  on identical evaluation items.
* **Minimum meaningful effect: delta = 0.02 nats/forecast.** It was pre-registered in Stage 0 before any Stage 0
  result and is kept unchanged, not re-chosen. Interpretation for a Gaussian forecast: 0.02 nats is the
  expected log-score loss from a mean bias of 0.2 predictive sd (0.5 x 0.2^2), or from mis-scaling the
  variance by about 35% (0.5 (log k + 1/k - 1) at k ≈ 1.35). Over 100 forecasts it compounds to a likelihood ratio of
  e^2 ≈ 7.4. Smaller gaps would not let a later study attribute a model's behaviour to one strategy with a
  few thousand evaluation items. Sensitivity at 0.01 and 0.04 is reported, but does not drive the decision.
* **Uncertainty:** analytic paired SE = sd(d)/sqrt(N). The decision interval is mean +/- 2.24 SE (two-sided
  97.5%), and a 95% CI is also reported. **Robustness:** a percentile bootstrap (2000 resamples, seed 52999) at
  the same level for the primary contrast. Disagreements with the analytic class are reported.
* **Per-replicate class (Q1):** MEANINGFUL if mean - 2.24 SE > delta; NEGLIGIBLE if mean + 2.24 SE < delta; otherwise
  INCONCLUSIVE.
* **Per-replicate class (Q2,** d = S(library) - S(continuous)**):** DISTINGUISHABLE if the interval excludes [-delta, delta];
  EQUIVALENT if it lies inside (-delta, delta); otherwise INCONCLUSIVE.
* **Confirmation (independent replication):** a cell's class counts only if **both** replicates agree;
  otherwise it is DISCORDANT. Multiplicity: if the true D <= delta, P(MEANINGFUL) <= 0.0125 per replicate, so a
  false confirmation has probability <= 1.6e-4 per cell, and <= 0.023 summed over all 144 primary cells.

## 5. Replication count (from the pilot)

Rule, fixed now: run `config/stage05_pilot.yaml` (seeds 51001-51004, 300 eval items, 1 replicate). Take the 90th
percentile of the item-level sd of the paired differences over all cells, for the primary contrast
(both conditions) and the secondary contrast: sd_q90. Set N = ceil((4 sd_q90 / delta)^2), capped at 6000. With
SE = delta/4, a true D = 2 delta is classified MEANINGFUL with probability Phi(1.76) ≈ 0.96 per replicate
(≈ 0.92 for both). A true D <= delta is classified MEANINGFUL with probability <= 0.0125. If the cap binds,
cells with SE > delta/4 are reported as under-powered. **The pilot is used for N only.** No grid level,
threshold or rule may change because of it.

**Pilot result** (`runs/20261009T190645936218Z_stage05_pilot_16ab5a7e45`, seeds 51001-51004, 300 items, 1 replicate). P1 held: 0/1368 T1
violations, 0/144 T2 failures, max quadrature error 1.8e-15, matched quadrature cap never hit. Over 360
primary and secondary contrasts, the item-level sd has quantiles 10% = 0.063, 50% = 0.131, **90% = 0.2906**,
max = 0.869. **N = ceil((4 x 0.2906 / 0.02)^2) = 3378** evaluation items per replicate (cap not binding). At this N,
36/360 contrasts are expected to have SE > delta/4 (pilot sd > 0.29); they will be reported as under-powered.
Only the sd values and P1 were inspected; pilot effect estimates were not used for anything.

## 6. Decision rules (applied mechanically by `decide()`)

The relevant regime is **E-CONT** (held-out systems, the test of a *continuous* population), **r = 1**,
**n in {2, 3, 5, 10}**, h in {1, 5}. n = 1 (a single transition) and n = 20 are boundary anchors.

E-LIB with K <= 8 is a tiny population, where an advantage is expected almost by construction. It is reported
for Q1 and Q2 but does not drive the PROCEED decision.

* **P1 (reference reliability):** T1 has 0 optimality violations; T2 has 0 calibration failures for the matched
  reference (Bonferroni, family alpha 1e-3); the maximum quadrature node-doubling error at targets is
  <= 1e-6; the matched reference hits the quadrature cap 0 times. This must hold in every cell and replicate.
* **P2 (stable across n):** for **each** h in {1, 5}, the primary class is confirmed MEANINGFUL at >= 2
  consecutive n in (2, 3, 5, 10), at r = 1.
* **P3 (not scale-fragile):** for **each** r in {0.25, 4}, at least one n in {2, 3, 5, 10} is confirmed
  MEANINGFUL (h = 1).

**PROCEED** if P1, P2 and P3 all hold.
**REVISE** if P1 holds but not (P2 and P3), and either (a) some E-CONT cell with n <= 10 is confirmed MEANINGFUL
(the advantage is narrow, or depends on the initial-state scale), or (b) no cell is MEANINGFUL against
`frontier_ctx` but some is against the Stage 0 frontier. Case (b) means the measured benefit is generic
stability knowledge, and the operational definition of "population knowledge" has to change.
**STOP this AR(1) formulation** if P1 holds and no E-CONT cell with n <= 10 is confirmed MEANINGFUL against either
frontier. Also STOP (no interpretation) if P1 fails: reference uncertainty prevents reliable interpretation.

## 7. Stopping rules and protections

1. The pilot only sets N. If the pilot shows a P1 failure, debug, then re-pilot with **new pilot seeds**. Main seeds stay untouched.
2. The confirmatory run uses a fixed N with both replicates in one job. There is no interim look, no extension of N,
   and no change to the grid, delta, z or rules after it starts.
3. If the confirmatory run fails P1, separability results are not interpreted. Any rerun uses new evaluation seeds and is
   reported as a new run alongside the failed one.
4. If compute is short, the job is run as-is on remote hardware (user policy: local jobs under 10 min). It is not
   shrunk to fit.

## 8. Reported regardless of outcome

Paired effects with 95% CIs and decision intervals per cell and replicate, for every contrast (vs frontier_ctx,
the Stage 0 frontier, the strict frontier, flat-prior, stability-prior, and the best member on the evaluation set);
frontier members; calibration (coverage 50/80/95, PIT) and mean log score of every predictor; fallback and
quadrature-cap rates; bootstrap agreement; and the sensitivity at delta in {0.01, 0.04}.
No novelty or publishability claim follows from reference separation alone.
