# GPU execution checklist (Phase 7; for use only after the user's explicit go-ahead)

Each step stops for the user where marked [USER]. Nothing here authorises anything.

## A. Before any freeze (CPU, this laptop or box CPU)
1. [USER] Decide which experiment (GPU_EXPERIMENT_ROADMAP.md section 2) and the GPU-hour budget (sets the cap).
2. Rewrite the draft pre-registration for the chosen experiment; state everything seen before it (maps, pilot outcome, this audit).
3. Operating characteristics with the analysis's own hierarchical-bootstrap critical value (audit A1 lesson), power lookup by the
   frozen rule; minimum models per arm fixed from it.
4. Head floor (F1 done: m = 8; F2 pending), engineering smoke on CPU.
5. Register the new seed roles in the right manifest (`config/stage2_seed_manifest.yaml`); run `tests_stage2/test_seed_roles.py`
   (no seed reused across roles or with Stage 0/0.5/0.6/1 tables). Update the stale `status: unused` fields of roles already used
   (f1_a2_validation, f2_map, f3_map, f2_validation, f2_v_mutation, f1n_head_floor, f1_v9_detectors, f1_oc).
6. Include the **gate fix** from `amendment2-candidate` (`eaf4d3a`: refuse any TEST-ONLY key first; shared `binding_for`) in the
   code to be frozen (S28/S34); its regression test must fail on the old runner and pass on the new one.
7. Disclosure entry for every decision made after seeing any result.

## B. GPU engineering (needs the user's go and a free GPU)
8. [USER] Confirm the GPU is free (nvidia-smi from the box session); log temperature and utilisation in every job.
9. J0 timing for the chosen family/head on the box; engineering smoke (2 models, test-only seed role).
10. Recompute the cap from J0 with the frozen rule; if the minimum models per arm does not fit the budget, stop: NOT RESOLVABLE
    (compute) is decided before the pilot, not after.

## C. Freeze
11. Full suite + mutation matrix on the exact code; record tested files.
12. Freeze tool `build`: manifest, read-only snapshot, `verify`; commit; [USER] stores the manifest hash outside the workspace.
13. Never edit a frozen file afterwards; amendments are new documents in a new manifest.

## D. Pilot
14. [USER] Relay the pilot prompt (pilot seeds only; detached tmux; one background waiter; no polling).
15. Push only small files to a `results-*` branch; never push weights or effect-bearing evaluation files of the pilot.
16. Verify here: provenance commit equals the freeze commit (or frozen files byte-identical), clean tracked tree, `verify` line in
    the wrapper log, checksums; then the disclosure entry.

## E. Confirmatory
17. [USER] Issues the authorization artifact on the box with their own key (never here; never printed, stored or relayed).
18. One run id per checkpoint directory; resume verifies the gate; results to a `results-*` branch.
19. Verify as step 16; run the frozen analysis exactly once; disclosure entry; put numbers in the paper only through
    `claims.yaml` / `numbers.yaml` pinned to the results commit.
