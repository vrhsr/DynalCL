# Response to internal hostile review 1 (2026-10-30)

Review: a fresh sub-agent given only the manuscript (paper-draft @ 38ad11b), the claims table and the evidence files at their
pinned commits; verdict "reject in current form" (13 MAJOR, 11 MINOR, 2 NIT). Every item below was checked against the
evidence before acting. Status: FIXED (text changed, evidence entry added), OPEN (needs new analysis; logged), or
DISPUTED (reviewer's reading checked and found incomplete, with the reason).

| Item | Status | What changed / why |
|---|---|---|
| M1 library headline contradicted by the files | FIXED | Confirmed: Stage 0.5 K = 2 distinguishable 26/36; 1A K = 1 identifiable 12/18; F1 K = 1, 2 all identifiable, K = 4 12/18. Abstract, Sec. 6 and conclusion rewritten; claims LIB-S05, LIB-1A, LIB-F1, F3-LIB-K2. A self-check during the rewrite found my own overstatement ("sixteen or more never separable") false for F1 (K = 16, 32 all PARTIAL); corrected. |
| M2 PARTIAL undefined | FIXED | Defined in Sec. 5 (nine-in-ten draws rule; per-draw meaning for a trained model); draw counts differ by map (claims MAP-DRAWS). Per-draw distributions in the paper: OPEN. |
| M3 "one pre-registered rule" false | FIXED | Sec. 5 now lists each study's rule (Stage 0 frontier rule; Stage 0.5 +/- 2.24 SE; Stage 0.6 max-t; maps 3 SE; F1 two-sided). Claims DESIGN-RULES, DESIGN-RULES-S06, F1-TWOSIDED. Abstract says "common margin", not "one rule". |
| M4 KL claim | FIXED | Sec. 5: KL identity only when one reference is the data-generating predictive; designed sets reported separately and not used for headlines. |
| M5 F3 vs 1A rows | FIXED (text) / OPEN (precision) | Table now prints each map's n grid; text explains the grid difference and the r = 4 precision difference and says the validity check covered three cells only. |
| M6 F3 null partly low power | FIXED | "Erased" removed; table counts borderline cells with estimate >= delta (14; 9 at q = 0.755; claim F3-BORDERLINE); abstract says the map is underpowered at moderate noise. Re-running F3 with a Rao-Blackwellised estimator: OPEN. |
| M7 comparator | FIXED (text) / OPEN (frontier) | Sec. 3 states what each context-only reference knows (true noise model; uniform on (-0.999, 0.999); F1 log-uniform noise prior) with claims DESIGN-PRIORS, DESIGN-STAB; Sec. 8 states comparator dependence. A frontier of comparators: OPEN. |
| M8 "identifiable" vs model-side power | FIXED (text) | Sec. 5 defines the term, states necessary-not-sufficient, reports the F1 lookup (seed sd <= LookupQoneThirtyTwo nats at MinModels models for 80% power), mentions pooled tests. A sequence-level test: OPEN. |
| M9 no sensitivity | FIXED (delta) / OPEN (prior, grid) | New Table 2: largest identifiable n at delta in {0.01, 0.02, 0.04}, generated from the same files. Prior concentration sensitivity: OPEN. |
| M10 "rarely" contradicted by F1 | FIXED | "Rarely" removed; F1's wide window is a headline. |
| M11 unsupported validation claims | FIXED | F2 validation statements removed (results pending); known-scale mutation claim removed (Stage 0 archive not retained); noisy-family mutation claim now backed by S06-MUTATION (40/40). Validation section states the checks are conservative. |
| M12 citations | FIXED / DISPUTED | Cao: the PDF supports "small to moderate context lengths" for exponentially distributed coefficients (quote verified in the PDF), not a general "only short contexts"; sentence narrowed. Koshelev: DISPUTED in part, the AR(1) example is in the paper's appendix (both quotes verified in the PDF); text now says "in a toy example in its appendix". Wakayama: "defines a Bayes gap". Gibson: "scored in nats" removed. |
| M13 gate "fixed" overstated | FIXED | "wrote a fix that is to be included in the next frozen release". |
| Minor: Stage 0 sigma | FIXED | Sec. 3 mentions the second scale (claim DESIGN-S0-SCALES). |
| Minor: Amendment 1 not disclosed | FIXED | Sec. 7 states 48 -> 96 GPU-h before the pilot (claim AMENDMENT1; macros from both freezes). |
| Minor: 0.00015-nat exceedance | FIXED | Sec. 7 says the tolerance was exceeded by less than a tenth of it, with no uncertainty attached by the rule. |
| Minor: "adequate power" | FIXED | Replaced by "fixed from the bootstrap-calibrated operating characteristics". |
| Minor: mis-marked cells promised | FIXED | Promise removed; Sec. 5 and 8 state the per-cell rule without global correction. |
| Minor: caption h = 1 for 1A/F1 | NOTE | The 1A and F1 maps are h = 1 only by design (their specs); the files have no h column because there is one horizon. |
| Minor: "monotonically" | FIXED | Now "the largest h = 1 gap is ..." per noise level. |
| Minor: ridge / "never separated" | FIXED | Sec. 1 rewritten. |
| Minor: Box-Hill, Garg, Xie, Kalman-ICL | PARTLY | Text now acknowledges classical model-discrimination design without citation (not retrieved). Retrieving these works for the bibliography: OPEN (literature task). |
| Minor: audit exemptions | FIXED | Sec. 9 states the exemptions. |
| NIT: surnames only in bib | OPEN | First names to be added from the PDFs. |

OPEN analyses (not run; each needs a decision on compute): comparator frontier; prior-concentration sensitivity; F3 with a
Rao-Blackwellised estimator; per-draw library distributions; a sequence-level test. Build after the revision: claims PASS
(36 verified, 1 pending), 55 macros, audit PASS (also checks control characters now), 9-page Track 1 PDF.
