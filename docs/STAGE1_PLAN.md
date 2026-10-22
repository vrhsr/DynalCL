# Stage 1 plan: do trained models behave like population Bayes or like the context-only comparator? (DRAFT for approval)

Status: **PLAN ONLY. Nothing is implemented, nothing is trained, no seed below has been used.** Every number here is a proposal and a
hypothesis. The pre-registration (`docs/PREREG_stage1.md`) is written only after you approve this plan, and training starts only after you
have reviewed and frozen it. Labels: VERIFIED (read or recomputed from a result file), DERIVED (reasoning or algebra stated here or in
docs/MATH*.md), ASSUMED (a planning guess to be measured), UNVERIFIED.

## 0. What Stage 1 inherits (VERIFIED from the results files)

| Fact | Source |
|---|---|
| Population-specific gap Delta = LS(pop Bayes) - LS(stability Bayes), E-CONT, h = 1: r = 1: +0.042 / +0.044 (n = 1), +0.041 / +0.048 (n = 2), +0.046 / +0.040 (n = 3), R1 / R2 | `runs/...stage05.../results/item_contrasts.npy` (recomputed, script in section 11) |
| Same at r = 0.25: +0.044 / +0.046, +0.048 / +0.053, +0.053 / +0.046. At r = 4: +0.020 to +0.027 (INCONCLUSIVE in Stage 0.5) | same |
| Per-item sd of that realized-target contrast: 0.24-0.31 (n = 1..3, r <= 1) | same |
| At h = 5 the gap is <= 0.014; at n >= 10 it is <= 0.019; with observation noise the long-context gap is < 0.0077 (Stage 0.6 STOP) | STAGE05_RESULTS.md, STAGE06_RESULTS.md |
| Library K = 2 vs continuous on held-out systems (E-CONT): r = 1: -0.016 to -0.042 (n = 1..3), -0.048 to -0.087 (n = 5..20); r = 4: -0.10 to -0.24 (n <= 3). K = 4, 8: within +/-0.017 everywhere | item_contrasts.npy |
| The strongest context-only reference is generic-stability Bayes (prior U(-0.999, 0.999)) in all 144 Stage 0.5 cells | STAGE05_RESULTS.md section 4 |

Consequence (DERIVED): a neural classification can only be attempted where the two references differ by about 2 delta (h = 1, n <= 3,
r <= 1). There the target signal is about 0.044 nats. Any model error or seed-to-seed spread of that size erases it. The whole design below is
built around that constraint.

## 1. Questions (you choose the scope; recommendation in section 10)

* **Q1 (primary, your candidate).** A model pretrained on the population prior P (P-STABLE truncated normal, mean 0.4, sd 0.3, |a| < 0.95),
  scored on held-out systems from P at short context: does it behave like population-aware Bayes (pop reference) or like the
  context-only comparator (stability reference)?
* **Q2 (secondary, memorisation vs generalisation).** A model pretrained on a finite library of K systems drawn from P, scored on held-out
  systems: does it behave like the K-atom library posterior (memorises) or like a continuous-prior / context-only reference (generalises)?
  Stage 0.5 shows the references differ by >= delta only for K = 2 (and K = 1, trivially), so for K >= 4 the score-based question is
  **unidentifiable in this family** (DERIVED from the table above). A designed probe set (section 3.4) may identify it by KL; this is
  secondary and descriptive unless the planning computation shows enough separation.

Out of scope: h > 1 (gap negligible), the noisy-observation family (Stage 0.6 STOP), long context, other dynamical families, novelty claims.

## 2. Pretraining arms (each arm differs only in the distribution of a)

| Arm | Pretraining distribution of a | Bayes-optimal predictor for that distribution (DERIVED) | Role |
|---|---|---|---|
| CONT | P (the population prior) | pop reference (matched P-STABLE Bayes) | Q1 test arm |
| UNIF | U(-0.999, 0.999) | stability reference (the locked context-only comparator) | **positive control** for "context-only behaviour"; also the capability control |
| LIB-K, K in {1, 2, 4, 16} | uniform over K atoms drawn from P (atoms drawn per model seed) | finite-library posterior over that model's own atoms | Q2 |

* x_0 ~ N(0, r^2) with r drawn uniformly from {0.25, 1, 4} per training sequence. **DERIVED:** the likelihood is conditional on x_0 and
  x_0 is independent of a (CLAUDE.md section 4), so the Bayes predictor does not depend on the x_0 distribution; mixing r leaves every
  arm's Bayes target unchanged and lets one model be scored at every r.
* sigma = 1, known and shared (as in Stages 0-0.5). Trajectories x_0..x_20 start at x_0 (no burn-in, invariant 1).
* Fresh sequences every step (online sampling), so CONT and UNIF see unlimited systems; LIB-K reuses its atoms with fresh noise and x_0.
* **Common random numbers across arms (proposal):** model seed index i uses the same initialisation, data order, x_0 and noise streams in
  every arm. Only a differs, drawn by the arm's inverse CDF from the same uniforms. Contrasts between arms are then paired by seed.

## 3. Models, training and evaluation

### 3.1 Model (ASSUMED sizes; justified below)
* Causal decoder-only transformer over the scalar sequence, linear input embedding, learned positions (n is position), pre-LayerNorm.
* Output head: a Gaussian mixture density for x_{n+1} (proposal: 4 components). Trained by negative log likelihood at every position
  n = 0..19. The model is therefore a full density predictor and is scored with log score (never point-only; CLAUDE.md section 4).
* Sizes: **S** (2 layers, d = 32, about 30k params) and **M** (4 layers, d = 64, about 200k params). Justification (DERIVED): the h = 1
  Bayes predictive is a fixed function of three statistics (sum x_{t-1}^2, sum x_{t-1} x_t, x_n). The task needs averaging plus a smooth
  nonlinearity, which small attention models can represent; two sizes test whether capacity changes the classification. A larger size is
  added only if the capability gate fails (new decision, not in this plan).
* Training: AdamW, lr 1e-3 with warmup and cosine decay, batch 256 sequences, float32. Step budget: chosen in the pilot by a frozen rule
  (section 6), from {25k, 50k, 100k, 200k}, using training-distribution validation loss only.
* Evaluation runs in float64. The adapter receives an immutable `ContextWindow` from `harness.make_context` only, casts it to float32 for
  the network, and returns a float64 `GaussianMixturePredictive` (existing class). Ground truth never enters the adapter (invariant 3).

### 3.2 Head-family floor (planning computation, CPU, before the pre-registration)
The pop predictive at h = 1 is a continuous scale-location mixture, not a 4-component mixture. Before freezing I compute, for each
(n, r) cell, the smallest KL(pop || best m-component mixture) for m in {1, 2, 4, 8} on 2000 reference contexts. The head is accepted only
if this floor is <= epsilon / 10 = 0.001 nats (section 5). Otherwise m increases. This is reference-only arithmetic, not training.

### 3.3 Evaluation (held-out systems, existing references only)
* Systems: fresh from evaluation seed streams (disjoint from all training streams by construction; continuous a, so no atom coincides
  with probability 1; tested). Contexts are cut only by `dynaicl.evaluation.harness.make_context`.
* Cells: E-CONT, h = 1, n in {1, 2, 3} x r in {0.25, 1} = **6 primary cells**. Descriptive: n in {5, 10, 20}, r = 4, in-distribution scores.
* References (all existing, frozen, imported read-only): `MatchedReference` / quadrature P-STABLE (pop), `StabilityPriorBayesPredictor`
  (stab), `FiniteLibraryPredictor` (each LIB model's own atoms), known-a oracle (descriptive).
* N = 40 000 systems per replicate. With per-item sd <= 0.31, the item-level SE of a realized-target contrast is <= 0.0016 = delta/13
  (DERIVED). Model inference is cheap, so N is set to make item noise negligible next to seed noise.
* **Estimators.** (a) Realized-target paired log score (the Stage 0.5 / 0.6 estimator). (b) A Rao-Blackwellised version: per context,
  E_{y ~ pop}[log p_pop(y) - log p_model(y)] = KL(pop || model), computed by quadrature in y. **DERIVED:** on held-out systems from P the
  target given the context is distributed exactly as the pop predictive, so (a) and (b) estimate the same quantity, and (b) has no target
  noise. Their agreement is a critical correctness check. KL integrals are "numerically approximated with verified convergence" (node
  doubling; closed-form Gaussian-Gaussian check).

### 3.4 Probe set (Q2, secondary)
Designed contexts with a on a fixed grid over (-0.95, 0.95) and n in {3, 5, 10, 20}, chosen to separate library, continuous and stability
references. For these, only behavioural distances KL(ref || model) are defined (no reference is "true"). Used only if the planning
computation shows that the reference KLs on the grid exceed delta for K = 4 or 16; otherwise Q2 for K >= 4 is reported as unidentifiable.

## 4. Estimands (per replicate; the unit of inference is the trained model)

For model m and cell c, with the expectation over held-out P systems:
* **R_pop(m, c) = E[LS(pop) - LS(m)]** (regret against population Bayes; >= 0 in expectation, DERIVED: pop is Bayes on P).
* **Delta(c) = E[LS(pop) - LS(stab)]** on the same items (reference gap, about 0.044).
* **Arm estimand:** R_pop(A, c) = mean over the arm's models. Nearest-reference midpoint Delta(c)/2.
* **Transfer contrast:** G(c) = E[LS(m_CONT,i) - LS(m_UNIF,i)], paired by seed index i (CRN). If both arms are Bayes for their own priors,
  G = Delta. If CONT ignores population knowledge, G is about 0. Shared approximation error cancels in G (DERIVED to first order).
* Controls (not the hypothesis): **C1** UNIF regret against stab on held-out **U** systems at n in {1, 2, 3} (its own distribution);
  **C2** every arm's regret against its own Bayes reference at n = 20 on its own distribution (all references nearly coincide there).
* Q2: R_lib(m, c) and R_cont(m, c) for LIB-K models on held-out P systems at n in {3, 5, 10, 20}, r in {1, 4}, and on in-library systems.

## 5. Thresholds (all hypotheses; justification stated)

| Symbol | Value | Justification |
|---|---|---|
| delta | 0.02 nats | Unchanged since Stage 0 (fixed before any result). |
| Midpoint | Delta(c)/2, about 0.021-0.025 | A model is "nearer pop" than "nearer stab" in expected log score iff R_pop < Delta/2. Uses the measured Delta in the same items, so no free number. |
| epsilon (capability) | delta/2 = 0.01 | A model whose own-distribution regret exceeds 0.01 has an error of half the target signal; it cannot be classified reliably. The pop and stab equivalence regions of width epsilon are then separated by about Delta - 2 epsilon, about 0.024 >= delta. |
| Target SE of an arm estimand | delta/4 = 0.005 | Same rule as Stage 0.5 (target SE <= delta/4). With a simultaneous critical value of about 2.5 the half-width is about 0.0125, leaving about 0.009 below the midpoint for the model's own regret. |
| Familywise alpha | 0.05 per replicate, two replicates must agree | Same structure as Stages 0.5/0.6; false classification requires two independent errors (<= alpha^2 for a fixed claim). |

## 6. Power, seeds and number of models

* **Unknown and decisive: the seed-to-seed sd s of a model's regret.** No model exists, so s is UNVERIFIED. SE of an arm mean is
  about sqrt(s^2 / M + se_item^2) with se_item <= 0.0016.

  | s (between-seed sd) | models per arm for SE <= 0.005 |
  |---|---|
  | 0.005 | 2 (floor 4) |
  | 0.01 | 5 |
  | 0.015 | 10 |
  | 0.02 | 18 |
  | 0.03 | 40 (infeasible at the cap) |

* **Pre-registered two-phase rule (your constraint: no training before the freeze).** The pre-registration fixes, before any training:
  1. **Pilot** (pilot seeds only): 6 models per arm for CONT, UNIF and LIB-2, size M. It may only set (i) the step budget, the smallest
     value in {25k, 50k, 100k, 200k} at which every pilot model passes C2 on training-distribution validation data, and (ii) M from the
     between-seed sd: M = max(4, ceil(s_UCL^2 / (0.005^2 - se_item^2))), with s_UCL the 80% chi-square upper confidence limit of the largest
     cell sd (df = 5, factor 1.46). Pilot means are never used for any decision (the same rule as the Stage 0.5 pilot); the pilot effect
     outputs are written to a file that is not opened (as in Stage 0.6).
  2. **Feasibility:** cap M_max = 16 per arm per replicate. If M > M_max, or no step budget passes C2, the verdict is
     **STOP (infeasible in this family)**, with no confirmatory run.
  3. **Confirmatory:** two replicates, each with M fresh training seeds per arm and fresh evaluation seeds.
* Proposed seed roots (unused; checked against every `config/*.yaml`): pilot train 71001, pilot eval 71101, pilot library 71201, pilot
  bootstrap 71999; confirmatory train 72001 / 72002, eval 72101 / 72102, library 72201 / 72202, bootstrap 72999. Torch seeds are derived from
  `NamedStreams` names, so adding models never shifts others (invariant 4). A seed-role table like `config/stage06_seed_manifest.yaml` is the
  single source of truth.

## 7. Inference and decision rule (proposal)

* **Hierarchical bootstrap**: resample models within arm (with seed pairing kept across arms), then systems (shared across models);
  studentized max statistic over the family, as in Stage 0.6. Family per replicate: 6 cells x {R_pop(CONT), G} = 12 contrasts, plus controls.
* **Per-cell classification of CONT (both replicates must agree):**
  * POP-LIKE: upper bound of R_pop < Delta/2 and lower bound of G > Delta/2.
  * STAB-LIKE: lower bound of R_pop > Delta/2 and |G| upper bound < Delta/2 (CONT is indistinguishable from its UNIF twin).
  * WORSE-THAN-STAB: lower bound of R_pop > Delta(c) + epsilon (the model loses even to the context-only reference).
  * INCONCLUSIVE: otherwise (including models between the two references whose intervals straddle the midpoint).
* **Program verdict, in the order BLOCKED, STOP, PROCEED, REVISE:**
  * **BLOCKED:** a critical check fails (section 8), or a control fails: C1 upper bound >= epsilon, or C2 upper bound >= epsilon in any arm
    (the models are not good enough to answer, and that is reported as a capability failure, not as a scientific result).
  * **STOP:** the feasibility rule fails (section 6).
  * **PROCEED** (to Q2 at scale or another family, on a new decision): CONT is classified, the same way, in >= 4 of 6 cells in both replicates.
  * **REVISE:** otherwise.
* The **scientific answer** is the per-cell classification, reported with effect sizes and intervals whatever the verdict.
* Operating characteristics are computed before the freeze with synthetic "models" (references with injected regret and seed noise),
  as in the Stage 0.6 dry run: probability of POP-LIKE when the truth is STAB-LIKE and vice versa, and power at s in {0.005, 0.01, 0.02}.

## 8. Validation before the freeze (new tests; nothing frozen is touched)

1. **Reference regression (critical):** pop and stab references on the Stage 0.5 seeds reproduce the stored Stage 0.5 per-item contrasts
   to <= 1e-9 (frozen Tier-1 tolerance).
2. **KL quadrature:** Gaussian-Gaussian closed form (<= 1e-10), node doubling (<= 1e-8), Monte Carlo agreement for mixtures (z-test).
3. **Oracle "models" (positive controls):** the pop reference wrapped as a model gives R_pop = 0 (machine precision) and POP-LIKE; stab
   wrapped gives STAB-LIKE; a library posterior wrapped gives the library class; a variance-inflated pop gives INTERMEDIATE or worse.
4. **Estimator agreement:** realized-target and Rao-Blackwellised R_pop agree within their SEs for the oracle models.
5. **Information access:** the adapter only sees `ContextWindow`; mutation "future target leaked into the input" must be detected
   (regret drops below the Bayes bound, which is impossible, DERIVED: no predictor beats pop on P in expectation).
6. **Data generators:** each arm's sampler draws a from the right law (KS test), LIB-K uses exactly K atoms, CRN coupling holds, sequences
   start at x_0; the numpy/torch sampler agrees in law with `dynaicl.systems.ar1`.
7. **Training determinism:** same seed gives identical weights on CPU (`torch.use_deterministic_algorithms`); unit tests use at most
   20 optimizer steps of a 1-layer model and evaluate nothing against references.
8. **Mutation matrix** for the new code (wrong prior in an arm, wrong reference, unpaired seeds, off-by-one position, leaked target).
9. **No test waits for typed input.** Tests run with non-interactive stdin.

## 9. Files, dependency and compute

* New, unfrozen locations only: package `dynaicl_neural/` (data, model, train, adapter, evaluate, analysis), `tests_stage1/`,
  `config/stage1*.yaml`, `scripts/stage1_*.py`, `docs/PREREG_stage1.md`, `docs/DISCLOSURE_LOG_STAGE1.md`, a new Stage 1 freeze manifest.
  `dynaicl/`, `tests/`, `requirements.txt` and `pyproject.toml` are in the Stage 0.6 v2 manifest and are imported or read only.
* **New dependency: PyTorch** (autograd, optimisers and attention for training; no alternative in the default stack). Pinned in a new
  `requirements-stage1.txt` to the exact version installed on the box for Python 3.13.5 (CPU or CUDA build depending on `nvidia-smi`),
  recorded in a Stage 1 environment manifest. References and scoring stay numpy/scipy float64.
* **Compute (ASSUMED until the throughput job J0 measures it):**

  | Job | Where | Runtime |
  |---|---|---|
  | A1 unit tests + validation | laptop | < 10 min |
  | A2 head floor, KL spreads, operating-characteristics dry run (references only) | laptop | 5-10 min |
  | J0 throughput benchmark: 300 steps per size on random sequences, no evaluation | laptop, then box | 2 min each |
  | Pilot: 18 models (3 arms x 6 seeds, size M) at up to 200k steps + evaluation | box, tmux | about 15 ms/step x 200k = 50 min per model; 16 in parallel on 32 CPUs: about 1-2 h wall |
  | Confirmatory: up to 6 arms x 2 sizes x 16 seeds x 2 replicates = 384 models + evaluation | box, tmux | about 6-12 h wall on CPU (much less on a GPU) |

  Results come back as small files (< 2 MB, no weights or checkpoints) on a results branch, as before.

## 10. Decisions I need from you (recommendation first)

1. **Scope:** Q1 only with arms CONT + UNIF (recommended: smallest design that answers your question; about 1/3 of the compute), or
   Q1 + Q2 (adds LIB-1/2/4/16).
2. **Pilot rule:** keep "no training before the freeze" and use the pre-registered two-phase pilot (recommended), or allow an unfrozen
   UNIF-only engineering pilot before the freeze (UNIF is outside the hypothesis, so it reveals nothing about Q1; it would give real numbers
   for steps and s).
3. **J0 throughput benchmark** (300 steps on random data, nothing evaluated): may it run before the freeze? (Recommended yes; it only
   measures seconds per step.)
4. **Model sizes:** S and M with M primary (recommended), or M only.
5. **PyTorch** as the one new dependency, version pinned from the box.

## 12. Consequences of the literature search (workstream B; details in docs/literature/GAP_AND_NOVELTY.md section 6)

* Behaviour can drift over training (ridge-like first, then specialising; transient ICL). The classification checkpoint is fixed in the
  pre-registration (the final step of the pilot-selected budget); intermediate checkpoints are reported descriptively only.
* The hierarchical bootstrap in section 7 is the "Multi-Bootstrap" structure (models x test items) of the MultiBERTs paper.
* Each model seed randomises initialisation, data order and data, not only initialisation.
* The general (i) vs (ii) question is already answered for linear regression and discrete Markov chains. What this design adds is the
  separate structure-aware context-only reference (UNIF arm / stability reference) and log-score inference powered against a stated effect.

## 11. Pending environment facts

* This laptop session (VERIFIED): branch `main`, clean tree, Python 3.13.5, no `nvidia-smi` here. The box is not reachable from this
  session (it is not in the session list), so its GPU, CPU count and disk are UNVERIFIED until you relay the check below.
* The planning spreads above came from a scratch script (session scratchpad, outside the repo) that reads `item_contrasts.npy` read-only;
  it will be added as `scripts/stage1_planning_spreads.py` if you approve.
* Name collision (VERIFIED by the literature search, workstream B): "DynaICL" is already the name of a method in
  Zhou, Jiang, Cotterell, Sachan, "Efficient Prompting via Dynamic In-Context Learning", arXiv:2305.11170 (2023), unrelated to dynamical
  systems. A paper should use a different name; your decision.
