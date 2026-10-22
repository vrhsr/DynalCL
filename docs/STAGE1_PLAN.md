# Stage 1 program plan, v2 (identifiability first; DRAFT for approval at checkpoint 1)

Status: **PLAN ONLY.** Nothing implemented, nothing trained, no Stage 1 seed used. v1 of this plan is in git history (branch
`stage1-planning`, commit `28990d0`). Every number is a proposal and a hypothesis until the pre-registration freezes it. Labels:
VERIFIED (read or recomputed from a result file), DERIVED (reasoning or algebra stated here), ASSUMED (planning guess, to be measured),
UNVERIFIED. Your checkpoint-A answers are applied: scope Q1 + Q2 with LIB-K arms and the probe set; two-phase pre-registered pilot
plus an allowed UNIF-only engineering smoke test; J0 before the freeze; sizes S, M, L as a pre-registered factor; PyTorch pinned from the box.

## 0. Program at a glance

| Stage | Family | CPU reference work (before any network) | Neural work | Gate to start neural work |
|---|---|---|---|---|
| 1A | Scalar AR(1), known sigma (Stages 0-0.6 references, frozen) | Separability map (section 2) | Q1, Q2 (where identifiable), ablations | Map done + Stage 1A pre-registration frozen |
| 2 | **F1: AR(1), unknown noise scale** (population prior on (a, sigma)) | New references, Stage-0-style validation, separability map, own pre-registration | Q1, Q2, K sweep | Reference validation passes + its own freeze |
| 3 | **F2: VAR(1), d = 2, matrix-normal-inverse-Wishart (MNIW) prior, stability-truncated** | Same | Same | Same |
| (map only) | F3: Stage 0.6 noisy-observation AR(1), short context | Separability map from the frozen Kalman references (no new reference) | Only if the map shows a window beyond 1A | Map + decision |
| (deferred) | F4: nonlinear / chaotic, particle-filter reference | Not started | Not planned | Needs a written justification and your decision (section 3.4) |

The common rule: **compute where the Bayes references differ by at least delta first (references only, CPU); train and classify only
there; report everything else as UNIDENTIFIABLE.**

## 1. What Stage 1A inherits (VERIFIED, recomputed from `runs/...stage05.../results/item_contrasts.npy`)

* Population-specific gap Delta = LS(pop) - LS(stab), E-CONT, h = 1, R1 / R2: r = 1: +0.042 / +0.044 (n = 1), +0.041 / +0.048 (n = 2),
  +0.046 / +0.040 (n = 3); r = 0.25: +0.044 / +0.046, +0.048 / +0.053, +0.053 / +0.046; r = 4: +0.020 to +0.027. Per-item sd 0.24-0.31.
* Library K = 2 vs continuous on held-out systems: r = 1: -0.016 to -0.042 (n = 1..3), -0.048 to -0.087 (n = 5..20); K = 4, 8: within +/-0.017.
* Stage 0.6: with observation noise the long-context gap is < 0.0077 nats in all cells.

## 2. Identifiability first: the separability map (CPU, references only)

### 2.1 Definition
For a family F, an evaluation distribution D, a cell c (context length n, horizon h, initial scale r, and family-specific factors) and
a pair of references (A, B):
* **Truth-matched pairs** (D is the prior of A, so A is Bayes on D): gap_AB(c) = E_D[LS(A) - LS(B)] = E_D[KL(p_A || p_B)] (DERIVED: law of
  total expectation, because y | context ~ p_A exactly). Estimated by per-context quadrature in y (Rao-Blackwellised, no target noise) and
  cross-checked against realized targets.
* **Probe and out-of-distribution sets** (no reference is true): behavioural divergence min(E[KL(A || B)], E[KL(B || A)]).
* **Identifiable** for (A, B) in cell c if the simultaneous 95% lower bound of the gap (studentized max over the map's cells, as in Stage
  0.6) is >= delta = 0.02. **Unidentifiable** if the upper bound is < delta. Otherwise **borderline** (not classified; reported).
* Precision: N per map cell set so the half-width is <= delta/10 (references are cheap; N up to 10^5).
* **No double dipping:** the map uses its own `selection` seeds. Cells are chosen from the map, then models are evaluated on fresh
  evaluation seeds. The selection rule (which cells, which K) is mechanical and frozen before any model is evaluated.

### 2.2 Pairs mapped in every family
Q1: (pop, ctx-only). Q2: (lib_K, cont) and (lib_K, ctx-only), for K in {1, 2, 4, 8, 16, 32, 64, 128, 256, 1024}, on (i) held-out
systems from the population prior, (ii) in-library systems, (iii) the probe set (parameter grid), (iv) out-of-support systems.
Library atoms are random; the map averages over 64 independent library draws per K and reports the spread across draws.

### 2.3 Honest assessment of "separability-first" as a contribution
* It is an identifiability and power analysis done before training. That is standard practice in statistics and experimental design; the
  idea itself is not new.
* In the ICL literature we retrieved, no paper maps whether the competing Bayes references are separable before classifying models (gap
  G3 in docs/literature/GAP_AND_NOVELTY.md). Its value is that it **changes conclusions**. In scalar AR(1) it predicts that a Raventós-style K sweep
  cannot show memorisation for K >= 4 by score, so any such claim there would be uninterpretable.
* Alone it is a methods or workshop-level contribution. It becomes part of a stronger paper only together with a family where the
  references separate widely (section 3) and a clear neural finding.

## 3. Richer families (each a separate stage with its own spec, validation and pre-registration)

### 3.1 Why scalar AR(1) cannot identify Q2 for K >= 4 (DERIVED heuristic; the map will measure it)
On held-out systems, a K-atom library posterior concentrates on the atom nearest the true a. Its excess log loss over the continuous
posterior then **saturates** at about E[(a - a_near)^2 x_n^2] / (2 sigma^2), while the continuous posterior's own excess decays like 1/n.
With one parameter, the squared nearest-atom distance scales like (prior sd / K)^2: for K = 4 that is about 0.01 nats or less, below delta at any
n. This matches Stage 0.5 (K = 4 within 0.017 through n = 20). In a d-dimensional parameter space it scales like K^(-2/d) (DERIVED,
nearest-neighbour scaling), so **more parameters keep libraries distinguishable at larger K**.

### 3.2 Preference order and identifiability of Q2

| Family | Parameters | References (planned) | Q1 window (DERIVED expectation) | Q2 identifiable by log score for K >= 4? |
|---|---|---|---|---|
| **F1 AR(1), unknown sigma** | 2: (a, log sigma) | Population: stability-truncated NIG-type prior; sigma^2 integrates analytically for fixed a, leaving 1-D quadrature in a (extends the Stage 0 P-NIG h = 1 conjugate code). Context-only: U(-0.999, 0.999) x scale-invariant prior on sigma over a wide bounded range. Library: closed-form finite mixture. | Likely longer: log sigma is learned at about 1/2 nat of Fisher information per step, so population knowledge of sigma helps for many more steps than knowledge of a. | **Likely yes up to some K (to be mapped):** a library in (a, log sigma) has 2-D atom spacing, and a misplaced log-scale atom costs about (Delta log sigma)^2 per step, which does not vanish with n. |
| **F2 VAR(1), d = 2, MNIW** | 7: A (4) + Sigma (3) | Population: MNIW truncated to spectral radius < 0.95; predictive = conjugate matrix-t posterior reweighted by the stability indicator (self-normalised importance sampling from the closed-form posterior; Monte Carlo error measured). Context-only: vague MNIW truncated to spectral radius < 0.999. Library: closed form. | Expected longest: 7 parameters identified slowly. | **Yes, most strongly** (7-D atom spacing). |
| F3 noisy-observation AR(1), short context | 1: a (noise known) | Frozen Stage 0.6 Kalman quadrature references (validated) | To be mapped at n = 2..9 | **No (DERIVED):** one parameter, and noise widens the posterior, which makes atoms relatively denser. |
| F4 nonlinear / chaotic | many | Particle filter with validated convergence | Unknown | Unknown; validation cost high |

**Recommendation:** F1 next (cheapest; partly built on validated Stage 0 code), F2 in parallel on CPU as soon as F1's references pass.
F3 needs only a map from existing references. F4 only if F1-F2 leave a question that needs nonlinearity, with a written justification.

### 3.3 Validation each new family needs before any network is trained on it (Stage-0 style)
Closed forms where they exist (the conjugate untruncated parts, library mixtures). Quadrature or importance sampling with measured
convergence (node doubling or Monte Carlo SE, target <= delta/100 per item). Independent 2-D or grid oracles. Calibration (PIT KS, SBC, coverage)
of the matched reference. Optimality checks (no context-only reference beats the matched one in expectation). Mutation matrix (wrong prior,
off-by-one likelihood, leaked target, unmatched reference, wrong truncation). Invariants unchanged: contexts only from `make_context`,
likelihood conditional on x_0, float64, `NamedStreams`. Each family gets `docs/MATH_<family>.md`, a validation report, a separability map, and its own
pre-registration and freeze before neural training.

### 3.4 F4 justification test
F4 is started only if (i) F1 and F2 are done, (ii) a specific question cannot be answered in linear-Gaussian families, and (iii) a
particle-filter reference can be validated to <= delta/100 per item at affordable cost. Otherwise it stays out.

## 4. Stage 1A design (scalar AR(1), known sigma)

### 4.1 Arms (differ only in the law of a; common random numbers by seed index)
CONT (population prior P: truncated normal, mean 0.4, sd 0.3, |a| < 0.95); UNIF (U(-0.999, 0.999): its Bayes predictor is the context-only
reference, so it is the positive control); LIB-K for each K that the map marks identifiable on at least one evaluation set (K = 1 and 2 at least;
larger K only through probe or out-of-support sets). Library atoms drawn per model seed. x_0 ~ N(0, r^2), r uniform on {0.25, 1, 4} (DERIVED:
the Bayes predictor does not depend on the x_0 law, because the likelihood is conditional on x_0 and x_0 is independent of a).

### 4.2 Models and factors
* Causal transformer, Gaussian-mixture output head (component count fixed by the head-floor computation: KL(ref || best m-mixture) <= 0.001 nats).
  Trained by NLL on every position n = 0..19. Density predictor, scored by log score (never point-only).
* **Size factor (pre-registered):** S (2 layers, d = 32, about 30k params), M (4 x 64, about 200k), L (8 x 128, about 1.6M). ASSUMED sizes; justification:
  the h = 1 Bayes predictor depends on three sufficient statistics, and Cole et al. show depth matters for least-squares-like estimation.
* **Training-length factor (pre-registered):** base budget B (set in the pilot from {25k, 50k, 100k, 200k} steps by the capability rule) and 4B.
* **Classification checkpoint (fixed):** the final step of each budget. Checkpoints at B/4 and B/2 are reported descriptively only.

### 4.3 Evaluation sets
(i) held-out systems from P (primary for Q1); (ii) in-library systems (Q2); (iii) probe grid of a in (-0.95, 0.95); (iv) out-of-support
systems (a in [0.95, 0.999) and its negative, outside P's support; the population reference cannot adapt there, the context-only one can: a
strong behavioural discriminator); (v) context lengths n = 21..80, beyond the training length. N = 40 000 systems per replicate for (i)-(ii)
(item SE <= 0.0016, about delta/13); probe and out-of-support sets sized by the map.

### 4.4 Estimands and classification (per replicate; two replicates must agree)
* R_pop = E[LS(pop) - LS(model)] (regret; >= 0 in expectation on P); G = E[LS(CONT_i) - LS(UNIF_i)], paired by seed index;
  behavioural distances D_X = E[KL(X || model)] for each reference X.
* **Q1 classes (CONT models):** POP-LIKE (upper bound of R_pop < Delta/2 and lower bound of G > Delta/2); STAB-LIKE (lower bound of R_pop >
  Delta/2 and |G| upper bound < Delta/2); WORSE-THAN-STAB (lower bound of R_pop > Delta + epsilon); INCONCLUSIVE otherwise.
* **Q2 classes (LIB-K models), only in identifiable cells:** LIB-LIKE, CONT-LIKE, CTX-LIKE by nearest reference in D_X, required to be
  separated by a margin of delta/2 at the simultaneous bounds; INCONCLUSIVE otherwise.
* **Controls (BLOCKED if they fail):** C1 UNIF regret against stab on its own distribution at short context < epsilon = 0.01; C2 every arm's
  regret against its own Bayes reference at n = 20 on its own distribution < epsilon. A capability failure is reported as such, not as a
  scientific finding.

### 4.5 Task-diversity sweep (where identifiable)
K from 1 through continuous: K in {1, 2, 4, 8, 16, 32, 64, 256, 1024, CONT}, restricted per evaluation set to the K the map marks identifiable.
Pre-registered estimand: the class of each K; the transition point K* = the smallest K classified CONT-LIKE (or CTX-LIKE) in both replicates,
with all larger identifiable K also not LIB-LIKE. A fitted mixture weight between library and continuous predictors (the Wurgaft et al. style) is EXPLORATORY.

## 5. Robustness and ablations (each with its purpose; each either pre-registered as a secondary family or EXPLORATORY)

| Ablation | Purpose | Status |
|---|---|---|
| Size S / M / L | Does capacity change the classification? (approximation error vs prior use) | Pre-registered secondary family |
| Depth vs width at matched parameter count (2 x 128 vs 8 x 64, about the same params) | Theory says depth matters for in-context least squares (Cole et al.); separates "too shallow to infer" from "uses the prior" | Pre-registered secondary |
| Training length B vs 4B; descriptive checkpoints B/4, B/2 | ICL can be transient (Singh et al.; Carroll et al.; Panwar et al.); the verdict must not depend on an arbitrary stopping point | Pre-registered secondary (B vs 4B); trajectory descriptive |
| Architecture family: transformer vs GRU vs a diagonal linear state-space model (written in plain PyTorch, no new dependency) | Is the behaviour attention-specific? Recurrent models carry sufficient statistics naturally | Pre-registered secondary (CONT and UNIF only) |
| Out-of-support systems | Discriminates prior use from context use where in-support gaps are small | Pre-registered secondary (Q1 and Q2) |
| Context lengths beyond training | Does the model keep updating like a Bayes posterior or saturate? | EXPLORATORY in 1A (gaps are small at long n in AR(1)) |

## 6. Statistical rigour and program discipline

* **Unit of inference: the trained model.** Each seed randomises initialisation, data order and data (and library atoms). Seeds come from a
  seed-role table (single source of truth, as `config/stage06_seed_manifest.yaml`); torch seeds derive from `NamedStreams` names.
* **Hierarchical resampling:** a Multi-Bootstrap over models (seed pairing across arms kept) and systems (shared across models), studentized
  max statistic over each family.
* **Multiplicity across the whole program:** each stage has exactly one primary family (Q1, and Q2 in identifiable cells) at alpha = 0.05 per
  replicate, plus pre-registered secondary families, each at alpha = 0.05 / (number of secondary families in that stage), Bonferroni. Every
  confirmatory claim also needs both replicates to agree (false claim <= alpha^2 for a fixed claim). Exploratory analyses carry no
  confirmatory alpha and are excluded from headline claims.
* **No selective reporting:** an append-only experiment ledger in `docs/DISCLOSURE_LOG_STAGE1.md` records every training run, evaluation,
  failure and abort, pre-registered or exploratory. The paper reports every pre-registered outcome.
* **Stage 0.6 discipline kept:** freeze manifest, read-only snapshot, authorization gate for confirmatory runs (the user issues it), one
  confirmatory run per decision, no edits to frozen files, the pilot effects file is never opened.

## 7. Power and number of models (GPU budget)

* The decisive unknown is the between-seed sd s of a model's regret (UNVERIFIED; no model exists). SE of an arm mean is about
  sqrt(s^2 / M + se_item^2), se_item <= 0.0016.

  | s | M for SE <= delta/4 = 0.005 | M for SE <= delta/8 = 0.0025 |
  |---|---|---|
  | 0.005 | 2 (floor 8 applies) | 7 |
  | 0.01 | 5 | 28 |
  | 0.02 | 18 | 109 (above cap) |
  | 0.03 | 41 | 244 (above cap) |

  (Computed as ceil(s^2 / (target^2 - 0.0016^2)); script output pasted in the session record.)

* **Two-phase rule (pre-registered):** the pilot (pilot seeds; 8 models per arm for CONT, UNIF, LIB-2; size M) sets (i) the budget B (capability rule
  C2 on training-distribution validation data) and (ii) M = max(8, ceil(s_UCL^2 / (0.005^2 - se_item^2))), with s_UCL the 80% chi-square upper limit
  of the largest cell sd (df = 7, factor 1.35). Pilot means are never used.
* **Cap: M_max = 64 models per arm per replicate** (replaces 16). Justification: at s = 0.03 the target needs 41 models; 64 leaves margin, and
  with small models the GPU cost is modest (section 9). The cap is confirmed once the box's hardware and J0 throughput are known; if J0 shows
  64 is not affordable for every factor, the cap stays 64 for the primary family and secondary factors are reduced, not the primary.
* If the required M exceeds 64 for a family, that family's verdict is **NOT RESOLVABLE at delta with this design** (reported; no confirmatory
  run for it). That replaces the old blanket STOP.

## 8. Operating characteristics (before the freeze; synthetic "models")

Synthetic models are references with controlled distortion: position pi between stab (0) and pop (1) by mixing predictives, an added
approximation error e, and seed-to-seed noise s on the predictive mean and log-variance. For pi in {0, 0.25, 0.5, 0.75, 1}, e in {0, 0.005, 0.01},
s in {0.005, 0.01, 0.02, 0.03, 0.05} and M in {8, 16, 32, 64}: probability of each class over 2000 simulated studies, both replicates, through the
real analysis code. Targets (hypotheses): P(wrong class) <= alpha^2 = 0.0025 at every setting; P(correct) >= 0.8 at s <= 0.02, M = 64, e <= 0.005.
The same for Q2 classes and the controls. Results go into the pre-registration.

## 9. Compute (GPU; ASSUMED until hardware facts and J0)

* Training is many tiny models: run several per GPU (multiple processes or `torch.func` model batching). J0 measures seconds per step for
  S, M and L on the box, single and batched.
* Planning guess (ASSUMED): M-size model, 100k steps, about 5 GPU-min single; about 100-200 models per GPU-hour when batched.
* Stage 1A confirmatory size (upper bound): primary Q1/Q2 arms (CONT, UNIF, about 4 identifiable LIB-K) x M x 64 seeds x 2 replicates = 768
  models; secondary factors (S, L, depth/width, 4B, architectures) on CONT and UNIF at the pilot-selected M: about 2000 more. At 150 models per
  GPU-hour: about 20 GPU-hours. Evaluation: references on CPU (32 cores), about 1 h.
* Local (laptop) jobs only under 10 minutes: unit tests, J0 local, separability-map smoke. Everything else runs on the box in tmux, one wait,
  results as small files on a results branch.

## 10. Files, dependency, environment

* New, unfrozen locations only: `dynaicl_neural/` (data, models, training, adapter, evaluation, analysis), `dynaicl_families/` (F1, F2 references),
  `tests_stage1/`, `config/stage1*.yaml`, `scripts/stage1_*.py`, `docs/PREREG_stage1*.md`, `docs/MATH_F1.md`, `docs/MATH_F2.md`, Stage 1 freeze manifests.
  The whole `dynaicl/` package, `tests/`, `requirements.txt` and `pyproject.toml` are frozen (Stage 0.6 v2 manifest) and are only imported or read.
* PyTorch pinned in `requirements-stage1.txt` to the exact version on the box (CUDA build if a GPU exists), recorded in
  `docs/STAGE1_ENVIRONMENT_MANIFEST.json` (torch, CUDA, cuDNN, driver, GPU model). Deterministic settings: `torch.use_deterministic_algorithms(True)`,
  CUBLAS workspace config; GPU bitwise reproducibility across runs on the same hardware is tested, not assumed. References and scoring stay numpy/scipy float64.

## 11. Order of work and checkpoints

1. **This plan, hardware facts, name options** (checkpoint 1).
2. `docs/PREREG_stage1.md` (1A) with the separability map, operating characteristics, compute plan (checkpoint 2). The map and the operating-characteristics
   simulations are CPU, reference-only, and run before this checkpoint (laptop if under 10 min, else box).
3. Implementation, tests, mutation matrix; J0 benchmark; the UNIF-only engineering smoke test (checkpoint 3).
4. Pilot on pilot seeds only; pilot effects written to an unopened file (checkpoint 4).
5. Freeze: manifest, snapshot, seed-role table, authorization gate (checkpoint 5).
6. Confirmatory runs (checkpoint 6).
7. Analysis, then the paper under `paper/` with a claims-to-evidence table (checkpoint 7).
* **In parallel on CPU (steps 2-4):** F1 (then F2) math, reference implementation, validation, separability map, and its own pre-registration.
  No network is trained on F1 or F2 before its own freeze.

## 12. What a main-track paper would need that this plan does not yet guarantee

See docs/literature/GAP_AND_NOVELTY.md section 7 for venue tiers. In short: (1) a family where Q1 and Q2 are both identifiable by wide margins (F1, F2);
(2) a clear neural finding, powered by seeds, that is not already known from linear regression or discrete Markov chains (for example how the diversity
threshold K* scales with parameter dimension in continuous-state dynamics, or whether models acquire generic stability knowledge before population
knowledge during training); (3) a predictive account: the separability theory of section 3.1 predicting K* and the n-window, tested against the neural
results; (4) breadth (architectures, sizes) and possibly an evaluation of public time-series foundation models against the references with CRPS
(UNVERIFIED feasibility: it needs models whose predictive can be scored). None of these is guaranteed; (2) depends on results we cannot know in advance.

## 13. Hardware check and names (pending your input)

* Hardware: VERIFIED for the laptop only (Python 3.13.5, no `nvidia-smi`). The box is UNVERIFIED until you paste the output of the read-only block given in
  the session message.
* Name options are in the session message; you choose before any paper drafting.
