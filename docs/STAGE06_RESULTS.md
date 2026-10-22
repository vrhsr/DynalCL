# Stage 0.6 confirmatory result: pre-registered verdict STOP

Run `phaseE-20261022` (Linux x86_64 box, 2026-10-22, 50/50 units, one uninterrupted pass, no refusals or resumes). Files: `results_stage06_confirmatory/phaseE-20261022/`
(branch `results-stage06-confirmatory-20261022`, commit `18d34b0`). Rules applied exactly as frozen: `docs/PREREG_stage06.md` (sha256 `ec42214a...`) plus `docs/PREREG_stage06_AMENDMENT_1.md`.
Labels: VERIFIED = read or recomputed by me from the files; DERIVED = my reading of the frozen rules; UNVERIFIED = not checked.
I have not changed any estimand, threshold, N, noise level, seed or rule, and none of this is a novelty or publishability claim.

## 1. What was run (VERIFIED from `provenance.json`, `report.md`)
Frozen manifest `fdb46788cd0fddba59cbc995adf7a3f6f410184e299b4dfc5cbecfa8f3f3fa05`; config hash `8304d1ab2d37efbf...` (equals the frozen value); confirmatory seeds 64101, 64102 (replicates) and 64999 (bootstrap);
git commit `c662e59`, tree not dirty; Python 3.13.5, numpy 2.2.2, scipy 1.15.1, pyyaml 6.0.2. The environment differs from the frozen one (Linux vs Windows), so the runner required, and got, a passing qualification of the confirmatory config (V4, V6, V11, V13).
Authorization: HMAC artifact bound to this manifest, snapshot, config, pre-registration, amendment and seeds, run id `phaseE-20261022`, valid 24 h. The key was generated on the box, never printed, and shredded after the run; the artifact is kept off-repo.
All 8 files in the run's `checksums.json` match the pushed files by SHA-256 (8 of 8).

## 2. Critical checks: all six PASS (VERIFIED, `report.md`)
integrity (replicate, selection and Stage 0.5 system sets disjoint); Tier-1 regression (36,000 items, max difference 8.0e-15, tolerance 1e-9); calibration (96 tests, min p 0.049 against a per-test level of 1.04e-5);
numerics (max change under node doubling 2.7e-14, budget 2e-4); reproducibility (8.0e-15, tolerance 1e-10); Tier-2 zero-noise reproduction of Stage 0.5 (all 12 |z| at most 2.80, critical value 3.341).
Observation, not a failure: the Tier-2 z-values at h = 1 are all negative (-1.85 to -2.80); the Stage 0.6 zero-noise advantage is slightly smaller than Stage 0.5's there (for example +0.0270 vs +0.0311 at r = 0.25). At h = 5 the signs are mixed. I did not investigate this further.

## 3. Verdict (DERIVED from the frozen rule `STOP: G- holds for all 18 gains in both replicates`)
**STOP.** In both replicates, all 18 long-context gains (noise-aware population Bayes minus the locked noise-aware stability-only comparator, L = n 10..40) have a simultaneous upper bound below delta = 0.02 nats.
* Gain estimates are small and positive: 0.0011 to 0.0069 nats. The largest adjusted upper bound over all 36 gain intervals is +0.0077 (R2, q = 0.755, h = 1, r = 0.25), about 39% of delta.
* No cell is SUPPORTED in either replicate; Q(h, r) is empty for every h and r.
* The "increment" (gain at positive noise minus gain at zero noise) is the pre-registered contrast for "beyond what it gives without noise". At q = 0.755, h = 1 it is slightly positive (+0.0006 to +0.0012, lower bounds above 0 in both replicates, but about 5% of delta). At q = 2.56 and 6.5 it is zero or negative, down to -0.0025 (q = 6.5, h = 5, r = 0.25).
* Descriptive pooled gains at q = 0 (no noise) are 0.0024 to 0.0058 nats, so noise did not raise the long-context advantage in any meaningful way (descriptive; not part of the decision).

## 4. What this means and does not mean
* DERIVED: in this design, additive observation noise at the three pre-registered levels does not create a meaningful long-context advantage for knowing the population prior over knowing only stability. If anything the advantage shrinks as noise grows.
* Together with Stage 0.5 (the population-specific advantage appears only at short contexts, h = 1, n at most 3, and shrinks with horizon and with r), the AR(1) families studied here give little long-context signal that separates population-aware inference from the strongest context-only comparator. The distinguishing regime in these families is short context.
* STOP is a strong negative claim over these cells only: noise ratios q in {0.755, 2.56, 6.5}, r in {0.25, 1, 4}, h in {1, 5}, L = n 10..40, delta = 0.02, scalar AR(1) with Gaussian noise, the stated priors and library sizes.
  It says nothing about other systems, horizons, noise forms, shorter contexts, or neural models.
* UNVERIFIED: whether the pre-registration prescribes a next step after STOP. I did not find one in the passages I read; what Stage 1 should do given this is the user's decision.
* One platform: the confirmatory run executed on Linux after a passing qualification. Tier-1 agrees with Stage 0.5 to 8e-15 and the arrays were bitwise identical across worker and thread counts in Phase D, but bitwise equality with a Windows run was not tested.

## 5. Not done
No sensitivity analysis, no re-run, no change of any threshold, and no use of the noise-naive secondary baselines or n-curves for any decision (descriptive files only; I did not analyse them here).
Neural Stage 1 is not started and not authorised.
