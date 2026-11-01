# Related-work gaps (Phase 2)

Current related work: four short paragraphs, 18 entries, surnames only (VERIFIED, `references.bib`, `02_related.tex`). BibTeX for
every item below is in LITERATURE_REVIEW.md section 5 (VERIFIED from primary records unless flagged there).

## Errors to fix in existing citations

| Key | Problem | Source |
|---|---|---|
| wurgaft2025 | Cited for discrete Markov chains; its tasks are Balls & Urns, regression, classification | Reviewers 1, 3 (arXiv HTML) |
| koshelev2023 | "in a toy example in its appendix": the quoted sentence is in the body (App. B.1 holds the AR(1) material per BIBLIOGRAPHY.md; Reviewer 3 says the figure is in App. A); also an SSRN working paper | literature agent; Reviewer 3 |
| sellam2022 | ICLR author order has Tenney third; "others" must be expanded | OpenReview |
| cole2025 | proceedings title casing | NeurIPS proceedings |
| all | given names, volumes, pages, DOIs | literature agent table |
| 6 entries | arXiv-only: mark as preprints (gibson2026, aswadi2026, talts2018, zhou2023dynaicl, cao2026, koshelev2023) | literature agent |

## Missing literature, by the argument it supports

| Argument in the paper | Missing works |
|---|---|
| ICL compared with optimal estimators (the template) | Garg et al. 2022; Akyurek et al. 2023; von Oswald et al. 2023; Bai et al. 2023; Xie et al. 2022 |
| Memorisation-to-generalisation transition | Nguyen and Reddy 2025; Goddard et al. 2025; Park et al. 2025 (Markov chains: the correct cite for that sentence); Lin and Lee 2024; Pathak et al. 2024; Kirsch et al. 2022 (arXiv) |
| ICL of AR processes, LDS, Kalman | Li et al. 2023; Sander et al. 2024; Goel and Bartlett 2024; Du et al. 2023 (IEEE CSL); Akram and Vikalo 2026 (TMLR); Zhou et al. 2025 (arXiv, LSA on AR(p)) |
| Information theory of ICL / Bayes | Jeon et al. 2024 (ICML); Wakayama and Suzuki 2026 (already cited) |
| The central theory (budget, nearest atom) | Clarke and Barron 1990, 1994; Barron, Rissanen, Yu 1998 (prequential / MDL) |
| "Asking where rival models' predictions differ" | Box and Hill 1967; Atkinson and Fedorov 1975; Lopez-Fidalgo et al. 2007; Chaloner and Verdinelli 1995; Rainforth et al. 2024 |
| Context-only comparator choice | Bernardo 1979 (reference priors); Clarke and Barron 1994 (Jeffreys) |
| Scoring | Gneiting and Raftery 2007 (strictly proper scores) |
| Premise challenges | Falck et al. 2024 (martingale test; note it assumes exchangeability, AR data are not) |
| Forecasting foundation models (motivation, future use of the references) | Chronos (TMLR), TimesFM, Moirai, ForecastPFN, Zeng et al. 2023, Tan et al. 2024 |
| Reproducibility / variance | Pineau et al. 2021 (JMLR); Henderson et al. 2018 |

## Must-read before writing the theory paragraph (content not yet read in this audit)

Clarke and Barron 1990 (the prior's log-density term in the cumulative risk), Lopez-Fidalgo et al. 2007 (KL-optimality), Jeon
et al. 2024 (error decomposition). The audit's derivations do not depend on them, but any sentence attributing a result to them
must be checked against the text.
