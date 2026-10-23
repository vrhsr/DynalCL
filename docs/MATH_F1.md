# MATH_F1: scalar AR(1) with unknown noise scale (Stage 2 family F1; references only)

Status: DRAFT, written before any F1 reference result. Labels as in docs/MATH.md. Plan v2 section 3.

## 1. Data-generating process
x_t = a x_{t-1} + sigma e_t, e_t iid N(0, 1), t = 1..T; x_0 ~ N(0, r^2) **independent of (a, sigma)** (so, as in MATH 1.1,
p(x_0) drops out of every posterior and the likelihood is conditional on x_0). System parameters theta = (a, sigma^2).

**Population prior P_F1 (ASSUMED design, fixed before any result):** a ~ TN(0.4, 0.3^2; -0.95, 0.95) (as Stage 0.5), and,
independently, sigma^2 ~ InverseGamma(alpha0 = 3, beta0 = 2) (mean 1, variance 1; computed with scipy: P(0.55 < sigma < 1.6) = 0.916,
5% and 95% quantiles of sigma 0.564 and 1.564).
Independence of a and sigma^2 is a modelling choice (a population of systems whose persistence and noise level vary
separately); it is not the NIG coupling of Stage 0 (where a | sigma^2 has variance proportional to sigma^2).

**Context-only reference C_F1:** a ~ U(-0.999, 0.999) and, independently, log sigma ~ U(log 0.01, log 100) (scale-invariant
over four orders of magnitude). It knows stability and nothing about the population's noise level.

**Library L_K:** K atoms (a_k, sigma_k^2) drawn iid from P_F1, uniform weights.

## 2. Likelihood as a function of (a, sigma^2) (DERIVED)
With S_xx = sum x_{t-1}^2, a_hat = S_xy / S_xx and R_min = sum (x_t - a_hat x_{t-1})^2 (computed from residuals, no
cancellation), the residual sum of squares is exactly
    R(a) = R_min + S_xx (a - a_hat)^2,
a sum of two non-negative terms (complete the square in MATH 1.3). The conditional likelihood is
    L(a, sigma^2) = (2 pi sigma^2)^(-n/2) exp(-R(a) / (2 sigma^2)).

## 3. Integrating sigma^2 out in closed form (DERIVED)
Define M_n(R) = int (sigma^2)^(-n/2) exp(-R / (2 sigma^2)) p(sigma^2) d sigma^2.
* **Inverse-gamma prior** IG(alpha0, beta0):
  M_n(R) = beta0^alpha0 Gamma(alpha0 + n/2) / [Gamma(alpha0) (beta0 + R/2)^(alpha0 + n/2)].
  (Substitute u = 1/sigma^2; the integrand is a Gamma kernel.)
* **Log-uniform prior** on [s_lo^2, s_hi^2] (density proportional to 1/sigma^2): with u = R / (2 sigma^2),
  M_n(R) = C (R/2)^(-n/2) Gamma(n/2) [P(n/2, R/(2 s_lo^2)) - P(n/2, R/(2 s_hi^2))],
  P the regularized lower incomplete gamma function and C = 1 / log(s_hi^2 / s_lo^2) (cancels in every ratio below).
  For R -> 0 at n = 1 the factor (R/2)^(-1/2) diverges and P(1/2, R/(2 s_lo^2)) ~ sqrt(R)/s_lo, so M_1 stays finite but
  the posterior over a has a spike of width about s_lo / |x_0| at a_hat. **Decision:** F1 uses n >= 2 only (at n >= 2,
  R_min > 0 with probability 1 and the posterior over a is bounded by a smooth function).

## 4. Posterior over a and one-step predictive (DERIVED; 1-D quadrature over a)
* p(a | D) is proportional to pi(a) M_n(R(a)) on the a-support.
* Given a, the predictive of y = x_{n+1} integrates sigma^2 against p(sigma^2 | a, D):
    p(y | a, D) = (2 pi)^(-1/2) M_{n+1}(R(a) + (y - a x_n)^2) / M_n(R(a)).
  For the inverse-gamma prior this is the Student-t density with 2 alpha_n degrees of freedom, location a x_n and scale^2
  beta_n(a) / alpha_n, where alpha_n = alpha0 + n/2 and beta_n(a) = beta0 + R(a)/2 (standard NIG-type algebra; TESTED
  against the generic ratio).
* p(y | D) = int p(a | D) p(y | a, D) da, by composite Gauss-Legendre over a: NUMERICALLY APPROXIMATED with verified
  convergence (node doubling; 2-D grid oracle over (a, log sigma)).
* Quadrature panels per context: 64 uniform panels over the support plus 64 panels over a core window
  a_hat +/- 40 s_core (clipped to the support), s_core = sqrt((2 beta_eff + R_min) / (S_xx max(1, 2 alpha_eff))) a
  heuristic width of the a-kernel (beta_eff = beta0, alpha_eff = alpha0 + n/2 for IG; beta_eff = s_lo^2/2 style lower
  bound, alpha_eff = n/2 for log-uniform). The union of edges is sorted; 8 nodes per panel. The heuristic only places
  nodes; correctness rests on the convergence tests.

## 5. Library posterior (DERIVED; ANALYTICALLY EXACT given the atoms)
log w_k = log pi_k - n log sigma_k - R(a_k) / (2 sigma_k^2) (constants cancel); predictive sum_k w_k N(y; a_k x_n, sigma_k^2).

## 6. Validation plan (before any network; Stage 0 style)
F1-V1 closed-form M_n against adaptive 1-D integration over sigma^2 (scipy.integrate.quad) for random R, n, both priors;
F1-V2 Student-t identity for the IG case; F1-V3 predictive density against a dense 2-D grid over (a, log sigma) for random
contexts (n in {2, 3, 5, 20}, r in {0.25, 1, 4}); F1-V4 node doubling of the a-quadrature at predictive quantiles 1e-3..1-1e-3;
F1-V5 calibration of the matched population reference on systems from P_F1 (PIT KS, 50/80/95% coverage); F1-V6 optimality:
no context-only or library reference beats the population reference in expectation on P_F1 (paired z); F1-V7 limit: as
alpha0 -> infinity with beta0 = alpha0 sigma0^2 the F1 population reference converges to the known-sigma Stage 1A reference;
F1-V8 library predictor against brute-force mixture evaluation; F1-V9 mutation matrix (wrong alpha0, off-by-one transition,
leaked target, unmatched reference, missing sigma integration) each detected by at least one check.
Tolerances: closed forms 1e-10 relative; quadrature and grid 1e-6 nats (as MATH 5.3: four orders below the smallest score gap
of interest); statistical checks at Bonferroni-corrected levels stated in the test.
