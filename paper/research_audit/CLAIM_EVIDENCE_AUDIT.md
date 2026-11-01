# Claim-by-claim audit (Phase 3)

The row-by-row classification (A-E) is in CLAIM_EVIDENCE_MATRIX.md. This file records the build check, the cases where a claims
check passes while the sentence says something else, and the language checks the brief asked for.

## 1. Build (VERIFIED, 2026-10-31)

`python paper/build.py` in `E:\study-buddy\DynaICL-paper-rev` (branch `paper-revision` = `paper-draft` @ bd4d390): claims
**PASS, 41 verified, 0 pending**; numbers.tex generated (all macros re-extracted at their pinned commits); tables generated;
numbers audit **PASS** (15 section files); `main.pdf` and `main_track2.pdf` built, 10 pages each; 39 s. Fresh-clone build from
GitHub: see REPRODUCIBILITY_AUDIT.md.

## 2. Checks that pass while the sentence overstates (the pipeline checks numbers, not wording)

| Where | Claims entry | What the entry checks | What the sentence says | Verdict |
|---|---|---|---|---|
| 06_results "Sensitivity to the margin" | F1-MAP-Q1 (via \FoneMaxN) | F1's largest identifiable n = 10 | the known-scale window at delta = 0.01 extends to n = 10 | Wrong provenance; the value coincides (1A at 0.01 is also 10, VERIFIED in tab_delta) |
| 06_results F2 paragraph | F2-MAP (min/max over identifiable held-out pop-ctx) | 0.0704-0.3375 over n in {10, 20} | "worth 0.070-0.338 nats at the longest contexts mapped" | Misleading: at n = 20 the range is 0.070-0.089 |
| 00_abstract "we report how" | none | - | dependence on comparator and prior reported | Not reported (batch 4 pending) |
| 06_results delta paragraph | none | - | "the unknown-noise family keeps the widest window" | False per tab_delta (tie at 0.01; F2 wider) |
| 09_methodology | (audit script) | digits and integers > 10 | "every result number in this paper is a macro" | Number words bypass the audit: "sixteen or more", "sixty-four systems", "beyond eight systems", "nine in ten draws", "eighty per cent power", "four orders of magnitude" |
| 06_results / 08_limitations "four-coefficient" | none | - | F2 library explanation via a 4-dimensional space | F2 atoms are (A, Sigma): 7 free parameters (VERIFIED MATH_F2 section 2, line "Library L_K: K atoms (A_k, Sigma_k)") |
| 03_setting context-only description | DESIGN-PRIORS, DESIGN-STAB | F1 noise prior and 1A stab interval | "replaces the population prior over the system by a uniform prior on a slightly wider stable interval ... and, in F1, a log-uniform prior on the noise scale" | Silent on F2's context-only prior (MNIW, B0 = 0, V0 = 100 I, IW(1.5, 0.01 I)); incomplete for F2 |
| 01_introduction | references only | - | Wurgaft et al. cited for discrete Markov chains | Miscitation (Reviewers 1 and 3, VERIFIED on arXiv HTML) |
| 02_related Koshelev | bib | - | "in a toy example in its appendix" | Reviewer 3: the quoted sentence is in the main text, the figure in Appendix A; reword |

## 3. Language checks requested by the brief

* **Generalisation beyond the four families.** The text mostly scopes correctly ("in our map", Limitations "Simple families").
  Exceptions: the conclusion's "these are where we would place neural studies" is fine; contribution (ii) "the population-specific
  window ... widens markedly when the noise scale is unknown or the system is bivariate" generalises a comparator choice to a family
  property (class D until G1 in EXPERIMENT_GAP_ANALYSIS.md).
* **Statements about neural models.** Limitations says "this paper makes no claim about trained models" (good). But the abstract's
  first sentence and Sec. 5 ("necessary in our designs for a per-cell behavioural classification") imply consequences for neural
  studies; acceptable as stated. "Memorisation of a few systems is visible by score" (Sec. 6) and "memorisation of sixty-four
  systems is still visible" read as claims about learners: rewrite as "a library reference of K systems is distinguishable from
  population Bayes".
* **Map observation turned into a guarantee.** "Libraries of sixteen or more systems never are [separable]" is a statement about the
  map's grid (n <= 20, delta = 0.02, one prior); keep "in our map", which the abstract does. "Population knowledge is worth X nats"
  (abstract, results, conclusion) is a guarantee-like phrasing of a comparator-relative quantity; scope it.
* **"Identifiable".** Conflicts with the statistical meaning (a model is identifiable if distinct parameters give distinct
  distributions); every "unidentifiable" cell here has a strictly positive gap (e.g. 1A n = 80: 5.6e-4, about 66 SE from zero;
  Reviewer 1, VERIFIED from the CSV). Rename (title change needs the user's approval).

## 4. Overall

No number is wrong. The interpretive layer has three substantive problems (comparator-driven "wider windows", "noise shrinks
population knowledge", "we report how" for analyses not yet returned) and a set of fixable wording and citation errors. The
claims machinery is sound for what it checks; it should also check semantic attachment (one macro per statement) and number
words.
