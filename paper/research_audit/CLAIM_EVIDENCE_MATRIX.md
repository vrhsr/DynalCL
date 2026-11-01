# Claim-evidence matrix (Phase 0; classification as in Phase 3)

One row per claim in the abstract, introduction contributions, results and conclusion of `paper-draft` @ `bd4d390`.
Class: **A** supported by our results (file and commit) / **B** supported by literature / **C** plausible but not shown /
**D** unsupported or misleading / **E** needs new work. "Sufficiency" judges whether the evidence supports the sentence *as
worded* (the claims build checks numbers, not wording). Evidence commits: `main`=3632e9e, `s06`=18d34b0, `map1a`=a499874,
`f1map`=66c5846, `pilot`=e260526, `batch1`=50a7664, `batch23`=56e73a8, `f1val`=ac8aecb, `lookup`=c073522.

## Abstract (`sections/00_abstract.tex`)

| # | Claim (short) | Evidence | claims id | Class | Sufficiency / problem |
|---|---|---|---|---|---|
| AB1 | Behavioural statements are "only testable where the candidate references themselves make different predictions" | logic | - | C | Overstated: a pooled or sequence-level test can separate references whose per-cell gaps are below delta (the paper says so in Sec. 5). Say "classifiable cell by cell at margin delta". |
| AB2 | Three kinds of reference built and validated in four families | S0-T1/T2, S05-RELIABILITY, F1-VALIDATION, F1-V9, F2-VALIDATION, F2-V11, S06-MUTATION | yes | A | Sufficient. Known-scale mutation evidence (Stage 0 Colab) has no retained archive and is (correctly) not claimed. |
| AB3 | Known sigma: "population knowledge is worth 0.023-0.054 nats and is separable only at very short contexts" | map1a | S1A-MAP-Q1 | A (numbers) / D (wording) | The range is over IDENTIFIABLE cells only (selected on being large); the gap falls to 0.0006 at n = 80. "Worth" omits that it is relative to one comparator (uniform on (-0.999, 0.999)). |
| AB4 | Noise: largest gap 0.011 at q = 6.5; no cell separable at the two larger noise levels | batch1 F3 map (n = 2..9) + s06 (n = 10..40) | F3-MAP, S06-VERDICT | A | Sufficient if the n range is stated. |
| AB5 | Map underpowered at moderate noise | batch1 | F3-BORDERLINE | A | Honest. Batch 4 (10x precision) pending. |
| AB6 | Unknown noise scale: "window much wider (gaps up to 0.316, separable up to n = 10)" | f1map | F1-MAP-Q1 | A (numbers) / D (interpretation) | The extra width is largely knowledge of the noise scale held by pop and withheld from ctx (log-uniform over four decades). Reviewer 3: noise-only gap alone 0.19 / 0.11 / 0.056 / 0.019 at n = 2/3/5/10 vs map 0.25-0.32 / 0.16-0.18 / 0.087-0.094 / 0.032-0.040 (DERIVED by R3; to be re-run as a pre-specified CPU analysis). |
| AB7 | "Libraries of one to four systems are distinguishable ... on held-out systems in many cells" | tab_library | LIB-1A, LIB-F1, LIB-S05 | C | Known sigma, K = 4: separable in 19% of (cell, draw) pairs; K = 2: 53%. True for K <= 2 and for F1; "many cells" too loose for K = 4 known sigma. |
| AB8 | Known sigma: libraries of sixteen or more never separable | map1a, tab_library | LIB-1A | A | Number "sixteen" is typed in words, outside the macro audit. |
| AB9 | Unknown sigma: separable libraries "become rare beyond eight systems" | tab_library (K = 8: 61%, K = 16: 10%, K = 32: 0%) | none | A (table, n <= 40 pooled) / D (unqualified) | "eight" not audited; no claims entry. Reviewer 2: the share rises with n (K = 8: 0.43 at n = 5 to 0.88 at n = 40; K = 16: 0.07 to 0.18) and the long-context limit for K = 16 is 0.037 nats with every draw >= delta; true only for the mapped n range. |
| AB10 | Bivariate: population knowledge up to 0.338; "both windows are wide"; libraries of 64 distinguishable in most cells | batch23 | F2-MAP | A (numbers) / D ("wide"; "population knowledge") | Window mapped only at n in {10, 20} (n = 5 MC-limited); its extent beyond 20 is unknown. The ctx prior IW(1.5, 0.01 I), V0 = 100 I is very vague (no mean for Sigma), so the gap includes noise-covariance knowledge. Library result A and now derivable (nearest-atom KL, STATISTICAL_AUDIT.md 6.2). |
| AB11 | "The map conclusions depend on delta, on the comparator and on the single population prior, and we report how" | tab_delta only | none | **D** | Only delta is reported. Comparator and prior dependence are not reported (batch 4 not returned). As written this is false. |
| AB12 | Pre-registered neural pilot ended not resolvable (compute) | pilot | S1A-PILOT | A | Sufficient. |

## Introduction (`01_introduction.tex`)

| # | Claim | Evidence | Class | Problem |
|---|---|---|---|---|
| IN1 | Below a task-diversity threshold models track the finite-pool posterior, above it the continuous prior [raventos2023, lu2025, panwar2024] | literature | B | Verify panwar2024/lu2025 support this exact statement (literature agent). |
| IN2 | Same contrast drawn for discrete Markov chains [gibson2026, wurgaft2025] | literature | B / D | Reviewer 3 (VERIFIED on arXiv 2506.17859v2): Wurgaft et al. study Balls & Urns, regression, classification, not Markov chains as a main task. Miscitation. |
| IN3 | Ridge with matched penalty = continuous-prior Bayes; OLS = usual context-only comparator | standard | B | Fine. |
| IN4 | Contribution (i): validated references, measured error, calibration, optimality, mutation tests for the last three families | as AB2 | A | Fine. |
| IN5 | Contribution (ii): window short for known scale, shrinks under noise, "widens markedly when the noise scale is unknown or the system is bivariate"; libraries separable only when small (scalar), also when large (bivariate) | maps | A / D | "widens" is a comparator artefact until a noise-matched comparator is mapped (E). |
| IN6 | Contribution (iii): pre-registered results incl. a null and a not-resolvable pilot | s06, main, pilot | A | Fine. |
| IN7 | Contribution (iv): machinery "that kept these results honest", "re-derives every number in this paper" | build | A / D | Numbers written as words (sixteen, sixty-four, eight, nine in ten, eighty per cent, four orders of magnitude) bypass the audit; one macro is used for a different quantity (see R9). "Every number" overclaims. |

## Results (`06_results.tex`, tables)

| # | Claim | Evidence | claims id | Class | Problem |
|---|---|---|---|---|---|
| R1 | Table 1 entries | map files at 4 commits | via make_tables | A | Windows contiguous (VERIFIED, audit script); F2 printed "n <= 20" although only n in {10, 20} are classified. |
| R2 | Stage 0: 2 of 60 regimes separable for all pairs | main | S0-SEP | A | Different comparator and rule; stated. |
| R3 | Stage 0.5 confirmed a one-step but not five-step advantage; REVISE | main | S05-DECISION | A | Fine. |
| R4 | F3 gaps per q; none identifiable at q >= 2.56 or h = 5 | batch1 | F3-MAP | A | Fine. |
| R5 | F3 SEs "several times" those of 1A | map files | none | A (VERIFIED here: median SE ratio 3.9 at q = 0, n <= 9) | Add a claims entry. |
| R6 | Noise-free F3 row agrees with 1A on three cells | batch1 | F3-MAP-VALID | A | Fine. |
| R7 | F1 wider "because the population also carries information about the noise level, which the context-only reference lacks" | f1map | F1-MAP-Q1 | C | Mechanism plausible; magnitude depends on the arbitrary ctx noise-prior width. E: noise-matched comparator. |
| R8 | F2: "0.070-0.338 nats at the longest contexts mapped" | batch23 | F2-MAP | **D** | VERIFIED: 0.338 is at n = 10; at the longest mapped n = 20 the range is 0.070-0.089. |
| R9 | Delta table: "with a known noise scale it extends to n = \FoneMaxN at the smaller margin" | tab_delta | F1-MAP-Q1 (wrong claim) | A (value) / D (provenance) | The macro \FoneMaxN is the F1 map's largest identifiable n (10); the 1A value at delta = 0.01 also happens to be 10. Right number, wrong source: the provenance pipeline does not catch semantic misuse. |
| R10 | "The unknown-noise family keeps the widest window" at every margin | tab_delta | none | **D** | VERIFIED in tab_delta: at delta = 0.01, F1 = 10 ties 1A = 10, and F2 = 20 exceeds F1 at every margin. |
| R11 | Library statements (Stage 0.5 26/36; 1A K = 1 12/18; K >= 16 none; F1 K = 1, 2 all, K = 4 12/18; F3 K = 2 gap 0.097 PARTIAL) | map files | LIB-*, F3-LIB-K2 | A | "mostly because many draws are borderline rather than separable" (F1 K = 16/32) has no claims entry (C). |
| R12 | F2: K = 16 identifiable 15/15, K = 64 13/15 | batch23 | F2-MAP | A | - |
| R13 | "A plausible reason (not tested here) ... sparse coverage of a four-coefficient space" | - | - | C -> **derivable** | Nearest-atom KL limit (DERIVED; numbers in STATISTICAL_AUDIT.md 6.2) predicts it; note Sigma adds 3 dimensions (7 in all), not 4. |
| R14 | "memorisation of a few systems is visible by score"; "memorisation of sixty-four systems is still visible" | maps | - | D (wording) | Statements about references, phrased as if about learners. |

## Pilot, limitations, methodology, conclusion

| # | Claim | Class | Problem |
|---|---|---|---|
| P1 | Pilot facts (B = 50k, 0.00215 vs 0.002, cap 24 < 32, Amendment 1 48 -> 96 h) | A | S1A-PILOT, S1A-PILOT-B, AMENDMENT1. |
| P2 | "neural effort was redirected to the unknown-noise family, whose map leaves more room" | A (fact) | The rationale is weakened by AB6. |
| L1 | "the F1 window in particular may partly reflect how vague the context-only noise prior is" | C | Likely "mostly" (R3 computation); needs the noise-matched comparator. |
| M1 | Freeze manifests, append-only logs, gate defect found and a fix written | A | GATE-DEFECT, DECISION-NO-AMENDMENT2. |
| M2 | "every result number in this paper is a macro ... the build fails if the audited text contains any other decimal or any integer above ten" | D | True for digits; result numbers written as words pass. |
| CO1 | Known scale: worth a few hundredths of a nat, only at very short contexts; noise shrinks it | A | Scoped to one comparator and prior. |
| CO2 | "The windows open when the noise scale is unknown and, more strongly, in the bivariate family" | D | Comparator artefact until shown with a noise-matched comparator. |
| CO3 | Library statements | A | As R11-R13. |
| CO4 | Where to place neural studies (F1 for population knowledge, F2 for memorisation) | C | F1-Q1 has a predetermined answer for converged models (GPU_EXPERIMENT_ROADMAP.md section 1). |

## Summary

* Numbers: every macro re-extracted and PASS (VERIFIED, build 2026-10-31). No number in the text is wrong; two are attached
  to the wrong statement (R8, R9).
* Wording and interpretation: 9 rows class D (AB3, AB6, AB10, AB11, IN7, R8, R10, R14, M2, CO2; some partial). The
  most consequential: AB11 (says the comparator and prior dependence is reported; it is not), and AB6/AB10/CO2 (attributes to
  "population knowledge about dynamics" what is largely knowledge of the noise scale).
