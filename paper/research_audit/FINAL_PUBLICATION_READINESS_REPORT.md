# Final publication readiness report (Phase 12)

## Update 2026-11-03 (revision 7; user decisions S51)

All three blockers below are cleared:
* **B1 archive:** `paper/tools/make_review_archive.py` builds an anonymised archive without git history (291 files, zip
  2.2 MB): pinned evidence blobs, code/specifications/disclosure logs at `e5dc809`, Track 1 sources; SHA-256 manifest;
  scrub + scan PASS. Built from an unzipped copy with git disabled: claims 66/66 and every generated file byte-identical
  to the git build (CHANGELOG 59-60; re-verified at the final commit, item 81).
* **B2 title:** "Where Bayesian References Disagree: Separability Maps for In-Context Learning of Linear Dynamical Systems"
  (user decision); "pre-registered" defined in Appendix B.
* **B3 fresh review:** `INDEPENDENT_THIRD_REVIEW.md`: 0 critical, 5 major, 15 minor, all applied in revision 7.
* Should-do items done: margin curves (Figure 3, post hoc), F2 split at n = 20, abstract 402 -> 302 words (277 before the review's qualifications).

Remaining before submission: the user's own read of the PDF; upload `review-archive.zip` as supplementary material; the
repository visibility decision during review (see the S51 disclosure entry and the session report). Scores now: correctness
of interpretation 8, reproducibility as submitted 8, presentation 7; **overall readiness 8/10 (ready to submit after the
user's read)** (ASSUMED: my judgement). The original assessment follows unchanged.

Manuscript: "Where Bayesian References Disagree: Pre-Registered Separability Maps for In-Context Learning of Linear Dynamical
Systems", branch `paper-revision` @ `6a35441` (revision 5a). Target: TMLR (user decision S40), submitted without neural
results. The original manuscript is preserved unchanged on `paper-draft` @ `bd4d390`.

Build state (VERIFIED, `python paper/build.py`, 2026-11-02): claims PASS (65 verified, 0 pending), 149 number macros PASS,
numbers audit PASS (18 section files), both PDFs built; Track 1 is 16 pages in TMLR submission format, with no overfull box
and no undefined reference or citation. Overfull boxes remain only in the Track 2 skeleton (placeholder sections, not for
submission).

## 1. Verdict

**Not ready to submit yet; close.** Three items block submission (section 3). None needs a GPU or new map computation. The
scientific content has had two rounds of independent (AI-simulated) review; every number has been recomputed by at least
one reviewer from the pinned files, and the interpretive errors the second review found are fixed (revision 5 / 5a).

## 2. Scores (1-10; my judgement, labelled ASSUMED where it is a forecast of reviewer reaction)

| Dimension | Score | Basis |
|---|---|---|
| Numerical correctness | 9 | Every printed number is a macro from a pinned file (VERIFIED by the build); both review rounds recomputed the tables independently and found no transcription error (REPORTED by the reviewers) |
| Correctness of interpretation | 7 | Second review found four interpretive regressions introduced by revisions 1-3 (M3, M4, m1, m2) plus M5; all fixed. Sentences changed in revision 5 have not been independently reviewed (risk: same failure mode) |
| Theory | 7 | Chain-rule budget and nearest-system limit are classical and cited (Cover and Thomas; Haussler and Opper; Clarke and Barron); F1 support caveat and garbling argument added; derivations checked by hand by the second reviewer (REPORTED) |
| Statistical design | 7 | Per-cell 3-SE rule with stated mis-mark bound, per-draw library rule, Monte Carlo criterion, sensitivity analyses; delta is a free design input and only three margins are shown (no n*(delta) curve) |
| Novelty | 4 | The bounds are not new and the paper says so; the contribution is applying them to design behavioural studies plus validated references and maps. TMLR does not require novelty (its stated criteria, VERIFIED in VENUES.md) |
| Interest to TMLR's audience | 6 | Second review: criterion 2 met (REPORTED). Without a trained-model result the practical consequence is argued, not shown (ASSUMED to be the main reviewer objection) |
| Reproducibility as submitted | 4 | The pipeline exists, but reviewers cannot see it: no anonymised artefact, and the LLM-use statement promises disclosure logs "released with the code (anonymised for review)" that do not yet exist |
| Presentation | 6 | Clear structure, figures and appendices; abstract long and dense; internal family labels (1A, F1, F2, F3) opaque (second review m10) |
| Anonymity and policy compliance | 7 | TMLR submission mode; working-name sentence removed; LLM-use statement present; the artefact promise above must be met before submission |
| **Overall readiness** | **6** | Becomes about 8 once the blockers are cleared (ASSUMED) |

## 3. Blockers (before submission)

| # | Item | Why it blocks | Who decides | Effort |
|---|---|---|---|---|
| B1 | **Anonymised code and data artefact** with a code/data availability statement (second review M6, R5) | The paper's reproducibility claims and its LLM-use statement both point to material that reviewers cannot access; leaving the promise unmet would be a false statement | The user (what to include; how to anonymise the history, since commit authors and the public repository name identify the authors) | about half a day: export the reference, map and claims-pipeline code and the small result files without git metadata; scrub names; check the archive builds the paper |
| B2 | **Title and the scope of "Pre-Registered"** (M2, R4) | The second review rates it a required change; revision 5 added Appendix B defining the scope, which may be enough, but the user approved the title | The user | minutes |
| B3 | **Short review of the sentences changed since revision 4** (`git diff 73660de..HEAD -- paper/sections`) | Revisions 1-3 introduced four interpretive errors that the claims build could not catch; revision 5 changed similar sentences | Me (a fresh sub-agent given only the diff, the manuscript and the evidence files) | under an hour |

Not a blocker: author names (TMLR submissions are anonymous; needed only for the camera-ready version). Not a blocker: neural
results (user decision S40).

## 4. Should do before submission (no new compute beyond seconds)

1. **n*(delta) curves** (M1(c), Q2): the largest separable n as a continuous function of delta, per family and r, computed
   from the estimates and standard errors already in the pinned map files. This is a re-reading of existing results, not a
   new run, but it is an analysis chosen after seeing results: disclose it, and generate it with `make_figures.py` from
   `numbers.yaml` like the other figures.
2. **F2 split at n = 20** (Q4) from `split.csv` @ `e08eee8` (already pinned), to show whether the order dependence persists.
3. **Shorten the abstract** (m10) to about two thirds of its length; keep every claim tied to a macro.
4. **Per-map estimator and sample size in Table 1**, and horizons, for readers who skip Section 5 (m3, m7; text done).
5. Optional: the prior budgets for tau = 0.15 and 0.6 (m4). A deterministic quadrature taking seconds, but it is a new
   analysis: spec, disclosure entry, pinned output.

## 5. Not needed for TMLR, recorded for later

* A trained-model demonstration (M1(a), R7 "preferably"). The planned seed-variance probe (with its F2 LIB-64 arm) and the
  memorisation study on F2 are drafted on CPU; nothing is frozen; GPU work needs the user's explicit go. The current
  CPU-torch permission covers unit tests and short smoke runs only, which cannot produce a demonstration.
* A non-conjugate dynamics-only comparator for F2 (M3 ideal fix).
* Descriptive family names throughout and "autoregressive" in the title (m10): the user's decision, cheap once decided.
* h > 1 for all families; F2 and F3 prior and comparator sensitivity.

## 6. Risks at review (ASSUMED)

| Risk | Likelihood | Mitigation in the paper |
|---|---|---|
| "No neural result, so what changes for practitioners?" | high | Sec. 5 and 10 state what the maps imply for model counts and seed variance; n*(delta) curves (section 4.1) would make it concrete |
| "The bounds are classical" | high | Stated as classical with citations; the contribution claimed is their use, not the bounds |
| "Pre-registered is overstated" | medium | Appendix B; title decision B2 |
| An interpretive sentence that does not follow from the numbers | medium | B3 |
| Reviewers cannot inspect the code | certain without B1 | B1 |

## 7. Recommended order

B3 (third review of changed sentences) and section 4.1-4.2 now; then the user decides B1 and B2; then build the artefact,
rebuild the paper from a fresh clone, and submit.
