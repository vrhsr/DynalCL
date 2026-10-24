# Stage 1A pre-registration, Amendment 1 (pre-pilot)

Status: part of the Stage 1 freeze v2 (`docs/FREEZE_MANIFEST_STAGE1_v2.json`). `docs/PREREG_stage1.md` (v3) is unchanged and remains
in force except where this amendment overrides it. The freeze v1 (`docs/FREEZE_MANIFEST_STAGE1.json`, sha256 `ef3dd65e...`, and
`dist/stage1_frozen_snapshot.zip`) is preserved untouched; the v1 manifest is itself listed in the v2 manifest.

## What changes (user decision, 2026-10-24)
The GPU-hour budget of the cap rule is raised from **48 to 96 GPU-hours** (`config/stage1.yaml`, `cap_rule.gpu_hours_limit`).
Wherever PREREG v3 says 48 GPU-hours (sections 7, 9, 12), read 96.

Because the cap rule and the secondary-family drop rule read the same configuration field, the drop rule now also uses 96 hours:
the primary experiment plus the retained secondary families must fit 96 GPU-hours, families still being dropped in the
pre-registered order and the primary families never reduced. (Interpretation chosen to keep one budget; flagged to the user.)

## Why
With the accepted contended J0 timings and the 32-model minimum, the 48-hour cap made the primary experiment feasible only at
B = 10k, so a convergence-driven B of 25k or more would have produced NOT RESOLVABLE (compute) for a reason unrelated to the
science. Made AFTER seeing the J0 timings and the UNIF-only pre-freeze evidence, BEFORE any pilot data (no pilot seed has been used).

## Re-derived cap table (pipeline.cap_from_j0; J0 effective 0.01141 s per model-step, evaluation 1 s per model, safety 1.25)
| B | cap at 48 h (v1) | cap at 96 h (this amendment) | largest lookup M (>= 32, <= cap) | primary feasible |
|---|---|---|---|---|
| 10k | 56 | 120 | 64 | yes |
| 25k | 24 | 48 | 32 | yes |
| 50k | 8 | 24 | none | **no: NOT RESOLVABLE (compute)** |
| 100k | 0 | 8 | none | cannot be selected (no next grid point) |

Limitation stated plainly: at 96 hours a convergence-driven B of 50k still gives NOT RESOLVABLE (compute); keeping 50k feasible
with these timings would need a budget of about 128 GPU-hours or a smaller minimum number of models.

## Unchanged
Everything else: estimands, families, alpha, classification rules, the budget grid and convergence criterion, the 32-model minimum,
the power lookup, the controls and critical checks, V-REPRO 1e-4, seeds, the verdict rules and the secondary families.
