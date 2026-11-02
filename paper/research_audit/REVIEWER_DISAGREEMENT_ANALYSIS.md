# Reviewer disagreement analysis (Phase 11)

This compares the first round of independent reviews (Phase 1, three sub-agents, synthesis in `INDEPENDENT_REVIEW.md`, on
the `paper-draft` manuscript `bd4d390`) with the second independent review (`INDEPENDENT_SECOND_REVIEW.md`, on revision 4,
`73660de`). Both rounds are AI-simulated. Where this file says "introduced in revision k", that is VERIFIED with
`git log -S` on `paper-revision`.

## 1. Where the two rounds agree

| Point | First round | Second review |
|---|---|---|
| Recommendation | Major revision (R1, R2); 4/10 leaning reject (R3) | Major revision, 5/10 |
| Numerical accuracy | every table value recomputes (R2); references reproduce within about 2 SE (R2) | every table entry it recomputed matched the pinned files; budgets and nearest-system limits reproduce independently |
| Budget and nearest-system accounts | proposed them as the organising idea (R1, R3) | "correct and well chosen" (S2); its derivation was checked by hand |
| No neural result; delta not tied to model precision | issues 5 and 14 | M1 |
| Honest reporting of nulls and limits | all three | S3 |

The second score is one point above R3's, on a manuscript that had absorbed the first round's critical items (issue 1
comparator decomposition, issue 2 theory, issue 3 noise framing, issue 6 terminology, issue 12 figures). None of those
reappears in the second review, which is weak evidence that the fixes held.

## 2. What the second review found that the first round and the audit missed

| Second-review item | Origin | Why it was missed |
|---|---|---|
| M3: the F2 split is order-dependent; "mostly dynamics" holds only in one order | Introduced in revision 3 (`7661aca`, CHANGELOG item 29), which replaced revision 1's "mostly noise-level" | I reported the symmetric average of the two paths and checked the claim against that average only. The order dependence was visible in the same file (`split.csv`); the Limitations even said the F2 labels were approximate, but the headline drew a conclusion anyway. The claims build verified the averaged numbers, which were correct, so it could not catch an interpretive error |
| M4: the budget bounds the per-sequence effect, not pooled evidence | Introduced in revision 1 (`c614a1e`), in the theory reframe | I wrote the pooling sentences while turning the first round's budget idea into text; no reviewer had seen them yet |
| M5: D(P‖Q) is infinite in F1 (support mismatch) | Present since the budget was first quoted (first-round R2 numbers; revision 1 text) | `theory.json` already recorded `pop_mass_outside` = 1.3e-12, but neither the first round nor I turned it into a statement about the bound |
| m1: PARTIAL definition wrong when all draws are borderline | Introduced after internal review 1 (`375244e`), which had asked for a definition | The definition was written from the 1A map, where mixed cells are separable/not separable mixes; F1 K = 32 was not checked against it |
| m2: the K^{-2/p} rate does not match the Monte Carlo values | Introduced in revision 1 | The rate came from the first round's nearest-atom account as a heuristic; the computed values were never fitted against it |
| M2: "Pre-Registered" in the title covers analyses chosen after results | Title introduced in revision 1 (user-approved at checkpoint 1) | The first round criticised the pre-registration machinery as process (issue 13), not the scope of the label. The batch 5 specification itself lists what was seen first, so the information was on record |
| M6 raised to major: no code or data artefact | First round had it as minor (issue 20, "no code statement") | Severity judgement: the second review ties it to the paper's own reproducibility claims |
| m9: garbling argument for observation noise | First round (R1, issue 3) gave the "spread over more forecasts" account | Not an error; the second review gives a cleaner argument that holds at every N |

Four of the eight (M3, M4, m1, m2) are errors that the revisions introduced, not errors inherited from the original
manuscript. All four are interpretive sentences whose numbers were correct.

## 3. Where the reviews disagree

1. **What the maps are for.** The first round (R1) proposed making the theory the contribution and the maps its numerical
   check, and the user adopted this. The second review accepts the theory but argues that binary maps at one delta are
   largely a re-expression of the smooth gap curves at an arbitrary threshold (M1), and asks for n*(delta) curves. These
   are compatible: the curves would show the maps as one slice of a continuous object. Not yet done.
2. **The title.** The first round did not object to "Pre-Registered" (it arrived after that round); the second asks to drop
   or qualify it. Revision 5 adds a provenance appendix that defines the term's scope; the title itself is the user's
   decision.
3. **Neural evidence.** The first round recommended a seed-variance probe or a reframe as a reference/theory paper; the
   second prefers a small demonstration in the F2 library setting, where the maps say the memorisation question is
   visible. The user's plan (probe with an F2 LIB-64 arm, then the memorisation study on F2) serves both, but neither is
   authorised to run, and the user chose TMLR without waiting for it.
4. **Where memorisation is visible.** The first round (issue 8) asked to scope "memorisation visible" sentences; the second
   (m8) found the conclusion still overstated it by naming only the bivariate family. Fixed in revision 5a.

## 4. Lessons for the remaining work

* The claims build checks numbers against pinned files; it cannot check what a sentence concludes from them. The four
  regressions were all of that kind. Where a sentence says "mostly X", the claim table should check every quantity the
  conclusion depends on (as `B5-SPLIT-PATHS` now does for both split orders), not only the summary statistic printed.
* Each revision added unreviewed interpretive text. A short third review restricted to sentences changed since revision 4
  (`git diff 73660de..HEAD -- paper/sections`) would cost little and target exactly this risk.
* Information already in result files (`pop_mass_outside`, the per-path split columns, the batch 5 "seen before" list)
  was enough to avoid M2, M3 and M5. Before writing a conclusion from a result file, reading all of its columns would have
  caught them.
