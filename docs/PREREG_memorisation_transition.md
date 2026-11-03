# Memorisation-transition study: pre-registration DRAFT 0.2 (2026-11-03; 0.1 of 2026-11-01). NOT FROZEN. NOT AUTHORISED. Nothing trained.

Changes in 0.2 (disclosure S52, made after seeing batch 7's reference-only operating characteristics): option B's Q2 cells
and tolerance (section 5c); option B's costing now depends on the training sequence length (section 5).

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
  CONT-F2; Q2 cells: the set C of section 5c (held-out, r = 1, n in {20, 40, 80}; chosen in 0.2), so models are trained at
  sequence length 81. Prerequisites on CPU (`docs/STAGE3_F2_DESIGN_CPU_SPEC.md`): the bivariate head floor and the F2
  operating characteristics with a power lookup by the frozen rule (both done: batches 6 and 7).
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

**Sequence length (0.2).** The table above uses the Stage 1A rate, measured at training length 20. Option B's Q2 cells need
length 81. If the per-step cost is linear in length (f_L = 81/20; ASSUMED, attention being quadratic this is not an upper
bound), option B costs: probe 28.7 h; pilot 115 h; confirmatory 92 / 231 / 462 h; **total 237 / 375 / 606 h** at
B = 10k / 25k / 50k. A leaner variant (5 arms without K = 2, pilot to 50k since 100k cannot qualify) costs 154 / 269 / 462 h
under the same assumption and 45 / 74 / 121 h if the cost does not depend on length. The probe's F2 arm measures the cost at
length 81, and that measurement replaces 1.5 x f_L before any freeze.

If the probe's seed spread requires 64 models per arm instead of 32 (tier 2 of section 5c), the confirmatory part doubles. The cap rule (frozen Stage 1A logic) declares NOT RESOLVABLE (compute) before the confirmatory run if the budget the
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
  the Q2 cell set will be chosen from that result before any freeze. (Superseded by section 5c: done.)

## 5c. Q2 cells and option-B threshold (batch 7, `results-stage2-cpu-batch7` @ `3896f37`, disclosure S52)
**Chosen after seeing these reference-only operating characteristics (no network result exists).** Batch 7 applied the frozen
Q2 rule to batch 5's extended library cells (held-out, r = 1, n in {20, 40, 80} x K in {16, 64, 256, 1024}). Per-cell s*(M)
(largest seed sd tolerated with P_correct >= 0.8 in every qualifying setting; larger is better; no setting ever classified
wrongly, max P_wrong = 0):

| K | n = 20 (M = 32 / 64 / 128) | n = 40 | n = 80 |
|---|---|---|---|
| 16 | 0.1 / 0.1 / 0.1 | 0.1 / 0.1 / 0.1 | 0.1 / 0.1 / 0.1 |
| 64 | 0.01 / 0.02 / 0.02 | 0.05 / 0.05 / 0.1 | 0.05 / 0.1 / 0.1 |
| 256 | none | 0.02 / 0.02 / 0.05 | 0.02 / 0.05 / 0.05 |
| 1024 | none / 0.01 / 0.01 | none | 0.02 / 0.02 / 0.02 |

* **Why the n = 20 row is not monotone in K.** A LIB-LIKE call needs the band on the model's distance to lib_K below half of
  s = min(sep(lib, pop), sep(lib, ctx)) (`classify_memorisation`). At n = 20 the population and context-only references are
  0.096 nats apart (mean held-out gap), and the library reference's mean gap to population Bayes falls with K (0.36 / 0.16 /
  0.075 / 0.039 for K = 16 / 64 / 256 / 1024): it starts farther from population Bayes than the context-only reference and
  passes the context-only reference's level near K = 256. The spec's separation lib-vs-ctx = |0.096 - lib-vs-pop| is
  therefore 0.26 / 0.064 / 0.021 / 0.057, and s = 0.26 / 0.064 / 0.021 / 0.039, in the same order as the tolerances (0.1;
  0.01-0.02; none; 0.01 at M >= 64). Every shortfall at n = 20 is INCONCLUSIVE, never a wrong call; at K = 256, s / 2 =
  0.010 leaves no room for an excess e = 0.01, and even with e = 0 the two-replicate band is too wide from s = 0.02 on; at
  K = 1024 the binding setting at M = 64 and s = 0.02 is a GENERALISING truth (s_lp / 2 = 0.019). At n = 80 the
  context-only reference is only 0.008 from population Bayes, so lib-vs-ctx is close to lib-vs-pop and every K is
  classifiable at 0.02.
* **Cell set C (primary):** K = 16 at n in {20, 40, 80}; K = 64 and K = 256 at n in {40, 80}; K = 1024 at n = 80. Pooled
  s*(M) on C by the frozen `lookup` (recomputed here from `oc_q2_f2.csv`) = **0.02 / 0.02 / 0.02** at M = 32 / 64 / 128.
* **Reduced set C'** (C without K = 1024 and without K = 256 at n = 40): **0.02 / 0.05 / 0.05**.
* **Option-B threshold** (the probe's go / no-go, `docs/PREREG_seed_variance_probe.md` section 2, on U, the upper 95% bound
  of the F2 LIB-64 seed sd): U <= 0.02: GO, 32 models per arm, C, all arms; 0.02 < U <= 0.05: GO, 64 models per arm, C',
  K = 1024 arm dropped; U > 0.05: NO-GO (option A considered). Both GO tiers also need the confirmatory compute to fit the
  user's GPU budget. The memorisation study's own pilot then applies the frozen rule 1.35 x pilot sd <= s*(M), i.e. a
  pilot sd of at most 0.0148 nats at tier 1 or 0.037 at tier 2.
* **K = 2:** no operating characteristics (batches 6 and 7 cover K >= 16); expected, not shown, to be the easiest cell
  (lib-vs-pop about 0.9 nats at n >= 10). Open: add K = 2 cells by a specified CPU run before any freeze, or drop the arm.
* Batch 6's lookup (cells n in {10, 20}, K in {16, 64}; s* = 0.01 / 0.01 / 0.02) is superseded for option B by C; it is
  kept unchanged and reported.

## 6. Seeds (proposed, UNUSED, NOT registered)
mt_pilot_train 87001, mt_pilot_eval 87101, mt_pilot_library 87201, mt_pilot_bootstrap 87999; mt_confirmatory_train
88001/88002, _eval 88101/88102, _library 88201/88202, _bootstrap 88999.

## 7. Seen before this draft
All reference maps, the theory quantities (S41), the Stage 1A pilot's budget outcome, the UNIF spread read; not batch 4, not
the box part of batch 5, no network result in any family. For 0.2: batches 4-7 (reference-only); no network result.

## 8. Decisions
1. Decided (S44): option B (F2) after the probe; option A kept as the fallback if the F2 budget is not available.
2. Open: GPU budget (sets the cap) and the go-ahead for the probe first.
3. Chosen in 0.2 (S52, after batch 7): Q2 cell set C / C' and the two-tier option-B threshold (section 5c).
4. Open: K = 2 arm (add its operating characteristics on CPU, or drop it); training length 81 is required by C.
