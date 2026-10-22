# MATH: derivations behind every DERIVED label

Labels: **DERIVED** (derived here), **TESTED** (named test), **ASSUMED**, **UNVERIFIED**.
Terminology: "analytically exact" means a closed form (evaluated in float64, so subject to rounding).
"Numerically approximated with verified convergence" means quadrature, grids or Monte Carlo, each with
its method, resolution and measured error. No numerical result here is called exact.

Notation: context x_0..x_n (n transitions). S_xx = sum_{t=1..n} x_{t-1}^2, S_xy = sum x_{t-1} x_t,
S_yy = sum x_t^2, a_hat = S_xy / S_xx, RSS(a) = sum (x_t - a x_{t-1})^2, c_h(a) = sum_{j=0}^{h-1} a^{2j}.

---

## 1. Data-generating process and the conditional likelihood

x_t = a x_{t-1} + sigma eps_t, eps_t iid N(0,1).

**1.1 Conditioning on x_0 is exact Bayes when x_0 is independent of a (DERIVED).**
p(a | x_0..x_n) ∝ p(a) p(x_0 | a) prod_t N(x_t; a x_{t-1}, sigma^2). If x_0 ⫫ a then p(x_0 | a) = p(x_0),
which drops out, leaving p(a) times the conditional likelihood. Our simulator draws
x_0 ~ N(m0, s0^2) independently of the system (ASSUMED design, enforced in `systems/conditions.py`).

**1.2 Two ways the assumption fails (DERIVED). Both are excluded in code.**
* Stationary start: p(x_0 | a) = N(0, sigma^2/(1-a^2)). Its log is -0.5 log(sigma^2/(1-a^2)) - (1-a^2) x_0^2/(2 sigma^2),
  and the (1-a^2)^{1/2} factor breaks Gaussian conjugacy in a. A posterior that ignores this term is not
  the Bayes posterior.
* A context cut from mid-trajectory (first state x_s, s > 0): x_s depends on a, so p(x_s | a) does not
  drop out, for the same reason. `evaluation/harness.make_context` always cuts x_0..x_n
  (TESTED: `test_j_evaluation_contexts_end_at_x_n_and_start_at_x0`). The calibration tests (E) would
  detect a violation.

**1.3 Quadratic form (DERIVED).**
log L(a) = -(n/2) log(2 pi sigma^2) - (S_yy - 2 a S_xy + a^2 S_xx) / (2 sigma^2)
= const - (S_xx / (2 sigma^2)) (a - a_hat)^2 for S_xx > 0. As a function of a, the conditional likelihood is
an unnormalised Gaussian. This fact drives sections 3-6.

**1.4 h-step law given a (DERIVED).** Iterating, x_{n+h} = a^h x_n + sigma sum_{j=0}^{h-1} a^j eps_{n+h-j}.
The eps are independent N(0,1), so x_{n+h} | a, x_n ~ N(a^h x_n, sigma^2 c_h(a)). We evaluate
c_h by Horner's rule c <- 1 + a^2 c, h - 1 times (the sum form). The closed form (1 - a^{2h})/(1 - a^2)
is 0/0 at abs(a) = 1 and loses about h·eps/abs(1 - a^2) relative accuracy near it (TESTED: D1 compares
the two where the closed form is well conditioned). On overflow c_h returns +inf, and every caller then
raises `FloatingPointError` ("not representable") rather than returning inf/NaN (TESTED:
`test_h_outlier_jump_is_finite_or_explicitly_unrepresentable`).

## 2. P-GAUSS: a ~ N(mu0, tau0^2), sigma known

**2.1 Posterior (DERIVED, ANALYTICALLY EXACT).** Prior times likelihood is
exp(-(a-mu0)^2/(2 tau0^2) - (a^2 S_xx - 2 a S_xy)/(2 sigma^2)), a Gaussian with precision
1/v_n = 1/tau0^2 + S_xx/sigma^2 and mean m_n = v_n (mu0/tau0^2 + S_xy/sigma^2). This matches the spec.
TESTED: A1 (raw-likelihood grid), C1 (sequential = batch), D2 (rates).

**2.2 One-step predictive (DERIVED, ANALYTICALLY EXACT).** x_{n+1} = a x_n + sigma eps with a ~ N(m_n, v_n)
independent of eps given D. A sum of independent Gaussians gives N(m_n x_n, sigma^2 + v_n x_n^2). This matches
the spec. TESTED: A1, A4, B1, C2.

**2.3 h > 1 (DERIVED form; NUMERICALLY APPROXIMATED).** p(y | D) = ∫ N(y; a^h x_n, sigma^2 c_h(a)) N(a; m_n, v_n) da.
The mean a^h x_n is nonlinear in a, so the mixture is not Gaussian. It is evaluated by the quadrature of
section 5 over N(m_n, v_n). TESTED: A1 (h = 3, 10 vs grid), A3 (convergence up to h = 50), B1 (h = 3 vs
importance sampling), C4 (chain rule).

**2.4 Explosive mass (DERIVED, ANALYTICALLY EXACT).** P(abs(a) >= 1) = Phi((-1-mu0)/tau0) + 1 - Phi((1-mu0)/tau0).
For the test regime (mu0 = 0.2, tau0 = 0.3, sigma = 1) this is **0.00386** (TESTED against 1e6 draws:
`test_h_explosive_probability_p_gauss_reported_and_correct`). tau0 = 0.3 was chosen to keep the
explosive mass below 0.5% while leaving the prior informative. The second P-GAUSS test regime
(mu0 = -0.3, tau0 = 0.25, sigma = 0.2) has P(abs(a) >= 1) = Phi(-2.8) + 1 - Phi(5.2) ≈ 0.0026.

## 3. P-NIG: a | sigma^2 ~ N(mu0, sigma^2/lambda0), sigma^2 ~ IG(alpha0, beta0)

**3.1 Posterior (DERIVED, ANALYTICALLY EXACT).** Collecting the exponent terms in a:
lambda0 (a - mu0)^2 + a^2 S_xx - 2 a S_xy + S_yy = lambda_n (a - mu_n)^2 + C, with lambda_n = lambda0 + S_xx and
mu_n = (lambda0 mu0 + S_xy)/lambda_n. So a | sigma^2, D ~ N(mu_n, sigma^2/lambda_n). The powers of sigma^2 give
alpha_n = alpha0 + n/2, and beta_n = beta0 + C/2. These match the spec.

*Numerical form (a correction to the implementation, not to the math).* The spec writes
C = S_yy + lambda0 mu0^2 - lambda_n mu_n^2, which is correct but subtracts large nearly equal terms. Setting
a = mu_n in the identity gives **C = RSS(mu_n) + lambda0 (mu_n - mu0)^2**, a sum of non-negative terms with
no cancellation. `references/conjugate.nig_posterior` uses this form. TESTED: A5 (2-D grid), C1
(sequential update uses the same identity per transition).

**3.2 One-step predictive (DERIVED, ANALYTICALLY EXACT).** y | sigma^2, D ~ N(mu_n x_n, sigma^2 (1 + x_n^2/lambda_n)).
An inverse-gamma scale mixture of normals is Student-t, so y | D ~ t_{2 alpha_n}(mu_n x_n,
(beta_n/alpha_n)(1 + x_n^2/lambda_n)). This matches the spec. TESTED: A5, B1, C2.

**3.3 Marginals used for SBC (DERIVED).** a | D ~ t_{2 alpha_n}(mu_n, beta_n/(alpha_n lambda_n)). sigma^2 | D ~ IG(alpha_n, beta_n).
TESTED: E (SBC on both a and sigma^2).

h > 1 under P-NIG is **not implemented** (it raises NotImplementedError); listed as future work.

## 4. P-STABLE: a on (-rho, rho), rho < 1, sigma known

**4.1 Correction to the spec: the posterior is closed form (DERIVED).** The spec calls P-STABLE
non-conjugate. That is imprecise. For a uniform prior on (-rho, rho), or a N(mu0, tau0^2) prior
truncated there, prior times the Gaussian-in-a likelihood (1.3) is a Gaussian kernel restricted to
(-rho, rho):

  a | D ~ TN(m, s^2; -rho, rho), with 1/s^2 = S_xx/sigma^2 (+ 1/tau0^2) and m = s^2 (S_xy/sigma^2 (+ mu0/tau0^2)).

For the uniform prior with S_xx = 0 the posterior is the prior. The truncated-normal family on a
fixed interval is closed under this update, so it is conjugate in the usual sense. **Decision:** quadrature
stays the primary implementation, as the spec asks, because it generalises to non-conjugate priors.
The closed form serves as an **independent oracle** (TESTED: A2, C2).

**4.2 Window (DERIVED).** The log posterior is f(a) = -0.5 P a^2 + c a + const on the support (P = 1/s^2).
With m = c/P and mode a* = clip(m, -rho, rho), the set {f >= f(a*) - Delta} is
abs(a - m) <= sqrt((a* - m)^2 + 2 Delta / P), intersected with the support. If the support is unbounded or the
mode is interior, the mass outside is 2(1 - Phi(sqrt(2 Delta))). At Delta = 40 that is ~4e-19, below the
float64 resolution of a unit mass. If the mode sits at a boundary, the density decays at least as fast
away from it, so the bound still holds.

**4.3 One-step predictive density in closed form (DERIVED; used as the oracle).** With c = x_n:
N(y; a c, sigma^2) N(a; m, s^2) = N(y; m c, sigma^2 + s^2 c^2) · N(a; m', s'^2), where
1/s'^2 = 1/s^2 + c^2/sigma^2 and m' = s'^2 (m/s^2 + y c/sigma^2). This is the standard Gaussian product
identity; check it by completing the square in a. Integrating over (-rho, rho) and dividing by the
posterior normaliser gives

  p(y | D) = N(y; m c, sigma^2 + s^2 c^2) · [Phi((rho-m')/s') - Phi((-rho-m')/s')] / [Phi((rho-m)/s) - Phi((-rho-m)/s)].

For the uniform prior with S_xx = 0 the posterior is U(-rho, rho), and p(y) = [Phi((y + rho|c|)/sigma) -
Phi((y - rho|c|)/sigma)] / (2 rho |c|). The CDF of this predictive has no elementary form and is not used.
TESTED: A2 (quadrature logpdf vs this formula at five y values per context, 12 contexts).

**4.4 Oracle accuracy finding (TESTED; recorded in DECISIONS D-07).** For one posterior truncated deep in a
Gaussian tail (standardised bounds -2.68, -2.63), `scipy.stats.truncnorm.var` was off by 6.1e-11. The
quadrature agreed with a 2,000,001-point Simpson rule to about 1e-16. The truncnorm comparison therefore
uses an oracle floor of 1e-9 relative. The independent grid comparison of the same moments keeps the
1e-11 floor. The grid oracle uses prior densities from scipy.stats (`oracles.scipy_prior_logpdf`), not the
reference's `coefficient_logpdf`, so it also checks the prior density independently.

## 5. Quadrature (all continuous-prior h > 1 predictives; P-STABLE at every h)

**5.1 Rule.** Composite Gauss-Legendre on the window from 4.2: `panels` x `nodes_per_panel` nodes
(default 16 x 8 = 128). Node masses = log GL weight + prior log density + conditional log-likelihood at
the node, normalised by log-sum-exp. The masses come from prior x likelihood. Only the node *placement*
uses the quadratic form.

**5.2 Integrand-adaptive panel placement (DERIVED heuristic; TESTED by convergence).** The h-step
integrand N(y; mu(a), s(a)^2), with mu(a) = a^h x_n and s(a) = sigma sqrt(c_h(a)), can be much sharper in a
than the posterior. Within one "resolution cell", dC = |d mu|/s + |d log s|, the component mean moves by
about one component sd at most, and log sd by about 1. Panel edges are placed at equal quantiles of the
density g(a) = panels/width + 2 dC/da (a uniform part that resolves the posterior, plus 2 panels per cell
where the integrand is sharp). The total panel count is ceil(∫ g), capped at 8192 (a cap hit is flagged).
History, both instances *found by tests*:
(i) With a fixed 128 nodes, A3 failed: P-GAUSS with a ≈ 0.99, x_n = 10, h = 50 changed by 2 nats under
node doubling.
(ii) The first fix used ceil(2C) panels spread uniformly. An independent audit showed it was still
under-resolved for wide posteriors with large x_0/sigma (P-STABLE, n = 0, x_0 = 50, h = 20: error 2e-5 nats),
because the cells concentrate near abs(a) = rho. Quantile placement fixed this (error ~1e-14), and those
regimes are now permanent A3 cases.

**5.3 Convergence verification (TESTED, A3).** The default resolution is compared with 4x the node count
at five predictive quantiles (1e-3 .. 1-1e-3), in 8 regimes x 4 horizons (h in {2, 5, 20, 50}). The regimes
include abs(a) ≈ 0.99, explosive data, x_n = 10, and wide posteriors with x_0/sigma up to 400. The worst
logpdf difference is **1.7e-13 nats** (P-GAUSS, a ≈ 0.99, x_n = 10, h = 50, 19,200 nodes), against a target of
1e-6 nats, and no case hits the panel cap.
Rationale for the target: it is 4 orders of magnitude below the smallest score gap of interest (0.02 nats,
PREREG), so quadrature error cannot change a conclusion. Each experiment run also records a node-doubling
error at actual targets (`quadrature_err_estimate`).

**5.4 Overflow.** Nodes whose h-step mean or variance overflows float64 are dropped only if their
posterior mass is <= 1e-15. Otherwise the predictive raises `FloatingPointError` (not representable).

**5.5 Limitation (UNVERIFIED in the far tails).** The window holds the posterior mass. For a target y far
in the predictive tail, the dominant a may lie outside the window, so the log density there is
underestimated. Convergence is verified at predictive quantiles 1e-3 .. 1-1e-3 and at actual
targets, not beyond.

**5.6 Posterior CDF and sampling (DERIVED).** F(a) = ∫_lo^a p / Z by the same composite rule on [lo, a].
Sampling is inverse-CDF by 60 bisection halvings, which reaches the float64 resolution of the window.

## 6. Finite library (ANALYTICALLY EXACT given the library)

w_k ∝ pi_k prod_t N(x_t; a_k x_{t-1}, sigma_k^2), i.e.
log w_k = log pi_k - (n/2) log(2 pi sigma_k^2) - RSS_k / (2 sigma_k^2). RSS_k is summed from residuals
directly (no S_yy - 2 a S_xy + a^2 S_xx cancellation). Weights are normalised by log-sum-exp, so a weight that
underflows exp() stays exactly representable in log space (TESTED: n = 5000, log-weight gap > 1e3).
Predictive: sum_k w_k N(a_k^h x_n, sigma_k^2 c_h(a_k)) by 1.4. This matches the spec.
TESTED: A6, B2, C1, C3 (K = 1 is the known system), C4, E (SBC with randomised tie-breaking), F.

## 7. Context-only baselines

**7.1 Flat-prior Bayes (DERIVED).** With p(a) ∝ 1 the posterior ∝ exp(-(S_xx/(2 sigma^2))(a - a_hat)^2) =
N(a_hat, sigma^2/S_xx), and by 2.2 the one-step predictive is N(a_hat x_n, sigma^2 (1 + x_n^2/S_xx)). This matches
the spec. h > 1 uses section 5. If S_xx = 0 the posterior is improper, and a config-fixed N(0, 1) prior is
used instead (flagged). sigma here is the condition's sigma (`uses_true_noise_scale`, DECISIONS D-05).

**7.2 OLS (DERIVED for h = 1; heuristic for h > 1).** sigma_hat^2 = RSS(a_hat)/(n - 1). Under
p(a, sigma^2) ∝ 1/sigma^2, standard Bayesian regression gives sigma^2 | D ~ scaled-Inv-chi^2(n - 1, sigma_hat^2) and
a | sigma^2, D ~ N(a_hat, sigma^2/S_xx). The one-step predictive is then t_{n-1}(a_hat x_n, sigma_hat^2 (1 + x_n^2/S_xx)),
which is the Student-t variant at h = 1. For h > 1 the variant uses
sigma_hat^2 [c_h(a_hat) + (h a_hat^{h-1} x_n)^2/S_xx], a delta-method propagation of Var(a_hat) ≈ sigma^2/S_xx. This is a
heuristic (it reduces to the exact form at h = 1). The Gaussian variant ignores parameter uncertainty
(NON-BAYESIAN; overconfident at short n). It falls back to persistence if n < 3 or S_xx = 0.

**7.3 Kernel analog.** Direct h-step Nadaraya-Watson on pairs (x_j, x_{j+h}) with a Gaussian kernel and
bandwidth c · scale. The selection schemes are defined in `baselines/kernel.py`. **Causality (corrected
during implementation):** each validation row's bandwidth scale uses only data that row may read
(rolling origin: sd(x_0..x_j); blocked: the fold's training observations). An earlier draft used
sd(x_0..x_n), which leaked post-origin data into the bandwidth (TESTED: J4, with a positive
control). The predictive variance is the mean squared out-of-sample validation residual at the selected
bandwidth.

**7.4 Persistence.** N(x_n, mean squared h-step increment within the context). With 1 <= n < h it uses
h · (mean squared 1-step increment), a random-walk scaling heuristic.

## 8. Scoring, calibration and tolerances

**8.1 Optimality of the matched reference (DERIVED).** For any predictor q that is a function of the
context, E_D[log p_D(Y|C) - log q(Y|C)] = E_C[KL(p_D(·|C) || q(·|C))] >= 0. Here p_D is the
posterior predictive under D (the matched reference), and the expectation is over (C, Y) drawn from D. Proof:
condition on C; the inner expectation over Y ~ p_D(·|C) is a KL divergence. This holds only for the
predictor whose prior and likelihood are D's. Under E-LIB, the continuous-prior predictor has no such
guarantee. TESTED: F (190 paired comparisons, one-sided z with Bonferroni), and T1 in every experiment
cell.

**8.2 CRPS (DERIVED).** For Z ~ N(m, v): E|Z| = 2 sqrt(v) phi(m/sqrt(v)) + m (2 Phi(m/sqrt(v)) - 1).
With CRPS(F, y) = E|X - y| - E|X - X'|/2, the Gaussian closed form
sd [z(2 Phi(z) - 1) + 2 phi(z) - 1/sqrt(pi)] follows, and so does the mixture closed form
sum_i w_i E|N(mu_i - y, v_i)| - (1/2) sum_ij w_i w_j E|N(mu_i - mu_j, v_i + v_j)|. The numerical CRPS integrates
(F - 1{. >= y})^2 by adaptive quadrature, split at y and at central quantiles. TESTED: numerical vs Gaussian
closed form (4 cases), vs mixture closed form (15 cases), vs Monte Carlo for Student-t (`tests/test_metrics.py`).

**8.3 Coverage from the PIT (DERIVED).** For continuous strictly increasing F, y ∈ [F^{-1}((1-c)/2),
F^{-1}((1+c)/2)] iff abs(F(y) - 1/2) <= c/2. TESTED: `test_coverage_from_pit_equals_quantile_interval_membership`.

**8.4 SBC by inverse-CDF equivalence (DERIVED).** If posterior draws are a_l = F^{-1}(U_l), then
#{l : a_l < a*} = #{l : U_l < F(a*)} ~ Binomial(L, F(a*)). For quadrature posteriors the rank is drawn this
way. It has the same distribution as drawing L samples, at a fraction of the cost. For discrete
(library) posteriors, ties are broken uniformly at random, which makes ranks exactly uniform under a
correct posterior (TESTED: `test_sbc_ranks_with_ties_are_uniform_for_a_correct_discrete_posterior`).

**8.5 Mixture quantile bracket (DERIVED).** Let q_k be component quantiles at level p. At
x = min_k q_k every F_k(x) <= p, so F(x) = sum w_k F_k(x) <= p. At max_k q_k, F >= p. Root-finding in this
bracket is therefore always valid. If rounding puts F(endpoint) - p on the wrong side, that endpoint is
the root to rounding.

**8.6 Tolerance policy.** Deterministic comparisons use 10 x (measured numerical error of both methods) +
1e-11 relative. The measured error is node doubling for quadrature, and refinement plus range-widening for
grids. 1e-11 is about 100x the rounding of pairwise summation over <= 1e4 terms. Statistical comparisons use
z x SE, with z from a Bonferroni split of family alpha = 1e-3 per check. Seeds are fixed, so outcomes
are deterministic; alpha is the probability that correct code would have failed at design time.
Summed over the ~10 statistical checks, the suite-wide false-alarm probability is <= 1e-2. Power against
real bugs is demonstrated by the mutation tests (G), not assumed. Check-specific constants and
their justifications live in the docstrings of `dynaicl/validation/checks.py`.

**8.7 Paired comparisons.** Every predictor is scored on identical (system, context, target) items, and the SE
of a mean difference is sd(d)/sqrt(N) (analytic; items are iid across systems).

## 9. Population-knowledge gain G (candidate metric; a hypothesis, not a standard)

G = (S_model - S_ctx) / (S_matched - S_ctx) on paired items, where S_ctx is the frontier score. With d1 = s_model - s_ctx
and d2 = s_matched - s_ctx per item, the delta method gives Var(G) ≈ [Var d1 - 2G Cov(d1,d2) + G^2 Var d2] / (N mean(d2)^2).
G is flagged **ill-conditioned** when abs(mean d2) < 3 SE(d2) or abs(mean d2) < delta (0.02 nats).

## 10. Corrections to the Stage 0 spec (summary)

1. P-STABLE is conjugate in the truncated-normal family, with a closed-form one-step predictive density (4.1, 4.3).
   Quadrature is kept as primary, and the closed form became a test oracle.
2. NIG beta_n: an algebraically equivalent, cancellation-free form (3.1).
3. Contexts must start at the trajectory's x_0 (1.2). The spec implies this but does not state it.
4. Quadrature node counts must adapt to the h-step integrand, not only to the posterior (5.2). This
   was found by a failing convergence test.
5. Kernel validation must also compute normalisation (bandwidth scale) causally (7.3). This was found
   while writing the leakage test.

## 11. Scale equivariance: only r = sd(x_0)/sigma matters (DERIVED; TESTED)

If x_0..x_T is generated by (a, sigma), then c x_0..c x_T (c > 0) is generated by (a, c sigma), with innovations unchanged.
The conditional log-likelihood in a depends on the data only through sum (x_t - a x_{t-1})^2 / sigma^2, which is invariant.
So every posterior over a (P-GAUSS, P-STABLE, the stability prior, the flat prior including its N(0, 1) fallback on the
dimensionless a, and a library whose sigma_k scale with sigma) is unchanged. Each predictive of y = x_{n+h} then
satisfies p_c(c y) = p(y)/c. Log scores shift by -log c for every predictor, so **paired log-score differences, PIT
values and coverage are invariant**.

The context-only estimators are equivariant too: a_hat is invariant and sigma_hat scales with c; kernel bandwidths are
multiples of sd(context); validation residual variances scale with c^2; persistence variances use context increments;
variance floors are relative. **Exception:** the absolute fallback variances used only with n = 0 (persistence) are not
equivariant, and n = 0 is not in the Stage 0.5 grid.

With x_0 ~ N(0, s0^2), the scaled problem has sd(x_0) = c s0. Results therefore depend on the scales only through
r = s0/sigma. Stage 0's cells sigma in {1, 0.25} with s0 = 1 are r in {1, 4}. TESTED: `tests/test_stage05.py::test_scale_equivariance_of_paired_differences`.
