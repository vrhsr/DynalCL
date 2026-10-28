# Candidate venues (workstream D4, read 2026-10-27)

Every fact below comes from the official page named in its row, downloaded with curl on 2026-10-27 (a few in the early hours of 2026-10-28)
and read as text. Quotes are copied from those pages. **No acceptance rates are given anywhere: none of the pages read states one.** Deadlines are
quoted only where an official page states them, with the date read; most current-cycle deadlines have already passed, and the next cycles
(NeurIPS 2027, ICML 2027, UAI 2027) had no call published on the pages read (the NeurIPS 2027 call-for-papers URL returned the 2026 site).
Policies change every year: re-read the page of the actual cycle before submitting.

Two scenarios:
* **(a) Reference-side methods paper:** validated Bayesian references, a separability-first pre-registered design, and honest null /
  not-resolvable results on AR-family ICL (Stage 0, 0.5, 0.6; Stage 1 pilot only as far as it was reported).
* **(b) Full paper with neural results** (Stage 1 and beyond).

## 1. Journals

### TMLR (Transactions on Machine Learning Research)

* Pages read: https://jmlr.org/tmlr/ ; https://jmlr.org/tmlr/acceptance-criteria.html ; https://jmlr.org/tmlr/author-guide.html ;
  https://jmlr.org/tmlr/editorial-policies.html
* **Format / length:** "Submissions may be any length, but a paper's length should be justified by its content and papers that are unusually long
  (not counting any Appendices) are likely to result in reviewing delays." TMLR LaTeX template; supplementary material up to 100MB.
* **Review criteria (official):** acceptance "should be based on positive answers to the following two questions. Are the claims made in the
  submission supported by accurate and convincing evidence? ... Would some individuals in TMLR's audience be interested in the findings of this
  paper, and does the paper communicate those findings clearly to its intended audience?" Also: "novelty of the studied method is not a necessary
  criterion for acceptance in TMLR", and the interest criterion "should not be used as a reason to reject work that isn't considered
  'significant' or 'impactful' because it isn't achieving a new state-of-the-art".
* **Negative results / pre-registration:** neither is named explicitly. The criteria above (evidence over novelty) fit a careful null result.
  The scope includes "experimental and/or theoretical studies yielding new insight into the design and behavior of learning in intelligent systems"
  and "formalization of new learning tasks ... and of methods for assessing performance on those tasks".
* **Reproducibility:** "Reproducibility Certification. This is awarded to papers whose primary purpose is reproduction of other published work."
  So it does **not** apply to our own original study. Authors are encouraged "to upload materials that improve reproducibility".
* **Anonymity / preprints:** "TMLR uses a double blind review process and submissions must be anonymized." "Authors are also allowed to upload their
  submissions to arXiv or other preprint servers at any time, either anonymously or including their identity, though double blind of the TMLR
  submission itself must be maintained by not linking to another version that includes the authors' names." Reviews are open (OpenReview).
* **Prior versions:** TMLR does "not accept submissions that are expanded versions of conference papers"; overlap with non-archival workshop papers
  and arXiv is acceptable.
* **Conference presentation:** home page news item: "2025.10.21: TMLR announces the Journal to Conference Certification and joins the
  NeurIPS/ICML/ICLR Journal-to-Conference Track." The editorial policies describe a "J2C Certification" based on whether the work "would be
  appropriate for the joint NeurIPS/ICLR/ICML Journal-to-Conference Track".
* **Deadlines:** rolling submission (no deadline).

### JMLR (Journal of Machine Learning Research)

* Page read: https://www.jmlr.org/author-info.html
* **Length:** "Papers longer than 35 pages will take a longer time to review ... papers above 50 pages require a note of justification in the cover
  letter, and may be desk rejected. (Note that these page counts include appendices.)" JMLR LaTeX style required.
* **Criteria (official):** "All claims should be clearly articulated and supported either by empirical experiments or theoretical analyses";
  "it should be clear how the work advances the current state of understanding and why the advance matters"; "JMLR favors papers of interest to a
  broader machine learning audience and may deem a paper unsuitable if the editorial board finds its audience too narrow."
* **Negative results / pre-registration:** not mentioned on the page read.
* **Anonymity / preprints:** the page does not mention blind review. "Authors may submit work to JMLR that is already available as a preprint."
  Prior conference or workshop versions are allowed if the JMLR paper extends them "in a substantive way".
* **Deadlines:** none (journal).

### ReScience C

* Pages read: https://rescience.github.io/ ; https://rescience.github.io/faq/
* Scope: "encourages the explicit replication of already published research"; titles use Re / Rp, and "Either one can be negated in case of
  failure to give: ¬Re and ¬Rp" (so failed replications are publishable).
* **Not suitable for our own work:** FAQ, "Can I submit the replication of my own research? No."
* Possible only for a separate side project (for example an independent replication of a published ICL result), which is not planned.

## 2. Conferences (main tracks)

### NeurIPS (2026 cycle; the 2027 call was not yet published)

* Pages read: https://neurips.cc/Conferences/2026/CallForPapers ; https://neurips.cc/Conferences/2026/MainTrackHandbook ;
  https://neurips.cc/Conferences/2026/ReviewerGuidelines
* **Format:** "The main text of a submitted paper is limited to nine content pages, including all figures and tables." References, appendices and
  the mandatory checklist do not count. One extra page for the camera-ready.
* **Negative results (explicit):** NeurIPS 2026 asks authors to pick a contribution type, including "Negative Results: The main contribution is in
  understanding a negative result. The bar for these submissions is expected to be high." Reviewer guidelines for that type: "it is important that
  the negative result not be simply an empirical observation that some experiment did not turn out as expected or hoped. It is important that a
  negative result be grounded in deeper analysis"; significance "The negative result should be informative in changing how the community addresses
  a question"; originality "The negative result must be surprising or unexpected in some way - that is, it should run counter to a popularly held
  understanding."
* **Pre-registration:** not mentioned in the 2026 main-track pages read (NeurIPS hosted pre-registration workshops in 2020 and 2021; see
  BIBLIOGRAPHY entry 110).
* **Anonymity / preprints:** double blind; "The existence of non-anonymous preprints (on arXiv or other online repositories, personal websites,
  social media) will not result in rejection." "aggressive advertising of papers under submission may be deemed a violation."
* **Deadlines (read 2026-10-27, 2026 cycle, passed):** "Abstract submission deadline: May 4, 2026 (AOE)"; "Full paper submission deadline,
  including all supplementary materials: May 6, 2026 AOE".

### NeurIPS Evaluations & Datasets track (formerly Datasets & Benchmarks)

* Page read: https://neurips.cc/Conferences/2026/CallForEvaluationsDatasets
* Scope includes: "Compare evaluation designs and demonstrate how different assumptions lead to different results or conclusions", "Propose new
  evaluation protocols, practices, or methodologies", and "Present negative results, critical analyses, and use-case-inspired evaluations".
  "Submissions need not introduce a new model or outperform prior work."
* Format follows the main track; "the default review mode for the E&D Track is now double-blind". Code release is "required at submission when the
  primary contribution is a reusable executable artifact, such as a benchmark suite, evaluation environment, data generator, or software tool".
* Deadlines (2026, passed): same as the main track (May 4 / May 6, 2026).

### NeurIPS reproducibility track (MLRC)

* Page read: https://neurips.cc/Conferences/2026/CallForReproducibility
* "Submissions must be first accepted to TMLR"; scope is "the reproducibility, replicability, and generalizability of published claims in ML",
  for papers "published in top ML conferences and journals from 2025 to present". It "welcomes rigorous work across the full spectrum of outcomes,
  including ... failures to reproduce". **Not suitable for our original study.**

### ICML (2026 cycle)

* Page read: https://icml.cc/Conferences/2026/CallForPapers
* **Format:** "8 pages for the main paper, with unlimited pages for references, the impact statement, and appendices"; one extra page for the final version.
* **Criteria:** "Submissions should report original and rigorous research of significant interest to the machine learning community. All claims must
  be clearly stated and supported by reproducible experiments and/or sound theoretical analysis."
* Negative results and pre-registration: not mentioned on the page read. ICML 2026 also had a separate position-paper track (BIBLIOGRAPHY entries
  113 and 116 are ICML position papers arguing for confirmatory/pre-registered research).
* **Anonymity / preprints:** double blind; "Authors are allowed to post versions of their work on preprint servers such as arXiv", but "under no
  circumstances should the work be advertised as an ICML submission". New in 2026: the originally submitted version and reviews of accepted papers are published.
* Deadlines (2026, passed): "Full paper submission deadline: January 28, 2026 AoE".

### ICLR (2027 cycle)

* Pages read: https://iclr.cc/Conferences/2027/CallForPapers ; https://iclr.cc/Conferences/2027/AuthorGuidelines
* **Format:** "At the time of submission, the main text should be 9 pages or fewer"; 10 pages during discussion and camera-ready. A reproducibility
  statement is recommended.
* **Criteria:** not listed on these two pages. The call states: "what we want most is your slow science, and your most complete and most exciting work."
* Negative results / pre-registration: not mentioned.
* **Anonymity / preprints:** double blind; "related arxiv papers by the same authors do not break anonymity". "all submissions (even rejected and
  withdrawn submissions) will remain public with authors' names attached to them."
* Deadlines (read 2026-10-27, passed): "Abstract deadline Sep 18, 2026 AOE"; "Paper deadline Sep 25, 2026 AOE"; decisions "Dec 16, 2026".

### AISTATS

* Pages read: https://aistats.org/aistats2027/dates.html (2027 key dates); https://virtual.aistats.org/Conferences/2026/CallForPapers (2026 call;
  the 2027 call page only links to OpenReview).
* **Format (2026 call):** "Submissions are limited to 8 pages (excluding references, the reproducibility checklist, and additional appendices)";
  9 pages for camera-ready.
* Anonymity / preprints (2026 call): double blind; "Tech reports (on arXiv or similar sites) and short papers in workshops without archival
  proceedings do not count as prior publication"; "If it is being posted to arXiv (or similar sites), we suggest using a neutral (non-AISTATS) format."
* Criteria, negative results, pre-registration: not stated on the pages read.
* Deadlines (read 2026-10-27, AISTATS 2027, passed): "Abstract submission deadline: September 29, 2026"; "Paper submission deadline: October 6, 2026".

### UAI (2026 cycle)

* Pages read: https://www.auai.org/uai2026/call_for_papers ; https://www.auai.org/uai2026/submission_instructions
* **Format:** "The main part of the manuscript must not exceed 8 pages in length"; unlimited references and appendices.
* **Criteria:** "Submissions will be judged on the basis of their technical correctness, novelty, whether claims are supported by convincing evidence,
  and clarity of writing. Reproducibility and ethical aspects will also be considered."
* Negative results / pre-registration: not mentioned.
* Anonymity / preprints: double blind; "Manuscripts in conferences or workshops without proceedings, technical report repositories, and arXiv are
  not considered dual submissions."
* Deadline (2026, passed): "February 25th, 2026 (23:59 AoE): Paper submission deadline". No UAI 2027 call was read.

## 3. Workshops (non-archival)

* NeurIPS workshop guidance (https://neurips.cc/Conferences/2026/WorkshopsGuidance): "All NeurIPS workshop papers are non-archival and therefore do
  not appear in proceedings." Suggested contribution date for 2026 workshops was "August 29, 2026, AoE" (passed).
* **"Foundation Models for Temporal Systems: From Forecasting to World Modeling"**, NeurIPS 2026 (https://neurips.cc/virtual/2026/workshop/137514):
  directions include "(iv) evaluation and reliability"; "contributed papers and posters managed through OpenReview". Its own call and deadline were not read.
* **I Can't Believe It's Not Better (ICBINB)**, ICLR 2026 edition (https://sites.google.com/view/icbinb-2026): "We invite papers that focus on the
  negative results"; the 2026 theme was LLM limitations ("Where Large Language Models Need to Improve"), deadline "January 31st, 2026" (passed).
  The series says it promotes "the idea that there is more to machine learning research than tables with bold numbers". A future edition might have
  a theme that fits; none read here does.
* No 2026-2027 in-context-learning workshop was found in the searches (SEARCH_LOG query 30).

## 4. Suitability (MY OPINION, not verified by any editor or reviewer)

**Scenario (a), reference-side methods paper with null / not-resolvable results.**
1. **TMLR is the best fit.** Its stated criteria are evidence and interest to some readers, explicitly not novelty or state of the art; rolling
   submission; any length (the validation and pre-registration detail fits); open reviews suit a transparency-first paper. Risk: the "interest" test,
   so the paper must state what memorisation/ICL researchers learn (for example that library vs continuous is unidentifiable by score for K >= 4,
   and that most naive "population advantage" is generic stability knowledge). The J2C certification is a possible route to a conference slot but
   is selective; I would not plan on it.
2. **NeurIPS Evaluations & Datasets track** (next cycle, if its scope is kept): plausible, because the scope explicitly includes comparing evaluation
   designs, new evaluation protocols and negative results. The paper would need to be framed as an evaluation-methodology contribution (a
   separability-first protocol for classifying ICL behaviour) with released, reusable reference code. Bar described as equal to the main track.
3. **NeurIPS main track "Negative Results" type:** unlikely in my view. The official bar requires the result to "run counter to a popularly held
   understanding"; "Bayes references converge at long context" is close to expected (our own write-ups call the vanishing gap DERIVED), so
   originality would be the weak point.
4. A non-archival workshop (time-series or a future ICBINB) is a low-cost way to get feedback first; workshops are non-archival, so a later TMLR
   submission remains possible (TMLR accepts overlap with non-archival workshop papers).
5. JMLR: not a good fit for (a) alone; its "audience too narrow" clause is the risk.
6. ReScience C and the MLRC reproducibility track: not applicable (own work; they publish reproductions of others' work).

**Scenario (b), full paper with neural results.**
1. If Stage 1 gives a clear classification in the identifiable window and the F1/F2 extensions add a predictive account (the S2/S3 scenarios in
   GAP_AND_NOVELTY.md): **ICML / NeurIPS / ICLR main track** become realistic targets, with all the uncertainty that implies; AISTATS or UAI fit a
   statistically framed version (8 pages, criteria include novelty and convincing evidence).
2. If the neural result is INCONCLUSIVE or "matches Bayes where Bayes is identifiable": **TMLR** again (evidence-first criteria), possibly combined
   with (a) into one paper.
3. **JMLR** for a long, complete version (references, theory of separability, neural results), if the audience-breadth test can be met.
4. Pre-registration is not rewarded explicitly by any venue page read; it should be presented as the reason the null and not-resolvable outcomes
   are trustworthy, citing the ML pre-registration precedent (BIBLIOGRAPHY entry 110) and the recent ICML position papers (entries 113, 116).

No publishability claim is made.
