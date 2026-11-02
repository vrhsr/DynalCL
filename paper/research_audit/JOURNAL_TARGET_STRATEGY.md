# Venue strategy (Phase 10)

Basis: `docs/literature/VENUES.md` (official pages read 2026-10-27, quotes there), TMLR's editorial policies and author guide
fetched again on 2026-11-01 (`LLM_USE_STATEMENT_DRAFT.md`), and the literature agent's verified records (LITERATURE_REVIEW.md).
No acceptance rate, impact factor or indexing claim is made: none was verified. No venue below is predatory; all are run by
established ML or statistics bodies. No acceptance is guaranteed anywhere. User decision (S40): TMLR for the reference-and-theory
paper, not waiting for neural results.

| # | Venue | Type | Scope / criteria (VERIFIED from official pages) | Fit for this paper | Main weakness against its bar | Timing |
|---|---|---|---|---|---|---|
| 1 | **TMLR** | journal, rolling, double blind, open reviews | accept if claims are "supported by accurate and convincing evidence" and "some individuals in TMLR's audience would be interested"; "novelty of the studied method is not a necessary criterion"; any length; LLMs allowed as assistive tools, authors fully responsible | **Best.** Evidence-first criteria match a validated, pre-registered reference study with a theory account; closest published neighbours appear there (Chronos and Akram and Vikalo's transformer state-estimation paper are TMLR papers, per their OpenReview records) | "interest": a reference-only paper must show readers what changes for their own ICL studies (the two bounds, where references can be told apart, the comparator lesson) | rolling; submit when ready |
| 2 | TMLR J2C certification | certification for TMLR papers | a TMLR paper may be certified for the NeurIPS/ICLR/ICML Journal-to-Conference track ("would be appropriate for the joint ... track") | Possible only with a stronger result (e.g. a neural memorisation transition predicted in advance) | conference-level significance without a neural result | after TMLR acceptance |
| 3 | NeurIPS Evaluations & Datasets track | conference track, double blind | "Compare evaluation designs and demonstrate how different assumptions lead to different results", "Propose new evaluation protocols", "Present negative results"; code release required when the contribution is a reusable artifact | Plausible if framed as an evaluation-design protocol (separability before classification) with the reference code released | bar described as equal to the main track; the 2027 call was not yet published | next NeurIPS cycle (deadlines around May) |
| 4 | NeurIPS main track, "Negative Results" type | conference | the negative result "must be surprising ... run counter to a popularly held understanding" | Weak: the short-context window is predictable from the budget, which the paper now says | originality | - |
| 5 | AISTATS / UAI | conferences, 8 pages | UAI: "technical correctness, novelty, whether claims are supported by convincing evidence"; AISTATS criteria not stated on the pages read | A shorter statistical version (the two bounds plus maps) fits the audience | novelty of classical bounds; 8-page limit for the validation and pre-registration material | AISTATS 2027 deadline passed (Oct 2026); next cycle |
| 6 | JMLR | journal, long papers | claims "supported either by empirical experiments or theoretical analyses"; "favors papers of interest to a broader machine learning audience and may deem a paper unsuitable if ... audience too narrow" | A later long version with neural results (option B) and the full theory | audience breadth for a reference-only paper | after neural results |
| 7 | Non-archival workshops (e.g. NeurIPS "Foundation Models for Temporal Systems"; an ICBINB edition with a fitting theme) | workshops | non-archival; overlap with a later TMLR or JMLR paper allowed | Feedback before or alongside TMLR | none (non-archival) | per call |

Not suitable: ReScience C and the NeurIPS reproducibility track (both for reproductions of other people's published work).

## Strategy
1. **Submit to TMLR** once the remaining items in FINAL_PUBLICATION_READINESS_REPORT.md are done (author block, code
   availability through an anonymised artefact, final second-review fixes). Do not wait for neural results (S40).
2. Optionally present a short version at a non-archival workshop for feedback; this does not block TMLR.
3. If option B (F2 memorisation transition) later resolves, write it as a separate paper (main-track or TMLR J2C route), citing
   the TMLR paper for the references, maps and bounds; a combined long version could go to JMLR.
4. Anonymity for TMLR: no link to the public repository (it names the authors); supply code as anonymised supplementary
   material; the LLM-use statement stays in, anonymised.
