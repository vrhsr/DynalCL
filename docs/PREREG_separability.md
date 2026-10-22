# Pre-registration: reference separability map (Stage 0, Section 7)

Status: **FROZEN before the main run.** The draft was written before any separability result. Section 5 (replication count) was filled in
from the pilot by the rule stated there. The document is then frozen, and its SHA-256 is recorded in the
main run's provenance. Nothing here is tuned to make a hypothesis come true.

## 1. Question

Are the reference strategies statistically distinguishable, by paired log-score differences, in the
regimes later models will be tested in? If not, no later model can be classified as using one strategy
rather than another. The strategies are:

* **continuous-prior Bayes** (generalises population knowledge),
* **finite-library posterior** (memorises the training systems),
* **context-only frontier** (no population knowledge).

## 2. Design (config/separability.yaml)

| Factor | Levels |
|---|---|
| Prior | P-STABLE truncated normal: mu0 = 0.4, tau0 = 0.3, rho = 0.95 (DECISIONS D-04) |
| Noise sigma | 0.25, 1.0 (x_0 ~ N(0, 1) independent of a, so sigma also sets the initial-state signal) |
| Context length n | 5, 20, 80 |
| Horizon h | 1, 5 |
| Library size K | 4, 16, 64, 256 (atoms iid from the prior, uniform weights, nested across K) |
| Condition | E-CONT (fresh systems from the prior), E-LIB (systems drawn from the K atoms) |

Cells: E-CONT 2 x 3 x 2 = 12 (every K is evaluated as a competitor in each cell). E-LIB 2 x 4 x 3 x 2 = 48.

Predictors per cell: the matched reference (E-CONT: quadrature continuous-prior Bayes; E-LIB: library
posterior), continuous-prior Bayes as a comparison under E-LIB, the library posteriors as comparisons
under E-CONT, the 7 context-only members, and two frontiers (`frontier_all`, `frontier_strict`; selected on a
disjoint selection split, DECISIONS D-05/D-06).

## 3. Metrics

* Primary: mean log predictive density. Paired differences on identical items, SE = sd/sqrt(N).
* Calibration of every predictor: PIT (KS p-value, 10-bin histogram) and 50/80/95% coverage. **Pass/fail for
  the matched reference only (T2).** For all others it is a measurement.
* Candidate metric G = (S_model - S_ctx)/(S_matched - S_ctx) with a delta-method SE. It is flagged
  ill-conditioned when abs(S_matched - S_ctx) < 3 SE or < delta (MATH 9).
* CRPS: off (DECISIONS D-21).

## 4. Decision rule (per pair of strategies, per cell)

delta = **0.02 nats per prediction** (the smallest gap of interest; a hypothesis: a log-likelihood ratio
of exp(0.02) ≈ 1.02 per step, which compounds to about 7x over 100 predictions). With d = mean
paired difference and SE its standard error:

* **separable**: abs(d) >= 3 SE and abs(d) >= delta.
* **equivalent** (TOST, 5% per side): d - 1.645 SE > -delta and d + 1.645 SE < delta.
* **detectable_below_delta**: abs(d) >= 3 SE but abs(d) < delta.
* **inconclusive**: otherwise.

**"References indistinguishable" in a cell** means every key pair is *equivalent*. Under E-CONT the key
pairs are matched vs frontier_all and matched vs each library. Under E-LIB they are matched vs continuous,
matched vs frontier_all, and frontier_all vs continuous.

**Regime of interest**: any cell. For the Stage 1 recommendation (Section 7 of the spec), "separable in at
least one regime of interest" means at least one cell in which each of the three strategy pairs
relevant to that condition is *separable*.

## 5. Replication count (from the pilot)

Rule, fixed before the pilot is run: run config/separability_pilot.yaml (seed 7110, 300 eval items per
cell). Take the 90th percentile, over all cells and key pairs, of the item-level sd of the paired
difference: sd_q90. Set N = ceil((4 sd_q90 / delta)^2), so that SE <= delta/4 for 90% of
comparisons. Justification: with SE = delta/4, a true gap of delta is detected at the 3-SE threshold with
probability Phi(4 - 3) ≈ 0.84, and a true gap of 0 is declared equivalent whenever abs(d) < 0.59 delta.
CPU cap: N <= 6000 eval items per cell. If the rule asks for more, N = 6000, and the cells with SE > delta/4
are reported as under-powered. Selection items: 1000 per cell.

**Pilot result** (run `runs/20261009T090102869678Z_separability_pilot_4071d8a6c5`, seed 7110, 300 items per
cell; its T1, T2 and T3 all passed): 204 key-pair comparisons. Item-level sd of the paired difference has
quantiles 10% = 0.0135, 50% = 0.0601, **90% = 0.2417**, max = 0.3927.
**N = ceil((4 x 0.2417 / 0.02)^2) = 2337** eval items per cell (below the 6000 cap). At this N, 21 of 204
key comparisons are expected to have SE > delta/4 (pilot sd > 0.242). Most are n = 5 comparisons against
the frontier, and they will be reported as under-powered. The pilot's separability counts are **not** used for
any conclusion. They come from a different seed and are under-powered by design.

## 6. Theorem-level checks (a violation indicates a bug, up to MC error)

* T1: no competitor beats the matched reference (one-sided z, Bonferroni over every comparison in the run,
  family alpha 1e-3).
* T2: the matched reference is calibrated (KS + three coverage tests per cell, Bonferroni, family alpha 1e-3).
* T3: sequential = batch and the h = 2 chain rule hold on the experiment's own priors.

If any of these fails, the separability results are **not interpreted**, and the bug is found first.

## 7. Diagnostic hypotheses (measured, not pass/fail)

* H1: the matched reference's advantage over flat-prior Bayes shrinks as n grows (E-CONT).
* H2: small-K libraries are overconfident (coverage below nominal) on E-CONT.
* H3: on E-CONT, the library approaches continuous-prior Bayes as K grows at fixed n.
* H4: on E-LIB, the library's advantage over continuous-prior Bayes changes with n.

Expectations written down in advance:
H1 should hold because the posterior concentrates, but the "gap" can be non-monotone at small n,
since the truncated prior also helps with long-horizon uncertainty. H2 should be strongest at small K and large n,
where the library posterior collapses onto one wrong atom. H3 should hold when K is large relative to the
posterior resolution at n (atom spacing ~1.9/K vs posterior sd ~ sqrt((1-a^2)/n)). At n = 80 and K = 4 the
library should be clearly worse. H4: at small n the two posteriors are both prior-like, so they should
be close. At large n the library should gain, because it identifies the exact atom.
If an effect is absent, we first check whether its absence is expected under these settings.

## 8. What counts as which outcome

* PROCEED candidate: T1-T3 pass, and at least one regime is separable for all key pairs.
* REVISE candidate: every cell is equivalent or inconclusive for some key pair, or G is ill-conditioned in
  most cells.
* STOP / redesign candidate: the matched reference's advantage over the best context-only estimator is
  below delta in every cell.
