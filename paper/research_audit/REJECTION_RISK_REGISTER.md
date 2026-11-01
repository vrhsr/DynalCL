# Rejection risk register (Phase 1)

Probability and impact are my judgement (H/M/L) for a TMLR submission of the current draft; "after fix" assumes the listed
CPU-only correction is done. No acceptance is ever guaranteed.

| # | Risk | Prob. now | Impact | Mitigation (GPU?) | Prob. after fix |
|---|---|---|---|---|---|
| R1 | Reviewer shows the F1/F2 "wider windows" are comparator artefacts (any reviewer with a calculator can: noise-only gap, prior KL) | H | Fatal for the headline | Noise-matched comparator maps; decomposition; reword (n) | L |
| R2 | "Findings follow from textbook theory" | H | Fatal for interest | Theory section; maps validate it; predict an unmapped family first (n) | M (becomes a strength if done well) |
| R3 | No neural result: "of interest to whom?" | H | High | Frame as a predictive design theory + validated references; optional small neural probe (y) | M |
| R4 | False or misattached sentences found (F2 range, Table 2 ordering, "we report how") | H (three exist) | Medium (credibility of a paper selling rigour) | Fix; add semantic checks to the pipeline (n) | L |
| R5 | "Identifiable" terminology objection | H | Medium | Rename (title needs approval) (n) | L |
| R6 | "Observation noise shrinks population knowledge" contradicted by the budget argument | M | Medium | Per-forecast wording; cumulative figure (n) | L |
| R7 | Library conclusions grid-dependent (F1 long n) | M | Medium | Asymptotic per-K KL; state n-ranges; extend grid (n) | L |
| R8 | Reads as a project log; no figures | H | Medium | Restructure; Figures A-C (n) | L |
| R9 | Thin related work / miscitation | H | Medium | Verified additions (n) | L |
| R10 | Pre-registration seen as process, not science | M | Low-medium | Shorten; frame as why nulls are trustworthy (n) | L |
| R11 | delta arbitrary | M | Medium | Cumulative / pooled criterion; gap / required-seed-sd per cell (n; seed sd y) | M |
| R12 | Double-blind violation (public repo, box paths, git authors) | M (if the repo is linked) | Desk reject | Anonymised artefact; no repo link in the review version (n) | L |
| R13 | LLM-assisted research and writing undisclosed | M | Policy issue (venue-dependent; UNVERIFIED for TMLR) | Check the venue policy; write an LLM-use statement; authors take responsibility for every claim (n) | L |
| R14 | Batch 4 returns results that change a stated conclusion (e.g. prior dependence) | M | Medium | Do not state those conclusions until the branch is verified (n) | L |
| R15 | Venue mismatch (main-track bar) | H for main track | High | Target TMLR for the reference/theory paper; main track only with a predicted-then-confirmed neural transition (y) | - |
