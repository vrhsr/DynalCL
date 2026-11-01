# Experiment status (Phase 0)

Status as of 2026-10-31, checked against `git branch -r` after `git fetch origin` and the disclosure logs (S1-S39, F1-F29).

| # | Experiment | Status | Outcome | Evidence (VERIFIED by the claims build unless noted) | GPU |
|---|---|---|---|---|---|
| 1 | Stage 0 references + validation (A-K checks) | DONE | 95 tests pass (REPORTED, CLAUDE.md 7.1); T1 0/516, T2 0/60 | claims S0-T1, S0-T2 | No |
| 2 | Stage 0 separability map (pre-registered) | DONE | PROCEED narrowly / REVISE signal; decision never formally made (CLAUDE.md 7.5) | S0-SEP, S0-ELIB | No |
| 3 | Stage 0 remote mutation matrix | DONE (Colab) | 5/5 mutations detected; **archive not retained** (REPORTED only) | none: cannot be cited as evidence | No |
| 4 | Stage 0.5 population advantage (pre-registered) | DONE | **REVISE** (P2, P3 failed) | S05-DECISION, S05-RELIABILITY, LIB-S05 | No |
| 5 | Stage 0.6 noisy probe (pre-registered, gate) | DONE | **STOP** (all 18 long-context gains < delta) | S06-VERDICT, S06-MUTATION | No |
| 6 | Stage 1A separability map | DONE | VALID; pop vs stab identifiable n <= 5 (r <= 1) | S1A-MAP-Q1, LIB-1A | No |
| 7 | F1 references, map, validation, mutation matrix | DONE | VALID / PASS | F1-MAP-Q1, F1-VALIDATION, F1-V9 | No |
| 8 | F3 (noisy, short context) map | DONE | VALID; underpowered at q = 0.755 (14 borderline cells with estimate >= delta) | F3-MAP, F3-BORDERLINE | No |
| 9 | F2 (VAR(1)) references, map, validation, mutation | DONE | VALID / PASS; n = 5 MC-LIMITED; n <= 3 not computable | F2-MAP, F2-VALIDATION, F2-V11 | No |
| 10 | F1 operating characteristics + power lookup | DONE | Q1 s* 0.01/0.02/0.03 at M = 32/64/128 | F1-LOOKUP | No |
| 11 | F1 head floor | DONE | m = 8 | F1-HEAD | No |
| 12 | Stage 1A neural: J0, smoke, UNIF spread, pilot | DONE | Pilot **NOT RESOLVABLE (compute)** (B = 50k, cap 24 < 32) | S1A-PILOT, S1A-PILOT-B | Yes (done) |
| 13 | Stage 1A Amendment 2 (128 GPU-h) | ABANDONED (S34) | Candidate on `amendment2-candidate`; not adopted | DECISION-NO-AMENDMENT2 | - |
| 14 | Stage 1A confirmatory | NOT RUN (by design) | - | - | Yes |
| 15 | Batch 4 sensitivity | **PENDING on the box** (relayed 2026-10-31; no results branch) | unknown; no number may be used | spec at 67f773c | No |
| 16 | F1 neural (Q1-F1, Q2-F1) | DRAFT pre-registration; not frozen; not authorised | - | PREREG_stage2_F1.md | Yes |
| 17 | F2 neural | DRAFT; F2 head floor and OC PENDING | - | PREREG_stage3_F2.md | Yes |
| 18 | Sequence-level (pooled) separability test | OPEN since review 1; never specified | - | - | No |
| 19 | Expected number of mis-marked map cells | **Promised in the 1A map spec section 4, never reported** (pre-registration deviation; the paper text promising it was removed, the spec promise remains) | computed in this audit for headline cells (STATISTICAL_AUDIT.md) | - | No |

## Not resolvable / abandoned, and what may be claimed

* Stage 1A neural: the only claim is the pre-registered outcome NOT RESOLVABLE (compute) and its cause (budget 50k chosen by a
  0.000146-nat exceedance of the convergence tolerance; cap 24 < 32). No effect information exists; no claim about networks.
* Amendment 2: may be mentioned only as "prepared, labelled post-pilot, not adopted" (as the paper does).

## What still needs GPU (nothing runs without the user's explicit go-ahead)

Only items 14, 16, 17 (and an optional measurement of trained-model seed variance). Everything the audit recommends before
submission of a reference-side paper is CPU-only (NO_GPU_ACTION_PLAN.md).
