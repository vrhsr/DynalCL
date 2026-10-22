# Gap analysis and novelty assessment (workstream B, 2026-10-22)

Based only on the 89 sources in [BIBLIOGRAPHY.md](BIBLIOGRAPHY.md), all fetched in this session. Entry numbers [n] refer to it.
**Scope limit:** one day of web search, mostly abstracts plus partial full-text reads (the fetch tool often read only the first 100k characters).
A "not found" below means not found in these sources. It is not proof that no such work exists. Labels: VERIFIED (in a fetched source),
DERIVED (my reasoning from those sources or from our result files), UNVERIFIED.

## 1. What is already known

1. **Memorisation vs generalisation as a function of pretraining task diversity is well established.** Below a diversity threshold, transformers
   track the Bayes predictor of the finite training pool; above it, the Bayes predictor of the continuous task prior (VERIFIED: Raventós et al. [1],
   Lu et al. [3], Panwar et al. [9], Kirsch et al. [12], Goddard et al. [10]). Intermediate regimes, transient phases and training-time drift
   are documented too (VERIFIED: [5], [9], [14], [2]).
2. **The same question has been asked on sequential data**, with explicit memorising and generalising Bayes references, KL in nats and multiple
   seeds, but for **discrete** Markov chains (VERIFIED: Gibson, Cui, Reddy [7], 16 seeds; Park et al. [8]; Edelman et al. [51]).
3. **Networks trained on a synthetic prior can approximate that prior's posterior predictive**, and log likelihood against the exact PPD is the
   established way to measure the gap (VERIFIED: PFNs [19]; also [9], [11], [22]).
4. **In-context learning of AR and linear dynamical systems** has mechanistic and approximation theory (VERIFIED: [36], [37], [38], [39], [43], [47])
   and empirical work comparing models against least squares or an oracle Kalman filter that knows the system, scored with MSE or L2
   (VERIFIED: [40], [45], [46]). Cole et al. [39] uses noisy one-dimensional linear dynamics, essentially our process, but its reference is least squares and
   it is approximation theory.
5. **Simulation-pretrained forecasters** are judged against classical estimators (VERIFIED: the Simulacrum [73], AR(5) vs MLE/OLS/Burg/Yule-Walker,
   MSE, pinball, coverage) or against fitted AR models (Chronos [65]). Synthetic-prior networks such as ForecastPFN [70] are point-only and do not
   measure their gap to their own prior's posterior.
6. **Context-only strategies can explain foundation models on dynamical data** (VERIFIED: context parroting beats leading time-series foundation
   models on 135 chaotic systems [57]).
7. **Point-prediction comparisons are known to be fragile** for telling posteriors apart (VERIFIED: Aswadi, Ma, Wei [16]).

## 2. Gaps (DERIVED from the sources above)

* **G1. Population-prior Bayes vs a strong context-only Bayes estimator.** In the regression papers ([1], [3], [9], [11]) ridge regression is
  simultaneously the continuous-prior Bayes predictor and the context-only estimator, so the two are never separated. Not found in these
  sources: a design that separates "knows the population prior" from "knows only generic structure" (our generic-stability prior).
* **G2. Continuous-state AR with matched Bayes references and proper scoring.** Not found in these sources: a neural study on continuous-state AR or linear-Gaussian
  data that compares the model against the population-prior Bayes predictive and/or a finite-library posterior with log score or CRPS. The
  dynamics papers use oracle or least-squares references and MSE ([39], [40], [45], [46], [73]).
* **G3. Reference-level identifiability.** Not found in these sources: a check, before training, of whether the candidate Bayes references differ enough
  (in nats, per context length and horizon) for a model classification to be possible at all. The memorisation papers report model-vs-reference
  curves but not a pre-registered separability map of the references themselves.
* **G4. Seed variance at the scale of the effect.** Seed-to-seed variance is rarely reported in this literature (VERIFIED as reported in [1] (appendix only), [7], [40]);
  none of the papers found sizes the number of models against a pre-specified minimum effect.

## 3. What our Stage 0.5 / 0.6 results add (VERIFIED from our result files; their relevance is DERIVED)

* **A quantitative separability map for scalar AR(1)** under a stable population prior, with a structure-aware context-only reference (G1, G3):
  * The population-specific advantage over generic-stability Bayes is about 0.043-0.050 nats/forecast, confirmed only at h = 1, n <= 3, r <= 1 (STAGE05_RESULTS.md).
  * Most of what a flat-prior baseline would credit to population knowledge (47-86% at n = 2-10) is generic stability knowledge (STAGE05_RESULTS.md).
  * With observation noise, the long-context gain is below delta = 0.02 in all 18 cells and both replicates; the largest adjusted upper bound is +0.0077 (STAGE06_RESULTS.md).
  * Finite-library and continuous-prior posteriors are practically interchangeable for K >= 4. They differ only for K = 2 on held-out systems.
* **Implication for the memorisation literature (DERIVED, a hypothesis):** in scalar AR(1) the transition studied in [1], [3] and [7] is barely
  identifiable from predictions. A Raventós-style K sweep would find the library and continuous references within delta for K >= 4, so
  "the model generalises" and "the model memorises" would mostly predict the same scores. That is a cautionary methodological point, not a
  positive finding about models.
* **Methodological contribution (DERIVED):** pre-registered, validated reference predictors (closed forms, quadrature with measured convergence,
  calibration, mutation testing), and a two-replicate decision rule, applied before any network exists.

## 4. Is the project question still open?

* **The general question ("does a pretrained model behave like the finite-pool posterior or the continuous-prior posterior?") is NOT novel.**
  It is answered for linear regression [1], [3], [9] and for discrete Markov chains [7], [8], with theory [3] and mechanism [6], [7].
* **The specific combination is open in these sources:** continuous-state AR, a population-prior Bayes reference, a separate structure-aware context-only
  reference, a finite-library reference, and proper scoring with seed-level inference. None of the 89 sources does all of this (G1, G2).
* **But our own results show that this setting leaves little room.** The only window where population Bayes and context-only Bayes differ by
  about 2 delta is h = 1, n <= 3. So a Stage 1 neural study can at best give a narrow answer there, and memorisation for K >= 4 is unidentifiable
  by score. Whether a narrow answer is worth the cost is your decision.

## 5. Plain novelty statement

* **Not novel:** the memorisation-vs-generalisation framing; matching a prior-trained network to its Bayes predictive; ICL of AR and linear
  dynamical systems in general.
* **Possibly novel (not found in these sources; not proven absent):** (a) separating population-prior Bayes from a structure-aware context-only
  Bayes reference, and showing that most of the naive "population advantage" is generic stability knowledge; (b) a pre-registered
  separability map of the references for AR(1), including the negative noisy-observation result; (c) if Stage 1 runs, a seed-powered
  neural classification in the short-context window.
* **Size of the contribution (my judgement, UNVERIFIED by any reviewer):** (a) and (b) are a careful negative or cautionary result in a
  deliberately simple family. They are closer to a methods or workshop note than to a main-track result unless Stage 1 adds a clear neural
  finding or the analysis extends to a family with more room (for example VAR(1) with structured coupling). I make no publishability claim.

## 6. Consequences for the Stage 1 design (DERIVED; folded into docs/STAGE1_PLAN.md v2 sections 4-6)

1. Behaviour can change over training ([5], [9], [14], [2]): fix the classification checkpoint in the pre-registration and report the training trajectory descriptively.
2. Seeds x items inference: use a hierarchical (multi-)bootstrap over models and systems ([86]); about 10 or more runs per arm are a reasonable floor ([84]).
3. Score full predictive distributions (log score, KL), never only means ([16], [19]).
4. Randomise initialisation, data order and data per model ([81], [82]).
5. Include the K = 2 library arm only if Q2 is in scope. K >= 4 is unidentifiable by score in this family (our Stage 0.5 result), so the visible transition reported in the K-sweep literature should not be expected here.
6. Rename before writing the paper: "DynaICL" is taken ([89]).

## 7. What would make this main-track (honest odds; my judgement, UNVERIFIED by any reviewer)

What reviewers at a main-track venue (NeurIPS, ICML, ICLR) would likely expect, based on the closest verified work ([1], [3], [7], [9]): a clear finding
about trained models, a mechanism or predictive account, and breadth. Our current assets are rigour (pre-registration, validated references) and a
negative separability result in one simple family. Rigour alone rarely carries a main-track paper.

| Scenario | Contents | Realistic tier | Main risk |
|---|---|---|---|
| S0 (now) | Scalar AR(1) reference analysis: separability map, Stage 0.5 REVISE, Stage 0.6 STOP | Workshop paper (ICL or time-series workshop at NeurIPS/ICML/ICLR) or a short TMLR methods/negative-result paper | Seen as obvious or too narrow |
| S1 | S0 + Stage 1A neural study (Q1 in the n <= 3 window; Q2 only via probe / out-of-support sets) | TMLR; main track unlikely | Narrow window; the answer may be INCONCLUSIVE or simply "matches Bayes", which [1], [9], [19] would lead one to expect |
| S2 | S1 + F1 (unknown sigma) with Q1 and Q2 identifiable over wider ranges, a K sweep and the size/architecture ablations | TMLR likely; main track possible if the K sweep shows something not seen in regression or Markov chains | Findings may replicate [1], [7] in a new family without new insight |
| S3 | S2 + F2 (VAR(1)) + a separability theory that predicts the transition K* and the context-length window from parameter dimension, confirmed by the neural results; optionally public time-series foundation models scored against the references | Main track is a realistic target; JMLR for a long version | Requires a positive, predictive result we cannot know in advance; more compute and calendar time |

Plainly: **the AR(1)-only study is not main-track material.** A main-track paper needs S3-level content, and even then acceptance is not assured.
What most raises the odds is item (3) of plan section 12: a quantitative prediction (from the references alone, before training) of where trained models
switch from memorising to generalising, then confirmed. That would be new relative to [1], [3] and [7], which report the transition empirically.
I make no publishability claim.
