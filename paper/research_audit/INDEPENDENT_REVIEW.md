# Independent reviews (Phase 1): synthesis

Three fresh sub-agents (2026-10-31/11-01), each given only the manuscript, `claims.yaml` / `CLAIMS.md`, evidence files at their
pinned commits (and, for Reviewer 2, the method docs and code), and web access to the literature. None saw
`REVIEW_1_hostile.md`, `REVIEW_RESPONSE_1.md`, `CLAUDE.md` or this audit. All were read-only.

**Independence caveat (disclosed).** The briefs for Reviewers 1 and 2 *asked them to check* the chain rule of KL (summed gaps vs
the prior KL) as one item. Reviewer 3's brief only asked whether findings "follow from textbook Bayesian asymptotics"; it derived
the same budget argument and the nearest-atom argument unprompted. Agreement on those two points is therefore partly prompted
(R1, R2) and partly independent (R3). The numerical results each reviewer reports are its own.

Full reports are kept in this session's transcript; the essentials and every issue are below.

## 1. Recommendations

| Reviewer | Focus | TMLR recommendation | Main-track |
|---|---|---|---|
| R1 | novelty and contribution | Major revision ("reject with encouragement to resubmit") | - |
| R2 | methodology and statistics | Major revision | - |
| R3 | skeptical, trying to reject | 4/10, Major (leaning reject as is) | 3/10, Reject |

## 2. Consolidated issues (severity = highest given by any reviewer; GPU = needed to fix)

| # | Issue | Raised by | Sev. | GPU | Evidence (summary) | Correction | Value |
|---|---|---|---|---|---|---|---|
| 1 | **F1 (and F2) "wide windows" are mostly the comparator's vague noise prior** | R1, R2, R3 | Critical/Major | n | R2 (own code, r = 1): F1 gap 0.28/0.18/0.09/0.03 at n = 2/3/5/10; with the population noise prior given to ctx 0.037/0.032/0.027/0.015 (window n <= 5, as 1A); sigma-only part 57-79%. Budgets: 1A 0.58, F1 2.57 (77% sigma), F2 about 17.4 nats (R2 MC; 5.7 with the population IW given to ctx). R3: noise-only gap 0.19/0.11/0.056/0.019 | Pre-specified noise-matched comparator maps; decompose; reword abstract, contributions, conclusion; reconsider F1 for Q1 | Very high |
| 2 | **Main patterns follow from classical theory, not derived or cited** (KL budget; nearest-atom limit; Clarke-Barron) | R1, R3 (R2 confirms numbers) | Critical | n | 1A summed gaps 0.566/0.567/0.571 vs KL 0.582 (R1); R2 about 0.55 | Theory section; maps as its validation (this turns the weakness into the contribution) | Very high |
| 3 | **"Observation noise shrinks population knowledge" is misleading** | R1 | Critical (R1) | n | Same a-prior in F3: budget 0.58 at every q; noise spreads it over n | "per-forecast gap"; cumulative view | High |
| 4 | **F1 library conclusion depends on the n grid** | R2 (my nearest-atom calc agrees) | Major | n | F1 K = 8 per-draw share 0.43 (n = 5) -> 0.88 (n = 40); K = 16 limit 0.037 nats, 100% of draws >= delta | State n-ranges; report asymptotic per-K KL; extend grid | High |
| 5 | **No neural result; significance** | R1, R3 | Major | y | Pilot NOT RESOLVABLE; no trained-model seed sd measured | Small neural demonstration or seed-sd probe; or frame as reference/theory paper | Very high (venue) |
| 6 | **"Identifiable" misused** | R1, R3 | Major | n | Every "unidentifiable" cell has a positive gap (1A n = 80: 5.6e-4, about 66 SE) | "separable / discriminable at margin delta"; separate MC-resolution flag | Moderate |
| 7 | Windows grid-limited; Table 2 ordering sentence false; F2 "longest contexts" range wrong | R1, R2, R3 | Major/Moderate | n | F2 0.338 is at n = 10 (n = 20: 0.070-0.089); F1 ties 1A at delta = 0.01; F2/F3 at grid end | Mark censoring; crossing brackets; fix sentences | Moderate-high |
| 8 | Wording overstates ("worth X nats", "memorisation visible", "many cells" for K <= 4, "we report how") | R3, R1, audit | Major | n | K = 4 known sigma 19%; comparator/prior dependence not reported | Scope sentences | Moderate |
| 9 | Library rule: 9-in-10 means 29/32, 15/16, 8/8; noisy labels; Table 3 not comparable across families (n grids) | R2 | Moderate | n | P(IDENT | p = 0.9) = 0.60/0.51/0.43 | Report shares per n with Clopper-Pearson intervals | Medium |
| 10 | F2 MC rule precision-based; dropped items; log bias | R2, audit | Moderate | n | All 19 MC-LIMITED cells are 0.32-1.51 nats; bias <= about 1e-4 | Bias bound; report excluded counts; validate per-item SE on more items | Medium |
| 11 | Related work thin; Wurgaft miscitation; Koshelev wording | R1, R3, literature agent | Moderate | n | arXiv HTML checks | Add verified literature (RELATED_WORK_GAPS.md) | Moderate |
| 12 | Paper reads as a project log; no figures; no appendices | R3, R1 | Major (pres.) | n | no `figure` environment | Restructure; Figures A-C | High |
| 13 | Pre-registration machinery is process, not science; pilot is operational | R1, R3 | Moderate | n | - | Shorten; reproducibility section + appendix | Moderate |
| 14 | delta not tied to trained-model precision | R1, R2, R3 | Major/Minor | partly | F1 lookup: seed sd <= 0.01 at 32 models | Show gap / required seed sd per cell; cumulative criterion | Medium |
| 15 | Multiplicity: minor; promised mis-mark count missing | R2, audit | Minor | n | expected wrong labels <= 0.19 over 144 Table 1 cells | Report the bound (closes spec deviation) | Low |
| 16 | F3 power at q = 0.755 | R2, R3 | Minor | n | 0.020-0.028 with SE about 0.0014 | Label power-limited; batch 4 | Medium |
| 17 | Macro misuse (\FoneMaxN for 1A) | R1, audit | Minor | n | - | 1A macro | Low |
| 18 | Bookkeeping: stale seed status; "single function" (F3 uses make_noisy_context); vacuous exact-equality disjointness | R2 | Minor | n | - | Fix text | Low |
| 19 | Pilot wording omits that 0.00215 is a max over 32 models and that a control failed at 10k | R2 | Minor | n | pilot_decision.json | Add half a sentence | Low |
| 20 | Placeholders, surnames-only bib, "Track 1 / not for circulation", no code statement | R3 | Minor | n | - | Fix | Low |

What all three agree is sound (VERIFIED by at least one reviewer independently): reference implementations (R2 reproduced 1A and
F1 within about 2 SE with independent code; R1 the 1A budget to about 3%); every table value recomputes exactly (R2); claims
build and number provenance (R1, R3); the pilot section is faithful (R2); no seed reuse across roles (R2); honest reporting of
nulls and failures (all).

## 3. Compared with internal review 1 (`REVIEW_1_hostile.md`): what is new

Review 1 already raised: library headline (fixed), PARTIAL undefined (fixed), mixed rules (fixed), KL claim scope (fixed), F3
power (text fixed), comparator dependence **qualitatively** (M7), no sensitivity (delta fixed; prior/comparator open), identifiable
vs model power (M8, partly), citations (partly).

New in this round:
1. **Quantified** comparator decomposition: the F1 window collapses to the 1A window with a noise-matched comparator (R2). Review 1
   said "may mostly reflect"; this round measured it.
2. The **KL-budget conservation** and **nearest-atom** accounts: the main patterns are predictable (R1, R3; numbers by R1, R2, audit).
3. Observation noise conserves the budget (R1): the F3 / Stage 0.6 framing must change.
4. F1 library conclusions depend on n (R2): the long-context limit makes K = 16 separable in every draw.
5. F2 prior KL about 17.4 nats; F2 context-only prior not described in the paper; seven, not four, parameters.
6. Two false or misattached sentences survive the claims build (F2 range; Table 2 ordering; \FoneMaxN).
7. Number words bypass the numbers audit.
8. Draw-rule operating characteristics (R2).
9. The planned F1 neural Q1 has a predetermined answer (audit, GPU_EXPERIMENT_ROADMAP.md section 1).
10. Missing figures; double-blind and LLM-use issues for submission.

What review 1 raised that this round did not re-raise: Stage 0 sigma, gate-fix wording, mis-marked-cells promise in the text (all
fixed in the draft).
