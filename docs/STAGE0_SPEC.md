# Original task specification (verbatim, as given by the user on 2026-10-09)

Kept so that any session can see the exact requirements Stage 0 was built against. Where the
implementation departs from it, see docs/MATH.md section 10 (corrections) and docs/DECISIONS.md.

---

# STAGE 0: TRUSTWORTHY REFERENCE-PREDICTOR FOUNDATION (CPU ONLY, NO TRAINING)

## 0. Role and working rules

You are my senior research software engineer and experimental-ML collaborator. Your job is to build and validate the reference machinery that every later experiment will treat as ground truth. A wrong reference silently invalidates the whole project, so correctness matters more than speed or feature count.

1. **Plan first.** Inspect the workspace, write PLAN.md (assumptions, file list, risks), print it, then proceed without waiting unless you hit a blocking ambiguity. If you do, state it and choose the most conservative option.
2. **Report only what you ran.** Paste real test output. Never claim a test passed that you did not run. Never weaken, skip, or delete a test to make it pass. When a test fails, decide whether the reference code, the test, or the math is wrong, and say which.
3. **Label every claim** in docs and the final report as DERIVED (derivation in docs/MATH.md), TESTED (name the test), ASSUMED, or UNVERIFIED.
4. **No fabricated results or literature.** No numerical tolerance or go/no-go threshold without a stated justification (MC standard error, quadrature convergence, or floating-point analysis). All thresholds are hypotheses.
5. **Preserve existing work.** Add dependencies only with a reason. Default stack: numpy, scipy, pytest, pyyaml, all in float64.
6. **Naming.** Use meaningful, purpose-specific class and function names (e.g. `ConjugateAr1Posterior`, `FiniteLibraryPredictor`, `MatchedBayesReference`, `EvaluationCondition`, never `Model1` or `Helper`).
7. **Terminology (strict).**
   - "Analytically exact" is only for closed-form results (still evaluated in float64, so subject to rounding).
   - "Numerically approximated with verified convergence" is for quadrature, grids, and Monte Carlo. State the method, resolution / node count / sample size, and the measured error.
   - Never describe a numerical calculation as mathematically exact. Never use the phrase "numerically exact."
8. **Out of scope (do not start):** the ~2,000-model sweep, chaotic-system or particle-filter posteriors, neural/transformer pretraining, cross-model validation, any claim of novelty or publishability.

## 1. Task 1: inspect the workspace

Review the repo, Python version, installed packages, existing code, and tests. Reuse and extend existing structure. Record findings and assumptions in PLAN.md.

## 2. Task 2: mathematical specification

Treat this section as a spec from me to be verified, not as truth. Re-derive every formula in docs/MATH.md and let the independent tests in Section 5 decide. If a formula is wrong, fix it and document the correction.

### 2.1 Data-generating process (scalar AR(1))

x_t = a * x_{t-1} + sigma * eps_t, eps_t ~ N(0,1) iid, t = 1..T. The initial state x_0 is fixed per trajectory and independent of a. The context is x_0..x_n (n transitions) and the target is x_{n+h}, h >= 1.

All likelihoods are conditional on x_0. The exact stationary likelihood has an a-dependent initial-state term that breaks conjugacy, so state this assumption explicitly in the docs.

### 2.2 Prior regimes

- **P-GAUSS:** a ~ N(mu0, tau0^2), sigma known. This prior is untruncated, so P(|a| >= 1) > 0 and some simulated trajectories are explosive. Compute and report that probability. Choose tau0 to keep it small and state the choice. Role: closed-form anchor.
- **P-NIG:** a | sigma^2 ~ N(mu0, sigma^2 / lambda0), sigma^2 ~ InverseGamma(alpha0, beta0). Role: closed-form one-step predictive with unknown noise.
- **P-STABLE:** a ~ truncated normal or uniform on (-rho, rho) with rho < 1, sigma known. This prior is not conjugate. Role: primary prior for the scientific experiments, handled by 1-D quadrature.

### 2.3 Evaluation conditions and matched references

Each evaluation condition defines a data-generating distribution D (a distribution over systems plus the likelihood). Implement at least:

- **E-CONT (held-out systems):** system parameters are drawn fresh from the continuous prior. The matched reference is the continuous-prior Bayes predictor. Assert that evaluation parameters are disjoint from library atoms.
- **E-LIB (in-library systems):** system parameters are drawn from the library atoms using the library weights, with fresh noise and trajectories. The matched reference is the finite-library posterior. The continuous-prior predictor is evaluated here as an ordinary comparison predictor and has no optimality guarantee under this condition.

**Prior-matching rule.** The matched Bayes reference for a condition must use exactly that condition's prior and likelihood. Assert this in code. All other predictors may use different information or assumptions by design (the finite library uses a discrete set, context-only estimators use no population information). Never force prior equality across predictors. Document each predictor's assumptions. A predictor's mismatch with a condition is a quantity to measure, not an error.

The evaluation harness must select the matched reference by condition and must refuse to compute optimality diagnostics against an unmatched reference.

### 2.4 Predictors and exactness status

Notation: S_xx = sum_{t=1..n} x_{t-1}^2, S_xy = sum x_{t-1} x_t, S_yy = sum x_t^2.

| Predictor | Prior | Horizon | Status |
|---|---|---|---|
| Conjugate Gaussian | P-GAUSS | h=1 | ANALYTICALLY EXACT. Posterior N(m_n, v_n) with 1/v_n = 1/tau0^2 + S_xx/sigma^2 and m_n = v_n (mu0/tau0^2 + S_xy/sigma^2). Predictive N(m_n x_n, sigma^2 + v_n x_n^2). |
| Conjugate Gaussian | P-GAUSS | h>1 | NUMERICALLY APPROXIMATED with verified convergence (1-D quadrature). Given a, x_{n+h} ~ N(a^h x_n, sigma^2 * sum_{j<h} a^{2j}); mixing over the posterior of a is non-Gaussian. Use the sum form, not (1-a^{2h})/(1-a^2), for stability near \|a\|=1. |
| Normal-inverse-gamma | P-NIG | h=1 | ANALYTICALLY EXACT. lambda_n = lambda0 + S_xx, mu_n = (lambda0 mu0 + S_xy)/lambda_n, alpha_n = alpha0 + n/2, beta_n = beta0 + 0.5 (S_yy + lambda0 mu0^2 - lambda_n mu_n^2). Predictive is Student-t with 2 alpha_n dof, location mu_n x_n, scale^2 = (beta_n/alpha_n)(1 + x_n^2/lambda_n). |
| Quadrature posterior | P-STABLE | any h | NUMERICALLY APPROXIMATED with verified convergence. Report node count and convergence error. |
| Finite library (K atoms, weights pi_k) | discrete | any h | ANALYTICALLY EXACT given the library. Posterior weights proportional to pi_k * prod_t N(x_t; a_k x_{t-1}, sigma_k^2), computed in log space. The h-step predictive is a mixture of N(a_k^h x_n, sigma_k^2 sum_{j<h} a_k^{2j}). |
| Brute-force grid posterior | any | any | NUMERICALLY APPROXIMATED, test-only independent check. Uses the raw likelihood and no conjugacy formulas. |

### 2.5 Context-only baselines (must not use the population or prior)

"Context-only" means a function of the context plus hyperparameters fixed in the config without looking at the training population or evaluation data. Implement:

- **Flat-prior Bayes** (known sigma): posterior N(a_hat, sigma^2/S_xx), a_hat = S_xy/S_xx, one-step predictive N(a_hat x_n, sigma^2 (1 + x_n^2/S_xx)). Handle S_xx = 0 and n < 2 explicitly.
- **OLS plug-in:** a_hat, sigma_hat^2 = RSS/(n-1), Gaussian predictive with a Student-t variant. Flag it as non-Bayesian and potentially overconfident at short n.
- **Kernel analog** (the parroting-flavoured baseline): Nadaraya-Watson regression on context pairs, with residual variance estimated inside the context. Bandwidth selection must respect time dependence:
  - Default: rolling-origin (forward-chaining) validation inside the context. Each validation point is predicted using only earlier context data. Set a minimum initial training window in the config. Below it, fall back to a documented plug-in bandwidth rule.
  - Comparison schemes: blocked cross-validation with a gap of at least h between training and validation blocks, and ordinary leave-one-out.
  - Ordinary leave-one-out is for comparison only, never the default, because adjacent pairs share observations and are dependent.
  - Report the selected bandwidths and downstream scores under each scheme. Do not assume which is optimistic. Measure the difference.
  - Validation uses only data inside the context. Short contexts give few validation points, so state this limitation.
- **Persistence:** point forecast x_n, with predictive variance estimated from context increments so it can be scored.

"Strongest context-only estimator" is not canonical. Report every member. Define the context-only frontier as the best member per (n, h, metric), selected on a separate simulated selection set disjoint from the evaluation set, and document it as a design choice.

### 2.6 Predictive interface

Every predictor returns a Predictive object (Gaussian, StudentT, GaussianMixture, QuadratureMixture, or empirical samples) exposing mean, variance, logpdf, cdf, quantile, sample. Point-only predictors, including any future MSE-trained neural model, are wrapped as PointPredictor and scored only with point metrics against the matched reference's posterior mean. They are never scored with log score or CRPS.

## 3. Task 3: information-access contract and leakage control

| Predictor | May access | Must not access |
|---|---|---|
| Matched Bayes reference | context, the evaluation condition's true prior and likelihood | true a, future values |
| Continuous-prior Bayes (as comparison) | context, continuous prior | true a, future values, library |
| Finite library | context, library atoms and weights built from the training stream only | evaluation systems under E-CONT |
| Context-only | context, config-fixed hyperparameters | population, prior, evaluation data |

Enforce this in code, not just in docs:
- Predictors accept only an immutable `ContextWindow` of values. Ground truth (a, sigma, seeds, future) lives in a separate `GroundTruth` object the evaluator keeps private.
- Use `numpy.random.SeedSequence` spawning with named, independent streams (library_systems, selection_systems, eval_systems, per-role noise, monte_carlo). Adding draws to one stream must not shift another.
- Train, selection, and evaluation splits are immutable objects with role tags. Under E-CONT, assert disjointness from library systems (parameter hashes and minimum distance). Under E-LIB, parameter overlap with the library is intentional by design. Leakage tests must distinguish intentional parameter overlap from unintended trajectory, noise, or target overlap, and assert the latter never occurs in either condition.
- Normalisation statistics come from the context only, never from the full trajectory.

## 4. Scoring rules

- Primary: log predictive density (strictly proper).
- Also: CRPS (closed form for Gaussian, numerical for Student-t and mixtures, with the numerical version validated against the Gaussian closed form), central-interval coverage, PIT.
- MSE only for point forecasts, against the target (or the matched reference's posterior mean for point-only models).
- Compare predictors with paired differences on identical (system, context, target) draws, with standard errors. Do not compare separately computed means. State the SE method (analytic or bootstrap).
- Theory: under condition D, the matched Bayes reference maximises expected log score among all predictors that are functions of the context, and E[log p_D - log q] = E[KL] >= 0. This holds only for the matched reference under its own condition.

## 5. Task 4: validation suite (pytest, fixed seeds)

Each statistical test must state its tolerance derivation. Control multiplicity (e.g. Bonferroni) so tests are not flaky.

- **A. Algebra vs independent check.** Brute-force grid posterior from the raw likelihood versus the closed-form posterior mean and variance, predictive logpdf and cdf, with grid-refinement convergence. Quadrature convergence in node count. Closed form versus quadrature at h=1. P-NIG versus 2-D numerical integration.
- **B. Independent Monte Carlo.** Posterior sampling followed by simulation, compared on predictive moments and quantiles with MC-SE tolerances. Importance-sampling check of the finite-library posterior.
- **C. Structural identities** (violations are bugs).
  - Sequential and batch updating agree.
  - n=0 reduces to the prior predictive.
  - A K=1 library equals a single known-system predictor.
  - Chain rule: the h=2 predictive equals marginalising the sequential one-step predictive over x_{n+1}, checked by 1-D quadrature.
- **D. Known-parameter behaviour.** Known (a, sigma) gives the expected N(a^h x_n, ...). Posterior variance shrinks like 1/n. Posterior mean error shrinks roughly like n^{-1/2}.
- **E. Calibration of the matched reference.** For each evaluation condition, simulation-based calibration (rank uniformity of the true a among posterior draws), PIT uniformity of x_{n+h}, and coverage of 50/80/95% intervals with binomial bands, across several n and h. This is a pass condition for the matched reference only. For every other predictor, calibration is a reported measurement, not a pass/fail test.
- **F. Optimality of the matched reference.** Per condition, the matched reference's mean log score is at least every other predictor's, within paired SE.
- **G. Negative controls (mutation tests).** Inject each of the following and assert at least one test detects it:
  - wrong prior variance in the matched reference
  - off-by-one in likelihood indices
  - future value leaked into the context
  - harness comparing against an unmatched reference
  Report which tests caught which mutation.
- **H. Numerics.** n = 0, 1, 2. S_xx = 0. Very small and large sigma. |a| near 1 and explosive. Large |x_n|. h up to ~50 with |a| near 1. Log-sum-exp underflow with long contexts and distant atoms. No NaN or inf anywhere. Reject or warn on non-float64 input.
- **I. Reproducibility.** Same config and seed give bitwise-identical outputs. A different seed gives different outputs. Changing one named stream leaves the others unchanged.
- **J. Leakage.** Perturbing the target or future values leaves all predictions unchanged. The library is independent of the evaluation stream seed. Disjointness and intentional-overlap checks as in Section 3. Kernel bandwidth selection never reads data after the validation point (rolling-origin) or inside the gap (blocked).
- **K. Kernel validation schemes.** Run rolling-origin, blocked, and leave-one-out selection on the same simulated contexts and report the differences in selected bandwidth and held-out score, with SEs.

Do not use any reference output as ground truth for later work until A, B, E, and G are green.

## 6. Task 5: reproducible scaffold

Adapt to the existing layout. Suggested structure:
- `systems/` (AR(1) simulator, populations, evaluation conditions and splits)
- `references/` (conjugate, quadrature, finite library, matched reference selection, Predictive classes)
- `baselines/` (context-only predictors)
- `metrics/` (scoring, calibration)
- `experiments/` (separability map)
- `config/` (schema and YAML files)
- `provenance` module
- `tests/`
- `docs/MATH.md`, `docs/DECISIONS.md`, `docs/RISKS.md`

Configuration lives in YAML validated against a schema. No experimental settings are hard-coded. Every run writes `runs/<run_id>/` containing config, config hash, git commit and dirty flag, package versions, platform, per-stream seeds, timestamps, results (CSV or JSON), and output checksums.

README: setup, mathematical assumptions, the exactness table with the Section 0 terminology, test commands, the minimal experiment command, and how to add a new predictor through the Predictive interface.

## 7. Minimal experiment: reference separability map

**Purpose:** find out whether the reference predictors are statistically distinguishable at all in the regimes later models will be tested in. If their expected score gaps sit within paired MC error everywhere, no later model can be classified as using one strategy rather than another.

**Design:**
- P-STABLE prior.
- A library of K unique systems drawn iid from that prior with uniform weights, for a small grid of K.
- A small grid of context lengths n, horizons h, and noise levels sigma.
- Both evaluation conditions, E-CONT and E-LIB.
- Predictors compared: matched reference, continuous-prior Bayes, finite-library posterior, and the context-only family and its frontier.
- Outputs, per condition: paired mean log-score differences with SEs, plus coverage and PIT for each predictor.

**Candidate metric (a hypothesis to justify or reject, not a standard):** population-knowledge gain G = (S_model - S_ctx) / (S_matched - S_ctx), normalised between the context-only frontier and the matched reference of the condition. Report where the denominator is near zero and G is ill-conditioned.

**Theorem-level checks (violations indicate a bug, up to MC error):**
- T1. The matched reference is at least as good as every other predictor in expected log score under its own condition.
- T2. The matched reference is calibrated under its own condition.
- T3. The identities in Section 5C hold.

**Diagnostic hypotheses (measure; do not treat as pass/fail):**
- H1. The matched reference's advantage over flat-prior Bayes shrinks as n grows, as posterior concentration suggests, with rate depending on prior width, sigma, and state scale.
- H2. A small-K library is overconfident (coverage below nominal) on E-CONT systems.
- H3. On E-CONT, the library predictor approaches continuous-prior Bayes as K grows at fixed n.
- H4. On E-LIB, the library predictor's advantage over continuous-prior Bayes changes with n.

For each hypothesis, report observed versus expected. If an effect is absent, first check whether its absence is theoretically expected under the chosen settings (for example, small state magnitudes, weak prior, or very large n) before suspecting a bug, and document the explanation. Do not tune the design to make a hypothesis come true.

**Pre-register first:** write docs/PREREG_separability.md with grids, metrics, replication counts (justified from a pilot variance estimate), and what would count as "references indistinguishable." Then run. It should finish in minutes to tens of minutes on CPU.

## 8. Optional extensions (only after Section 5 is green; otherwise list as future work)

- AR(1) with observation noise: Kalman-filter likelihood with a grid over a. Numerically approximated with verified convergence, not conjugate.
- VAR(1) with a matrix-normal-inverse-Wishart prior.

## 9. Final report (in this order)

1. Files created or changed.
2. Equations and assumptions implemented, pointing to docs/MATH.md, including any corrections to Section 2.
3. Exactness table using the Section 0 terminology, with the conditions for each entry.
4. Tests run with actual output, pass/fail counts, failures, and mutation-test detection results. Report theorem-level results separately from diagnostic-hypothesis outcomes (observed vs expected, with explanation).
5. Remaining mathematical and implementation risks, including anything you could not verify.
6. The smallest experiment to run next.
7. Criteria for proceeding to Stage 1, revising the design, or stopping. Each is a hypothesis with a justification.
   - **PROCEED** candidates: all validation green, including mutation detection. References separable (paired gap clearly above SE) in at least one regime of interest. Theorem-level checks pass.
   - **REVISE** candidates: references indistinguishable in every regime of interest (change prior, noise, or horizon), or G ill-conditioned (change the metric).
   - **STOP / redesign** candidates: the Bayesian reference cannot be validated independently, or the matched reference's advantage over the best context-only estimator is negligible in every realistic regime of this family.
8. A closing statement that passing software tests establishes neither novelty nor publishability.
