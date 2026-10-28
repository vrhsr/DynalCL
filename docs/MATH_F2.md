# MATH_F2: bivariate VAR(1) with a stability-truncated matrix-normal-inverse-Wishart prior (family F2; references only)

Status: DRAFT (2026-10-27), written before any F2 reference result. Labels as in docs/MATH.md: DERIVED (shown here),
ASSUMED (a design choice), TESTED (named check in section 9), UNVERIFIED. Notation: d = 2; vectors are columns.

## 1. Data-generating process
x_t = A x_{t-1} + e_t, e_t iid N(0, Sigma), t = 1..T, x_t in R^2; x_0 ~ N(0, r^2 I_2) **independent of (A, Sigma)**, so
(as MATH 1.1) p(x_0) drops out of every posterior and the likelihood is conditional on x_0. Regression form for a context
with n transitions: Y = X B + E with Y = [x_1 .. x_n]^T (n x d), X = [x_0 .. x_{n-1}]^T (n x d), B = A^T, rows of E iid
N(0, Sigma). Contexts are cut only by the frozen harness conventions (start at x_0, never burn in; CLAUDE.md section 4),
applied row-wise to the d-dimensional trajectory (section 8).

## 2. Priors (ASSUMED design, fixed before any result)
MNIW(B0, V0, nu0, Psi0): Sigma ~ IW(nu0, Psi0) (density proportional to |Sigma|^{-(nu0+d+1)/2} exp(-tr(Psi0 Sigma^{-1})/2)),
and B | Sigma ~ MN(B0, V0, Sigma), i.e. vec(B) | Sigma ~ N(vec(B0), Sigma kron V0) (V0: d x d covariance over predictors).
Stability truncation at radius c: p_c(B, Sigma) proportional to MNIW(B, Sigma) 1[rho(B) < c], rho = spectral radius
(rho(B) = rho(A)).

* **Population P_F2:** B0 = 0.4 I, V0 = 0.09 I, nu0 = 7, Psi0 = 4 I, truncated at c = 0.95. Chosen to mirror F1: each
  marginal Sigma_ii ~ IG((nu0 - d + 1)/2, Psi0_ii / 2) = IG(3, 2) (mean 1, variance 1, as F1's sigma^2 prior), and at
  Sigma = I each coefficient has prior mean 0.4 (diagonal) or 0 (off-diagonal) and sd 0.3 before truncation (as F1's a).
  Unlike F1, A and Sigma are coupled (Var(B | Sigma) scales with Sigma); this is what makes the prior conjugate.
* **Context-only C_F2:** B0 = 0, V0 = 100 I, nu0 = 1.5, Psi0 = 0.01 I, truncated at c = 0.999 (stability only).
  nu0 = 1.5 > d - 1 keeps the IW proper; each Sigma_ii ~ IG(0.25, 0.005) is very heavy-tailed on the log scale (computed
  with scipy before freezing the choice; section 9, F2-V0): the intent, as for F1's log-uniform scale, is a reference that
  knows stability but little about the population's coefficients or noise level. A conjugate prior cannot be fully
  scale-free; this residual scale information is a stated limitation.
* **Library L_K:** K atoms (A_k, Sigma_k) drawn iid from P_F2 (truncated), uniform weights.

## 3. Conjugate posterior (DERIVED; standard, e.g. the Bayesian multivariate regression algebra)
Given a context, with S_xx = X^T X, S_xy = X^T Y, S_yy = Y^T Y:
  V_n = (V0^{-1} + S_xx)^{-1},  B_n = V_n (V0^{-1} B0 + S_xy),  nu_n = nu0 + n,
  Psi_n = Psi0 + S_yy + B0^T V0^{-1} B0 - B_n^T V_n^{-1} B_n.
Psi_n is computed from residual form to avoid cancellation:
  Psi_n = Psi0 + (Y - X B_n)^T (Y - X B_n) + (B_n - B0)^T V0^{-1} (B_n - B0)
(expand both forms; they agree by the normal equations V_n^{-1} B_n = V0^{-1} B0 + S_xy). Untruncated posterior:
Sigma | D ~ IW(nu_n, Psi_n), B | Sigma, D ~ MN(B_n, V_n, Sigma). Marginally B | D is matrix-t.
The truncated posterior is p_c(B, Sigma | D) proportional to MNIW_n(B, Sigma) 1[rho(B) < c]: the indicator does not depend
on the data, so truncation commutes with conditioning (prior x likelihood x indicator). Its normaliser
P_n(c) = Pr(rho(B) < c | D, untruncated) is not available in closed form.

## 4. One-step predictive (h = 1)
**Untruncated, closed form (DERIVED).** y = x_{n+1} | D ~ t_{nu_n - d + 1}(B_n^T x_n, Psi_n (1 + x_n^T V_n x_n) / (nu_n - d + 1)),
a d-variate Student-t with nu_n - d + 1 degrees of freedom (marginalise B | Sigma, then Sigma ~ IW).
**Given B, integrating Sigma (DERIVED; Rao-Blackwellisation).** Sigma | B, D ~ IW(nu_n + d, Psi_n + (B - B_n)^T V_n^{-1} (B - B_n))
(the matrix-normal term adds d to the degrees of freedom and its quadratic form to the scale), hence
  p(y | B, D) = t_{nu_n + 1}(B^T x_n, Psi_B / (nu_n + 1)),  Psi_B = Psi_n + (B - B_n)^T V_n^{-1} (B - B_n)
(nu_n + d - d + 1 = nu_n + 1 degrees of freedom). TESTED (F2-V3) against direct integration of the Gaussian over sampled
Sigma.
**Truncated (DERIVED).** p_c(y | D) = E[1[rho(B) < c] p(y | B, D)] / E[1[rho(B) < c]], expectations under the untruncated
matrix-t posterior of B (the Sigma-integral above is exact given B; only B is sampled).

## 5. Monte Carlo estimator, its error, and the effective sample size (DERIVED)
Draw B_1..B_J iid from the untruncated posterior of B (Sigma_j ~ IW(nu_n, Psi_n), then B_j ~ MN(B_n, V_n, Sigma_j); the
Sigma_j are discarded), s_j = 1[rho(B_j) < c], f_j(y) = p(y | B_j, D).
* **Estimator R (ratio).** p_R = sum_j s_j f_j / sum_j s_j. Because the weights are 0/1, the accepted draws are iid from the
  truncated posterior, so p_R is a plain mean over the J_acc accepted draws: unbiased given J_acc >= 1, with
  SE(p_R) = sd_acc(f) / sqrt(J_acc). The self-normalised effective sample size (sum s)^2 / sum s^2 equals J_acc exactly.
* **Estimator C (complement control variate).** With the closed-form untruncated predictive p_U(y) of section 4,
  E[s f] = p_U(y) - E[(1 - s) f] and E[s] = 1 - E[1 - s], so p_C = (p_U - mean_j((1 - s_j) f_j)) / (1 - mean_j(1 - s_j)).
  It is exact when no draw is unstable and has small variance when the rejected fraction q = 1 - J_acc / J is small.
  Delta method: Var(p_C) ~ Var((1 - s)(f - p_c)) / (J (1 - q)^2).
* **Rule (ASSUMED, fixed before results):** use C when q <= 0.5 and R otherwise (a rule on q alone, not on the estimated
  variances, so the choice adds no selection bias). Both estimators are consistent.
* **Error on the log score (DERIVED, delta method):** SE(log p_hat) ~ SE(p_hat) / p_hat, estimated per item from the same
  draws. **Target: SE(log p_hat) <= delta / 100 = 2e-4 nats per item** (task B2: two orders of magnitude below delta, so that
  per-item Monte Carlo noise is negligible against the 0.02-nat decision margin even before averaging over items; a cell mean
  over N items then carries Monte Carlo error <= 2e-4 / sqrt(N)). Draws are added in batches until the target holds or a cap J_max is reached; items that hit the cap are counted
  and reported, never silently kept (section 9, F2-V5). Common random numbers: the same draws serve every y of one context.
* **Bias:** log p_hat is biased by about -Var(p_hat) / (2 p_hat^2) = -SE^2/2 <= 2e-8 nats at the target (DERIVED; second-order
  delta method), negligible.
* **Diagnostic:** per item, J, J_acc, q, the estimator used, SE(log p_hat); summary quantiles per cell. A cell where the
  rejection fraction under the context-only posterior approaches 1 (explosive-looking contexts) is flagged.

## 5b. Interval Rao-Blackwell estimator I (DERIVED; the default for h = 1, added 2026-10-28 after timing)
**Why.** Timing (disclosure S30) showed that estimators R and C cannot meet the 2e-4 target for the context-only reference
at n <= 5 within 2^21 draws: the untruncated posterior puts up to 99% of its mass on unstable B, and the 0/1 indicator
dominates the variance. Estimator I removes the indicator and Sigma from the Monte Carlo.
**Stable interval.** For a real 2 x 2 matrix, both eigenvalues have modulus < c iff |det| < c^2 and |tr| < c + det / c (Jury
conditions, scaled by c). With b12, b21, b22 fixed, det = b22 b11 - b12 b21 and tr = b11 + b22 are linear in b11, so each
condition is a half-line in b11 and the stable set is an interval (L, U) (possibly empty). TESTED: F2-V5b (equality with the
spectral-radius test on a grid).
**Conditional of b11 (Sigma integrated).** B | D is matrix-t: p(B | D) proportional to |Psi_n + D^T W D|^{-(nu_n + d)/2},
D = B - B_n, W = V_n^{-1} (integrate Sigma ~ IW out of the matrix normal). With only D_00 = e free, the entries of D^T W D are
quadratic (Q_00), linear (Q_01) or constant (Q_11) in e, so the determinant is alpha e^2 + beta e + gamma and
e | rest ~ t_{nu'}(-beta / (2 alpha), (gamma - beta^2 / (4 alpha)) / (alpha nu')), nu' = nu_n + d - 1. (For d = 1: t_{nu_n}
with scale^2 Psi_n / (W nu_n).)
**Estimator.** With draws of (b12, b21, b22) from the untruncated posterior (b11 and Sigma of the draw are discarded):
a_j = P(b11 in (L, U) | rest) (Student-t CDF, closed form) and g_j(y) = integral over (L, U) of p(y | B, D) p(b11 | rest)
d b11, with p(y | B, D) the Student-t of section 4. Then p_c(y | D) = E[g] / E[a] (both expectations under the untruncated
posterior), estimated by sum_j g_j / sum_j a_j, a ratio of means of smooth draw-wise quantities; SE of the log by the delta
method for a ratio of means, Var = (Var(g) - 2 p Cov(g, a) + p^2 Var(a)) / (J mean(a)^2).
**Inner integral.** b11 = m* + s* tan(theta), m*, s* the location and scale of the product of p(b11 | rest) and a Gaussian
approximation of the y-likelihood in b11 (through y_0 | y_1 at b11 = location); theta over (atan((L - m*)/s*),
atan((U - m*)/s*)); 32-point Gauss-Legendre. The integrand is bounded and decays like cos(theta)^nu' at the ends.
NUMERICALLY APPROXIMATED with verified convergence: in the d = 1 case the estimator is deterministic and matches nested
scipy quadrature to 1e-14 at 32 nodes (16 nodes: about 5e-7); node doubling 32 -> 64 <= 1e-9 relative (F2-V5d).
Two earlier variants were rejected on measured evidence (disclosure S30): sampling Sigma and integrating b11 against a
Gaussian (closed form, but the Sigma noise needed > 4M draws per item for population contexts that estimator C handled with
25k), and Gauss-Legendre in the conditional CDF variable (algebraic convergence: 2.5e-6 nats error at 128 nodes).

## 6. h-step predictive (h > 1)
Given (B, Sigma), x_{n+h} | D ~ N(A^h x_n, sum_{k=0}^{h-1} A^k Sigma (A^k)^T) (DERIVED by iterating the recursion). The sum
is linear in Sigma but not of the form C Sigma C^T, so Sigma cannot be integrated to a Student-t: for h > 1 both B and Sigma
are sampled (no Rao-Blackwellisation, no closed-form control variate; estimator R with the same error and ESS formulas,
J_acc counted the same way). Whether the map uses h > 1 is decided in its spec after timing (docs/STAGE2_F2_MAP_SPEC.md).

## 7. Library references (DERIVED; ANALYTICALLY EXACT given the atoms)
log w_k = log pi_k + sum_{t=1}^n log N(x_t; A_k x_{t-1}, Sigma_k) (normalised by log-sum-exp); predictive
sum_k w_k N(y; A_k^h x_n, sum_{j<h} A_k^j Sigma_k (A_k^j)^T). Atoms are drawn from P_F2 by sampling the untruncated MNIW prior
and rejecting rho >= 0.95 (exact sampling from the truncated prior).

## 8. Spectral radius and stability (DERIVED)
For a real 2 x 2 matrix with trace tau and determinant delta, the eigenvalues are tau/2 +/- sqrt(tau^2/4 - delta); if the
discriminant is negative, |lambda| = sqrt(delta); otherwise rho = max(|tau/2 + sqrt(D)|, |tau/2 - sqrt(D)|). Computed
batch-wise in closed form and TESTED against numpy.linalg.eigvals (F2-V1). The simulator draws (A, Sigma) per system, x_0, and
Gaussian innovations through NamedStreams (Stage-0 conventions: one stream per item, float64).

## 9. Validation plan (Stage 0 style; before any network)
F2-V0 prior sanity: truncation acceptance under P_F2 and C_F2 priors (Monte Carlo, reported), marginal prior quantiles.
F2-V1 spectral radius closed form vs numpy (random matrices incl. complex-eigenvalue cases), tolerance 1e-12 relative.
F2-V2 conjugate update: posterior density / (prior x likelihood) constant over random (B, Sigma) points (closed-form identity,
1e-10); both Psi_n forms agree.
F2-V3 Rao-Blackwell identity: p(y | B, D) (Student-t) vs Monte Carlo over Sigma | B, D (statistical) and vs the d = 1 scalar case.
F2-V4 untruncated predictive: Monte Carlo over the posterior (estimator R with c = infinity) vs the closed-form matrix-t
(statistical, |z| <= 4) and 2-D normalisation of the closed form on a grid (1e-6).
F2-V5 truncated predictive, IS convergence: SE(log p_hat) <= 2e-4 per item (reported per cell; cap hits reported), doubling J
halves the variance (rate check), estimators R and C agree within their combined SE.
F2-V6 reduced-case oracle (d = 1): the F2 code with d = 1 is a truncated normal-inverse-gamma AR(1); compared with nested
scipy.integrate.quad over (a, sigma^2) (no closed form used) within 4 SE + 1e-6.
F2-V7 d = 2 independent estimator: sampling from the truncated PRIOR with likelihood weights (a different algorithm, no
posterior sampling) agrees with the posterior estimator within the combined SE (|z| <= 4) on short contexts where prior
sampling is efficient.
F2-V8 library predictive vs brute-force per-atom evaluation (1e-12).
F2-V9 calibration of the matched population reference on P_F2 systems: PIT is not defined for a 2-D target, so (i) PIT of each
coordinate's marginal predictive (the marginal of a t-mixture is a 1-D t-mixture), (ii) coverage of the central 50/80/95%
regions of the bivariate predictive measured by the probability-integral transform of the predictive density value
(Monte Carlo reference distribution), (iii) continuous SBC of rho(A) and of each coefficient.
F2-V10 optimality: no context-only or library reference beats the population reference in expectation on P_F2 systems.
F2-V11 mutation matrix: wrong prior, off-by-one likelihood, leaked target, unmatched reference, wrong truncation radius, missing
Sigma integration (plain Gaussian at the posterior mean), wrong spectral radius (max |diagonal| instead of eigenvalues):
each detected by at least one check; clean baseline passes.
Tolerances: closed forms 1e-10 relative; Monte Carlo checks at |z| <= 4 (two-sided p about 6e-5 per check, Bonferroni-safe
for up to about 100 checks at family level 0.01), which is stated per check in the test.

## 10. Assumptions and where each is verified
| # | Assumption | Status | Where verified |
|---|---|---|---|
| 1 | x_0 independent of (A, Sigma); likelihood conditional on x_0 | ASSUMED (design) | simulator code review; F2-V9 calibration would fail otherwise |
| 2 | MNIW algebra of sections 3-4 | DERIVED | F2-V2, F2-V3, F2-V4 |
| 3 | Accepted draws iid from the truncated posterior | DERIVED (0/1 weights) | F2-V5 (rate), F2-V7 (independent estimator) |
| 4 | Delta-method SE adequate at J_acc >= 1000 | ASSUMED | F2-V5 doubling check; minimum J_acc enforced |
| 5 | The context-only prior carries little scale information | ASSUMED (limitation) | F2-V0 quantiles reported |
| 6 | Truncation acceptance under the posterior is not tiny for population-like contexts | UNVERIFIED | F2-V0, F2-V5 diagnostics |
