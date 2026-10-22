# Stage 0.6 pre-registration: the noisy-observation probe

Status: FROZEN together with `docs/FREEZE_MANIFEST_STAGE06.json` (its SHA-256 is printed at the freeze and must be stored
outside the workspace). Every number below is fixed. Changes after the freeze are recorded in
`docs/DISCLOSURE_LOG_STAGE06.md` ("After the freeze").

Supporting documents (all in the manifest): `MATH_STAGE06.md` (derivations), `STAGE06_AUDIT.md` (Phase A audit),
`STAGE06_VALIDATION_REPORT.md` (validation evidence), `STAGE06_DECISION_DRY_RUN.md` (planning and operating
characteristics), `STAGE06_MUTATION_MATRIX.md`, `STAGE06_CALIBRATION_DIAGNOSTIC.md`, `STAGE06_NOISE_LEVEL_VERIFICATION.md`,
`STAGE06_SELECTION_AUDIT.md`. Configuration: `config/stage06.yaml` (confirmatory), `config/stage06_pilot.yaml` (Phase D
pilot), `config/stage06_test.yaml` (pytest only); seeds: `config/stage06_seed_manifest.yaml`.

## 1. Question

Stage 0.5 found that knowing the population prior helps materially only at very short contexts when observations are
noise-free (REVISE). Stage 0.6 asks: **when the AR(1) state is observed through additive Gaussian noise, does knowledge of
the population prior give a meaningful long-context advantage over knowing only stability, beyond what it gives
without noise?**

## 2. Data-generating process

* Latent state: x_t = a x_{t-1} + sigma_w e_t, e_t iid N(0, 1), with sigma_w = 1 (scale equivariance, MATH_STAGE06).
* Observations: y_t = x_t + sigma_v v_t, v_t iid N(0, 1), t = 0..45. Noise ratio q = sigma_v^2 / sigma_w^2.
* Initial state: x_0 ~ N(0, (r sigma_w)^2), latent, independent of a; scale r = sd(x_0) / sigma_w.
* Coefficient: a ~ truncated normal (mean 0.4, sd 0.3) on [-0.95, 0.95] (the population prior, P-STABLE).
* Grid: q in {0 (control), 0.755, 2.56, 6.5}; r in {0.25, 1, 4}; h in {1, 5}; context length n in 2..40 (n = number of
  transitions; context y_0..y_n; target y_{n+h}).

## 3. Predictors

* **Population reference:** the posterior predictive of y_{n+h} given y_0..y_n under the true model and the population
  prior. The likelihood is the Kalman prediction-error decomposition. The integral over a uses composite Gauss-Legendre
  on a shared node set: (-0.999, 0.999), cut points +/-0.95, 64 panels per unit, 8 nodes per panel, 1040 nodes.
  "Numerically approximated with verified convergence" (V1, V6, V7, V8, V18), not analytically exact.
* **Comparator (LOCKED): noise-aware stability-only Bayes.** It is identical except for the prior: U(-0.999, 0.999).
  Same likelihood, the same known sigma_w, sigma_v and x_0 prior, the same node set. The pair differs only in the
  prior (V11 parity null: bitwise identical when given the same prior).
* **Secondary, noise-misspecified (descriptive only):** the 8 noise-naive context-only members of Stage 0.5. They are
  scored at n in {2, 5, 10, 20, 40}, h in {1, 5}, on all 4000 systems of each replicate (the same systems and seeds).
  They are never used in the verdict.
* The secondary frontier selection proposed in the Phase C plan (item 12) is NOT part of this design (it was not in
  the approved decisions; disclosure entry 17).

## 4. Sample, seeds and units

* Two independent replicates, R1 and R2. Evaluation roots: 64101 and 64102. Bootstrap root: 64999. Each replicate has
  **N = 4000 systems**. Systems are the independent units: each system draws its own a, x_0, process noise and
  observation noise from per-item streams. The runner's integrity unit verifies three things: distinct systems within
  each replicate; disjointness between R1 and R2; disjointness from the selection split (63001) and from the Stage 0.5
  systems used by Tier-2. Within a replicate, the same systems are used for every q, r, n and h (common random
  numbers; V19), so all contrasts are paired.
* N is fixed at 4000 and is never changed after any estimate. The runner computes no effect estimate until every unit
  is complete; `analyze` refuses while any unit is missing.
* Sample-size rationale (STAGE06_DECISION_DRY_RUN.md section 2). The planning spreads come from the verified Stage 0.5
  items. The expected simultaneous half-widths at N = 4000 for gains and increments are:
  * 0.0026-0.0049 with the zero-noise spread (kappa = 1);
  * 0.0051-0.0097 if noise doubles the spread (kappa = 2).

  Both are well inside delta = 0.02.

## 5. Primary estimand, family and secondary quantities

* Per item: paired gain = log p_pop(y_{n+h} | y_0..y_n) - log p_stab(y_{n+h} | y_0..y_n) (nats/forecast). Positive
  values favour population knowledge.
* **Long-context region L = {10, ..., 40}** (31 context lengths).
* **gain(q, h, r)** = mean over systems of the within-system mean over n in L, with equal weight per n. It is
  computed separately in each replicate.
* **noise_increment(q, h, r)** = gain(q, h, r) - gain(0, h, r), formed per system (paired).
* **Primary family per replicate:** 18 gains (q > 0, h, r) + 18 noise increments = 36 contrasts.
* Descriptive only: full n-curves (n = 2..40), pooled R1/R2 estimates, the stricter GO variant, the noise-naive
  baselines, calibration diagnostics.

## 6. Inference

* **Cluster bootstrap over whole systems.** One draw resamples N systems with replacement, and its multiplicity
  vector is applied to every one of the 36 contrasts (the same resampled systems for all conditions).
* **Studentized max statistic:** T* = max_k |theta*_k - theta_k| / se*_k, where se*_k is the per-draw standard error,
  sd*_k (ddof 1) / sqrt(N).
* **Critical value:** c = the ceil(B (1 - alpha))-th smallest T*.
* **Band:** theta_k +/- c se_k, with se_k = sd_k / sqrt(N). It is a two-sided simultaneous band at familywise level
  1 - alpha, with **alpha = 0.05 per replicate**.
* **Draws:** B = 20000 first.
* **Monte Carlo error of c:**
  * Measured by the distribution-free 95% order-statistic interval of the (1 - alpha) quantile.
  * Requirement: relative half-length <= 0.01, i.e. 1% of c and therefore 1% of every half-width.
  * If it is not met, the same generator continues to 40000 and then 80000 draws.
  * If it is still not met, the analysis is invalid (BLOCKED).
  * The planning runs gave 0.0066-0.0076 at B = 20000.
* **Streams:** bootstrap generator `NamedStreams(64999).stream("stage06_bootstrap", replicate index)`.
* **Failures:** draws are never discarded. Any of the following makes the replicate invalid and the verdict BLOCKED:
  * a non-finite or zero per-draw SE;
  * a constant contrast;
  * a non-finite item;
  * a degenerate critical value.
* **One-sided bounds and null hypotheses.** All flags come from this single band:

  | Flag | Rule | Tests H0 | Against |
  |---|---|---|---|
  | G+ | lower bound of gain > delta | gain <= delta | gain > delta |
  | I+ | lower bound of increment > 0 | increment <= 0 | increment > 0 |
  | G- | upper bound of gain < delta | gain >= delta | gain < delta |
  | NEG | upper bound of gain < 0 | gain >= 0 | gain < 0 |

  Each false rejection requires the band to miss that contrast's true value. So all 4 x 36 one-sided claims hold
  jointly with probability >= 1 - alpha per replicate (asymptotic, strong familywise control). Because the band is
  two-sided, each side individually errs with probability of about alpha / 2.
* **Replicates are analysed separately.** No pooled estimate enters the verdict.

## 7. Decision rule (frozen; implemented in `dynaicl/experiments/stage06_analysis.py::decide`)

* delta = 0.02 nats/forecast (fixed).
* SUPPORTED(q, h, r) = G+ and I+ in the same replicate.
* **Q(h, r)** holds if, for an adjacent positive-noise pair (0.755, 2.56) or (2.56, 6.5), both cells are SUPPORTED in
  **both** replicates.
* Verdicts are evaluated in the order BLOCKED, GO, STOP, REVISE:
  * **BLOCKED** if any of these holds:
    * a critical check fails (section 9);
    * a replicate's analysis is invalid (section 6);
    * any of the 18 primary cells is missing in either replicate;
    * any primary gain has an adjusted upper bound < 0 (NEG) in either replicate;
    * there are not exactly two replicates.
  * **GO**: for some h, Q(h, r) holds for at least **2 of the 3** scales r.
  * **STOP**: G- holds for all 18 gains in both replicates.
  * **REVISE**: otherwise (valid, but narrower or inconclusive). Wide intervals give REVISE, never STOP.
* **Stricter variant (descriptive):** for some h, the SAME adjacent pair satisfies Q at >= 2 scales.
* Properties:
  * GO is a conjunction. It needs the critical checks, completeness, a valid bootstrap and a SUPPORTED adjacent pair
    in both replicates at >= 2 scales.
  * **False GO.** A false SUPPORTED flag is needed in BOTH independent replicates, so for a fixed claim the probability
    is <= alpha^2 = 0.0025. The dry run observed 0 false GOs in all null scenarios.
  * **STOP is an intersection claim** over 18 cells x 2 replicates. Using the simultaneous bounds is conservative
    (an intersection-union test would allow unadjusted one-sided bounds), and this is intended: STOP is a strong
    negative claim, and one frozen band keeps all flags coherent.
  * **NEG at its boundary.** Under exactly zero gains, the NEG rule fires at up to about alpha/2 per replicate (dry run:
    2-7% of pairs BLOCKED). DERIVED: each true gain is an expected KL divergence, so it is >= 0, with equality only if
    the predictives coincide. Exact-zero gains are the least favourable case.
* Operating characteristics (synthetic, STAGE06_DECISION_DRY_RUN.md section 3):
  * GO probability:
    * kappa = 1: 89% at gains 0.025 and 100% at 0.03.
    * kappa = 2: 88% at 0.03 and 100% at 0.04.
  * STOP probability:
    * Zero null: 94-98%.
    * Gains of delta/2: 99% at kappa = 1, but only 2-3% at kappa = 2. In that case the verdict is REVISE; this is a
      known limitation.

## 8. Tier-1 and Tier-2 zero-noise reproduction

* **Tier-1 (unchanged frozen tolerance 1e-9 nats per item):** the Kalman path at sigma_v = 0, on the Stage 0.5 seeds,
  reproduces the stored Stage 0.5 per-item gains (matched - stability; the frontier was stability-only in every
  E-CONT cell). Coverage:
  * in-run: the first 500 items of every (replicate, r, n, h) cell;
  * qualification: all 3378 items.
* **Tier-2 (fresh seeds).**
  * Estimands: for each (r, h), the per-system mean of the zero-noise gain over n in {2, 3, 5, 10, 20} (the Stage 0.5
    context lengths available in both designs).
  * Comparison: each Stage 0.6 replicate (4000 systems) against the pooled Stage 0.5 systems (2 x 3378), giving
    2 x 6 = 12 comparisons.
  * Test statistic: z = (m06 - m05) / sqrt(se06^2 + se05^2), using the independent system-level SEs.
  * Cutoff: two-sided Bonferroni over 12 at alpha = 0.01, z_crit = 3.3415.
  * **Precision condition:** combined SE <= delta / (z_crit + z_0.80) = 0.02 / (3.3415 + 0.8416) = 0.00478, so a
    delta-sized discrepancy is detected with probability >= 0.8.
  * Outcomes:
    * FAIL if any |z| > z_crit;
    * else UNINFORMATIVE if any combined SE exceeds 0.00478. UNINFORMATIVE is never reported as a pass;
    * else PASS.
  * Only PASS satisfies the critical check (FAIL and UNINFORMATIVE give BLOCKED).
  * Planning, from the Stage 0.5 spreads: expected combined SE 0.0011-0.0018 in every cell, so Tier-2 is expected to
    be informative.
  * Both designs estimate the same quantity at q = 0 (identical model, prior, x_0 prior and predictive, MATH_STAGE06),
    so the criterion is satisfiable by correct code.

## 9. Critical checks (computed in the run; any failure gives BLOCKED)

| Check | Pass condition |
|---|---|
| integrity | distinct systems in each replicate; R1, R2, the selection split and the Stage 0.5 Tier-2 systems are pairwise disjoint (exact-equality tests of trajectories, innovations and observation noise) |
| tier1 | Tier-1 max abs difference <= 1e-9 |
| calibration | KS test of the population reference's PIT at n in {10, 40}, h in {1, 5}, for every (replicate, q, r) unit (96 tests); every p >= 1e-3 / 96 |
| numerics | node-doubling change of the per-item gain on the first 100 systems of every unit <= 2e-4 (the error budget, delta/100) |
| reproducibility | batch scores = canonical per-context scores (first 20 systems, n in {2, 21, 40}) to <= 1e-10 |
| tier2 | outcome PASS |

The bootstrap validity and Monte Carlo precision (section 6) and completeness (section 7) are also required.

## 10. Noise levels: finite-n information retention

* The positive q were set so that the prior-averaged asymptotic (Whittle) Fisher information about a, relative to zero
  noise at the same r, is 1/2, 1/4 and 1/8. This is DERIVED and numerically verified: STAGE06_NOISE_LEVEL_VERIFICATION.md.
* These levels are NOT exactly equivalent to 2x, 4x or 8x shorter contexts. Information retention is not an
  equivalent context length, it varies with n and r, and noise also changes the predictive variance.
* Finite-n retention R_avg = E_prior[I_q / I_0] (exact finite-n Fisher information), over n in L:

| q | r = 0.25: min-max (mean) | r = 1: min-max (mean) | r = 4: min-max (mean) |
|---|---|---|---|
| 0.755 | 0.474-0.494 (0.489) | 0.478-0.495 (0.490) | 0.537-0.581 (0.553) |
| 2.56 | 0.217-0.243 (0.236) | 0.221-0.243 (0.237) | 0.279-0.312 (0.292) |
| 6.5 | 0.094-0.118 (0.112) | 0.097-0.119 (0.113) | 0.142-0.159 (0.149) |

## 11. Integrity, environment and execution

* The runner (`python -m dynaicl.experiments.stage06_probe`) refuses on any of the following (V24 and the post-freeze
  refusal test):
  * a manifest SHA-256 different from the value supplied on the command line;
  * any changed or missing frozen file;
  * a config whose hash is not frozen for its mode;
  * seeds not equal to the seed manifest's allocation for the mode, or a seed shared between roles;
  * an environment different from `docs/STAGE06_ENVIRONMENT_MANIFEST.json` without a passing qualification report;
  * a checkpoint with a different schema, config, manifest, unit, array shape or dtype, or an invalid SHA-256;
  * a missing unit at analysis time.
* **Environment qualification.** `qualify` runs in the execution environment and writes its report outside the frozen
  set. It runs V4 (full Tier-1), V6 (quadrature convergence), V11 (parity null) and V13 (batch = per-context). The
  runner accepts the report only if all four pass, for this manifest, this config and this exact environment
  (python, implementation, numpy, scipy, pyyaml, system and machine are compared).
* **Checkpoints.** Each unit is written atomically: the arrays first, then the metadata carrying their SHA-256. An
  interrupted run resumes; it never recomputes or repairs a checksum failure silently.
* Workload estimate (DERIVED from measured per-system costs: primary pair 28 ms/system/(q, r) over all n and h;
  noise-naive family 81 ms/system/(q, r) at 5 n values):
  * primary units: 24 x about 121 s ~ 48 CPU-min;
  * noise-naive units: 24 x about 324 s ~ 130 CPU-min;
  * integrity, Tier-1 and analysis: a few minutes;
  * **total about 3 CPU-hours**, about 1.5-2.5 h wall on a 2-vCPU Colab runtime, about 25-30 min on 8 cores.
* Storage of per-item results at (system, q, h, r, n) resolution: primary units 24 x 7.49 MB (population and
  stability log scores as float64, PIT as float32), noise-naive units 24 x 3.84 MB, about 272 MB of checkpoints in
  total. If resources fail, the run stops and is reported; N is never reduced.

## 12. What was seen before the freeze

`docs/DISCLOSURE_LOG_STAGE06.md` entries 1-17. In summary:

* The Stage 0.5 results and spreads were known and used (planning only).
* Validation checks report errors, counts and p-values, never Stage 0.6 effect sizes.
* The selection-split audit compared context-only predictors only.
* The decision dry run used synthetic data.
* No confirmatory seed (64101, 64102, 64999) has been used, and no confirmatory output exists.
