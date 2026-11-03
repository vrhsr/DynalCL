# Manuscript changelog (branch `paper-revision`; original preserved on `paper-draft` @ `bd4d390`)

Decisions: the user's checkpoint-1 decisions of 2026-11-01 (disclosure S40). Every number below is a macro pinned in
`numbers.yaml` / `claims.yaml`; build after this change: claims PASS (50 verified), 93 macros, numbers audit PASS (16 section
files), Track 1 PDF 14 pages with no overfull box, Track 2 PDF built.

## Revision 1 (commit: see `git log` on `paper-revision`; first revision commit after `3edab95`)

| # | Change | Where | Type | Approved by |
|---|---|---|---|---|
| 1 | Title "Where Bayesian References Disagree: Pre-Registered Separability Maps for In-Context Learning of Linear Dynamical Systems" | main.tex | title | decision 4 |
| 2 | "identifiable / unidentifiable" -> "separable / not separable at margin delta"; note that the result files keep the old labels; one sentence on why "identifiable" is avoided | 05_design, 06_results, 07_pilot, table captions | terminology | decision 4 |
| 3 | New Section 6 "Two quantities that bound the maps": chain-rule budget (cited as classical: Cover and Thomas; Haussler and Opper for the single-prior analogue), its three consequences, budgets per family, nearest-system limit and its K^(-2/p) heuristic | 05b_theory.tex (new) | reframing (content) | decision 1 |
| 4 | Abstract, introduction contributions, results and conclusion reframed around the two quantities; F1/F2 larger gaps attributed mostly to noise-level knowledge (budgets pinned at `cd2759f`); "observation noise shrinks it" -> the same budget spread over more forecasts | 00, 01, 06, 10 | reframing (content) | decision 1 |
| 5 | "we report how [the conclusions depend on the comparator and prior]" removed (batch 4 not delivered) | 00_abstract | correction | decision 5 |
| 6 | F2 sentence: "0.070-0.338 at the longest contexts mapped" -> "up to 0.338 at n = 10 and 0.070-0.089 at the longest mapped context, n = 20 ... end of the window not mapped" (claim F2-LONGEST) | 06_results | correction | decision 5 |
| 7 | Margin-table sentence "the unknown-noise family keeps the widest window" (false) replaced; \FoneMaxN (F1 quantity) replaced by \OneAMaxNHalfDelta (claim MAP-1A-HALF-DELTA) | 06_results | correction | decision 5 |
| 8 | Numbers written as words above ten (sixteen, sixty-four, thirty-two, eighty, nine in ten, four orders of magnitude, hundredths) replaced by macros or reworded; `check_numbers.py` now fails on number words above ten | sections, tools | pipeline | decision 5 |
| 9 | Bivariate libraries described as seven-parameter (A: 4, Sigma: 3), not "four-coefficient"; the library result explained by the nearest-system limit instead of an untested hypothesis | 03, 05b, 06, 08 | correction | decision 5 |
| 10 | F2 context-only prior stated (V0 = 100 I, IW(1.5, 0.01 I), radius < 0.999; claim DESIGN-F2-CTX); F1 range as [0.01, 100] from MATH_F1 | 03_setting | completeness | decision 5 |
| 11 | Wurgaft et al. no longer cited for Markov chains; Park et al. 2025 (verified arXiv record, ICLR 2025) added | 01, 02 | citation fix | decision 5 |
| 12 | Koshelev et al.: "in a toy example in its appendix" -> "in a toy example in the main text" (quote located in Section 4.1 of the arXiv PDF, model in Appendix B.1; checked with pdftotext) | 02_related | citation fix | decision 5 |
| 13 | Related work rewritten with verified additions: Garg, Akyurek, Xie, Nguyen-Reddy, Goddard, Park, Jeon, Falck, Li et al., Sander et al., Goel-Bartlett, Du et al., Akram-Vikalo, Box-Hill, Atkinson-Fedorov, Lopez-Fidalgo et al., Haussler-Opper, Cover-Thomas; the "not reviewed" sentence on optimal design replaced | 02_related, references.bib | literature | decision 5 |
| 14 | Bibliography: full given names, venues, volumes, pages, DOIs from primary records; arXiv-only entries marked; Sellam et al. ICLR author order | references.bib | bibliography | decision 5 |
| 15 | Expected number of wrongly marked held-out cells stated (< 1 per map, from Phi(-3)); closes the 1A map spec's unmet promise | 05_design, 08_limitations | completeness | decision 5 |
| 16 | Pilot: control failure at the first grid point and "for every pilot model" added (Reviewer 2); neural redirection sentence replaced by the reason Q1 is predictable for converged networks and Q2 is the open question | 07_pilot | content | decisions 3, 5 |
| 17 | Limitations updated (budgets bound comparator dependence; grids and censoring; long-context limit assumptions) | 08_limitations | content | decisions 1, 5 |
| 18 | Table 1 restructured to one row per (family, r) with a notes column: the original was 278 pt wider than the text block; windows with holes printed as sets; star where a window reaches the last grid point; Table 2 stars | make_tables.py | table | decision 5 |
| 19 | Extractors: `ge`/`lt` filters for csv max/min, `csv_min_all`, `json_keys`; new claims LIB-1A-ALL, F2-LIB-KMAX, F2-LONGEST, MAP-1A-HALF-DELTA, DESIGN-DRAWS, DESIGN-F2-CTX, DESIGN-B5-GRID, THEORY-KL, THEORY-NA; LIB-F1 extended (longest library n) | tools, claims.yaml, numbers.yaml | pipeline | decision 5 |
| 20 | Track 2 skeleton includes the new theory section (it reuses Track 1 sections) | main_track2.tex | build | - |

## Revision 1a (user's approval of revision 1, 2026-11-01)

| # | Change | Where | Type | Approved by |
|---|---|---|---|---|
| 21 | Q1 sentence softened to the user's wording: population Bayes minimises expected log loss, so a network at the population-risk minimum would equal it; at finite capacity and budget the population-vs-context-only comparison measures how close training gets; library memorisation vs generalisation is the open question the nearest-system limit locates. "predictable answer" and "almost by construction" removed | 07_pilot, 10_conclusion | content (softened) | user, item 1 |
| 22 | LLM-use statement added as an unnumbered section (anonymised; no author, repository or machine names), in Track 1 and Track 2; the bracketed sentence uses the replacement wording "read the final text and checked the main claims against the claims-to-evidence table" (the user's template choice was left unfilled; the more modest wording was used, easy to switch) | sections/11_llm_use.tex, main.tex, main_track2.tex | statement | user, item 2 |

## Revision 1b: figures (`ac23b13`)

| # | Change | Where | Type | Approved by |
|---|---|---|---|---|
| 23 | Figure 1 (gap vs n per family; filled = separable, open = not, cross = MC-limited; delta dashed) and Figure 2 (library share vs K; nearest-system limit vs K; marked provisional until batch 5) generated by `tools/make_figures.py` from the files pinned in the new `figures:` block of numbers.yaml; run by build.py; pgfplots (no new Python dependency) | 06_results, main.tex, main_track2.tex, build.py | figures | user (figures go-ahead) |

## Revision 2: batch 4 sensitivity results (verified S45; pinned `763e82b`)

| # | Change | Where | Type | Approved by |
|---|---|---|---|---|
| 24 | New Table 3 (generated from a `tables.sensitivity` block in numbers.yaml): comparator frontier and prior dependence for the known- and unknown-scale families, and the noisy family at ten times the sample size; new results paragraph | 06_results, make_tables.py, numbers.yaml | results | plan (S39, S40) |
| 25 | F3 moderate-noise window at ten times the sample size added to the F3 sentence (q = 0.755: n <= 5 / 4 at r = 0.25 / 1) | 06_results | results | as above |
| 26 | Abstract: "Varying the comparator and the population prior moves the windows as these budgets predict." (the removed "we report how" is now supported, for the scalar families) | 00_abstract | content | decision 5 of S40 (restore once batch 4 delivered) |
| 27 | Limitations: priors/comparators now varied in the two scalar known/unknown-scale families (not noisy, not bivariate); F3 power bullet updated | 08_limitations | content | as above |
| 28 | Claims SENS-FRONTIER-1A, SENS-PRIOR-1A, SENS-FRONTIER-F1, SENS-F3; 11 new macros | claims.yaml, numbers.yaml | pipeline | - |

Build: claims 54 verified, 104 macros, numbers audit PASS, 17-page PDF, no overfull box.

## Revision 3: batch 5 results (verified S46; pinned `e08eee8`)

| # | Change | Where | Type | Approved by |
|---|---|---|---|---|
| 29 | **Correction of revision 1:** "the larger gaps when the noise scale is unknown or the system is bivariate ... mostly knowledge of the noise level" was true for F1 and for the F2 prior budget, but the split shows the F2 gap at the mapped contexts (n >= 10) is mostly dynamics; abstract, introduction, theory, results and conclusion corrected | 00, 01, 05b, 06, 10 | correction | S40 decision 2 (split) |
| 30 | F1/F2 split reported (symmetric two-path parts; F1 dynamics-only window n <= 5 as in the known-scale family); F1 window on the denser grid (n <= 14 / 12); F2 window ends between n = 20 and 40 | 06_results | results | as above |
| 31 | Cumulative gaps vs budget: new Figure (1A summed to n = 160 is 0.551-0.558 vs 0.582; noisy family spends the same budget more slowly; F1 dynamics part below its 0.582 budget) | 05b, 06, make_figures.py | results, figure | S40 decision 1 |
| 32 | F2 libraries to K = 1024 and n = 80 (all separable at n = 80); F1 libraries to n = 160 (K = 16 mean at its limit, 59-66% of libraries separable); library figure no longer provisional, second bivariate series added, legend moved below the axes | 06, numbers.yaml figures | results, figure | user (figures; provisional until batch 5) |
| 33 | Limitations: grids (F1/F2 window ends now located), long-context limit (mean vs per library), split labels approximate in F2 | 08 | content | - |
| 34 | Claims B5-SPLIT-F1, B5-SPLIT-F2, B5-CUM, B5-F2-LIB, B5-F1-LIB; 25 macros | claims.yaml, numbers.yaml | pipeline | - |

| 35 | (user spot-check) F1 against the noise-matched reference: window n <= 5 at r = 0.25 and r = 1, empty at r = 4 (borderline at n = 2 only; dynamics part 0.031 of 0.326 nats; the report's 0.0315 is 0.031472, so 0.031 at three decimals); abstract wording "at short contexts at most"; claim B5-SPLIT-F1-R, 3 macros | 06_results, 00_abstract | results | user |

Build: claims 60 verified, 132 macros, numbers audit PASS, 18-page PDF, no overfull box.

## Revision 4: TMLR format, history appendix, anonymity (user go-ahead S49)

| # | Change | Where | Type |
|---|---|---|---|
| 36 | TMLR style (official `tmlr.sty` / `tmlr.bst` from github.com/JmlrOrg/tmlr-style-file, Apache-2.0, licence copied); submission mode (anonymous authors, author-year citations); 15 pages | main.tex, main_track2.tex | format |
| 37 | Stage 0 / 0.5 / 0.6 history moved from Sections 5-7 to Appendix A (all numbers still macros); the neural pilot moved to Appendix B, with a pointer in Section 9 | 05, 06, 09, new 12_appendix_history, main.tex | structure |
| 38 | Anonymity: the sentence on the project's working name (which led to the public repository) removed; PDF text and metadata checked for identifying strings (none) | 02_related | anonymity |

Build: claims 60, 132 macros, numbers audit PASS (18 section files), Track 1 15 pages without overfull boxes.

Not yet done (planned): figures (gap vs n with bands; library share vs K against the nearest-system limit; cumulative gap vs
budget, after batch 5); results of batches 4 and 5; the LLM-use statement (draft awaiting approval); author names; appendices;
restructuring of the Stage 0/0.5/0.6 history into an appendix; TMLR template.

## Revision 5: corrections from the second independent (AI-simulated) review

Review saved in `INDEPENDENT_SECOND_REVIEW.md`; what it found that the first audit missed is in
`REVIEWER_DISAGREEMENT_ANALYSIS.md`.

| # | Change | Where | Type | Review item |
|---|---|---|---|---|
| 39 | **Correction of revision 3:** "the F2 gap at the mapped contexts is mostly dynamics" depends on the order of the split (r = 1, n = 10: noise first 0.213 noise / 0.122 dynamics; dynamics first 0.099 / 0.236). Both orders now reported for F1 and F2; F1 is noise-dominated in both orders; for F2 no part is said to dominate (the conjugate prior makes the dynamics-first reference's marginal coefficient prior differ from the population's) | 00, 01, 06, 08, 10 | correction | M3 |
| 40 | Pooling: the budget bounds the per-sequence effect, not the evidence pooled over sequences or items; the old sentences ("bounds how much such pooling can gain", "bounds what any pooling ... can gain") were wrong and are replaced; the margin is described as a design choice tied to model count and seed variance | 05_design, 08 | correction | M4, M1 (part) |
| 41 | F1 budget: the population noise prior puts mass 1.3e-12 outside the context-only range, so D(P‖Q) is formally infinite; the reported value is for the restriction to that range (new macro from theory.json) | 05b_theory | correction | M5 |
| 42 | New Appendix B "Provenance of the maps and analyses": "Pre-registered" in the title refers to the studies of Appendices A and C; for each map or analysis, what was seen before its specification; contributions (iii)/(iv) reworded | 01, 12_appendix_history | content | M2 |
| 43 | PARTIAL definition corrected (draws disagree, including all-borderline cells such as F1 K = 32) | 05_design | correction | m1 |
| 44 | K^{-2/p} stated as asymptotic only; the decay at the evaluated K is slower, so the Monte Carlo values are used | 05b_theory, 08 | correction | m2 |
| 45 | Estimator and sample size of each map stated (four claims DESIGN-N-*, eight macros from the pinned specs; `regex_int` now accepts "40 000") | 05_design, claims.yaml, numbers.yaml, build_claims.py | content, pipeline | m3 |
| 46 | Table 3: the repeated baseline row labelled "same setting as above" | numbers.yaml | table | m4 |
| 47 | Cumulative noisy-family sentence: the sums start at n = 2, the budget also covers n = 0, 1 | 06 | correction | m5 |
| 48 | F2 Monte Carlo criterion stated as in the spec (target per-item SE; at most 1% of items over target; cell MC SE below delta/100) | 04_validation | correction | m6 |
| 49 | Limitations: horizons (one-step maps; F3 also h = 5; budget argument one-step only) | 08 | content | m7 |
| 50 | Conclusion: "in our families, the bivariate one" -> "only the bivariate one at large library sizes" | 10 | wording | m8 |
| 51 | Garbling argument for observation noise (noisy cumulative gap never exceeds the noise-free one) | 05b_theory | content | m9 |
| 52 | Citations added, both checked on Crossref: Clarke and Barron 1990 (doi 10.1109/18.54897), Amisano and Giacomini 2007 (doi 10.1198/073500106000000332) | references.bib, 02, 05b | citation | m11 |

Not done from the review (decisions for the user): title qualification of "Pre-Registered" (M2; the user approved the
title), an anonymised code artefact (M6), an n*(delta) curve (M1, optional), abstract shortening and tooling condensation (m10).

Build: claims 65 verified / 0 pending, 149 macros, numbers audit PASS (18 section files), Track 1 16 pages without overfull
boxes or undefined references.

### Revision 5a

| # | Change | Where | Type | Review item |
|---|---|---|---|---|
| 53 | Item 50 corrected: the review's point was that small scalar libraries are also separable, so the conclusion now says "at small library sizes in every family we mapped, and at large ones only in the bivariate family" | 10 | correction | m8 |
| 54 | Cumulative figure, noisy panel: tick labels at n = 2, 5, 10, 20, 40 (optional per-panel `opts` in the cumulative figure block) | numbers.yaml, make_figures.py | figure | m5 |

## Revision 6: title, margin curves, F2 split at n = 20, shorter abstract (user decisions S51)

| # | Change | Where | Type | Source |
|---|---|---|---|---|
| 55 | Title: "Where Bayesian References Disagree: Separability Maps for In-Context Learning of Linear Dynamical Systems" ("Pre-Registered" dropped); Appendix B now says "pre-registered" in this paper means only the studies of Appendices A and C | main.tex, 12_appendix_history | title | user S51 (review M2) |
| 56 | New Figure 3: largest separable n against the margin (240-point log grid, 0.003-0.6 nats), per map and series, from the pinned map files; MC-limited cells excluded; labelled post hoc in the text, caption and Appendix B. Agrees with Table 2 at its three margins | make_figures.py (`delta_curves`), numbers.yaml, 06_results | figure (post hoc) | user S51 (review M1(c), Q2) |
| 57 | F2 split at n = 20 in both orders for every r (claim B5-SPLIT-F2-N20, 12 macros): dynamics larger in both orders at r = 0.25, equal parts with noise first and dynamics larger with dynamics first at r = 1, order-dependent at r = 4 | 06_results, claims.yaml, numbers.yaml | results (post hoc reading of pinned files) | user S51 (review Q4) |
| 58 | Abstract shortened from 402 to 277 words; every number still a macro; dropped: the 1A gap range, the sentence on comparator and prior sensitivity, the noise-matched clause | 00_abstract | presentation | user S51 (review m10) |

Build: claims 66 verified / 0 pending, 161 macros, numbers audit PASS, Track 1 17 pages without overfull boxes.
