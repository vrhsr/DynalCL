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

## 3. Network-side hypotheses (stated, not assumed)
* H-mem: for K well below K_sep, converged networks are lib_K-like (they reproduce the training law's Bayes predictor).
* H-trans: there is a K_net above which networks are pop-like on held-out systems. Outcomes and their meaning, fixed now:
  K_net < K_sep (transition observed: memorisation then generalisation, both classifiable); no transition below K_sep
  (networks memorise up to the limit of what can be classified; K_net, if any, is not identifiable by score in this family);
  networks never lib-like (generalisation from the smallest K).

## 4. Design (proposed)
* Option A, F1 (cheaper, scalar): arms LIB-K, K in {1, 2, 4, 8, 16, 32, 64} and CONT-F1; cells: held-out lib-vs-pop cells
  IDENTIFIABLE or PARTIAL in the F1 map plus batch 5's long-context cells; the transition is classifiable only for K <= 16.
* Option B, F2 (the family where the prediction leaves room): arms LIB-K, K in {2, 16, 64, 256, 1024} and CONT-F2; needs
  the bivariate head floor and F2 operating characteristics first (PENDING, CPU).
* Rules as the frozen Stage 1A Q2: per-model own-library gate, two-way rule `classify_memorisation`, hierarchical-bootstrap
  critical value (audit A1), alpha 0.025 per replicate, two replicates that must agree; models per arm from the lookup with
  the seed sd measured by the probe (minimum 32).

## 5. Compute (estimate and basis)
GPU-h = arms x models x replicates x B x 0.0114 s (contended J0, size M, S19) x 1.25 / 3600; measured pilot rate 0.01076 s
(S26).
* Option A (8 arms, 32 models, 2 replicates): B = 25k: **51 h**; B = 50k: **101 h**.
* Option B (6 arms, 32 models, 2 replicates, ASSUMED 1.5x per step for d = 2): B = 50k: **114 h**.
* Plus a pilot (pilot seeds; budget choice by the Stage 1A convergence rule) of about 10 h (32 models x 100k steps, S26
  rate). The training budget B is chosen by the pilot, so the totals are ranges; the cap rule (frozen Stage 1A logic) decides
  NOT RESOLVABLE (compute) before the confirmatory run if the budget the user sets cannot hold the required models.

## 6. Seeds (proposed, UNUSED, NOT registered)
mt_pilot_train 87001, mt_pilot_eval 87101, mt_pilot_library 87201, mt_pilot_bootstrap 87999; mt_confirmatory_train
88001/88002, _eval 88101/88102, _library 88201/88202, _bootstrap 88999.

## 7. Seen before this draft
All reference maps, the theory quantities (S41), the Stage 1A pilot's budget outcome, the UNIF spread read; not batch 4, not
the box part of batch 5, no network result in any family.

## 8. Open decisions (the user's)
1. Option A (F1), Option B (F2), or A then B.
2. GPU budget (sets the cap) and the go-ahead for the probe first.
