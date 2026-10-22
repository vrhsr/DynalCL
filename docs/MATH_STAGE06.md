# MATH_STAGE06: noisy-observation model, Bayesian reference, information parity

Status: **Phase B: implemented and validated (not frozen).** Phase A decisions approved by the user: x_0 latent with a known
prior, the noise-aware stability-only comparator, the q levels (conditional; see STAGE06_NOISE_LEVEL_VERIFICATION.md), and n = transitions. Labels: DERIVED (derived here),
VERIFIED (inspected artifact, named passing test, or a recorded scratch check), ASSUMED, UNVERIFIED.
"Scratch-checked" means a one-off numerical check recorded in DISCLOSURE_LOG_STAGE06.md. It is not a substitute
for the Phase B tests.

## 1. What Stage 0.5 did (VERIFIED from code; see STAGE06_AUDIT.md section 2)

x_0 ~ N(0, (r sigma)^2), independent of a. x_t = a x_{t-1} + sigma eps_t. Context x_0..x_n (n transitions); target x_{n+h}.
Likelihood conditional on x_0. Population prior (E-CONT): a ~ N(0.4, 0.3^2) truncated to (-0.95, 0.95).
Stability-only prior: a ~ U(-0.999, 0.999). sigma = 1 (WLOG, MATH.md section 11); r in {0.25, 1, 4}.

## 2. Stage 0.6 model

### 2.1 Equations (proposed)

    a ~ pi(a)                                   (bounded support (-rho, rho), rho < 1)
    x_0 ~ N(0, (r sigma_w)^2)                   independent of a
    x_t = a x_{t-1} + sigma_w eps_t,  t >= 1    eps_t iid N(0, 1)
    y_t = x_t + sigma_v nu_t,         t >= 0    nu_t iid N(0, 1), independent of eps, a, x_0

* **Observed context:** y_0..y_n (n transitions, n + 1 observations; this is the Stage 0.5 indexing). The latent path is never observed.
* **Primary target:** y_{n+h} (observable). The latent target x_{n+h} is exploratory only.
* **Horizons:** h = 1 (y_{n+1}) and h = 5 (y_{n+5}), forecast from the information in y_0..y_n only.
* **Noise-level parameterisation:** q = sigma_v^2 / sigma_w^2. It is independent of a, which a ratio to the stationary
  variance sigma_w^2/(1 - a^2) would not be.
* **Known to every noise-aware predictor:** sigma_w, sigma_v and the initial-state sd r sigma_w. Unknown-noise variants are out of
  scope (exploratory only), because knowing the noise variance would otherwise be confounded with population knowledge.

### 2.2 Alternatives considered for the initial state and the noise placement

| Option | Description | Assessment |
|---|---|---|
| **A (proposed)** | x_0 latent with a known prior N(0, (r sigma_w)^2); every observation, including y_0, is noisy. | Uniform noise model. The population reference is the *exact* Bayes predictor of the generative process (up to quadrature). It recovers Stage 0.5 exactly at sigma_v = 0 (section 4). It requires r to be known: it is shared by both primary predictors (parity) and is not information about a. |
| B | x_0 observed noise-free; noise on t >= 1 only. | Keeps Stage 0.5's conditioning, but a single noiseless anchor is physically arbitrary and understates the effect of noise at short n. |
| C | Diffuse x_0 (P_0 -> infinity). | No need for r, but the reference would ignore the known initial-state distribution, so it is not Bayes-optimal for the generative process. The T1 theorem check would no longer apply. |
| D | Stationary x_0 ~ N(0, sigma_w^2/(1 - a^2)). | Couples x_0 to a, which breaks the Stage 0.5 invariant (MATH.md 1.2) and the sigma_v -> 0 nesting. Rejected. |

**What changes relative to Stage 0.5:** observations are noisy, and x_0 becomes latent (with its Stage 0.5 sampling
distribution now used as a prior). Unchanged: the dynamics, the priors, r, the n indexing and delta.

## 3. Likelihood given a: Kalman filter (DERIVED; ANALYTICALLY EXACT given a, evaluated in float64)

Initialise m_{0|-1} = 0 and P_{0|-1} = (r sigma_w)^2. For t = 0..n:

    predict (t >= 1):  m_{t|t-1} = a m_{t-1|t-1},   P_{t|t-1} = a^2 P_{t-1|t-1} + sigma_w^2
    innovation:         e_t = y_t - m_{t|t-1},       S_t = P_{t|t-1} + sigma_v^2
    update:             K_t = P_{t|t-1}/S_t,  m_{t|t} = m_{t|t-1} + K_t e_t,  P_{t|t} = P_{t|t-1} sigma_v^2 / S_t

    log p(y_{0:n} | a) = sum_{t=0}^{n} log N(e_t; 0, S_t)

Derivation: by the chain rule p(y_{0:n}) = prod_t p(y_t | y_{0:t-1}). Given a, (x, y) is jointly Gaussian, and by induction
x_t | y_{0:t-1} ~ N(m_{t|t-1}, P_{t|t-1}), so y_t | y_{0:t-1} ~ N(m_{t|t-1}, S_t). The update is Gaussian conditioning.
`P_{t|t} = P_{t|t-1} sigma_v^2 / S_t` is algebraically equal to (1 - K_t) P_{t|t-1}, and it avoids cancellation when K_t ≈ 1.
Scratch-checked against Cholesky conditioning on the joint covariance of y_{0:n} (agreement <= 2e-15, disclosure entry 2).

## 4. Zero-noise limit: recovering Stage 0.5 (DERIVED; scratch-checked)

At sigma_v = 0 with r > 0 and sigma_w > 0:
* t = 0: S_0 = (r sigma_w)^2 > 0, K_0 = 1, m_{0|0} = y_0 = x_0, P_{0|0} = 0.
* t >= 1: P_{t|t-1} = sigma_w^2, S_t = sigma_w^2, e_t = y_t - a y_{t-1}, K_t = 1, P_{t|t} = 0.

So log p(y_{0:n} | a) = log N(y_0; 0, (r sigma_w)^2) + sum_{t>=1} log N(y_t; a y_{t-1}, sigma_w^2). The first term does not depend on
a, so the posterior over a is **identical** to Stage 0.5's, and so is the predictive N(a^h y_n, sigma_w^2 c_h(a)).
**No singularity:** every S_t > 0 because r > 0 and sigma_w > 0. (r = 0 together with sigma_v = 0 would make S_0 = 0. r = 0 is not in the design.)
**Implementation (changed from the Phase A proposal, disclosure entry 4):** the Kalman path is used for **every** q,
including q = 0, where it is well-defined without any guard (every S_t > 0). The Stage 0.5 path is the independent check.
VERIFIED:
* V3: the Kalman path at q = 0 vs the Stage 0.5 path, 720 comparisons, worst error 1.3e-4 x tolerance.
* V4 (Tier-1): the stored Stage 0.5 per-item contrasts are reproduced on the Stage 0.5 seeds, 243,216 items, max |diff|
  **9.3e-15** (tolerance 1e-9, fixed before running).
* V5 (continuity): the measured log-log slopes are **1.999** for fixed data (DERIVED expectation O(sigma_v^2)) and
  **0.994** for consistent data (DERIVED expectation O(sigma_v)), over sigma_v in {1e-1..1e-4}.

## 5. Predictive given a (DERIVED; scratch-checked for h in {1, 5})

    x_{n+h} | y_{0:n}, a ~ N( a^h m_{n|n},  a^{2h} P_{n|n} + sigma_w^2 c_h(a) ),   c_h(a) = sum_{j<h} a^{2j}
    y_{n+h} | y_{0:n}, a ~ N( a^h m_{n|n},  a^{2h} P_{n|n} + sigma_w^2 c_h(a) + sigma_v^2 )

nu_{n+h} is independent of everything in the conditioning set, so sigma_v^2 adds exactly once. **Omitting sigma_v^2 is the
classic bug.** Scratch check: it changes the variance by exactly sigma_v^2. Phase B adds a mutation test for it.

## 6. Unknown a: the Bayesian reference (DERIVED status; NUMERICALLY APPROXIMATED with verified convergence)

    pi(a | y_{0:n}) ∝ pi(a) p(y_{0:n} | a),     p(y_{n+h} | y_{0:n}) = ∫ N(y_{n+h}; mu_h(a), V_h(a)) pi(a | y_{0:n}) da

**Not conjugate.** For sigma_v > 0, S_t and K_t depend on a non-linearly, so log p(y | a) is not quadratic in a. (At sigma_v = 0 it is,
which is what Stage 0.5's quadratic window used.) Stage 0.5's window construction therefore **does not apply**. Proposed scheme:
* composite Gauss-Legendre over a **shared node set** on (-0.999, 0.999) with cut points at +/-0.95: 64 panels per unit length,
  8 nodes per panel, **M = 1040 nodes** (`KalmanQuadratureSettings`). Every prior-support endpoint is a panel edge, so the
  population prior (zero outside +/-0.95) is integrated exactly over its own support, and **both primary predictors use
  identical nodes** (VERIFIED, V11);
* node masses ∝ GL weight x pi(a_i) x p(y_{0:n} | a_i), normalised by log-sum-exp;
* the Kalman filter is vectorised over nodes, and one pass over y_{0:N} serves all n (shared prefix). It is used only after an equivalence
  test against an independent per-n implementation.

**Reference status (Section 0 terminology):** Kalman given a is ANALYTICALLY EXACT. The reference over unknown a is
NUMERICALLY APPROXIMATED with verified convergence (method, M and measured error to be reported). It is **not** called an
exact Bayesian reference.

**Error budget (proposed):** |numerical error in the per-forecast paired gain| <= 2e-4 nats = delta/100. Justification: the decisions
compare intervals of half-width about 2.24 x SE against delta. With the planned SE around 0.004-0.005 (to be confirmed in precision
planning), 2e-4 is <= ~2% of an interval half-width and 1% of delta, so it cannot change a classification except for an estimate
within 2e-4 of a boundary. VERIFIED (V6): over 8 hard cases x h in {1, 5} (broad posteriors at q = 6.5, concentrated
posteriors at q = 0 / n = 40 / r = 4, prior-boundary cases at a = +/-0.949 and 0.998, large states at h = 5), the default
resolution differs from 4x nodes by at most **6e-15** in the paired gain and 4e-15 in the logpdf. That is 10 orders of
magnitude inside the budget (the check requires <= 2e-5). The independent oracle (V7: Cholesky likelihood +
scipy.quad) agrees within 1.6e-6 x tolerance.

## 7. Scale equivariance (DERIVED; to be TESTED in Phase B)

Under (x, y, sigma_w, sigma_v, r sigma_w) -> c (...), every Kalman mean and innovation scales by c and every variance by c^2. The
log-likelihood shifts by -(n+1) log c, which does not depend on a, so the posterior over a is unchanged, and p_c(c y_{n+h}) = p(y_{n+h}) / c.
Paired gains therefore depend only on (r, q, n, h, prior), and sigma_w = 1 is WLOG. The noise-naive baselines remain equivariant
(MATH.md section 11).

## 8. Identifiability and information (DERIVED)

y is ARMA(1,1): (1 - aB) y_t = sigma_w eps_t + sigma_v (1 - aB) nu_t. With known noise levels, a is identified, e.g. by
gamma_y(0) = sigma_w^2/(1 - a^2) + sigma_v^2 and gamma_y(1) = a sigma_w^2/(1 - a^2). Each observation carries less information as q
grows. The asymptotic per-observation Fisher information (Whittle) is

    I(a; q) = (1/4 pi) ∫_{-pi}^{pi} ( d/da log f(lam; a, q) )^2 dlam,    f ∝ 1/|1 - a e^{-i lam}|^2 + q   (sigma_w = 1).

It reduces to the AR(1) result 1/(1 - a^2) at q = 0 (scratch-checked at a in {0, 0.4, 0.8, 0.94}, exact to 6 decimals). Retention
I(a;q)/I(a;0) is strongly a-dependent. For example, at q = 1 it is 0.25 at a = 0, 0.39 at a = 0.4 and 0.95 at a = 0.94.

**Two effects compete, and Stage 0.6 measures the net:** (i) slower posterior concentration means the prior matters for longer,
which supports the hypothesis; (ii) the irreducible target variance sigma_v^2 compresses log-score differences, which works against it.
Neither direction is assumed.

**Proposed data-free rule for the noise levels:** choose q so that the *prior-averaged* retention E_pi[I(a;q)/I(a;0)] equals 1/2, 1/4
and 1/8. That means a context needs about 2x, 4x or 8x as many transitions for the same asymptotic information about a. Computed from
the population prior alone (no simulation): **q ≈ 0.755, 2.560, 6.500** (sigma_v/sigma_w ≈ 0.869, 1.600, 2.549). This is asymptotic
(n -> infinity). In Phase C it is complemented by a pilot-seed, prior-predictive check of the posterior-variance inflation for a at
n in {10, 20, 40}, with no effect estimates.

## 9. Information-parity table

| Predictor | Observation model known | Noise levels known | Initial-state information | Prior over a | Population information | Latent state | Future obs. |
|---|---|---|---|---|---|---|---|
| Population-aware reference (noise-aware) | yes (y = x + noise) | sigma_w, sigma_v | x_0 ~ N(0, (r sigma_w)^2) | TN(0.4, 0.3^2) on (-0.95, 0.95) | **yes (the prior)** | none | none |
| **Primary comparator:** noise-aware stability-only Bayes | yes | sigma_w, sigma_v | x_0 ~ N(0, (r sigma_w)^2) | U(-0.999, 0.999) | none (generic stability only) | none | none |
| Noise-naive flat-prior / stability Bayes (Stage 0.5) | no (treats y as x) | sigma = sigma_w only | conditions on y_0 as if exact | flat / U(-0.999, 0.999) | none | none | none |
| Noise-naive OLS (Gaussian, Student-t), kernel (3 schemes), persistence | no | estimated from y | conditions on y_0 | none | none | none | none |
| Known-a Kalman oracle (tests only) | yes | yes | yes | point mass at the true a | n/a (oracle) | none | none |

The primary pair differs **only** in the prior over a. Noise-naive members are secondary, non-decisional baselines, and are
misspecified by design for q > 0 (errors-in-variables bias in a_hat). At q = 0 they coincide with Stage 0.5.

## 10. Theorem-level checks (violations are bugs, up to numerical or MC error)

* Zero-noise recovery (section 4), independent numerical agreement (Kalman vs Cholesky; production vs independent integration; MC),
  the analytic special cases, information-access isolation, determinism, and surfacing of failures.
* Calibration of the population-aware reference, when systems, x_0 and noise are drawn as in section 2.1.
* Non-negative expected gain of the population-aware reference over **every** other predictor in that setting (Bayes optimality in
  expected log score; MATH.md 8.1 extends, since the reference is the posterior predictive of the generative model).

## 11. Open decisions for the user (also in STAGE06_AUDIT.md section 6)

Initial-state option A; the primary-comparator set; the q levels (data-free rule above); n indexing; git for the freeze.

## 12. Stability-only equivalence audit (Phase B; VERIFIED)

* **Intended prior** (as used in Stage 0.5): a ~ U(-0.999, 0.999), density 1/1.998 on [-0.999, 0.999] (boundary included,
  measure zero), zero outside. `StableCoefficientPrior(rho=0.999, shape="uniform")`; known sigma.
* **The Stage 0.5 implementation** (`baselines/stability_prior.StabilityPriorBayesPredictor`) conditions on x_0 = y_0 and uses
  the noise-free AR(1) likelihood with sigma = sigma_w. **Under the noisy model it is NOT the intended predictor for q > 0**:
  it ignores sigma_v in the likelihood and in the target variance. It is equivalent only at q = 0 (section 4). It is
  therefore kept solely as a noise-naive *secondary* baseline. It was not reused for the primary comparator.
* **The noise-aware comparator** is `kalman_quadrature.noise_aware_stability_predictor`: the same class, Kalman likelihood,
  noise model, x_0 prior and nodes as the reference, with only the prior changed to U(-0.999, 0.999).
* **Parity null test (V11):** the population-aware factory given the stability prior reproduces the comparator
  **bitwise** for every n = 2..40, h in {1, 5}, all four q and all three r (936 per-context comparisons, plus the batch
  path). Shared code, nodes and convergence criterion.
* **Comparator correctness (V7):** it matches the independent oracle (Cholesky + adaptive quad) with the stability prior.
* A noise-naive predictor mislabelled as noise-aware is detected (mutation test; V7 and V11 fail).

