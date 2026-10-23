# Independent audit: Stage 1A references, KL machinery, analysis and operating characteristics; F1 (unknown sigma)

Scope: only the files listed in the brief (plus frozen `dynaicl/` modules for imports: `harness.make_context`, `splits.generate_split`,
`conditions`, `library`, `rng`, `priors.sample_systems`). No repository file was modified. Scratch scripts are in
`scratchpad/audit/` (t1_*, t2_*, t4_*, t5_*, t6_*), run from `E:\study-buddy\DynaICL` with `PYTHONPATH=.`.
I did not run `tests_stage1/test_ar1_batch_references.py` because it reads `runs/`, which is out of bounds. `test_analysis.py` and
`test_kl_quadrature.py` were run: **17 passed in 32 s**.

Labels: DERIVED (my own derivation), TESTED (I ran a check; numbers given), CONCERN/DEFECT (with a failure scenario).

## Findings

| id | severity | file:line | claim | evidence | suggested fix |
|---|---|---|---|---|---|
| A1 | **MAJOR** | scripts/stage1_operating_characteristics.py:86, 146 (also dynaicl_neural/analysis.py:278-282, OC docstring lines 13-15) | The OC simulates bands with `critical_value_gaussian`, but the real analysis uses `critical_value_bootstrap`. The docstring says a test "checks the two agree". In the OC's own regime they do not agree, so the OC misstates both the procedure's power and the Gaussian-c error rate. | In the OC regime the SE is about 99% the seed component (s^2/M = 1.25e-5 vs system part (0.07)^2/40000 = 1.2e-7), so se has only M-1 df. Over 200 simulated replicates (20 statistics, pi = 0.5, e = 0.005, kappa = 1): **Gaussian-c familywise coverage 0.695 (M = 8), 0.830 (M = 16), 0.935 (M = 64), 0.765 (M = 8, s = 0.002)** vs nominal 0.95. Per-statistic exceedance 0.0175 at M = 8 vs about 0.0025 nominal. **Median bootstrap c is 6.34 / 3.87 / 3.12 vs Gaussian 2.89 / 2.95 / 2.98**; bootstrap coverage 0.995 / 0.960 / 0.955. Effect on the OC's P(PROCEED), 150 studies each: M = 16, pi = 0, e = 0.005, s = 0.01: **0.83 (Gaussian) vs 0.13 (bootstrap c)**; M = 16, pi = 1: 0.98 vs 0.67; M = 8, pi = 1: 0.24 vs 0.00. `test_simultaneous_coverage_bootstrap_and_gaussian` compares the two only where the system term dominates (s_u^2/M is about 7% of the variance) and M = 12, so it cannot detect this. | Run the OC with the procedure that will actually be used: a bootstrap with reduced B, or a calibrated approximation such as a multivariate t with M-1 df or Satterthwaite df. Add a coverage test in the seed-dominated, small-M regime. Never use the Gaussian c for real inference at M <= 32. Report that at M = 8 the bootstrap band is very conservative (c about 6.3) and has almost no power. |
| A2 | MINOR | scripts/stage1_operating_characteristics.py:69-70 | Each model's seed effect is drawn independently for each of the 10 cells. In reality one trained model is evaluated in all cells, so its deviation is shared or correlated across cells. This changes c and the joint (>= 7 of 10) PROCEED event. | With the seed effect shared across cells (per arm), the Gaussian c drops from 2.9 to 2.3-2.4. P(PROCEED) changes: 0.24 -> 0.57 (M = 8, pi = 1, s = 0.01); 0.02 -> 0.32 (M = 8, pi = 0); 0.06 -> 0.43 (M = 32, pi = 1, e = 0.005, s = 0.02); 0.83 -> 0.89 (M = 16, pi = 0, e = 0.005); 0.00 -> 0.21 (M = 16, pi = 0.75). Boundary truths (pi = 0.5 or 0.25, five settings, 300 studies each): **0 false PROCEED under either model**. So power is misstated (here understated); error rates were not affected in the settings tried. Combined with A1, the net direction is unknown. | Simulate a model-level effect shared across cells, with a correlation parameter (for example rho in {0, 0.5, 0.9}), and report OC for each value. |
| A3 | MINOR | scripts/stage1_operating_characteristics.py:68-70 | `sys_eff` is common to both arms, so it cancels exactly in G = UNIF - CONT. In reality G_j = KL(pop‖UNIF)_j - KL(pop‖CONT)_j has a system sd of about sd(KL(pop‖stab)) when CONT is about pop. The OC therefore understates SE(G). | Missing term about sd/sqrt(40000) = 4.65e-4 (kappa = 1, sd = 0.093). Seed term s·sqrt(2/M) = 8.8e-4 at s = 0.005, M = 64, so SE(G) is understated by about 12% in that corner. It is negligible for s >= 0.01 or M <= 32. Power is slightly overstated only in the low-s, high-M corner. | Give G's system effect variance proportional to pi (or to G itself), not zero. |
| A4 | MINOR | dynaicl_families/ar1_unknown_sigma.py:166-181 (`nodes`) | When a_hat - 40 s_core > rho, the core window collapses to the point rho and only 64 uniform panels (width 2rho/64, about 0.03) remain. These cannot resolve a posterior pinned at the edge with decay length s^2/(a_hat - rho). | TESTED vs a 400001-point Simpson grid (sigma^2 integrated with the verified closed forms), 6 contexts per case. Explosive a = 1.10, n = 60, sigma = 0.6: **error 2.0e-7 (pop_F1) and 8.7e-6 nats (ctx_F1)**, which exceeds the stated 1e-6 budget. Node doubling shows the same size, so a doubling test there would catch it. OOS a = 0.99 (n = 40), a = 0.999 (n = 80) and a = 1.05 (n = 40): <= 2.4e-14. The F1 tests use only P_F1 data, so they never reach this regime. | When the core is clipped, add boundary panels geometrically refined toward +/-rho (as the 1A PINNED branch does), or raise when the core collapses. Add a node-doubling test on OOS or explosive contexts if F1 is ever evaluated off-population. |
| A5 | NOTE | dynaicl_families/separability.py:149-162 (`reference_window`) | The window rule has a gap between "pinned" (mode > 10 sd outside) and "interior". If the kernel mode is just under 10 sd outside the support, [m - 10s, rho] can hold a small fraction of the truncated mass. The docstring's claim that "each excluded mass is far below 1e-8" is false there. | TESTED: stab with context (0.1, 10.0899), (m - rho)/s = 9.99: window mass **0.838**. `kl_per_context` raises (`lost mass 1.62e-01`), so it is not silent. Realistic map-like contexts (HELD/PROBE/OOS, r in {0.25, 4}, n in {1, 5, 80}, 4000 each, pop and stab): a-window fraction 1.0 everywhere, max mass error 2.7e-12, 0 pinned. | Build the a-window from truncated-normal quantiles (or from the exponential bound with rate (m - rho)/s^2 whenever m > rho), not from the untruncated kernel. |
| A6 | NOTE | dynaicl_families/separability.py:233-313; dynaicl/systems/splits.py:85-108 | Common random numbers by design. All r share systems and innovations (x_0 = r·z). The Q2 HELD/PROBE/OOS items are the same in every (K, draw) unit and are prefixes of the Q1 items. Libraries are nested across K within a draw (`build_library_from_prior`). | Read from the code. Per-cell estimates and SEs are valid, but cells and draws are not independent. The "DRAW_FRACTION >= 0.9 of draws" rule counts draws that share their evaluation error. | Disclose when interpreting patterns across cells or across draws. Optionally evaluate each draw on fresh items. |
| A7 | NOTE | dynaicl_families/kl.py:1-10, separability.py:183 | `panel_width = 0.5` and the "component sd >= sigma" argument assume known sigma = 1. `reference_window` has no rule for F1 references. | F1 predictives are Student-t mixtures with polynomial tails (the repo's own test history found a +/-60 window lost 2.6e-4 mass). | If KL is needed for F1, design a tail-aware window (e.g. a tan substitution) and scale `panel_width` with the predictive scale. |
| A8 | NOTE | dynaicl_families/ar1_unknown_sigma.py:121-130 | The log-uniform marginal raises for (n = 81, R = 1e-12): P(40.5, 5e-9) underflows. | Raises FloatingPointError; it is not silent. Unreachable: at n = 80, R >= R_min ~ sigma^2 chi^2_79. | None needed. Optionally compute log P by series in log space. |
| A9 | NOTE | scripts/stage1_operating_characteristics.py:105-125 (Q2 OC) | Q2 system effects are independent across D_lib, D_pop and D_stab. Real distances to one model on the same systems are positively correlated, so contrast variance is overstated (conservative). The SD factor of 3x the mean is ASSUMED. Same Gaussian-c issue as A1. | Read from the code. | As A1. Simulate correlated per-system distances. |
| A10 | NOTE | scripts/stage1_operating_characteristics.py:196-197 | `P_wrong_class` counts only POP<->STAB swaps. With pi = 0 and e = 0.01 = EPSILON the truth sits exactly on the WORSE-THAN-STAB boundary. | Read from the code. WORSE outcomes appear in `P_WORSE`, not in `P_wrong_class`. | Document this, or include WORSE in the wrong-class rate for truth STAB-LIKE. |
| A11 | NOTE | scripts/stage1_operating_characteristics.py:180 | The Q2 seed is `OC_SEED + 1` = 70102, an arithmetic derivation that could collide with another registered role. I could not check, because the seed table is out of scope. | | Register 70102 explicitly or use `derived_seed`. |

No CRITICAL findings. Nothing wrong was found in: the KL identity and where it is used, `kl_quadrature`, the TN and library predictives,
`log_ndtr_diff`, the direction and sign of the Rao-Blackwell estimator, `two_level` (plain and weighted), `covariance_of_estimates`,
the three classification functions, the F1 closed forms, the Student-t identity, R(a), the `log_gammaincc` asymptotics, the log-uniform branch logic,
context and target cutting, leakage, and stream independence between sets.

## Task 1: KL identity, kl.py, reference_window

**DERIVED.** If (ctx, y) ~ D and p_A(y|ctx) is the conditional density of y given ctx under D, then
E[log p_A(y|ctx) - log p_B(y|ctx)] = E_ctx[∫ p_A(y|ctx) log(p_A/p_B) dy] = E_ctx[KL(p_A(·|ctx) ‖ p_B(·|ctx))] (tower property).
p_A must equal the true conditional. That needs A's prior to equal D's system distribution and the same likelihood. x_0 must be independent of
the system (MATH 1.1), so conditioning on x_0 is exact, and contexts must start at x_0 (`make_context` cuts x_0..x_n; target
`trajectories[:, n+1]`, no leakage).

**Where it is used.** `run_q1`: CHECK and the KL(pop‖stab) primary only on HELD (ContinuousPriorCondition(POP_FROZEN) = TN(0.4, 0.3²; ±0.95), sigma = 1,
matching `population_prior()`). `run_q2_unit`: KL(pop‖lib) and CHECK on HELD only (pop is truth); INLIB uses realized scores with lib as truth
(uniform weights, sigma = 1 match `LibraryCondition` sampling). The summariser uses KL(pop‖·) as primary only for (HELD, pop|stab) and
(HELD, lib|pop), and min of both directions elsewhere (behavioural). **Correct.**
TESTED (t1_identity.py, 20000 items): INLIB lib‖pop, realized vs KL paired z = +1.40 (n = 1) and +0.72 (n = 3), with sd 0.153 -> 0.018 (8x variance
reduction). Negative controls where the precondition fails: INLIB pop‖stab z = -5.07; PROBE z = -18 to -44. So the identity only holds where the
code uses it.

**kl.py.** Composite 8-node Gauss-Legendre with panels <= 0.5. Chunks are sorted by panel count; each context gets p >= its own required panels, so
the width bound holds. `diff = where(pw > 0, lp - lq, 0)` drops p = 0 terms correctly and lets KL = +inf if q = 0 where p > 0 (correct).
TESTED vs scipy.quad on the whole real line (4 pairs x 4 (n, r) x 6 contexts): **max |diff| 1.5e-15**. The repo's Gaussian-oracle, node-doubling
and pinned tests pass.

**reference_window.** DERIVED: for the pinned case (m - rho > 10 s), log density at rho - t relative to rho is -t(2(m - rho) + t)/(2s²) <= -10t/s. By the
hazard argument (log-concave, hazard >= 10/s) the tail fraction beyond t = 6s is <= e^-60. Correct. Library: atoms below e^-60 relative weight carry
<= 256 e^-60, about 2e-24, and the kept set is never empty. 12-sigma y-padding: 2Φ(-12) = 3.6e-33. Correct. The gap is in A5.

## Task 2: closed-form predictives

**DERIVED** (MATH 4.3 re-derived): N(y; ac, σ²) N(a; m, s²) = N(y; mc, σ² + s²c²) · N(a; m', s'²), with 1/s'² = 1/s² + c²/σ² and
m' = s'²(m/s² + yc/σ²). Integrating over (-ρ, ρ) and dividing by the posterior mass gives the code's `log_gauss + num - den`. The posterior
(1/s² = S_xx/σ² + 1/τ0², m = s²(S_xy/σ² + μ0/τ0²)) matches. Library: w_k ∝ π_k exp(-(a_k² S_xx - 2a_k S_xy)/(2σ²)), S_yy cancels;
predictive Σ w_k N(a_k c, σ²). Matches.

TESTED (t2_predictive.py): TN predictive vs scipy.quad over a (60 random contexts, n in {1, 2, 3, 5, 10, 40}, σ in {0.5, 1, 2}, both priors, 5 y
values from -4 to +3.5 predictive sd): **max 2.8e-13 nats**. Library (K in {1, 2, 4, 64}, random Dirichlet weights, σ = 1.3) vs brute force:
**5.3e-15**. `log_ndtr_diff` vs mpmath (60 dps, with reflection): <= 2e-16 relative in both tails and across zero. 7e-14 at width 2e-3 and 1.8e-8
at width 1e-9 (unreachable: the widths are 2ρ/s >= about 6 for pop).

## Task 3: Rao-Blackwell estimator

**DERIVED.** KL(pop‖B | ctx) = E[d | ctx] with d = LS(pop) - LS(B), so E[KL] = E[d] (unbiased for the same estimand) and Var(KL) <= Var(d).
The code computes d = pop - stab and `kl_per_context(pop, stab)`, i.e. KL(truth ‖ other). Direction and sign are consistent, and CHECK = d - KL has
expectation 0. In the analysis, R_pop = E[KL(pop‖model)] = E[LS(pop) - LS(model)] on held-out systems (any model whose predictive depends only on
the context). G = R_pop(UNIF) - R_pop(CONT) = E[LS(CONT) - LS(UNIF)] > 0 when CONT is better, and it equals Δ when CONT = pop and UNIF = stab.
This is consistent with `classify_q1_held`'s Δ/2 thresholds and the OC's G = πΔ. **No defect.**

## Task 4: analysis.py

**DERIVED.** X_mj = μ + u_m + e_j + η_mj. Var(grand mean) = s_u²/M + s_e²/N + s_η²/(MN). E[var(row means)]/M = s_u²/M + s_η²/(MN), and
E[var(col means)]/N = s_e²/N + s_η²/(MN). So E[se²] exceeds the true variance by s_η²/(MN), as the docstring states. The weighted version with
multiplicity weights (sw = M, sv = N, ddof via sw - 1) is exactly the unweighted formula on the resampled matrix. Correct.
`covariance_of_estimates` has diagonal equal to `two_level` se² (ddof 1 in np.cov), adds the column covariance only within an item set, and keeps
the model part across sets. Correct. `critical_value_bootstrap`: studentized, centred at the original estimate, index ceil(B(1 - α)) - 1 (empirical
quantile). Correct. `critical_value_gaussian`: correlation, clipped eigen-root, max|Z| quantile. Correct (division by zero if a variance is 0, an edge
case only).

Classification: `classify_q1_held` classes are mutually exclusive (WORSE checked first; POP needs g.lo > Δ/2, STAB needs g.hi < Δ/2). STAB-LIKE
admits R_pop up to Δ + ε (by design). `classify_behavioural`: two hits are impossible because C_YX = -C_XY gives lo(C_YX) = -hi(C_XY).
`classify_memorisation`: contrast keys are used with the right sign ((Y, X) = D_Y - D_X). LIB-LIKE uses s = min sep while GENERALISING uses
the specific sep(lib, Y); a mild, intentional asymmetry. No logic errors found. The strict inequalities are tested at the boundary in
`test_classify_q1_held`.

TESTED (coverage, t4_coverage.py): see A1. The Gaussian approximation undercovers in the seed-dominated regime. The bootstrap is close to
nominal at M >= 16 and very conservative at M = 8.

## Task 5: OC script

What matches the docstring: truths R_pop(CONT) = (1 - π)Δ + e, R_pop(UNIF) = Δ + e, G = πΔ (lines 69-72). The system and interaction sd are
scaled by sqrt(N_SIM/N_REAL), which leaves both the s_e²/N and s_η²/(MN) terms equal to their N = 40000 values (DERIVED). Two independent
replicates use one c, and a class counts only if both agree. `truth_class` uses the same strict inequalities as `classify_q1_held`. PROCEED means
>= 7/10 cells confirmed in the same POP/STAB class (it does not require the class to be correct; correctness is in `P_wrong_class`).

Where the OC can misstate operating characteristics: A1 (the Gaussian c is not the analysis's bootstrap c; power overstated by up to 0.70 in
P(PROCEED) at M = 16), A2 (seed effects independent across cells), A3 (G has no system variance), A9 (Q2). The data are Gaussian, so there is no
KL skew; harmless at N = 40000. Δ is treated as known (its map SE is about 3.5e-4, negligible). False PROCEED at boundary truths was 0/300 in every
setting I tried.

## Task 6: F1 (unknown sigma)

**DERIVED.** IG: ∫(σ²)^(-n/2) e^(-R/2σ²) β^α/Γ(α) (σ²)^(-α-1) e^(-β/σ²) dσ² = β^α Γ(α + n/2) / [Γ(α)(β + R/2)^(α + n/2)].
Log-uniform (density ∝ 1/σ², which is the same as uniform in log σ): with u = R/(2σ²), (σ²)^(-n/2-1) dσ² = (2/R)^(n/2) u^(n/2-1) du, giving
C (R/2)^(-n/2) Γ(n/2)[P(n/2, R/2s_lo²) - P(n/2, R/2s_hi²)]. Both match the code. The posterior over a is ∝ π(a) M_n(R(a)), and
p(y|a, D) = (2π)^(-1/2) M_{n+1}(R + (y - a x_n)²)/M_n(R). For IG this ratio is Γ(α_n + 1/2)/(Γ(α_n)√(2πβ_n)) (1 + d²/(2β_n))^(-(α_n+1/2)),
the t density with ν = 2α_n and scale² = β_n/α_n. RSS(a) = S_yy - 2aS_xy + a²S_xx = S_xx(a - â)² + R_min. All correct.

Branch logic: main = log Q_lo + log1p(-Q_hi/Q_lo); if Q_hi > 0.5, P_hi - P_lo directly (better conditioned); if Q_lo <= 1e-280, both in log space
via the DLMF 8.11.2 series (u_k = (s-1)...(s-k)). Correct.
TESTED vs mpmath (60 dps), n in {2, 3, 5, 20, 41, 81}, R from 1e-12 to 1e12 (covering all three branches; the log-space branch starts at R
about 1.3e7): **max relative error 7.6e-16** (only (81, 1e-12) raises; A8). IG log M_n: 6.7e-16. Asymptotic log Q (s up to 40.5, u from 700 to 1e8): 2.1e-16.
IG(3, 2) claims: mean 1, var 1, P(0.55 < σ < 1.6) = 0.9156, 5%/95% σ = 0.5636 / 1.5639. **Confirmed.**

Nodes: uniform plus core edges sorted; duplicate edges give zero-width panels whose log weight is -inf and drop out of the logsumexp (correct).
The core heuristics match MATH_F1 section 4. Accuracy: 1e-14 except when the core collapses (A4).

## Task 7: other checks

Context cutting and targets: `make_context` gives x_0..x_n, the target is x_{n+1}, and S_xx sums x_0..x_{n-1}² (correct). Streams: HELD/PROBE/OOS
use different stream codes (0/2/3) of the selection role. In-library sets use an independent derived root. Libraries use their own stream name.
`assert_no_unintended_overlap` and `assert_parameters_disjoint` run. Independence between sets holds, and the dependence that exists is the
intended CRN (A6). No sign, off-by-one or leakage defect found. Constants are consistent across files: pop TN(0.4, 0.3; 0.95), stab
U(±0.999), probe grid -0.95..0.95 step 0.05, OOS (0.95, 0.999), seeds 70001 / 70101 / 70201. The head-floor script's m = 1 moment-matching
floor is the exact KL minimiser over Gaussians (standard), and its EM floors are upper bounds, so its m choice is conservative.
