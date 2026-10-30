# Hostile review: "Identifiability First" (paper-draft @ 38ad11b)

Evidence via `git show` at pinned pairs. arXiv abstracts checked: 2510.10981, 2603.18564, 2607.17060, 2604.12151, 2506.17859, 2308.05753, 2502.08136.

## MAJOR

**M1. The library headline contradicts the authors' own evidence files** (00_abstract.tex:10-11, 06_results.tex:25-30, 10_conclusion.tex:5-6). "A finite library is almost never distinguishable from continuous-prior Bayes on natural evaluation sets" holds only for K >= 16. The pinned files show:
- Stage 0.5 confirmatory, E-CONT (held-out systems), K = 2 vs continuous: DISTINGUISHABLE in 26/36 cells.
- F1 map, HELD lib|pop: IDENTIFIABLE in 49/144 cells (K = 1 and K = 2 in all 36, K = 4 in 12/18, including n = 40). INLIB lib|pop: 21 identifiable.
- 1A map, HELD lib|pop, K = 1: 12/18 identifiable.
- F3 HELD pop-lib, K = 2: mean gap up to 0.097 nats (about 5 delta), but labelled PARTIAL in all 48 cells at q <= 0.755.

Sec. 6 omits the 1A, F1 and Stage 0.5 library results: selective reporting.

**M2. "PARTIAL" is undefined, and it hides separations.** It appears in 276 (1A), 253 (F1) and 735 (F3) cells and is never named in the paper. 05_design.tex:8 says only "fraction of independent library draws that agree". A trained model sees one library, so per-draw separability is the relevant quantity. Requiring every draw to agree makes small-K libraries "not identifiable" by construction. Draws differ by map (16 in F3, 32 elsewhere).

**M3. The paper claims "one pre-registered rule" but uses several** (00_abstract.tex:6-7, 01_introduction.tex:21-22, 05_design.tex:6-8).
- Stage 0 used separable/equivalent/"detectable_below_delta" labels and a flat-prior/OLS "frontier", not the stab reference.
- Stage 0.5 used mean +/- 2.24 SE with two replicates.
- Stage 0.6 used a max-|t| bootstrap.
- F1 marks negative estimates as IDENTIFIABLE (1046 cells with estimate < -delta), so its rule is two-sided |gap|, whereas Sec. 5 states a one-sided rule.
- F1 records no SE.

06_results.tex:4, :25-26 quote Stage 0 counts as if from this rule.

**M4. The gap is not a KL on most sets used** (05_design.tex:3-5). E[log p - log q] is an expected KL only when P is the data-generating predictive. That fails for lib|stab and lib|ctx on HELD, and for all OOS/PROBE sets, which the paper uses for its memorisation claims at 06_results.tex:29-30. There the gap can be negative (see F1), and "non-negative" is false.

**M5. The noise-free F3 row vs the 1A row is explained only partly** (06_results.tex:19-21; tab_maps.tex rows 1 and 3).
- The rows use different n grids: 1A uses {1, 2, 3, 5, 10, ...}, F1 uses {2, 3, 5, 10, 20, 40}, F3 uses 2..9. None of this is stated.
- At r = 0.25, F3 "n <= 7" vs 1A "n <= 5" is a grid artefact (1A has no n = 6 or 7, and 1A is 0.0163 at n = 10). It is not explained.
- At r = 4, the 1A window includes n = 1 (0.030), which F3 lacks. The SE explanation is correct only for n = 2-4: F3 0.0215 +/- 0.0015 vs 1A 0.0226 +/- 0.0003. F3 n >= 5 is UNIDENTIFIABLE, not borderline.
- The "pre-registered validity check" (map_checks.json ii) compares only 3 cells (r = 1; n = 2, 3, 5) with a loose |z| <= 4 bound, and max |z| = 2.19. It never tested r = 0.25 or r = 4, the rows where the table disagrees. "Agrees within sampling error" overstates it.

**M6. The F3 null is partly a power artefact** (00_abstract.tex:9-10, 01_introduction.tex:23 "erased", 06_results.tex:8-10).
- F3 SEs are about 5x those of 1A.
- At q = 0.755, n = 3-7 (r <= 1), point estimates are 0.020-0.024, i.e. above delta, yet they are BORDERLINE. At q = 0, r = 1, n = 6-8 they are also above delta and BORDERLINE.
- The table prints "none" and "n <= 2", which lumps BORDERLINE with UNIDENTIFIABLE.
- The F3 range n = 2..9 is never stated in the paper.
- "Short contexts do not rescue the advantage" and "erased" do not follow at q = 0.755.

**M7. The "context-only" reference is not context-only, and is it the strongest comparator?** (01_introduction.tex:12-13, 03_setting.tex:14-15).
- In family (a) stab is given sigma = 1, which is population knowledge.
- Whether "the stable interval" is |a| < 1 or the population's own truncation |a| < 0.95 is not stated. If it is 0.95, stab knows the prior's support.
- In F1, the population noise prior is IG(3, 2), which is informative (f1_mutation_matrix.json), while ctx gets an unspecified "vague" prior. The 0.316-nat gap at n = 2 may mostly reflect how vague that prior is. The "window opens" conclusion (06:10-12, 10:6) is comparator-dependent.
- There is no frontier of context-only predictors (OLS plug-in, flat-prior, weakly informative scale prior, parroting).

**M8. "Identifiable" conflates reference separation with what can be learned about a model.**
- Identifiability is a property of a statistical model. Here the label means "expected per-cell gap >= delta".
- Real classification of a network depends on between-seed variance and the number of models. The authors' own lookup (F1-LOOKUP: Q1 resolvable at M = 32 only if seed sd <= 0.01 nats) is defined as macros but never reported.
- Per-cell framing ignores pooled evidence: a sequence-level test can separate references where every cell is below delta. So 05_design.tex:13-14 ("can only be classified ... in cells where") is neither necessary nor sufficient.

**M9. No sensitivity analysis for delta, the prior or the grid** (05_design.tex:2-3). delta = 0.02 is asserted to be "practically meaningful" with no justification relative to measurable neural variance. Every conclusion turns on it: at delta = 0.01, 1A is identifiable to n = 10 at r <= 1. There is one population prior, N(0.4, 0.3) truncated at 0.95, and no ablation over prior concentration. Yet "rarely" is stated as a property of "scalar autoregressive families".

**M10. "Rarely" is contradicted by F1** (00_abstract.tex:7). F1 HELD pop|ctx is identifiable in 12/18 cells, and 1121/1512 F1 cells are IDENTIFIABLE overall.

**M11. Validation claims lack evidence or are weaker than stated** (01_introduction.tex:18-21, 04_validation.tex).
- "Each with ... mutation tests" has no claims-table entry for the known-scale or noisy families.
- All F2 validation statements (closed forms to 1e-10, nested quadrature, independent estimators, 04:23-27) have no evidence entry. F2-MAP is PENDING.
- The pass counts are near-vacuous as reported: Stage 0.5 T1 used z_crit = 4.95 and T2 a per-test level of 8.7e-7, and F1 used family alpha 0.01 over 180 tests. Thresholds and power are never stated.

**M12. Citations unsupported by the abstracts.**
- Cao 2026 (02_related.tex:12-13): the abstract says Transformers "consistently match or outperform" baselines across all settings. There is no short-context restriction and no least-squares framing.
- Koshelev 2023 (02:18-21), called "the closest work", is an agent-based-model forecasting paper whose abstract mentions no AR(1) prior. The quote needs a page reference or must go.
- Wakayama (02:10): theory with a defined Bayes Gap, not "a measured gap".
- Gibson (02:5): "Bayes references scored in nats" cannot be verified from the abstract.

**M13. The gate "fixed" claim is overstated** (09_methodology.tex:8-9). Disclosure S28/S34 shows the fix is a candidate on an unmerged backup branch, not in any frozen runner. Say "a fix was written; it is not yet in a frozen release".

## MINOR

- 03_setting.tex:4: "known sigma = 1", but Stage 0 used sigma in {0.25, 1} (summary.json). The Stage 0 regimes quoted at 06:4 are E-CONT, not held-out-map cells.
- 07_pilot.tex:6: the 96 GPU-h budget was itself raised by Amendment 1 (config/stage1.yaml:24 "was 48.0"). This is not disclosed. Also, the 25k-vs-50k choice rested on a 0.00015-nat exceedance with no uncertainty attached. Say so.
- 07_pilot.tex:7: "adequate power" has no stated power or effect size, and the cited lookup is F1's, not 1A's.
- 05_design.tex:9-10 promises "expected number of mis-marked cells reported with each map". It is not reported anywhere.
- 05:10-11 (specs before seeds) and 06:29-30 (edge-coverage confound) lack evidence entries.
- Caption "h = 1": the 1A and F1 files have no h column; unverifiable.
- 06:6 "monotonically": true for the per-q max, 47/48 cells; at q = 6.5 the gap *rises* with n (0.003 to 0.006).
- 01_introduction.tex:13-15: ridge with the correct lambda embeds the prior variance, and OLS is the context-only comparator. "Never separated" is overclaimed.
- 02_related.tex:25 novelty claim: classical model-discrimination design (Box-Hill) does exactly "where do references differ" before data. Missing: Garg 2022, Xie 2022, Goel-Bartlett / Du et al. (Kalman ICL).
- 09:9-10 "build fails if any other number": integers <= 10 and 10^-6, 10^-10 are exempt.

## NIT

- references.bib gives surnames only. Bertinetto "Preface" is a weak cite for pre-registration precedent.

## Verdict (TMLR): reject in current form

Careful reference engineering, but claims are selectively drawn from the maps, rules are mixed, and "identifiable" neither licenses nor forbids the neural conclusions it motivates.

## Five changes that would most improve the paper

1. Report all library results (1A, F1 and Stage 0.5, K = 1-4), define PARTIAL, and give per-draw distributions. Rewrite the library headline as "indistinguishable for K >= 16".
2. Use one rule and one estimator across maps. Fix the KL claim. Show BORDERLINE separately and state each map's n grid. Re-run F3 at 1A precision, or present it as underpowered.
3. Add sensitivity analyses: delta (0.005-0.04), prior concentration, and a frontier of context-only comparators, including a sigma-agnostic one in family (a) and several noise priors in F1.
4. Replace per-cell "identifiability" with a model-side power analysis: seed sd, M and a sequence-level test. Report the lookup.
5. Cut claims without evidence (F2 validation, mutation tests for (a) and F3, the gate "fixed" claim) and the unsupported citations (Cao, Koshelev). Disclose Amendment 1's budget change.
