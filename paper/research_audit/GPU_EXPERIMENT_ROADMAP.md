# GPU experiment roadmap (Phase 7: PLAN ONLY, nothing runs)

No GPU, CUDA or torch job, freeze, authorization or confirmatory run may start without the user's explicit go-ahead. Inputs:
`docs/PREREG_stage2_F1.md` (draft 0.1), `docs/PREREG_stage3_F2.md` (draft 0.1), the Stage 1A pilot (S26), J0 (S19), the UNIF
spread read (S20), the F1 power lookup (S33), and this audit's derivations (STATISTICAL_AUDIT.md section 6).

## 0. Cost basis (REPORTED from verified result files; disclosures S19, S26)

* Contended J0 (size M, shared A4000, another user's job at ~100%): 0.0114 s per model-step effective at concurrency 8-16.
* Pilot measured: 32 models x 100k steps in 9.56 h with 8 concurrent processes = 0.01076 s per model-step.
* Formula used below: GPU-h = arms x models per arm x replicates x B x 0.0114 s x 1.25 (safety) / 3600. F1 uses an m = 8 mixture
  head (Stage 1A used m = 2): the cost per step is ASSUMED similar (head cost is small next to the transformer); must be measured
  in an engineering smoke. Bivariate F2: ASSUMED 1.5x per step (2-D input and full-covariance head); UNVERIFIED.
* The GPU is shared; every GPU job is preceded by the user confirming it is free (CLAUDE.md section 0).

## 1. A design problem in the current plan (must be decided before any F1 freeze)

**Q1-F1 as drafted has a predetermined answer.** A model trained on P_F1 minimises expected log loss on P_F1, whose minimiser
is the population Bayes predictive; a converged CONT-F1 model is therefore POP-LIKE by construction, and a CTX-LIKE outcome would
only indicate under-training, which the pre-registered convergence criterion and control C2 are designed to exclude (DERIVED).
Worse, the F1 context-only comparator spreads sigma over four decades, so most of the F1 gap is noise-scale knowledge that any
trained network acquires from the scale of its training data (Reviewer 3, STATISTICAL_AUDIT 6.1). A Q1-F1 study would spend most
of its GPU budget confirming that training converged.

The questions whose answers are **not** fixed by risk minimisation are:
* **Q2 (memorisation transition):** a model trained on K atoms is Bayes-optimal on its training law only if it reproduces lib_K;
  Raventos et al. found networks depart from lib_K towards the continuous prior above a task-diversity threshold. Whether and at
  which K this happens in dynamical families is genuinely open, and the maps say where it is observable by score.
* **Off-support behaviour:** on systems outside the training support (OOS sets), risk minimisation does not fix the network's
  predictive; which reference it resembles there is an empirical question (designed sets; gap is not a KL).

## 2. Experiments, prioritised

| Pri | Experiment | Question / hypothesis | Design | Baselines / references | Models, seeds | Metrics | GPU-h (basis) | Value | If NOT RESOLVABLE |
|---|---|---|---|---|---|---|---|---|---|
| **P0** | Seed-variance probe (F1 CONT, and LIB-8) | Is the between-seed sd of regret <= 0.01 nats (the F1 lookup's threshold at M = 32)? Decides whether any neural classification is feasible. | 16 models per arm, 2 arms, checkpoints 10k/25k/50k; evaluation on the F1 held-out cells; pilot seed role only | pop, lib_8 | 32 models | between-seed sd of regret per cell; convergence curve | 32 x 50k x 0.0114 x 1.25 / 3600 = **6.3 h** | Very high per GPU-hour: it is the quantity every power statement rests on (UNIF-only proxy 0.0017 at 10k, S20) | Report the measured sd; that alone bounds what any study can resolve |
| **P0** | F1-Q2 transition (scalar, cheaper) | From which K do LIB-K models stop resembling lib_K and resemble pop, on held-out systems? H: transition between K = 4 and 32 (where the references remain separable at n <= 20: per-draw 91% / 61% / 10% at K = 4 / 8 / 16) | arms LIB-K, K in {1, 2, 4, 8, 16, 32} + CONT; per-model library; cells from the F1 map (HELD lib or pop, K <= 16; designed sets for larger K, labelled behavioural) | lib_K, pop | 7 arms x 32 x 2 replicates | classify_memorisation (frozen Stage 1A rule), per-model own-library gate | B = 25k: 7x32x2x25000x0.0114x1.25/3600 = **44 h**; B = 50k: 89 h | High: an answer not fixed by theory; directly comparable to Raventos et al. | Report as NOT RESOLVABLE with the measured sd; the paper stays a reference paper |
| **P1** | F2-Q2 transition (bivariate) | Same, where references stay separable to K >= 1024 (DERIVED nearest-atom limit). H: K* is observable by score in F2 and not in scalar families | arms LIB-K, K in {2, 16, 64, 256, 1024} + CONT | lib_K, pop | 6 arms x 32 x 2 | as above | B = 50k, 1.5x per step: 6x32x2x50000x0.0114x1.5x1.25/3600 = **114 h** (ASSUMED rate) | Highest scientific value (a predicted, testable transition); most expensive; prerequisites below | As above |
| P2 | Off-support behaviour (CONT models from P0/P1) | On OOS systems, does a CONT model extrapolate like pop (truncated) or like ctx (stability only)? | no new training: evaluate P0/P1 CONT models on OOS-A / OOS-SIGMA sets | pop, ctx | reuse | behavioural gap (not a KL) | evaluation only (< 1 h) | Moderate | Exploratory only |
| P3 | Q1-F1 as drafted | POP-LIKE vs CTX-LIKE in 12 cells | as draft | pop, ctx | 2 arms x 32 x 2 | classify_q1_held | B = 50k: 2x32x2x50000x0.0114x1.25/3600 = 25 h | Low (predetermined for converged models; section 1); keep only as a control inside P0/P1 | - |
| - | Stage 1A Amendment 2 | - | abandoned (S34) | - | - | - | 128 h | Not recommended | - |

Prerequisites (all CPU, before any freeze): F1-Q2 operating characteristics with the analysis's bootstrap critical value and the
per-draw separability (exists for Q2 at designed sets, S33; extend to the HELD K <= 16 cells); F2: extended library map
(K in {256, 1024}, n up to 40), bivariate head floor, F2 OC and power lookup; noise-matched comparator maps (to re-decide whether
any Q1 study is worth running).

## 3. What the paper can claim in each outcome

* No GPU work: a reference-side paper (TMLR) whose contribution is the theory of reference distinguishability plus validated maps
  (see FINAL report / NO_GPU_ACTION_PLAN.md); the Stage 1A pilot stays a reported NOT RESOLVABLE.
* P0 seed-variance probe only: adds a measured feasibility bound for neural classification in these families (useful; small).
* P0 transition RESOLVED: a first pre-registered memorisation-transition result in a continuous-state dynamical family, with a
  prediction made before training (strongest venue options).
* P0 transition NOT RESOLVABLE: reported as such, with measured sd; no claim about networks.
