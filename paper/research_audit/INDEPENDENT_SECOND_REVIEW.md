# Second independent review (Phase 11), AI-simulated

**What this is.** A TMLR-style review written by a fresh sub-agent that did not share the main session's context (Phase 11
of the audit brief). It read the manuscript at `paper-revision` commit `73660de` (revision 4), the claims and numbers
files, the evidence files at their pinned commits (through `git show`), four method documents and web sources for citations.
It did not open the excluded pilot files and created nothing in either repository. It is model output, not a human review:
its verifications are its own (labelled in its text), and its recommendation is a simulation of a TMLR reviewer, not a
prediction of the real outcome.

**Recommendation:** Major revision, 5/10 (criterion 1, accurate and convincing evidence: not yet met for several
interpretive claims; criterion 2, interest to part of the TMLR audience: met).

**How it was used.** Every finding was checked against the files before any change (M3 and M5 re-verified from
`split.csv` @ `e08eee8` and `theory.json` @ `cd2759f`; m1 from `f1_map_decisions.csv` @ `66c5846`; m6 from
`STAGE2_F2_MAP_SPEC.md`). The fixes are revision 5 / 5a in `CHANGELOG.md` (items 39-54). What it found that the first
audit missed: `REVIEWER_DISAGREEMENT_ANALYSIS.md`.

## Response status (after revision 5a, `paper-revision` @ `6a35441`)

| Item | Status | Where / what remains |
|---|---|---|
| M1 margin not tied to anything measured; precondition untested | **Partly addressed** | Margin now described as a design choice tied to model count and seed variance (Sec. 5); Table 2 and Figure 2 show how the windows move. Not done: n*(delta) curves (option c), a recipe for delta from seed variance, a trained-model demonstration (option a; needs a GPU or CPU-torch decision beyond the current narrow scope) |
| M2 "Pre-Registered" covers analyses chosen after results | **Partly addressed** | New Appendix B with a provenance table (what was seen before each specification); contributions reworded. Title unchanged: it was approved by the user, so a change is the user's decision |
| M3 F2 split order-dependent | **Fixed** | Both orders reported for F1 and F2 (claim B5-SPLIT-PATHS); "mostly dynamics" removed from abstract, introduction, results and conclusion. Not done: a non-conjugate dynamics-only comparator (new computation) |
| M4 pooling statements misread the bound | **Fixed** | Sec. 5 and Limitations rewritten |
| M5 F1 budget formally infinite | **Fixed** | Sec. 6 states the support mismatch (mass 1.3e-12) and that the value is for the restriction |
| M6 no code/data artefact | **Open (user decision)** | Needs an anonymised archive or repository and an availability statement |
| m1 PARTIAL definition | Fixed | Sec. 5 |
| m2 K^{-2/p} rate | Fixed (rate asymptotic only) | SEs for the theory values in the library figure not added |
| m3 estimators and sample sizes | Fixed in Sec. 5 | Not added to Table 1 |
| m4 duplicate "(the maps)" rows | Fixed (label) | Prior budgets for tau = 0.15 and 0.6 not reported (a new quadrature computation; needs a spec and a disclosure entry) |
| m5 cumulative baseline; tick labels | Fixed | Sec. 7 sentence; figure ticks |
| m6 F2 per-item SE statement | Fixed | Sec. 4 |
| m7 horizons | Fixed in Limitations | Not in Table 1 |
| m8 conclusion on where memorisation is visible | Fixed (5a) | Sec. 10 |
| m9 garbling argument | Fixed | Sec. 6; the x_0 versus y_0 conditioning was checked by derivation (both cumulative sums are divergences of joint laws whose initial value has the same law under P and Q, and the noisy joint is a garbling of the clean one), DERIVED, not re-run |
| m10 names, abstract length, title "Linear Dynamical Systems", tooling | **Open** | Renaming and title are user decisions; abstract shortening and tooling condensation not yet done |
| m11 Clarke-Barron, Amisano-Giacomini, equivalence testing | Fixed for the two citations (Crossref checked) | Equivalence testing not discussed |
| m12 bibliography | No action needed | - |
| Q4 F2 split at n = 20 | Open | Available in `split.csv` @ `e08eee8`; not yet in the paper |
| Q6 in-library evaluations in the main text | Open | Stage 0 in-library result is in Appendix A only |

---

## The review (verbatim, as returned by the sub-agent)

```text
TMLR REVIEW: "Where Bayesian References Disagree: Pre-Registered Separability Maps for In-Context Learning of Linear Dynamical Systems" (anonymous, 15 pp.)

Materials used: main.pdf, the LaTeX sections and generated tables and figures in E:\study-buddy\DynaICL-paper-rev\paper (commit 73660de), claims.yaml and numbers.yaml, evidence files read through `git show` at the pinned commits, method documents (MATH_F1.md, STAGE1_SEPARABILITY_MAP_SPEC.md, STAGE2_F2_MAP_SPEC.md, STAGE2_BATCH5_SPEC.md), and web sources for citations. I did not open any of the excluded files. I created nothing in either repository. The two scratch scripts are in C:\Users\Ramana\AppData\Local\Temp\claude\e--study-buddy-DynaICL\bd3df7a4-8736-46d2-9c91-75fbaf70608c\scratchpad\ (check_theory.py, check_maps.py).

======================================================================
1. SUMMARY AND CLAIMED CONTRIBUTIONS
======================================================================
Behavioural studies of in-context learners classify a trained model as "like" one Bayes reference or another. The paper asks, before any network is trained, where the candidate references themselves differ enough for such a classification. The setting is in-context forecasting of four autoregressive families:
- scalar AR(1) with known noise scale ("1A");
- AR(1) observed through Gaussian noise, with a Kalman likelihood ("F3");
- AR(1) with unknown noise scale ("F1");
- a bivariate VAR(1) with a stability-truncated MNIW prior ("F2").

The three references are population Bayes, a finite-library posterior, and a "context-only" Bayes predictor with a stability-only prior. The paper maps, cell by cell over (r, n, K, q), where pairs of references are "separable": estimate − 3 SE ≥ δ = 0.02 nats per forecast.

Claimed contributions:
(i) validated reference implementations;
(ii) two classical quantities used as design tools:
  - the chain-rule budget Σ_n g_n = D(m_P^N‖m_Q^N) ≤ D(P‖Q);
  - the nearest-library-system divergence as the long-context limit of the library gap;
(iii) the separability maps with δ-, comparator- and prior-sensitivity analyses;
(iv) pre-registered results (a Stage 0.6 STOP, and a neural pilot that ended "not resolvable (compute)"), plus the provenance tooling that produced them.

Headline results:
- Known σ: the population window is very short (n ≤ 5; budget 0.58 nats). Observation noise thins it further.
- Unknown σ: the gaps are larger but mostly knowledge of the noise level.
- F2: the gaps are larger and said to be "mostly dynamics".
- Scalar libraries of ≥16 systems are not separable; bivariate libraries up to K = 1024 become separable at long contexts.

======================================================================
2. STRENGTHS
======================================================================
S1. Unusually careful numerical and statistical engineering of the references: measured quadrature error, node-doubling checks, calibration/SBC/optimality tests, mutation matrices. I re-extracted many of the reported numbers from the pinned evidence files and found no transcription error (Section 7).

S2. The budget argument is correct and well chosen (DERIVED; see M5 for its interpretation).
- Because x_0 ⟂ θ, the one-step predictives are conditionals of the two Bayes marginals. The chain rule gives Σ g_n = D(m_P^N‖m_Q^N), and data processing gives ≤ D(P‖Q).
- It explains the qualitative pattern of all four families with one idea.
- The near-attainment check is a convincing empirical confirmation: Σ_{n=0}^{160} g_n = 0.551–0.558 against 0.582 (VERIFIED in batch5/cumulative.csv, SE ≈ 0.003).

S3. The paper is candid about nulls, power limits (F3 borderline cells, the 10× precision rerun), Monte Carlo limits in F2, dependence between cells, and the absence of any neural result.

S4. Per-draw library reporting (Table 4) rather than a single pooled verdict is the right choice, since a trained model sees one library.

S5. Sensitivity analyses on comparator width, comparator noise knowledge and population prior (Table 3) address an obvious objection. They show the known-σ window is driven by what the comparator knows about noise, not by its stability interval.

S6. For the TMLR audience working on Bayesian accounts of in-context learning (ICL), "do your references actually disagree on your evaluation data, and at what margin?" is a useful and under-discussed caution. The negative result is informative in itself: in scalar AR(1), library and continuous priors separate only for K ≲ 8.

======================================================================
3. MAJOR WEAKNESSES
======================================================================

M1. The central practical claim (per-cell separability at δ is the precondition for behavioural classification) is asserted but never tested, and δ is not tied to anything a behavioural study measures.
- Location: Abstract; Sec. 1; Sec. 5 "What separable does and does not mean"; Sec. 10; Limitations "Margin".
- Reason:
  - δ = 0.02 is "fixed in advance as a small log-score difference, not derived from the seed variance of trained models" (Sec. 8, VERIFIED in text).
  - The window endpoints move strongly with δ (Table 2; VERIFIED by recomputation: known σ, r = 1 gives n_max = 10 / 5 / 2 at δ = 0.01 / 0.02 / 0.04). So the binary maps are largely a re-expression of the smooth gap curves g_n (Fig. 2) at an arbitrary threshold.
  - The paper's own power lookup says classification at M = 32 models has power ≥ 0.80 only if the between-seed SD of regret is ≤ 0.01 nats (VERIFIED: LookupQoneThirtyTwo = 0.01 from f1_power_lookup.json). Whether trained models meet this is unknown, because the only neural study ended before any evaluation (Appendix B).
  - No experiment shows that a model can be classified where the maps say "separable" and cannot be classified elsewhere.
- Fix (any one):
  - (a) A small, cheap demonstration, e.g. a small transformer on the F2 library task or a scalar family on CPU-scale budgets, showing that classification succeeds or fails where the maps predict.
  - (b) Reframe the contribution around the gap curves and the two bounds, with δ presented as a user-chosen input and the maps as one example. Supply a recipe for choosing δ from seed variance and the number of models.
  - (c) At minimum, report window endpoints as continuous functions of δ (n*(δ) curves) instead of one δ plus a 3-point table.

M2. The "pre-registered" framing in the title and Contribution (iv) overstates the main-text evidence.
- Location: Title; Sec. 5 "Each map's specification was committed before its seed was first used"; Appendix A.
- Reason:
  - The confirmatory pre-registered studies (Stage 0.5, 0.6, the pilot) are in the appendices. The main-text maps are exploratory reference computations with specifications committed before seed use.
  - Several main-text analyses were explicitly chosen after seeing earlier results. STAGE2_BATCH5_SPEC.md (pinned 6d8a9fd) states under "Seen before this spec": the prior KL budgets, the nearest-atom limits, "a reviewer's scratch F1 computation with the context-only reference given the population noise prior", and "the F1 per-draw library share rising with n" — "These are why the analyses below were chosen" (VERIFIED).
  - Those analyses supply the F1/F2 decompositions, the longer-context library extensions, the denser F1 grid and the cumulative-gap figure, all of which carry headline claims in the abstract.
  - Committing a specification before seed use protects against seed-hacking. It does not make an analysis confirmatory.
- Fix:
  - Retitle (e.g. drop "Pre-Registered" or say "with pre-specified analyses").
  - Add a table labelling every main-text result as confirmatory (pre-registered hypothesis and decision rule) or exploratory (pre-specified computation, chosen after which results), with the commit of the specification and what was known at the time.

M3. The claim that the F2 gap is "mostly knowledge of the dynamics" (Abstract, Contribution iii, Sec. 7, Sec. 10) depends on the decomposition order.
- Evidence (VERIFIED in results_stage2/batch5/split.csv @ e08eee8, r = 1, n = 10):
  - T = 0.335 nats.
  - Path 1 (dynamics measured last): D1 = 0.122, N1 = 0.213, so noise is larger.
  - Path 2: N2 = 0.099, D2 = 0.236, so dynamics is larger.
  - The reported split (D = 0.18, N = 0.16) is the average of the two paths. The interaction (D2 − D1 ≈ 0.11 nats) is about five times the reported D − N difference (≈ 0.02).
  - The same reversal holds at r = 0.25 (D1 0.134 < N1 0.174; D2 0.238 > N2 0.070) and r = 4 (D1 0.088 < N1 0.166; D2 0.186 > N2 0.067).
- The spec and the Limitations already concede that the "ctx_dm" reference does not carry the population's marginal coefficient prior, because the MNIW coefficient prior scales with Σ. So the D2 path's "dynamics" label is itself approximate.
- By contrast, the F1 claim is robust: both paths give a noise-dominated split, e.g. D1 = 0.040 vs N1 = 0.249 at r = 1, n = 2.
- Fix: report D1, N1, D2, N2 and the interaction for F2. Remove "mostly dynamics" from the abstract and conclusion, or state it as order-dependent. Ideally construct a non-conjugate dynamics-only comparator so the label is meaningful.

M4. The "pooling" statements misread what the budget bounds.
- Location: Sec. 5 last sentence ("Section 6 bounds how much such pooling can gain"); Limitations ("The budget bounds what any pooling over forecasts can gain").
- Reason (DERIVED):
  - D(m_P^N‖m_Q^N) ≤ D(P‖Q) bounds the expected log-likelihood ratio of one sequence.
  - Evidence pooled over many independent sequences (or evaluation items) grows linearly in their number. A behavioural test that pools contexts can therefore detect arbitrarily small, nonzero per-forecast gaps given enough items and low enough seed variance.
  - The budget bounds the size of an effect per sequence, not its detectability. It is relevant only if one also fixes a per-sequence margin (the analogue of δ), which the paper never states.
- Fix: rewrite both sentences. Something like: "at a per-sequence margin Δ, a sequence-level comparison can only be meaningful if D(P‖Q) > Δ; the budget bounds the effect per sequence, not the evidence accumulated across sequences."

M5. The F1 budget, as stated, is not a valid finite bound.
- Location: Sec. 6, "2.57 nats in F1, of which 1.99 come from the noise-scale priors".
- Reason (VERIFIED in MATH_F1.md @ 3a29c15):
  - The population prior is σ² ~ IG(3, 2), which has support (0, ∞).
  - The context-only prior is log σ ~ U(log 0.01, log 100), with compact support.
  - P therefore puts positive mass where Q has zero density, so D(P‖Q) = +∞ and the stated inequality is vacuous.
  - The mass is tiny: P(σ > 100) = 1.33e-12 (DERIVED by my own computation; it also appears as "pop_mass_outside" in theory.json @ cd2759f). The reported 1.99 is the divergence computed on the overlapping support.
- Practical effect on the maps is negligible. Correctness of a displayed bound is not.
- Fix: define the budget for P restricted to Q's support and bound the residual, or use a context-only prior with full support. State this in the text.

M6. Reproducibility artefacts are referenced but not provided.
- The paper's distinctive claim is that "every result number … is re-extracted from a result file at a pinned commit" (Sec. 9) and that disclosure logs are "released with the code (anonymised for review)" (LLM statement).
- The manuscript contains no code, data or supplementary link (VERIFIED: no URL or repository mention in sections/*.tex).
- Reviewers cannot inspect the references, the maps or the claims pipeline that Contribution (i) and (iv) rest on.
- Fix: provide an anonymised repository or archive and a data/code availability statement.

======================================================================
4. MINOR WEAKNESSES
======================================================================
m1. The definition of PARTIAL in Sec. 5 is wrong for some cells.
- The paper says a PARTIAL cell "means that some libraries are separable from the continuous prior and others are not".
- In the F1 map, all 18 K = 32 cells are PARTIAL while 0% of (cell, draw) pairs are separable (VERIFIED: f1_map_decisions.csv @ 66c5846, mean frac_lo_ge_delta = 0.000 at K = 32, no IDENTIFIABLE or UNIDENTIFIABLE cells). There, PARTIAL means "some draws borderline".
- Reword, or split PARTIAL into "mixed separable" and "mixed borderline".

m2. The K^{-2/p} heuristic for the nearest-system limit does not match the authors' own Monte Carlo values.
- Known σ (p = 1): 0.0242 at K = 4 to 0.000105 at K = 256 implies a slope of about −1.31, not −2.
- F2 (p = 7): 1.24 at K = 2 to 0.091 at K = 1024 implies a slope of about −0.42, against a predicted −0.29 (DERIVED from theory.json).
- My own Monte Carlo of E[min_k (a − a_k)²/(2(1 − a²))] gives 0.0259 ± 0.0012 at K = 4, 0.0108 at K = 8 and 0.0035 at K = 16, close to the paper's values. The slow approach to K^{-2} comes from the low prior density near |a| = 0.95.
- Either drop the rate or say it is only asymptotic.
- The 32 (scalar) and 8 (F2) library draws also make the theory values noisy: e.g. the F2 ratio between K = 64 and K = 256 is only 1.27. Report SEs in Fig. 3 (right).

m3. Cross-map comparisons mix estimators and sample sizes.
- 1A uses a Rao-Blackwellised per-context KL with N = 40,000; F3 uses realised targets (STAGE1_SEPARABILITY_MAP_SPEC.md §3; SE ≈ 0.0004 in 1A vs ≈ 0.0015–0.002 in F3, VERIFIED).
- The grids also differ ({1, 2, 3, 5, 10, …} vs {2, …, 9}).
- The F3 10× rerun helps. Put the per-map estimator and N in Table 1 so readers do not read precision differences as family differences.

m4. Table 3 has two rows labelled "(the maps)" for the identical known-σ configuration, with different numbers.
- r = 0.25: 0.049 vs 0.047. r = 1: 0.045 vs 0.041 (VERIFIED in sensitivity.csv @ 763e82b; independent samples).
- Say so, or merge the rows. Also report the prior budget for each τ, since the text says the windows move "as the budget predicts" but gives no budget values for τ = 0.15 and 0.6.

m5. Figure 1 does not compare like with like.
- The middle and right panels start at n = 2 and are compared with the full budget. "By n = 40 the noise-free family has spent up to 0.43 of its 0.58 nats" omits the n = 0, 1 terms; 1A's cumulative at n = 40 including them is 0.48–0.51 (VERIFIED in cumulative.csv).
- The middle panel's x-axis has a single tick label.

m6. The "per-item SE ≤ 0.01" statement for F2 (Sec. 4) is imprecise.
- The MC rule allows up to 1% of items to exceed the per-item target (STAGE2_F2_MAP_SPEC.md l. 27–29).
- The batch-5 split shows flagged items, e.g. 11 of 4000 at r = 1, n = 10.

m7. Horizon coverage is uneven: h = 5 appears only for F3; 1A, F1 and F2 are h = 1 only. Say this in Table 1 or extend.

m8. The conclusion overstates where the library question is visible: "the nearest-system limit locates where its answer would be visible by score: in our families, the bivariate one". Table 4 shows scalar libraries with K ≤ 4–8 are also separable. Rephrase as "only at small K in scalar families".

m9. A plain explanation of the noisy-family claim is missing. The noisy observations y are a garbling of x, so D_noisy(N) ≤ D_clean(N) for every N, with both tending to D(P‖Q) when a is identifiable. This is cleaner than "spread over more forecasts", and it also bounds the finite-N statement "the total population advantage does not [shrink]", which holds only as N → ∞. (Check that the conditioning on x_0 vs y_0 is consistent.)

m10. Presentation.
- The internal labels (1A, F1, F2, F3, Stage 0/0.5/0.6) are opaque and out of order. Use descriptive names (KNOWN-σ, UNKNOWN-σ, NOISY, VAR).
- The abstract is very long and dense.
- "Linear Dynamical Systems" in the title suggests general state-space LDS; "autoregressive" is more accurate.
- Sec. 9 and Appendix B spend space on tooling details (HMAC authorization gate, a gate hole "to be included in the next frozen release", a numbers-audit linter) that do not bear on the scientific claims. Condense them.

m11. Related work. Worth discussing:
- Information-theoretic asymptotics of Bayes redundancy (Clarke & Barron 1990, IEEE Trans. IT 36(3):453–471; existence and content checked by web search). It gives the rate at which D(m_P^N‖m_Q^N) approaches D(P‖Q).
- Density-forecast comparison tests from econometrics, e.g. Amisano & Giacomini 2007, JBES 25:177–190 (checked by web search), which are the natural statistical frame for "separable by log score".
- Equivalence testing, since "not separable" is an equivalence decision.

m12. Bibliography. The Akram & Vikalo venue (TMLR 2026) is not shown on the arXiv abstract page, but a web search shows an MLAnthology TMLR 2026 entry, so it is fine. Several 2026 arXiv citations are recent preprints; I checked four (see Section 7).

======================================================================
5. QUESTIONS FOR THE AUTHORS
======================================================================
Q1. For a network trained on the population, population Bayes is the risk minimiser (as you note in Sec. 10 and App. B). So the population-vs-context-only maps measure optimisation, not inductive bias. What behavioural hypothesis do these maps let a future study test that a simple "regret to population Bayes" curve would not?

Q2. Can you give n*(δ) curves and a principled recipe for choosing δ (or a per-sequence margin) from seed variance and the number of models?

Q3. Do the pilot's convergence records (validation NLL across seeds, which are not effect-bearing) give any estimate of between-seed SD at short contexts? That would directly inform M1.

Q4. For F2, what are D1, N1, D2 and N2 at n = 20, and how large is the interaction there? Can you build a dynamics-only comparator whose coefficient prior is the population's marginal?

Q5. How was the 2.57 / 1.99-nat budget handled given the support mismatch in F1? Was the restriction to [0.01, 100] intended?

Q6. Why are in-library evaluations (where memorisation would also show) absent from the main text, given that Stage 0 found library and continuous posteriors equivalent on in-library systems in all 48 cells?

Q7. How many library draws underlie each theory value in Fig. 3 (right)? Are the non-monotone ratios (e.g. F2 K = 64 → 256) Monte Carlo noise?

======================================================================
6. REQUESTED CHANGES
======================================================================
Required for acceptance:
R1. Correct the F2 decomposition claim (M3): report both paths and the interaction, and remove or qualify "mostly dynamics" in the abstract, introduction and conclusion.
R2. Rewrite the pooling statements (M4).
R3. Fix the F1 budget (M5).
R4. Retitle, or clearly separate confirmatory from exploratory results, with a provenance table of when each analysis was specified and what had been seen (M2).
R5. Provide anonymised code, data and the claims pipeline (M6).
R6. Fix the PARTIAL definition (m1), the duplicate "the maps" rows (m4), and the Fig. 1 baseline issue (m5).
R7. Strengthen the link between the maps and behavioural classification (M1). At minimum, (b) plus (c); preferably a small neural demonstration.

Would strengthen the work:
- A small trained-model demonstration in the F2 library setting, where the maps predict that the memorisation/generalisation question is actually visible.
- h > 1 for all families.
- Sensitivity analyses for F2 and F3 priors and comparators.
- The garbling argument for observation noise (m9).
- The Clarke–Barron asymptotics and density-forecast tests in related work (m11).
- Descriptive family names and a shorter abstract (m10).
- Moving tooling details to the supplement.

======================================================================
7. CHECKS I RAN
======================================================================
Theory (my own Python, scratchpad check_theory.py):
- 1A budget KL(TN(0.4, 0.3²; ±0.95) ‖ U(±b)): 0.5313 / 0.5816 / 0.5825 for b = 0.95 / 0.999 / 0.9999. Matches theory.json and the paper's 0.58 — VERIFIED.
- F1 noise-scale part (IG(3, 2) vs log-uniform), on Q's support: 1.2955 / 1.9887 / 2.3941 for [0.1, 10] / [0.01, 100] / [0.001, 1000]. Matches the paper's 1.30 and 1.99 — VERIFIED. 1.99 + 0.58 = 2.57 — DERIVED.
- P(σ > 100) = 1.33e-12 > 0, hence D(P‖Q) = ∞ (M5) — DERIVED.
- Nearest-atom limit, known σ (4,000 Monte Carlo replicates): 0.0259 ± 0.0012 at K = 4, 0.0108 at K = 8, 0.0035 at K = 16, 0.00047 at K = 64, 0.00006 at K = 256. Consistent with the paper's 0.024, 0.011 and 0.004. The slope is not K^{-2} (m2).
- Chain-rule and data-processing derivation in Sec. 6 checked by hand — correct.

Map tables (scratchpad check_maps.py, reading pinned CSVs with `git show`):
- Table 1: every entry reproduced from map_decisions.csv @ a499874 (1A), f1_map_decisions.csv @ 66c5846 (F1), map_decisions.csv @ 50a7664 (F3) and @ 56e73a8 (F2). This includes the gap ranges, the window ends, the borderline-with-estimate-≥ δ counts (1/3/1; 5/4/0; total 14, 9 at q = 0.755), and that no F3 h = 5 cell is separable — VERIFIED.
- Table 2 (δ = 0.01 / 0.02 / 0.04 at r = 1): reproduced exactly — VERIFIED.
- Table 4 (1A and F1 rows): pooled frac_lo_ge_delta reproduced (92 / 53 / 19 / 8 / 0…; 100 / 99 / 91 / 61 / 10 / 0…) — VERIFIED.
- Text library counts: 1A K = 1 12/18 IDENTIFIABLE; K ≥ 16 all UNIDENTIFIABLE; F1 K = 4 12/18; K = 16/32 all PARTIAL; K = 256 all not separable; F2 K = 16 15/15 and K = 64 13/15 — VERIFIED.
- Batch 5 (e08eee8):
  - split.csv: F1 dense windows n ≤ 14 (r = 0.25) and n ≤ 12 (r = 1); noise-matched windows n ≤ 5, 5, none (borderline at n = 2, r = 4); F2 T separable at n ≤ 20, borderline at n = 40 for all r, not separable at n = 80 — VERIFIED. F2 path reversal (M3) — VERIFIED.
  - cumulative.csv: 1A sums 0.551 / 0.554 / 0.558 at n = 160; F3 at n = 40: max 0.434 (q = 0), 0.150 (q = 6.5) — VERIFIED.
  - f2_library.csv: all K ≤ 1024 SEPARABLE at n = 80 for every r, K = 1024 means 0.067–0.082 — VERIFIED.
  - f1_library_long.csv: K = 16 at n = 160 means 0.032–0.037, shares 0.59–0.66 — VERIFIED.
- sensitivity.csv @ 763e82b: σ-agnostic max 0.384 with n = 20 IDENTIFIABLE; the two "maps" rows differ (m4) — VERIFIED.

Method documents:
- MATH_F1.md: priors and supports — VERIFIED.
- STAGE1_SEPARABILITY_MAP_SPEC.md: Rao-Blackwellised estimator, 3-SE rule, 90% draw rule — VERIFIED.
- STAGE2_F2_MAP_SPEC.md: MC-LIMITED rule with the 1% item allowance — VERIFIED.
- STAGE2_BATCH5_SPEC.md: "Seen before this spec" paragraph, and the ctx_dm caveat — VERIFIED.

Citations (web):
- Koshelev et al. 2023: the AR(1) quote "the Bayesian model knows a little more information" and the MSFE/LPS comparison — VERIFIED in the arXiv PDF.
- Cao et al. 2026: exponential coefficients; beats OLS, ridge and ℓ1 at k ≤ 30; "implicit prior inference" — VERIFIED (arXiv HTML).
- Aswadi et al. 2026: point-prediction comparisons are "fragile" — VERIFIED (abstract).
- Gibson et al. 2026: finite sets of Markov chains, memorise/generalise phases — VERIFIED (abstract).
- Wakayama & Suzuki: Bayes Gap; task-mixture uncertainty vanishes exponentially fast — VERIFIED (abstract).
- Raventós et al. 2023: below and above the diversity threshold — VERIFIED (abstract).
- Zhang & Gilpin: context parroting, ICLR 2026 — VERIFIED.
- Akram & Vikalo: TMLR 2026 per an MLAnthology search result — VERIFIED (secondary).
- Haussler & Opper 1997: content confirmed only through the technical report and secondary sources — partially VERIFIED.
- Not checked: Lu et al. 2025, Panwar et al. 2024, Cole et al. 2025, Falck et al. 2024 and the rest — UNVERIFIED.

Not done: I did not run the authors' build_claims.py (it may write files), and I did not re-run any map.

======================================================================
8. RECOMMENDATION
======================================================================
Major revision. Score 5/10.

Criterion 1 (claims supported by accurate and convincing evidence):
- Where I could check, the numerical evidence is accurate. Every table entry I recomputed matched the pinned files, and the budgets and nearest-system limits reproduce independently.
- Several headline interpretive claims go beyond that evidence:
  - the F2 "mostly dynamics" decomposition is order-dependent (M3);
  - the pooling statements misread the bound (M4);
  - the F1 budget is formally infinite as defined (M5);
  - the "pre-registered" label covers analyses chosen after seeing results (M2).
- The motivating claim, that per-cell separability at δ = 0.02 is the relevant precondition for behavioural classification, is untested, and δ is not tied to anything measurable (M1).
- All of these can be fixed, mostly by rewording and adding analyses, without new large-scale compute.

Criterion 2 (interest to some of TMLR's audience): met.
- Researchers who compare in-context learners with Bayes references will find the budget argument, the nearest-system limit and the scalar-vs-bivariate library contrast useful when designing experiments. The candid reporting of nulls is valuable.
- The interest would rise substantially with even a small trained-model demonstration that the maps predict where classification is possible.

Sources (web): https://arxiv.org/abs/2308.05753 ; https://arxiv.org/html/2603.18564 ; https://arxiv.org/abs/2607.17060 ; https://arxiv.org/abs/2604.12151 ; https://arxiv.org/abs/2510.10981 ; https://arxiv.org/abs/2306.15063 ; https://arxiv.org/abs/2505.11349 ; https://arxiv.org/abs/2410.16546 ; https://mlanthology.org/tmlr/2026/akram2026tmlr-transformers/ ; https://tr.soe.ucsc.edu/research/technical-reports/UCSC-CRL-96-27 ; https://scilit.com/publications/b52ffd7b0743b3448b85465243c94fe9 ; https://econpapers.repec.org/RePEc:bes:jnlbes:v:25:y:2007:p:177-190
```
