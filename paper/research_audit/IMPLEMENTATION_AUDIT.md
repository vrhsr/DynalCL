# Implementation audit (Phase 4)

Scope: code against `docs/MATH*.md` and the paper's Sections 3 and 5. Read-only; no methodology changed. Branch `stage1-planning`
@ `6a9c0d0`. Reviewer 2's independent code check is merged in INDEPENDENT_REVIEW.md when it returns.

## 1. Tests run locally (VERIFIED, real output; stdin closed, no `-s`)

| Suite | Command | Result | Time |
|---|---|---|---|
| Stage 0 + Stage 0.6 (non-slow) | `python -m pytest -q -p no:cacheprovider tests -m "not slow"` | **170 passed, 4 deselected** | 22 min 4 s (over the 10-min guideline: the CPU was shared with four audit agents; disclosed) |
| Stage 1 references | `tests_stage1/test_analysis.py test_ar1_batch_references.py test_f1_references.py test_kl_quadrature.py` | **53 passed** | 7 min 0 s |
| Stage 2 subset | `tests_stage2/test_seed_roles.py test_f3_map.py test_f1_checks.py` | **10 passed** | 1 min 42 s |
| Not run here | `tests_stage1/test_neural.py`, `test_pipeline_e2e.py` (import torch: excluded by the no-torch rule); `test_authorization.py` (creates test keys: excluded by the no-key rule); `tests_stage2/test_f2_references.py` (about 12-15 min, S32); Stage 0 slow tests (F optimality) | box or a later session | - |

The background wrapper returned exit 1 although all three pytest logs end in "passed"; the exit code came from the wrapper's
final command, not from pytest (each log checked).

## 2. Code versus MATH and paper (VERIFIED by reading unless noted)

| Item | Finding |
|---|---|
| Context cutting | 1A/F1 contexts via `dynaicl_families/sampling.py` -> frozen `harness.make_context`; F2 coordinate-wise `make_context` (`f2_var.py:536-541`); F3 via the frozen `make_noisy_context`. Direct slicing appears only in leakage checks and an intentional mutation (`f1_mutations.py:62`, marked BUG). Consistent with invariant 4. |
| F2 MC estimator and MC-LIMITED rule | `f2_map.py:25-27,57-77,129-149` implements MATH_F2 section 5 and the S34 criterion exactly: per-item target 0.01, cell SE = sqrt(SE_items^2 + SE_MC^2), SE_MC = sqrt(sum se_i^2)/N, MC-LIMITED if SE_MC > delta/100 or > 1% flagged items. Non-finite items are dropped and counted as flagged (small selection effect; STATISTICAL_AUDIT section 3). |
| F2 draw rule | 8 draws; ">= 0.9 x 8" means 8 of 8 (`classify_draws`). The paper's draw-count sentence omits F2. |
| Held-out vs atom disjointness (F2) | `held_unit` checks exact equality of continuous A matrices with atoms: guards against shared RNG streams, not against near-duplicates (by design; nearness is the quantity being measured). |
| 1A / F1 per-draw fraction | `scripts/stage1_separability_summarize.py:91-102`, `scripts/stage1_f1_map.py:116-126`: per draw lo >= delta, PARTIAL rule as the spec. `tab_library` averages the per-cell fraction (1A, F1) or recomputes from rows (F3, F2): same definition. |
| Table generator | `make_tables.py`: windows printed as "n <= max identifiable n"; VERIFIED contiguous for 1A, F1, F3; F2 has a MC-LIMITED hole at n = 5 (annotated). |
| Numbers audit | `check_numbers.py` scans digits only: number words pass; one macro used for a different quantity (\FoneMaxN for the 1A delta = 0.01 window). |
| Seed roles | `config/stage2_seed_manifest.yaml`: disjointness tested (`test_seed_roles.py` passed). The `status: unused` field is documentation only (no code reads it) and is stale for roles already used. |
| Worker-count independence | Units seeded through `NamedStreams` per unit/item; Stage 0 test_i covers it for the frozen code (REPORTED; not re-run for stage2 code). |
| Spec before seed | Spec first-commit times precede result commits for 1A (e18825c < a499874), F1 (2874fde < 66c5846), F3 (9b0fcd5 < 50a7664), F2 (0a7acf7 < 56e73a8) (VERIFIED, `git log --diff-filter=A`). Order of commits, not proof that seeds were unused before. |
| Independent numerical cross-check | 1A held-out pop vs stab gaps summed over n agree with the closed-form prior KL (0.582 nats) to about 3% (Reviewer 1; partial sum re-run here). An external check of the reference code that none of the internal tests provides. |

## 3. Contradictions found

1. Paper Sec. 3 describes every context-only reference as "a uniform prior on a slightly wider stable interval" (+ log-uniform
   noise in F1); F2's is a vague MNIW (V0 = 100 I, IW(1.5, 0.01 I)) (VERIFIED MATH_F2 section 2; Reviewer 3 confirmed in
   `f2_var.py`).
2. Paper Sec. 6 "four-coefficient space"; code and MATH_F2: atoms (A_k, Sigma_k), seven free parameters.
3. 1A map spec section 4 promises the expected number of wrongly marked cells; not reported anywhere.

No defect was found in the reference formulas or estimators within the scope read.
