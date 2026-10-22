# Stage 0.5 results: decisive population-advantage experiment

**Pre-registered decision: REVISE.** It was applied mechanically by `decide()` with the frozen rules
(docs/PREREG_stage05.md, sha256 fcf7f3a5...). Full tables: [STAGE05_RESULTS_TABLES.md](STAGE05_RESULTS_TABLES.md).
Run: `runs/20261010T053729455237Z_stage05_population_advantage_51c7621b7a` (Google Colab, Python 3.13.16, pinned stack,
84 min, 2 workers). The config hash 51c7621b7a8f and the pre-registration hash match the frozen versions. All 13
output checksums verify.

Labels: TESTED (computed in this run), DERIVED (docs/MATH.md), ASSUMED, UNVERIFIED.

## 1. Pre-registration and thresholds (deliverable 1)

docs/PREREG_stage05.md was written before the pilot and frozen before the confirmatory run.
* delta = 0.02 nats/forecast. It was carried over unchanged from Stage 0, where it was fixed before any result.
  For a Gaussian forecast it equals the loss from a mean bias of 0.2 predictive sd, or a ~35% variance mis-scaling.
* Per-replicate decision interval: mean +/- 2.24 SE. A class counts only if two independent replicates agree.
* N = 3378 items per replicate, from the pilot (sd_q90 = 0.2906; target SE <= delta/4).
* Rules: P1 reference reliability; P2 a confirmed MEANINGFUL advantage at >= 2 consecutive n in {2, 3, 5, 10}
  for both h = 1 and h = 5 (E-CONT, r = 1); P3 the same for r in {0.25, 4} at h = 1.

## 2. Configurations and fresh seeds (deliverable 2)

`config/stage05.yaml`: P-STABLE truncated normal (mu0 0.4, tau0 0.3, rho 0.95); sigma = 1; r = sd(x_0)/sigma in
{0.25, 1, 4}; n in {1, 2, 3, 5, 10, 20}; h in {1, 5}; E-CONT, and E-LIB with K in {2, 4, 8}; 1000 selection items.
Seeds: library 52001, selection 52002, evaluation R1 52101, R2 52102, bootstrap 52999 (pilot 51001-51004). None of
them appear in Stage 0. The context-only family has 8 members: the Stage 0 seven plus generic-stability Bayes.

## 3. Reference reliability (P1): passed (TESTED)

* T1: 0 optimality violations / 2736 paired comparisons (min z -0.44).
* T2: 0 calibration failures for the matched reference / 288 cell-replicates (min p 7.8e-4; per-test level 8.7e-7).
* Quadrature node-doubling error at targets <= 1.3e-15. The matched reference never hit the quadrature cap.
* Bootstrap and analytic primary classes agree in 288/288 cell-replicates.
* Power: 42/288 primary contrasts have SE > delta/4 (37 of them in E-LIB). The maximum SE is 0.0063.

## 4. Primary question: matched population-aware Bayes vs the strongest context-only estimator (deliverable 3)

**The strongest context-only estimator was the generic-stability Bayes member in all 144 cells.** It knows only
that abs(a) < 0.999, and nothing about the population. Pooled effects (average of the two replicates, 95% CI) and
the confirmed class, E-CONT (held-out systems):

| h | r | n = 1 | n = 2 | n = 3 | n = 5 | n = 10 | n = 20 |
|---|---|---|---|---|---|---|---|
| 1 | 0.25 | **+0.045 M** | **+0.050 M** | **+0.049 M** | +0.032 D | +0.019 I | +0.005 N |
| 1 | 1 | **+0.043 M** | **+0.044 M** | **+0.043 M** | +0.028 D | +0.018 I | +0.004 N |
| 1 | 4 | +0.025 I | +0.024 I | +0.023 I | +0.014 D | +0.011 N | +0.003 N |
| 5 | 0.25 | +0.013 N | +0.014 D | +0.014 D | +0.011 N | +0.008 N | +0.003 N |
| 5 | 1 | +0.013 N | +0.012 N | +0.012 N | +0.010 N | +0.008 N | +0.003 N |
| 5 | 4 | +0.014 D | +0.009 N | +0.010 N | +0.006 N | +0.006 N | +0.002 N |

M = confirmed MEANINGFUL, N = confirmed NEGLIGIBLE, I = INCONCLUSIVE in both replicates, D = DISCORDANT.
All 72 E-CONT replicate means are positive. Every replicate 95% CI excludes zero at n <= 10. At n = 20, 6 of the 12 replicate CIs include zero.

**Why the verdict is REVISE, not PROCEED:**
* P2 fails at h = 5. At r = 1, the population-specific advantage is confirmed NEGLIGIBLE at every n (0.008-0.013).
  It holds at h = 1 (n = 1, 2, 3).
* P3 fails at r = 4. No cell is confirmed MEANINGFUL. The point estimates are 0.023-0.025 at n <= 3, which is
  above delta, but the intervals straddle delta. It holds at r = 0.25.

**The most consequential finding: decomposing the Stage 0 "population advantage"** (TESTED, pooled; r = 1, h = 1):

| n | matched - flat-prior (the Stage 0 contrast) | stability - flat-prior (generic knowledge) | matched - stability (population-specific) |
|---|---|---|---|
| 2 | +0.311 | +0.267 (86%) | +0.044 (14%) |
| 3 | +0.182 | +0.139 (76%) | +0.043 (24%) |
| 5 | +0.081 | +0.053 (65%) | +0.028 (35%) |
| 10 | +0.034 | +0.016 (47%) | +0.018 (53%) |

At h = 5 the generic share is larger still (n = 2: 0.555 total vs 0.543 generic). Most of what Stage 0 credited to
"population knowledge" is knowing that the system is stable. The population-specific remainder is real
(every replicate 95% CI excludes zero at n <= 10) but small: about 2 delta at best. It is confined to one-step
forecasts at n <= 3, and roughly halved when the initial transient is large (r = 4).

**In-library (E-LIB), matched library vs frontier:** the advantage is larger and lasts longer for the
smallest population. At h = 1, K = 2 is confirmed MEANINGFUL through n = 10 for r <= 1 (0.044-0.068). For K = 4 and 8 it
lasts through n = 5 for r <= 1, but only to n <= 2 at r = 4. At h = 5, only K = 2 is MEANINGFUL (up to n = 3-5). This is expected: a population of 2-8 systems is
far more informative than the continuous prior.

**Sensitivity (not decision-driving):** confirmed MEANINGFUL E-CONT cells number 13/36 at a 0.01 threshold, 6/36 at 0.02,
and 0/36 at 0.04. The conclusion is threshold-sensitive in exactly the way the effect sizes (about 0.04-0.05)
predict.

## 5. Secondary question: library vs continuous prior (deliverable 4)

| Condition | K = 2 | K = 4 | K = 8 |
|---|---|---|---|
| E-CONT (library mismatched) | DISTINGUISHABLE 26/36 (library worse by 0.03-0.21) | EQUIVALENT 34/36 | EQUIVALENT 36/36 |
| E-LIB (library matched) | EQUIVALENT 20/36, DISTINGUISHABLE 1/36 | EQUIVALENT 36/36 | EQUIVALENT 36/36 |

With 4 or more systems, the finite-library posterior and the continuous-prior posterior are **practically
interchangeable** in this family, both on held-out and on in-library systems. They separate only when a 2-system
library is applied to held-out systems, where it is simply a bad prior. **Q1 vs Q2:** Q1 shows a small,
confirmed, narrow effect. Q2 shows essentially no usable distinction. The weak three-way separation in
Stage 0 is therefore mainly a limitation of the library-vs-continuous framing in scalar AR(1): one parameter,
fast posterior concentration, and atoms dense relative to posterior width (DERIVED reasoning, MATH 1.3 / 6).
It is not mainly a failure of Q1. Q1 itself survives only narrowly.

## 6. Calibration and baseline performance (TESTED; measurements)

At E-CONT, r = 1, coverage 50/80/95 averaged over n and both replicates:
* matched reference: 0.499/0.799/0.949 (h = 1) and 0.495/0.799/0.949 (h = 5).
* stability prior: 0.506/0.803/0.952 and 0.524/0.829/0.966. It is slightly conservative at h = 5.
* flat prior: over-wide at h = 5 (0.972 at the 95% level).
* OLS Student-t and persistence: miscalibrated (95% coverage 0.85-0.93; KS p down to 1e-53).
* library K = 2: overconfident (0.913 at h = 5).

`frontier_stage0` was flat-prior Bayes in 141/144 cells. `frontier_strict` was OLS Student-t in 89 and kernel-blocked
in 53. Matched minus the strict frontier is enormous at n = 1 (e.g. +2533 nats at r = 0.25, h = 1), because without
known sigma the context-only estimators fall back to degenerate variances. This is a property of those baselines, not
evidence for population knowledge.

## 7. Decision: REVISE (deliverable 5)

Per the frozen rules (TESTED): P1 holds, P2 fails (h = 5), P3 fails (r = 4). A confirmed meaningful
population-specific advantage exists, but only for one-step forecasts, n <= 3, and r <= 1. It depends on the
horizon and on the initial-state scale. That matches the user's REVISE definition ("advantage exists only in
narrow conditions, depends heavily on initial-state scale, or requires a different operational definition of
population knowledge"). **All three clauses apply:**
1. narrow (n <= 3, h = 1);
2. scale-dependent (r = 4 is about half the size);
3. the operational definition must change: against the Stage 0 baseline (flat prior) the "population advantage" looked
   3-7x larger at n = 2-5 (7x at n = 2), because it included generic stability knowledge.

**What the revision has to address (hypotheses for the user's choice, not results):**
* *Operational definition (required, whatever else changes).* Any later model study must classify models against a
  structure-aware context-only reference, not a flat-prior one. Otherwise a model that has learned only "systems
  are stable" would be credited with population knowledge. The stability member is already in the code.
* *Is this AR(1) formulation worth continuing?* The population-specific signal (about 0.045 nats per forecast, only at n <= 3) is small.
  A trained model's score error of a similar size would mask it. Whether a model study can resolve it depends on
  model-vs-reference variance, which is **UNVERIFIED** (no model exists yet).
* *Could a different family help?* Possibly, but this must be tested, not assumed. The population-specific gain is
  bounded by how much the population prior concentrates relative to generic structural knowledge, and by how fast
  the context alone identifies the parameters. Families where parameters are identified *slowly* (AR(1) with
  observation noise, where the Kalman likelihood flattens the posterior) or where the population encodes structure
  no generic constraint captures (VAR(1) with a structured coupling prior) *could* lengthen the window.
  Neither is shown here.

## 8. Smallest defensible next experiment (deliverable 6)

The decision is REVISE, so **no Stage 1 neural experiment is supported yet.** The smallest defensible next step is a
CPU-only, pre-registered **Stage 0.6 identification-difficulty probe**, built on the same machinery:
* Question: does slower parameter identification extend the window in which the population-specific advantage
  (matched minus the stability-aware frontier) exceeds delta?
* Design: scalar AR(1) **with observation noise** y_t = x_t + tau v_t (spec Section 8 extension; Kalman likelihood,
  quadrature over a). tau/sigma in {0, 0.5, 1}. tau = 0 reproduces this run as an internal anchor. E-CONT, r = 1, h = 1,
  n in {2, 3, 5, 10, 20, 40}. Same prior, same delta, same two-replicate rule, fresh seeds.
* Gate before running: the Kalman reference must pass the A/B/C/E/G-style validation (grid oracle, calibration,
  mutations), because it would be a new reference.
* Outcome rule (to pre-register): if confirmed MEANINGFUL cells extend to n >= 10 at some tau > 0, a Stage 1 model study
  on that family becomes defensible. If not, the AR-family formulation of "population knowledge" should be stopped in
  favour of a family chosen on a stated structural argument.

If the user instead chooses to proceed within the narrow regime found here, the minimal Stage 1 would be: E-CONT,
h = 1, n in {1, 2, 3}, r = 1. References: the matched reference, the stability-aware frontier, and K = 2 and K = 8 libraries.
Models would be classified only where the two references differ by >= delta, which is exactly the confirmed cells above.
This is a narrower and riskier study, and it is not recommended before the Stage 0.6 probe.

No claim of novelty or publishability follows from reference-predictor separation alone.
