# Stage 0.6 Phase C freeze procedure (PROPOSAL; nothing is frozen yet)

Status: a proposal awaiting the user's approval. No confirmatory seed has been used.

## 1. Decisions needed from the user before the freeze

| # | Decision | Proposal | Basis |
|---|---|---|---|
| 1 | Noise levels | Keep q = 0.755, 2.56, 6.50 (asymptotic rule), or switch to the finite-n calibrated q = 0.721, 2.363, 5.714 (n = 20) | STAGE06_NOISE_LEVEL_VERIFICATION.md. The difference is 4-14%. |
| 2 | Long-context region L | n_L = 10, so L = {10, ..., 40} | Stage 0.5 (VERIFIED artifact): the zero-noise r = 1, h = 1 gain was confirmed meaningful only at n <= 3, discordant at 5, inconclusive at 10 and negligible at 20. L begins where the zero-noise advantage no longer clears delta. |
| 3 | Primary estimand | Per (positive q, h, r): the system-level gain averaged over n in L (each system contributes the mean of its 31 contexts), averaged over systems | Avoids treating the dependent contexts of one trajectory as independent |
| 4 | Uncertainty | Cluster bootstrap over systems (whole systems resampled, never (system, n) pairs), B = 4000 percentile intervals at the decision level; the analytic system-level SE is also reported | Systems are independent; contexts within a system are not |
| 5 | Primary family | 18 cells: q in {0.755, 2.56, 6.5} x h in {1, 5} x r in {0.25, 1, 4}. The full n-grid and q = 0 are descriptive or control | |
| 6 | Zero-noise control contrast | Per (q > 0, h, r): G_L(q) - G_L(0), with a paired cluster bootstrap. The same systems' latent paths are used across q (by construction, V14) | GO must not be triggered by an advantage that exists without noise |
| 7 | Per-replicate class | SUPPORTED if the decision interval lower bound > delta; ABSENT if the upper bound < delta; otherwise UNRESOLVED (an interval touching delta is UNRESOLVED). The control contrast must also have its lower bound > 0 | delta = 0.02 nats/forecast, unchanged |
| 8 | GO / REVISE / STOP / BLOCKED (numerical) | GO: in BOTH replicates, SUPPORTED with control > 0 in at least 2 of 3 q levels, at h = 1 AND h = 5, for r = 1 and at least one other r. STOP: ABSENT (upper bound < delta) in both replicates for every primary-family cell. BLOCKED: any reference-validation, integrity or Tier-1/Tier-2 failure. REVISE: otherwise. | Mirrors the prompt's definitions; to be finalised in PREREG_stage06.md |
| 9 | Tier-2 reproduction | Comparable cells: q = 0, r in {0.25, 1, 4}, h in {1, 5}, n in {2, 3, 5, 10, 20}, vs Stage 0.5. Pass if each abs(difference) <= 3 x combined SE, and the confirmed classes agree in >= 80% of cells. A failure means BLOCKED | Fresh seeds, so agreement means within sampling error |
| 10 | N systems per replicate | From the verified Stage 0.5 per-item sd (0.07-0.18 at n = 10..20): N = 4000 gives a decision half-width <= about 0.3 delta even at the conservative per-n sd. The L-averaged sd is expected to be smaller (to be confirmed by the precision calculation in the pre-registration, using Stage 0.5 artifacts only) | Section 5 below |
| 11 | Noise-naive secondary baselines | Score them only at n in {2, 5, 10, 20, 40} on 1000 systems per replicate (non-decisional, descriptive). The primary pair runs on the full grid | Workload (section 4) |
| 12 | Secondary frontier selection | Per (q, h) on the selection split (seed 63001), over all context-only members including noise-naive ones; frozen map. Not used for the primary verdict | |

## 2. Freeze steps (after approval)

1. `config/stage06.yaml` plus a strict schema; `docs/PREREG_stage06.md` (rules from section 1, with the exact numbers).
2. Re-run the full Stage 0.6 validation suite on the exact files to be frozen. It must be green.
3. **Freeze manifest** `docs/FREEZE_MANIFEST_STAGE06.json`: SHA-256 of the pre-registration, MATH_STAGE06, the config, the seed
   manifest, every `dynaicl/**/*.py`, the Stage 0.6 tests, the validation report, the run instructions/notebook, and
   `requirements.txt`; plus the Python, numpy/scipy/pyyaml/pytest versions, platform and BLAS info.
4. A read-only snapshot archive `dist/stage06_frozen_snapshot.zip` of code, configs, docs and tests, with its SHA-256 recorded in
   the manifest. Files in the archive are marked read-only.
5. **Print the manifest's own SHA-256**, for the user to store outside the workspace. A manifest stored beside its files
   only protects against accidental change.
6. The confirmatory runner verifies every manifest entry at start-up and refuses to run on any mismatch.
7. Limitations are documented: a SHA-256 manifest is integrity evidence, not version control or full provenance.

## 3. Phase D (after the freeze)

Smoke tests; a small pilot on 62001/62101 (runtime and numerics only, no effect estimates reported); an interruption-and-resume
test with atomic, checksummed checkpoints; the full Stage 0.6 mutation matrix on remote compute; and a measured runtime estimate.

## 4. Workload (measured; see section 6 of the Phase B report for the timing method)

Measured on an idle CPU (this machine, Python 3.13.5, numpy 2.2.2), pilot seed 62001, 256 systems, q = 2.56, r = 1:
* primary pair (population + stability), all n = 2..40 x h in {1, 5}: **28.0 ms per system per (q, r)**;
* the noise-naive family (8 members) at n in {2, 5, 10, 20, 40} x h: **81 ms per system per (q, r)**.

Confirmatory budget for 2 replicates x 4 q x 3 r: N = 2000 per replicate is about 55 CPU-min; N = 4000 is about 77 CPU-min (noise-naive on
1000 systems), plus selection, bootstrap and the Tier-2 reproduction (small). That is about 12 min on 8 local cores, which is over
the 10-min local policy, so the confirmatory run goes **remote (Colab)**: about 40-60 min on 2 vCPU (estimate, not measured on Colab).

## 5. Precision preview (verified Stage 0.5 artifacts only)

Item-level sd of (population - stability), zero noise, E-CONT, Stage 0.5: n = 5: 0.109-0.252; n = 10: 0.085-0.176;
n = 20: 0.070-0.107. With the most conservative value (0.176), N for decision-interval half-width <= delta/2 is 1555
(z = 2.24) and for <= delta/4 is 6220. Noise is expected to change these sd values. They are a planning proxy only.
