# Project inventory (Phase 0, read-only)

Audit session 2026-10-31. Branch `paper-revision` created from `paper-draft` @ `bd4d390` (worktree
`E:\study-buddy\DynaICL-paper-rev`); evidence branch `stage1-planning` @ `6a9c0d0`. Labels: VERIFIED (read or run in this
session, source named), DERIVED (math, location given), REPORTED (from a file not re-checked), ASSUMED, UNVERIFIED.

## 1. The exact research question

* **As the paper states it** (VERIFIED, `paper/sections/01_introduction.tex`): for in-context forecasting of autoregressive
  systems, "in which cells could a model's behaviour be classified at all?", i.e. where three Bayes references
  (population prior, finite-library posterior, context-only Bayes with a vague stability prior) differ in expected log score by
  more than delta = 0.02 nats per forecast, before any network is trained.
* **As the project defines it** (VERIFIED, `CLAUDE.md` section 1; `docs/PREREG_stage1.md` section 1): the long-run question is
  whether a pretrained transformer behaves like continuous-prior Bayes (generalisation), like a finite-library posterior
  (memorisation), or like a context-only estimator. The paper answers only the precondition (are the references separable).
* **Assessment.** The question is a design question (a power / separability analysis for a future behavioural experiment), not a
  question about learning systems. That is legitimate for TMLR only if the paper delivers either (a) a general, reusable method
  or (b) a result a reader could not have predicted. See NOVELTY_ANALYSIS.md: much of the map is predictable from two
  closed-form quantities (DERIVED there).

## 2. Hypotheses, by study (pre-registered ones marked)

| Study | Pre-registered? | Question / hypothesis | Source (VERIFIED) |
|---|---|---|---|
| Stage 0 separability map | Yes (`docs/PREREG_separability.md`, frozen) | Where are matched, library and frontier strategies separable at delta = 0.02; diagnostic hypotheses H1-H4 (H4 contradicted) | PREREG_separability.md sections 1, 7 |
| Stage 0.5 | Yes (`docs/PREREG_stage05.md`, frozen sha256 fcf7f3a5...) | Q1: matched population Bayes beats the strongest context-only estimator by a meaningful amount; Q2: library vs continuous distinguishable. Decision PROCEED / REVISE / STOP | PREREG_stage05.md section 1; summary.json @ 3632e9e: verdict REVISE (P2, P3 failed) |
| Stage 0.6 | Yes (v1 text + Amendment 1, frozen v2) | Does noise-aware population Bayes give a meaningful long-context (n = 10..40) advantage under observation noise beyond the zero-noise advantage? | PREREG_stage06.md section 1; results summary.json @ 18d34b0: STOP |
| Stage 1A separability map | Spec committed before the run (not a pre-registration with hypotheses) | Mechanical selection of neural cells (IDENTIFIABLE / PARTIAL) | STAGE1_SEPARABILITY_MAP_SPEC.md |
| F1, F3, F2 maps | Specs committed before seed use (F3: S31; F2: S35; F1: S16 context) | Same mechanical selection, new families | STAGE1_F1_SEPARABILITY_MAP_SPEC.md, STAGE2_F3_MAP_SPEC.md, STAGE2_F2_MAP_SPEC.md |
| Stage 1A neural | Yes (PREREG v3 + Amendment 1, frozen v2, manifest 94cf1c51...) | Q1 trained-on-population models POP-LIKE vs STAB-LIKE in identifiable cells; Q2 transition K* from LIB-like to generalising | PREREG_stage1.md section 1; pilot_decision.json @ e260526: NOT RESOLVABLE (compute) |
| F1 neural, F2 neural | DRAFTS only (not frozen, not authorised) | Same Q1/Q2 in the F1 / F2 families | PREREG_stage2_F1.md, PREREG_stage3_F2.md |
| Sensitivity batch 4 | Spec committed before seed use (S39) | Comparator frontier, prior dependence, F3 at 10x precision | STAGE2_SENSITIVITY_SPEC.md; **results not yet returned** |

## 3. The claimed contribution (VERIFIED, `01_introduction.tex` "Contributions")

(i) validated references for four linear-Gaussian families; (ii) separability maps with power limits and a delta sensitivity;
(iii) pre-registered results including a null (Stage 0.6 STOP) and a not-resolvable neural pilot; (iv) the integrity machinery
(freeze manifests, append-only disclosure logs, authorization gate, claims table re-deriving every number) as methodology.

## 4. New versus established (my assessment; details in NOVELTY_ANALYSIS.md)

| Component | Status | Reason |
|---|---|---|
| Bayes references for AR(1) / VAR(1) (conjugate, truncated, Kalman) | Established mathematics; careful implementation is new work, not new knowledge | Textbook conjugate and Kalman algebra (MATH*.md cite it as standard) |
| Validation (SBC, calibration, optimality, mutation matrices) | Established methods, applied unusually thoroughly | Talts et al. 2018 SBC; mutation testing is standard software practice |
| "Separability map before training" as a protocol | Plausibly new as an explicit protocol for ICL studies; close to classical model-discrimination design (Box-Hill 1967, T-optimality) and to power analysis | Literature agent search pending; the paper itself says it "has not reviewed" optimal design |
| The specific numbers in the maps | New, but largely predictable: the population window from KL(prior_pop or prior_ctx), the library window from nearest-atom KL | DERIVED in this audit (STATISTICAL_AUDIT.md section 6) |
| F1 / F2 "wide windows" | New numbers; interpretation not supported: mostly noise-scale knowledge given to pop and withheld from ctx | Reviewer 3 and this audit (DERIVED) |
| Pre-registration and disclosure machinery | Good practice, documented in unusual detail; precedent exists (NeurIPS 2020 pre-registration workshop) | Not a scientific contribution at TMLR's bar on its own |
| Neural results | None | The one study ended NOT RESOLVABLE (compute) |

## 5. Manuscript structure (VERIFIED, `paper/main.tex`, build log)

Track 1 (`main.tex`), 10 pages, 11 sections: abstract; introduction; related work (4 short paragraphs); setting and references;
validation; separability-first design; results (3 generated tables, **no figures**); neural pilot; limitations; methodology;
conclusion. No appendices. 18 bibliography entries (surnames only). Track 2 (`main_track2.tex`) is a neural skeleton with
placeholders only: not a result, not audited as one.

Evidence pipeline (VERIFIED by running `python paper/build.py` in the new worktree, 39 s): claims 41 verified / 0 pending; 60+
macros re-extracted from 12 pinned commits; numbers audit PASS (15 section files); both PDFs built (10 pages each).

## 6. Where each piece of evidence lives

| Evidence | Branch / commit | Path |
|---|---|---|
| Stage 0 map, Stage 0.5 | `main` @ 3632e9e | `runs/20261009T094047949167Z_separability_9123175bb3/`, `runs/20261010T053729455237Z_stage05_population_advantage_51c7621b7a/` |
| Stage 0.6 confirmatory | `results-stage06-confirmatory-20261022` @ 18d34b0 | `results_stage06_confirmatory/phaseE-20261022/` |
| 1A map | `results-stage1-map-1A` @ a499874 | `results_stage1/map_1A/` |
| F1 map, OC v2 | `results-stage1-step3` @ 66c5846 | `results_stage1/map_F1/` |
| Pilot decision | `results-stage1-pilot` @ e260526 | `results_stage1/pilot/pilot_decision.json` (eval/ never opened) |
| F3 map, F1-V9, F1 OC/lookup | `results-stage2-cpu-batch1` @ 50a7664 | `results_stage2/f3_map/`, `f1_mutation_matrix/`, `f1_power_lookup/` |
| F1 validation (A2) | `stage1-planning` @ ac8aecb | `results_stage2/f1_validation/` |
| F2 map, F2 validation, F2-V11, F1 head floor | `results-stage2-cpu-batch23` @ 56e73a8 | `results_stage2/f2_*`, `f1_head_floor/` |
| Sensitivity (batch 4) | **not on origin** (checked `git branch -r` after `git fetch`, 2026-10-31) | expected `results-stage2-cpu-batch4` |

## 7. Pending work and GPU need

| Item | Needs GPU? | State |
|---|---|---|
| Batch 4 sensitivity (comparator, prior, F3 precision) | No (box CPU, ~12 CPU-h) | Relayed; not returned |
| Noise-matched comparator in F1 and F2; F2 comparator frontier | No (box CPU) | Not specified yet (gap found in this audit) |
| Analytic KL-budget and nearest-atom predictions beside the maps | No (laptop, seconds-minutes) | Prototype in this audit's scratch scripts |
| F2 library map at larger K and longer n | No (box CPU) | Not specified |
| Figures, appendices, bibliography, related work | No | Not done |
| F1 neural, F2 neural | **Yes** | Drafts; not authorised |
