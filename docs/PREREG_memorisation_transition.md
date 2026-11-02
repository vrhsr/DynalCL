# Memorisation-transition study: pre-registration DRAFT 0.1 (2026-11-01). NOT FROZEN. NOT AUTHORISED. Nothing trained.

Status: CPU draft for the user's review (S40 decision 3). No GPU, no torch, no seed used; seeds below are proposals only.
Follows the seed-variance probe (`docs/PREREG_seed_variance_probe.md`), whose result sets the number of models per arm.
`docs/PREREG_stage2_F1.md` (F1 draft, Q1 + Q2) is kept; this draft replaces its order of work, not its machinery.

## 1. Question
A network trained on a library of K systems minimises its loss by reproducing the library posterior lib_K; networks trained on
regression tasks are known to depart from that towards the continuous prior above a task-diversity threshold (Raventos et al.
2023). In a dynamical family: from which K on does a network trained on K systems behave like population Bayes rather than
like its own library posterior on held-out systems, and is that transition visible by score?

## 2. Committed reference-side prediction (written before batch 5's box results and before any network exists)
Basis: the long-context limit of the held-out gap between lib_K and population Bayes, E[min_k KL_stat(theta || theta_k)]
(paper Section 6; Monte Carlo values pinned in `results_stage2/batch5/theory.json`, commit `cd2759f`, S41). At margin
delta = 0.02 nats, a library of K systems is separable from population Bayes at long contexts only while that limit exceeds
delta. Even a network that memorises its library perfectly cannot be told apart from population Bayes, by score on held-out
systems at that margin, once K reaches the size where the limit falls below delta. **Committed prediction, per family (the
library size at which a network trained on K systems stops being separable from population Bayes at long contexts, whatever
it learned):**

| Family | limit at the bracketing K (nats) | Predicted K_sep (delta = 0.02, long contexts) |
|---|---|---|
| AR(1), known sigma | 0.024 at K = 4; 0.011 at K = 8 | **K_sep = 8** (separable for K <= 4) |
| AR(1), unknown sigma (F1) | 0.035 at K = 16; 0.018 at K = 32 | **K_sep = 32** (separable for K <= 16) |
| bivariate VAR(1) (F2) | 0.237 at K = 64; 0.091 at K = 1024 | **K_sep > 1024** (separable for every K evaluated) |

Corollaries committed now: (a) at the context lengths of the maps (n <= 20 or 40) separability ends earlier than K_sep (the
library posterior has not concentrated; per-draw shares in the paper's Table 3); (b) a memorisation-to-generalisation
transition at K_net >= K_sep is unobservable by score in that family, so a study whose transition might lie above K_sep there
cannot classify it; (c) only F2 leaves room above K = 32.
Batch 5's reference-only results (F1 libraries at n up to 160; F2 libraries up to K = 1024 and n up to 80) may refine the
cell selection and the finite-n boundary. If they do, the change is written as an amendment to this draft before any freeze,
with both versions kept and the change disclosed; this table stays as the committed pre-batch-5 prediction.

**Observed after the commitment (batch 5, reference-only, `results-stage2-cpu-batch5` @ `e08eee8`, disclosure S46; the table
above is unchanged):** F2: separability of lib_K from pop grows with n and every K up to 1024 is separable at n = 80, as
predicted. F1: at n = 160 the mean K = 16 gap (0.032-0.037) matches its limit (0.035) and K = 32 lies below delta, as
predicted, but only 59-66% of K = 16 libraries are individually separable: the limit is a mean over libraries, so a design
that gates each model on its own library must expect a fraction of the K = 16 models to be unclassifiable.

## 3. Network-side hypotheses (stated, not assumed)
* H-mem: for K well below K_sep, converged networks are lib_K-like (they reproduce the training law's Bayes predictor).
* H-trans: there is a K_net above which networks are pop-like on held-out systems. Outcomes and their meaning, fixed now:
  K_net < K_sep (transition observed: memorisation then generalisation, both classifiable); no transition below K_sep
  (networks memorise up to the limit of what can be classified; K_net, if any, is not identifiable by score in this family);
  networks never lib-like (generalisation from the smallest K).

## 4. Design
* **Option B, F2 (primary; user decision S44), after the seed-variance probe:** arms LIB-K, K in {2, 16, 64, 256, 1024} and
  CONT-F2; cells: held-out lib-vs-pop cells separable or PARTIAL in the F2 map and its batch 5 extension (K up to 1024, n up
  to 80). Prerequisites on CPU (`docs/STAGE3_F2_DESIGN_CPU_SPEC.md`): the bivariate head floor and the F2 operating
  characteristics with a power lookup by the frozen rule.
* **Option A, F1 (fallback if the F2 budget is not available):** arms LIB-K, K in {1, 2, 4, 8, 16, 32, 64} and CONT-F1;
  cells: held-out lib-vs-pop cells separable or PARTIAL in the F1 map plus batch 5's long-context cells; the transition is
  classifiable only for K <= 16.
* Rules as the frozen Stage 1A Q2: per-model own-library gate, two-way rule `classify_memorisation`, hierarchical-bootstrap
  critical value (audit A1), alpha 0.025 per replicate, two replicates that must agree; models per arm from the lookup with
  the seed sd measured by the probe (minimum 32).

## 5. Compute: full GPU total and its basis
Basis: GPU-h = arms x models x replicates x steps x t x 1.25 (safety) / 3600, with t = 0.0114 s per model-step (contended J0,
size M, S19; the measured pilot rate was 0.01076 s, S26) and, for F2, an ASSUMED factor 1.5 that the probe's F2 arm measures
and replaces before any freeze. The pilot follows the Stage 1A pattern (8 models per arm, trained to the last grid point
100k; budget B chosen by the convergence rule from {10k, 25k, 50k}; 100k cannot qualify), so the confirmatory part is a range.

| Part | Option B (F2, primary) | Option A (F1, fallback) |
|---|---|---|
| Seed-variance probe (F1 arms 9.5 h + F2 arm 4.75 h) | 14.3 h | 14.3 h (9.5 h without the F2 arm) |
| Pilot: arms x 8 models x 100k steps | 6 x 8: **28.5 h** | 8 x 8: **25.3 h** |
| Confirmatory: arms x 32 models x 2 replicates x B | 6 arms: **23 / 57 / 114 h** at B = 10k / 25k / 50k | 8 arms: **20 / 51 / 101 h** |
| **Total** | **66 / 100 / 157 h** | **60 / 90 / 141 h** (55 / 86 / 136 h without the F2 probe arm) |

If the probe's seed spread requires 64 models per arm instead of 32, the confirmatory part doubles (option B up to 228 h at
B = 50k). The cap rule (frozen Stage 1A logic) declares NOT RESOLVABLE (compute) before the confirmatory run if the budget the
user sets cannot hold the required models. The A4000 is shared; all GPU work waits for the user's go-ahead and a free GPU.

## 5b. Head and power for option B (batch 6, `results-stage2-cpu-batch6` @ `6ffd8fc`, disclosure S48)
* **Bivariate head: m = 8** components (full covariances), the smallest m whose mean floor is <= 0.001 nats in every cell
  (worst cell at m = 8: 0.00048 +/- 0.00007, held-out lib_1024, r = 4, n = 2; m = 4 fails in 18 library cells at n <= 3).
* **Power lookup (Q2, frozen rule, cells of the batch 2-3 F2 map):** s*(M) = 0.01 / 0.01 / 0.02 nats at M = 32 / 64 / 128,
  against 0.10 for F1. Every shortfall is INCONCLUSIVE (never a wrong classification), and the binding cell is r = 1, n = 10,
  K = 16, where the library and context-only references differ by only 0.045 nats.
* **Consequence for option B.** By the frozen pilot rule (the smallest M whose s*(M) covers 1.35 x the measured seed sd), the
  probe's F2 arm must measure a between-seed sd of at most about 0.0074 nats for 32-64 models per arm, or 0.0148 for 128.
  With 128 models the confirmatory part grows fourfold (6 arms x 128 x 2 replicates: 456 GPU-h at B = 50k, 228 h at 25k,
  ASSUMED 1.5x per step), which the shared card cannot realistically absorb. So option B is feasible only if the probe's F2
  sd is of the order the UNIF proxy suggested (0.0017 at 10k steps, scalar, S20), or if cells with a larger
  library-vs-context-only separation loosen the tolerance. The second point is checked on CPU by re-running the operating
  characteristics on batch 5's cells (spec `docs/STAGE3_F2_OC_B5_SPEC.md`, relay `pilot_tooling/RELAY_stage2_cpu_batch7.md`);
  the Q2 cell set will be chosen from that result before any freeze.

## 6. Seeds (proposed, UNUSED, NOT registered)
mt_pilot_train 87001, mt_pilot_eval 87101, mt_pilot_library 87201, mt_pilot_bootstrap 87999; mt_confirmatory_train
88001/88002, _eval 88101/88102, _library 88201/88202, _bootstrap 88999.

## 7. Seen before this draft
All reference maps, the theory quantities (S41), the Stage 1A pilot's budget outcome, the UNIF spread read; not batch 4, not
the box part of batch 5, no network result in any family.

## 8. Decisions
1. Decided (S44): option B (F2) after the probe; option A kept as the fallback if the F2 budget is not available.
2. Open: GPU budget (sets the cap) and the go-ahead for the probe first.
