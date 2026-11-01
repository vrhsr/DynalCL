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

Not yet done (planned): figures (gap vs n with bands; library share vs K against the nearest-system limit; cumulative gap vs
budget, after batch 5); results of batches 4 and 5; the LLM-use statement (draft awaiting approval); author names; appendices;
restructuring of the Stage 0/0.5/0.6 history into an appendix; TMLR template.
