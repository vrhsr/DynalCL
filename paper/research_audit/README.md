# Research audit (checkpoint 1, 2026-11-01)

Independent audit of the Track 1 manuscript (`paper-draft` @ `bd4d390`), done read-only on branch `paper-revision`. No manuscript
file has been changed. Phases 0-8 of the audit brief (`docs/SESSION_PROMPT_paper_audit.md` on `stage1-planning`).

| Phase | Files |
|---|---|
| 0 Inventory | PROJECT_INVENTORY.md, EXPERIMENT_STATUS.md, CLAIM_EVIDENCE_MATRIX.md |
| 1 Independent reviews | INDEPENDENT_REVIEW.md, REJECTION_RISK_REGISTER.md |
| 2 Literature and novelty | LITERATURE_REVIEW.md, NOVELTY_ANALYSIS.md, RELATED_WORK_GAPS.md |
| 3 Claims | CLAIM_EVIDENCE_AUDIT.md |
| 4 Implementation, reproducibility | IMPLEMENTATION_AUDIT.md, REPRODUCIBILITY_AUDIT.md |
| 5 Statistics | STATISTICAL_AUDIT.md, EXPERIMENT_GAP_ANALYSIS.md |
| 6 No-GPU plan | NO_GPU_ACTION_PLAN.md |
| 7 GPU roadmap (plan only) | GPU_EXPERIMENT_ROADMAP.md, GPU_EXECUTION_CHECKLIST.md |
| 8 Figures and tables | FIGURE_TABLE_AUDIT.md |
| 9 Manuscript reconstruction (after checkpoint 1; the manuscript on this branch has changed since) | CHANGELOG.md (revisions 1-5a) |
| 10 Venue strategy | JOURNAL_TARGET_STRATEGY.md, LLM_USE_STATEMENT_DRAFT.md |
| 11 Second independent review | INDEPENDENT_SECOND_REVIEW.md, REVIEWER_DISAGREEMENT_ANALYSIS.md |
| 12 Readiness | FINAL_PUBLICATION_READINESS_REPORT.md |

Audit scratch scripts (not part of the repository; audit seed 20261031, not a project seed role):
`C:\Users\Ramana\AppData\Local\Temp\claude\e--study-buddy-DynaICL\bd3df7a4-8736-46d2-9c91-75fbaf70608c\scratchpad\audit\`
(`kl_budget.py`, `table_checks.py`, `nearest_atom.py`, pytest logs). Any number from them that enters the paper must first be
produced by a committed, pinned script through `claims.yaml` / `numbers.yaml`.

Results seen in this audit before any new specification (to be recorded in the disclosure log when the user approves): the prior
KL budgets (1A 0.582, F1 2.570, F2 about 17.4 nats), the nearest-atom limits, and Reviewer 2's scratch F1 noise-matched
comparator gaps (0.037 / 0.032 / 0.027 / 0.015 at n = 2 / 3 / 5 / 10, r = 1).
