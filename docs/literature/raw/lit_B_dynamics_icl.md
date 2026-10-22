# Literature hunt B: in-context learning (ICL) of AR processes, Markov chains, linear dynamical systems, Kalman filtering and chaotic dynamics

Compiled 2026-10-22 for DynaICL. Each entry below was retrieved in this session (arXiv abstract or HTML page, NeurIPS/PMLR/ICLR proceedings page, NSF-PAR record, or the paper PDF). Quotes are verbatim fragments returned by the fetch tool. Answers about baselines, metrics and seeds come from targeted reads of the HTML or PDF full text. They are labelled **[full-text read]** when they come from the paper body and **[abstract only]** when only the abstract was checked.

Caveats:
- The fetch tool reads long HTML pages in 100k-character chunks. Usually only the first chunk was read, so "not reported" means **not found in the text read**. It does not mean the paper lacks it.
- Venue information comes from the arXiv Comments field or the proceedings page named in each entry.

Legend for the comparison columns: **Bayes** = compared to a Bayes-optimal predictor for the training prior. **Finite pool** = compared to a finite-library (memorising) posterior, or the training set of systems is varied. **Ctx-only** = compared to a context-only estimator (OLS/least squares/RLS fitted in context, Kalman with estimated parameters, nearest-neighbour/parroting). **Metric**. **Seeds** = seed-to-seed variance reported.

---

## A. Most relevant to DynaICL's three-way question (continuous Bayes vs finite library vs context-only)

### A1. Distinct mechanisms underlying in-context learning in transformers
- Authors: Cole Gibson, Wenping Cui, Gautam Reddy. 2026. arXiv preprint, arXiv:2604.12151 (v1 14 Apr 2026; comment "46 pages, 19 figures").
- URL fetched: https://arxiv.org/abs/2604.12151 ; https://arxiv.org/html/2604.12151
- Verified claim: transformers are "trained on a finite set $S$ of discrete Markov chains", and "Memorization and generalization phases are delineated by two boundaries that depend on data diversity".
- [full-text read]: the K transition matrices "are drawn once from a symmetric Dirichlet ensemble" (C = 10 states). The model is compared against four Bayes predictors: "The two memorizing predictors instead assume knowledge of 𝒮". The generalizing ones assume only the Dirichlet prior. Metric: autoregressive KL in nats. Seeds: "Evaluated over 16 different model seeds", with 95% CIs or SDs on some plots. They note "Identification is more sample efficient than generalization".
- Bayes: YES (both continuous-prior and finite-set Bayes). Finite pool: YES (K varied). Ctx-only: partly (the generalizing in-context-count predictors). Metric: KL / log loss. Seeds: YES.
- Relevance: the closest methodological twin to DynaICL's E-LIB vs E-CONT design, but for discrete Markov chains, not continuous-state AR(1). The "identification is more sample efficient" finding parallels DynaICL's short-context library/population advantage.

### A2. Competition Dynamics Shape Algorithmic Phases of In-Context Learning
- Authors: Core Francisco Park, Ekdeep Singh Lubana, Itamar Pres, Hidenori Tanaka. ICLR 2025 (Spotlight). arXiv:2412.01003.
- URL fetched: https://arxiv.org/abs/2412.01003 ; https://arxiv.org/html/2412.01003v4
- Verified claim: "learning to simulate a finite mixture of Markov chains". Behaviour decomposes into "fuzzy retrieval vs. inference approach with either unigram or bigram statistics".
- [full-text read]: N chains, from 2^2 to 2^11. "both approaches are in fact Bayesian inference protocols with priors": retrieval uses a discrete prior over the training chains, inference uses a Dirichlet prior. "if the data-diversity is large (small), the model is closer to an inference (retrieval) approach". Retrieval is worse OOD "especially with increased context length". Metric: KL.
- Bayes: YES (both priors, framed as algorithms). Finite pool: YES. Ctx-only: in-context bigram (inference). Metric: KL. Seeds: not found in text read.
- Relevance: a direct analogue of library vs continuous strategies, with context length and diversity as the axes. Discrete chains only.

### A3. In-Context Learning Strategies Emerge Rationally
- Authors: Daniel Wurgaft, Ekdeep Singh Lubana, Core Francisco Park, Hidenori Tanaka, Gautam Reddy, Noah D. Goodman. 2025. arXiv preprint (Comments: "Preprint"), arXiv:2506.17859.
- URL fetched: https://arxiv.org/abs/2506.17859 ; https://arxiv.org/html/2506.17859v2
- Verified claim: compares to "a memorizing predictor, which assumes a discrete prior on the set of seen tasks" and reports "a superlinear trend in the timescale for transitioning from generalization to memorization".
- [full-text read]: tasks are Balls & Urns (Markov-like), linear regression and binary classification. Model behaviour is fit as a posterior-weighted mixture of the memorizing and generalizing Bayes predictors (a loss-complexity tradeoff). Metric: symmetrised KL or Euclidean distance.
- Bayes: YES. Finite pool: YES. Ctx-only: no. Metric: KL/distance. Seeds: not found in text read.
- Relevance: a formal framework for "finite-library posterior vs continuous-prior Bayes" behaviour. Not on dynamical systems.

### A4. Pretraining task diversity and the emergence of non-Bayesian in-context learning for regression
- Authors: Allan Raventós, Mansheej Paul, Feng Chen, Surya Ganguli. NeurIPS 2023 (poster). arXiv:2306.15063.
- URL fetched: https://arxiv.org/abs/2306.15063 ; https://arxiv.org/html/2306.15063v2 ; https://neurips.cc/virtual/2023/poster/72459
- Verified claim: "a task diversity threshold for the emergence of ICL". Below it the model behaves "like a Bayesian estimator with the non-diverse pretraining task distribution as the prior". Above it "its behavior aligns with that of ridge regression".
- [full-text read]: pretraining on "the uniform distribution over a finite set of M tasks". The discrete-prior dMMSE estimator vs ridge (Bayes for the Gaussian prior). Threshold about 2^14-2^15 tasks (base model). Metric: MSE / D. Seeds: only in an appendix ("four small PTs, each with a different random seed", SD error bars).
- Bayes: YES (both). Finite pool: YES. Ctx-only: no. Metric: MSE. Seeds: appendix only.
- Relevance: the canonical finite-pool vs continuous-prior result. It is linear regression, not dynamics.

### A5. Asymptotic theory of in-context learning by linear attention
- Authors: Yue M. Lu, Mary I. Letey, Jacob A. Zavatone-Veth, Anindita Maiti, Cengiz Pehlevan. PNAS 122(28) e2502599122 (2025). arXiv:2405.11751. DOI 10.1073/pnas.2502599122.
- URL fetched: https://arxiv.org/abs/2405.11751
- Verified claim: "In the low diversity regime, the model tends toward memorization of training tasks". At high diversity "it achieves genuine in-context learning and generalization beyond the scope of pretrained tasks".
- [abstract only] Bayes: per the abstract, compared to optimal estimators (details not read). Finite pool: YES (task diversity). Metric: MSE (regression). Seeds: not checked.
- Relevance: exactly solvable theory of the memorisation-to-generalisation transition. IID regression, not AR.

### A6. Panda: A pretrained forecast model for chaotic dynamics
- Authors: Jeffrey Lai, Anthony Bao, William Gilpin. ICLR 2026 (mlanthology). arXiv:2505.13755.
- URL fetched: https://arxiv.org/abs/2505.13755 ; https://arxiv.org/html/2505.13755 ; https://mlanthology.org/iclr/2026/lai2026iclr-panda/
- Verified claim: "Trained purely on simulated data, Panda exhibits emergent properties", including "zero-shot forecasting of unseen chaotic systems".
- [full-text read]: about 2×10^4 ODEs evolved from "129 previously-published low-dimensional chaotic systems". Reports "clear scaling of zero-shot performance on unseen systems" as the number of unique systems grows, at constant total timepoints (from about 2×10^4 down to 156 systems). Baselines: Chronos, Time-MoE, TimesFM, DynaMix. Metrics: sMAPE, MAE, KL, spectral Hellinger. Seeds: mean ± std over test systems and windows, not over seeds.
- Bayes: no. Finite pool: YES (number of training systems varied). Ctx-only: no explicit one. Metric: sMAPE/MAE. Seeds: no.
- Relevance: the only dynamics paper found that varies the size of the training-system library, using point-forecast metrics with no Bayes reference.

---

## B. AR processes and linear dynamical systems (theory of in-context AR learning)

### B1. How do Transformers perform In-Context Autoregressive Learning?
- Authors: Michael E. Sander, Raja Giryes, Taiji Suzuki, Mathieu Blondel, Gabriel Peyré. ICML 2024 (arXiv comment "20 pages ICML 2024"). arXiv:2402.05787.
- URL fetched: https://arxiv.org/abs/2402.05787 ; https://arxiv.org/html/2402.05787v2
- Verified claim: "a trained one-layer linear Transformer implements one step of gradient descent". It "predicts the next token by first learning" the context matrix W in context.
- [full-text read]: "a noiseless setting", with W orthogonal or unitary. Baseline is gradient descent on the inner objective. No Bayes or OLS comparison. Metric: MSE. Seeds: none reported.
- Bayes: no. Finite pool: no. Ctx-only: GD on the in-context objective. Metric: MSE. Seeds: no.
- Relevance: the mechanism for in-context AR(1) with noiseless orthogonal W. DynaICL's noisy scalar AR(1) with a population prior is outside its scope.

### B2. On Mesa-Optimization in Autoregressively Trained Transformers: Emergence and Capability
- Authors: Chenyu Zheng, Wei Huang, Rongzhen Wang, Guoqiang Wu, Jun Zhu, Chongxuan Li. NeurIPS 2024 (arXiv comment "Accepted by NeurIPS2024"). arXiv:2405.16845.
- URL fetched: https://arxiv.org/abs/2405.16845 ; https://arxiv.org/html/2405.16845v2
- Verified claim: the trained model implements "one step of gradient descent to minimize an ordinary least squares (OLS) problem", and under a stronger moment condition "the learned mesa-optimizer recovers the distribution".
- [full-text read, first chunk]: noiseless AR, x_{t+1} = W x_t, with the initial point from "a controllable distribution". Reference is in-context OLS. Metric: squared error ("ratio or MSE loss"). No Bayes comparison. Seeds: none in main text (Appendix B.1 "GPU and random seed" not read).
- Bayes: no. Finite pool: no. Ctx-only: OLS (as the target algorithm). Metric: MSE. Seeds: not found.
- Relevance: shows that the initial-state distribution matters for what is learned. This echoes DynaICL invariant 1 (likelihood conditional on x_0).

### B3. Uncovering mesa-optimization algorithms in Transformers
- Authors: Johannes von Oswald, Maximilian Schlegel, Alexander Meulemans, et al. (13 authors). 2023, revised 2024. arXiv preprint, arXiv:2309.05858. No venue on the arXiv page. A search result listed an ICLR 2024 workshop, but that was not fetched.
- URL fetched: https://arxiv.org/abs/2309.05858
- Verified claim: "standard next-token prediction error minimization gives rise to a subsidiary learning algorithm". "Our findings explain in-context learning as a product of autoregressive loss minimization".
- [abstract only] Bayes / finite pool / metric / seeds: not checked in full text.
- Relevance: the origin of the "in-context least-squares on linear dynamics" view of autoregressive transformers.

### B4. In-Context Learning of Linear Dynamical Systems with Transformers: Approximation Bounds and Depth-Separation
- Authors: Frank Cole, Yuxuan Zhao, Yulong Lu, Tianhao Zhang. NeurIPS 2025 (arXiv comment: "NeurIPS 2025 camera ready version"). arXiv:2502.08136.
- URL fetched: https://arxiv.org/abs/2502.08136 ; https://arxiv.org/html/2502.08136v3 ; NeurIPS 2025 PDF (read pages 1-4)
- Verified claim (abstract, PDF): "transformers with logarithmic depth can achieve error bounds comparable with those of the least-squares estimator". For single-layer linear transformers there is "a non-diminishing lower bound on the approximation error".
- [full-text read]: model x_t = W x_{t-1} + ξ_t, ξ Gaussian, x_0 = 0, with W eigenvalues in (w_min, w_max) ⊂ (0,1). Experiments use "noisy one-dimensional linear dynamical systems" (d = 1, T = 500, w in [0, 0.8]). There is no LS, Bayes or Kalman baseline in the experiments. Metric: L2 test error. No error bars.
- Bayes: no. Finite pool: no. Ctx-only: LS (theory only). Metric: L2/MSE. Seeds: no.
- Relevance: the scalar noisy AR(1) setting (d = 1) is almost exactly DynaICL's. The reference is least squares, not population Bayes, and it is approximation theory only.

### B5. Why Do Transformers Fail to Forecast Time Series In-Context?
- Authors: Yufa Zhou, Yixiao Wang, Surbhi Goel, Anru R. Zhang. 2025. arXiv preprint, arXiv:2510.09776.
- URL fetched: https://arxiv.org/abs/2510.09776 ; https://arxiv.org/html/2510.09776v1 (both chunks)
- Verified claim: linear self-attention "cannot achieve lower expected MSE than classical linear models for in-context forecasting". "as the context length approaches to infinity, LSA asymptotically recovers the optimal linear predictor". Under CoT rollout "predictions collapse to the mean exponentially".
- [full-text read]: Gaussian AR(p), stable. The Bayes one-step risk uses the true coefficients (w = ρ). The gap "diminishes at a rate no faster than 1/n". In experiments, the OLS baseline is fit "on the same training series used for LSA" (not in context per test sequence). How coefficients are sampled is unspecified. Metric: MSE. Seeds: "averaged over 7 seeds with error bars indicating the standard error of the mean" (context and layer scaling only).
- Bayes: YES, against the known-parameter (oracle) Bayes risk, not a population-prior Bayes. Finite pool: no. Ctx-only: OLS. Metric: MSE. Seeds: YES (partial).
- Relevance: a gap to the optimum that shrinks with context length. This is qualitatively parallel to DynaICL's vanishing long-context gap, but the comparator differs (oracle known-a vs population Bayes).

### B6. Optimal In-Context Learning of Autoregressive Processes under Heterogeneous Second-Order Moments of the Prompts
- Authors: Hanna Tseran, Masaaki Imaizumi. NeurIPS 2026 (poster page). No arXiv listing found. The OpenReview page (id OEIZ6QQAsu) was blocked by a verification screen.
- URL fetched: https://neurips.cc/virtual/2026/poster/153067
- Verified claim: "We prove that there exists a parametrization under which the model converges", per the search summary of the same abstract to a function approximating "the optimal second-order moment-based AR(1) estimator". The abstract also offers "further insight into ICL's robustness to new tasks".
- [abstract only] Bayes: not stated (the target is a moment-based AR(1) estimator, i.e. context-only). Metric / seeds: unknown.
- Relevance: the only paper found that targets scalar AR(1) estimators in-context explicitly. Only the poster abstract was verified.

### B7. Transformers as Algorithms: Generalization and Stability in In-context Learning
- Authors: Yingcong Li, M. Emrullah Ildiz, Dimitris Papailiopoulos, Samet Oymak. ICML 2023, PMLR 202:19565-19594. arXiv:2301.07067.
- URL fetched: https://arxiv.org/abs/2301.07067 ; https://proceedings.mlr.press/v202/li23l.html
- Verified claim: generalization bounds where the prompt is "a trajectory arising from a dynamical system". The paper aims to "formalize in-context learning as an algorithm learning problem".
- [abstract only] Bayes / finite pool / metric / seeds: not checked.
- Relevance: an early statistical treatment of ICL on dependent (dynamical-system) prompts.

### B8. State space models, emergence, and ergodicity: How many parameters are needed for stable predictions?
- Authors: Ingvar Ziemann, Nikolai Matni, George J. Pappas. L4DC 2025, PMLR 283. arXiv:2409.13421.
- URL fetched: https://arxiv.org/abs/2409.13421 ; https://proceedings.mlr.press/v283/ziemann25a.html
- Verified claim: "for every non-ergodic linear system there exists a critical threshold", and "a learner using fewer parameters than said threshold cannot achieve bounded error for large sequence lengths".
- [abstract only] Relevance: theory for ICL-like prediction in non-ergodic linear systems (DynaICL's per-trajectory a acts as a non-ergodic latent).

### B9. Transformers learn to implement preconditioned gradient descent for in-context learning
- Authors: Kwangjun Ahn, Xiang Cheng, Hadi Daneshmand, Suvrit Sra. NeurIPS 2023. arXiv:2306.00297.
- URL fetched: https://arxiv.org/abs/2306.00297
- Verified claim: a single attention layer's global minimum "implements a single iteration of preconditioned gradient descent". With L layers, critical points "implement $L$ iterations of preconditioned gradient descent".
- [abstract only] Setting: linear regression (IID), not dynamics. Relevance: background mechanism only.

---

## C. Kalman filtering / state estimation in context

### C1. Can a Transformer Represent a Kalman Filter?
- Authors: Gautam Goel, Peter Bartlett. L4DC 2024, PMLR 242:1502-1512. arXiv:2312.06937.
- URL fetched: https://arxiv.org/abs/2312.06937 ; https://proceedings.mlr.press/v242/goel24a.html
- Verified claim: "show that Transformers can approximate the Kalman Filter in a strong sense", "up to a small additive error which is bounded uniformly in time".
- [abstract only] It is a representation result for a known LTI system. It involves no learning across systems or unknown parameters. Bayes: Kalman (known parameters) by construction. No experiments on finite pools or seeds were checked.
- Relevance: representability only. The DynaICL noisy variant needs filtering under parameter uncertainty, which this paper does not cover.

### C2. Can Transformers Learn Optimal Filtering for Unknown Systems?
- Authors: Haldun Balim, Zhe Du, Samet Oymak, Necmiye Ozay (arXiv order; IEEE lists Zhe Du first). IEEE Control Systems Letters 7:3525-3530 (2023), DOI 10.1109/LCSYS.2023.3335318. arXiv:2308.08536.
- URL fetched: https://arxiv.org/abs/2308.08536 ; https://arxiv.org/html/2308.08536v3 ; https://par.nsf.gov/biblio/10492361
- Verified claim: the trained transformer "matches the optimal performance given by the Kalman filter for linear systems", and "adapts exceedingly well to different unseen systems".
- [full-text read]: n = 10, m = 5 random systems (spectral radius 0.95), M = 20000 source systems, T = 50. The KF is "designed with the exact system knowledge" (oracle). A second baseline is online AR via "recursive least squares (RLS)". Metric: ℓ2 prediction error. No seed variance. Degradation for slow-mixing systems and under noise-distribution shift. The number of training systems is not varied empirically (theory rate O(1/√(MT))).
- Bayes: oracle KF only (not population-Bayes). Finite pool: no. Ctx-only: RLS. Metric: L2/MSE. Seeds: no.
- Relevance: the closest prior work to DynaICL's Kalman variant. Its comparator is the known-parameter KF, so "matching KF" cannot distinguish population-Bayes from context-only behaviour.

### C3. Transformers as Implicit State Estimators: In-Context Learning in Dynamical Systems (v1 title: "Can Transformers In-Context Learn Behavior of a Linear Dynamical System?")
- Authors: Usman Akram, Haris Vikalo. 2024-2026. arXiv preprint, arXiv:2410.16546 (v3 7 Mar 2026).
- URL fetched: https://arxiv.org/abs/2410.16546 ; https://arxiv.org/abs/2410.16546v1 ; https://arxiv.org/html/2410.16546
- Verified claim: "In linear-Gaussian regimes, its predictions closely match those of the Kalman filter", and "prediction accuracy degrades gracefully when key parameters, such as the state-transition matrix, are withheld". In nonlinear regimes "its performance approaches that of EKF and PF".
- [full-text read]: n = 8. F, Q and σ² are given in context by default, and some experiments withhold them. "Both Q and R are re-sampled independently for each training example." Baselines: KF with true parameters, plus OLS, ridge and SGD. Metric: MSE and MSPD (prediction difference). Seeds: none found.
- Bayes: oracle KF. Finite pool: no (fresh sampling). Ctx-only: OLS/ridge/SGD. Metric: MSE. Seeds: no.
- Note: a search-engine summary claimed that "smaller models or shorter contexts emulate linear regression…". It is NOT in the v1 or v3 abstracts as fetched, so it is not reported here.

---

## D. Markov chains (discrete) in context

### D1. The Evolution of Statistical Induction Heads: In-Context Learning Markov Chains
- Authors: Ezra Edelman, Nikolaos Tsilivis, Benjamin L. Edelman, Eran Malach, Surbhi Goel. NeurIPS 2024 (mlanthology; DOI 10.52202/079017-2050). arXiv:2402.11004.
- URL fetched: https://arxiv.org/abs/2402.11004 ; https://arxiv.org/html/2402.11004v1 ; https://mlanthology.org/neurips/2024/edelman2024neurips-evolution/
- Verified claim: "Transformers trained on this task form statistical induction heads". "then, there is a rapid phase transition to the correct in-context bigram solution". Chains are "drawn from a prior distribution over Markov chains".
- [full-text read, first chunk]: Dirichlet rows. A fresh chain is sampled per sequence. "all the models converge near the Bayesian optimal solution", with the posterior mean (c_ij+1)/(N_i+k). Metric: CE training, KL test. Seeds: not found in text read.
- Bayes: YES (Dirichlet posterior mean). Finite pool: no. Ctx-only: unigram/bigram counts. Metric: KL. Seeds: not found.
- Relevance: the discrete analogue of DynaICL's continuous-prior Bayes reference.

### D2. How Transformers Learn Causal Structure with Gradient Descent
- Authors: Eshaan Nichani, Alex Damian, Jason D. Lee. ICML 2024 (arXiv comment "v2: ICML 2024 camera ready"). arXiv:2402.14735.
- URL fetched: https://arxiv.org/abs/2402.14735
- Verified claim: gradient descent ends up "encoding the latent causal graph in the first attention layer", and for in-context Markov chains "we prove that transformers learn an induction head".
- [abstract only] Relevance: mechanism (induction head = in-context counting estimator, i.e. context-only).

### D3. Transformers on Markov data: Constant depth suffices
- Authors: Nived Rajaraman, Marco Bondaschi, Kannan Ramchandran, Michael Gastpar, Ashok Vardhan Makkuva. NeurIPS 2024 (Main Conference Track). arXiv id not confirmed.
- URL fetched: https://proceedings.neurips.cc/paper_files/paper/2024/hash/f8a2070082ad05b4deeff4ffb4312a6f-Abstract-Conference.html
- Verified claim: a constant-depth transformer "is able to achieve low test loss" on k-th order Markov sources, and "a transformer with a constant number of layers can represent" the in-context conditional empirical distribution.
- [abstract only] Relevance: in-context k-gram estimator (context-only).

### D4. An Information-Theoretic Approach to Understanding Transformers' In-Context Learning of Variable-Order Markov Chains (earlier title: "Transformers Learn Variable-order Markov Chains in-Context")
- Authors: Ruida Zhou, Chao Tian, Suhas Diggavi. AISTATS 2026 (arXiv comment). arXiv:2410.05493.
- URL fetched: https://arxiv.org/abs/2410.05493
- Verified claim: "a Bayesian formulation, where the context-tree weighting (CTW) algorithm" "provides an optimal solution". CTW is used as the Bayes-optimal baseline.
- [abstract only; full-text claims from search not verified] Bayes: YES (CTW). Metric: compression / log-loss. Seeds: not checked.
- Relevance: an explicit Bayes-optimal reference for discrete sequence ICL, using a log-loss metric.

### D5. Attention with Markov: A Framework for Principled Analysis of Transformers via Markov Chains (ICLR 2025 title: "Attention with Markov: A Curious Case of Single-Layer Transformers")
- Authors: Ashok Vardhan Makkuva, Marco Bondaschi, Adway Girish, et al. (7 authors). ICLR 2025. arXiv:2402.04161.
- URL fetched: https://arxiv.org/abs/2402.04161
- Verified claim: "show the existence of global minima (bigram) and bad local minima (unigram)" for single-layer transformers.
- [abstract only] Relevance: low. It is mainly a loss-landscape study.

---

## E. Chaotic / physical dynamics, foundation models and LLMs

### E1. Zero-shot forecasting of chaotic systems
- Authors: Yuanzhao Zhang, William Gilpin. ICLR 2025. arXiv:2409.15771.
- URL fetched: https://arxiv.org/abs/2409.15771 ; https://arxiv.org/html/2409.15771v3
- Verified claim: "foundation models produce competitive forecasts compared to custom-trained models", and the paper identifies "context parroting as a simple mechanism".
- [full-text read]: Chronos at 8M-710M parameters vs NBEATS, TiDE, NVAR, Transformer and LSTM. Metrics: sMAPE and valid prediction time, plus attractor KL and correlation dimension. "The VPT of Chronos increases monotonically with context length." Variation is over initial conditions, not seeds.
- Bayes: no. Finite pool: no. Ctx-only: shuffled-context and last-k controls. Metric: sMAPE/VPT. Seeds: no (initial-condition spread only).

### E2. Context parroting: A simple but tough-to-beat baseline for foundation models in scientific machine learning
- Authors: Yuanzhao Zhang, William Gilpin. ICLR 2026 (arXiv comment). arXiv:2505.11349.
- URL fetched: https://arxiv.org/abs/2505.11349 ; https://arxiv.org/html/2505.11349v2
- Verified claim: "foundation models often forecast through a simple parroting strategy". The parroting baseline "scores higher than leading time-series foundation models".
- [full-text read]: parroting "scans the context for nearly repeating motifs and copies…" (1-NN). Compared against Chronos, Chronos-Bolt, TimesFM-2.0 and Time-MoE on 135 dysts systems. Metrics: sMAPE, VPT, MSE, MAE, KL. Context scaling exponent α ≈ 1/d_cor (Spearman 0.51 ± 0.08). No seed variance.
- Bayes: no. Finite pool: no. Ctx-only: YES (nonparametric context-only parroting beats pretrained models). Metric: point metrics. Seeds: no.
- Relevance: strong evidence that a context-only estimator can explain pretrained-model behaviour on dynamics. This mirrors DynaICL hypothesis (c).

### E3. Transformers for dynamical systems learn transfer operators in-context
- Authors: Anthony Bao, Jeffrey Lai, William Gilpin. 2026. arXiv preprint, arXiv:2602.18679 (comment "5 pages, 4 figures").
- URL fetched: https://arxiv.org/abs/2602.18679 ; https://arxiv.org/html/2602.18679
- Verified claim: "attention-based models apply a transfer-operator forecasting strategy in-context". They also find "an early tradeoff in training between in-distribution and out-of-distribution performance".
- [full-text read]: each model is trained on one system. Appendix G derives "the Bayes-optimal in-context predictor is the Dirichlet-multinomial posterior mean", but there is no empirical comparison to it. Metric: cross-entropy. "standard errors across 100 replicate experiments" (replicates are system pairs).
- Bayes: derived but not tested. Finite pool: no (single system). Metric: CE. Seeds: replicates (system pairs).

### E4. LLMs learn governing principles of dynamical systems, revealing an in-context neural scaling law
- Authors: Toni J.B. Liu, Nicolas Boullé, Raphaël Sarfati, Christopher J. Earls. EMNLP 2024 (DOI 10.18653/v1/2024.emnlp-main.842). arXiv:2402.00795.
- URL fetched: https://arxiv.org/abs/2402.00795 ; https://arxiv.org/html/2402.00795v4
- Verified claim: "the accuracy of the learned physical rules increases with the length of the input context window", "revealing an in-context version of neural scaling law".
- [full-text read]: systems are Markov chains, the noisy logistic map, Brownian motion, GBM and Lorenz. The LLM's extracted transition density is compared to ground truth. Baselines: "unigram and bi-gram models … linear and non-linear autoregressive models". Metrics: Bhattacharyya distance (stochastic) and SDM. Runs were "repeated ten times with trajectories initiated by different random seeds", but no CIs were reported.
- Bayes: no (compares to ground-truth transition = oracle). Finite pool: no. Ctx-only: AR / n-gram baselines. Metric: distributional (Bhattacharyya). Seeds: 10 repeats, no variance reported.
- Relevance: one of the few distributional (not MSE) evaluations of in-context dynamics learning.

### E5. Chaos as an interpretable benchmark for forecasting and data-driven modelling (dysts)
- Author: William Gilpin. NeurIPS 2021 Datasets and Benchmarks track. arXiv:2110.05266.
- URL fetched: https://arxiv.org/abs/2110.05266 ; NeurIPS D&B proceedings page
- Verified claim: "a growing database currently comprising 131 known chaotic dynamical systems", and "we correlate forecasting performance with the degree of chaos present".
- Relevance: the benchmark used by E1, E2 and A6. Background only.

### E6. True Zero-Shot Inference of Dynamical Systems Preserving Long-Term Statistics (DynaMix)
- Authors: Christoph Jürgen Hemmer, Daniel Durstewitz. NeurIPS 2025 (Main Conference Track). arXiv:2505.13192.
- URL fetched: https://arxiv.org/abs/2505.13192 ; NeurIPS 2025 proceedings page
- Verified claim: "the first DSR model able to generalize zero-shot to out-of-domain DS", and "DynaMix outperforms TS foundation models in terms of long-term statistics".
- [abstract only] Relevance: in-context dynamical-systems reconstruction. No Bayes reference was checked.

### E7. In-Context Learning of Stochastic Differential Equations with Foundation Inference Models
- Authors: Patrick Seifner, Kostadin Cvejoski, David Berghaus, Cesar Ojeda, Ramses J. Sanchez. NeurIPS 2025. arXiv:2502.19049.
- URL fetched: https://arxiv.org/abs/2502.19049
- Verified claim: "FIM-SDE achieves robust in-context function estimation across a wide range of synthetic and real-world processes".
- [abstract only] Relevance: amortised in-context estimation of SDE drift and diffusion, i.e. ICL of stochastic dynamics. No Bayes comparison was checked.

### E8. Large Language Models Are Zero-Shot Time Series Forecasters
- Authors: Nate Gruver, Marc Finzi, Shikai Qiu, Andrew Gordon Wilson. NeurIPS 2023. arXiv:2310.07820.
- URL fetched: https://arxiv.org/abs/2310.07820
- Verified claim: "LLMs such as GPT-3 and LLaMA-2 can surprisingly zero-shot extrapolate time series". The abstract notes GPT-4's "poor uncertainty calibration".
- [abstract only] Relevance: the LLM in-context forecasting baseline. No Bayes comparison was checked.

---

## F. In-context system identification (control community)

### F1. From system models to class models: An in-context learning paradigm (v1 title: "In-context learning for model-free system identification")
- Authors: Marco Forgione, Filippo Pura, Dario Piga. IEEE Control Systems Letters 7:3513-3518 (2023) per search. The arXiv page lists the related DOI 10.1109/LCSYS.2023.3335036. arXiv:2308.13380.
- URL fetched: https://arxiv.org/abs/2308.13380 ; https://arxiv.org/html/2308.13380v2
- Verified claim: "we learn a meta model that represents a class of dynamical systems", and "the meta model implicitly discerns its dynamics".
- [full-text read]: LTI and Wiener-Hammerstein classes. "infinite stream of dynamical systems", resampled "at each iteration". Baselines: per-system subspace identification and NLSQ fitted on 400 samples (context-only system ID). Metric: RMSE. Seeds: not reported.
- Bayes: no. Finite pool: no. Ctx-only: YES (system ID per system). Metric: RMSE. Seeds: no.

### F2. On the adaptation of in-context learners for system identification
- Authors: Dario Piga, Filippo Pura, Marco Forgione. 2023. arXiv preprint, arXiv:2312.04083.
- URL fetched: https://arxiv.org/abs/2312.04083
- Verified claim: "This paper discusses the role of meta-model adaptation", and "meta-model adaptation can enhance predictive performance in three realistic scenarios".
- [abstract only]

### F3. In-Context Operator Learning with Data Prompts for Differential Equation Problems (ICON)
- Authors: Liu Yang, Siting Liu, Tingwei Meng, Stanley J. Osher. PNAS (DOI 10.1073/pnas.2310142120, listed on the arXiv page). arXiv:2304.07993.
- URL fetched: https://arxiv.org/abs/2304.07993
- Verified claim: the aim is to "learn operators from the prompted data and apply it to new questions", by "training a single neural network as an operator learner".
- [abstract only] Relevance: ICL for ODEs and PDEs (deterministic operators). Background only.

---

## G. Tangential (verified, low relevance)

- **What does a Bayes-filtered transformer believe? A predictive Monte Carlo approach.** Afiq Abdillah Effiezal Aswadi, Haotong Ma, Susan Wei. 2026, arXiv:2607.17060. https://arxiv.org/abs/2607.17060. "PMC returns an approximation to the implicit prior and posterior over the latent task". The tasks are 0-Markov and 1-Markov exchangeable settings, not dynamical systems. It could serve as a method to read out a trained model's *implicit prior* (a possible Stage-1 diagnostic for library vs continuous prior).

---

## Summary table

| # | Paper | Bayes-opt ref | Finite pool / library | Context-only ref | Metric | Seed variance |
|---|---|---|---|---|---|---|
| A1 | Gibson+ 2026 (Markov, finite S) | YES (cont. + finite) | YES | partly | KL (nats) | YES (16 seeds) |
| A2 | Park+ ICLR25 | YES (framed) | YES | in-ctx bigram | KL | not found |
| A3 | Wurgaft+ 2025 | YES | YES | no | KL/dist | not found |
| A4 | Raventós+ NeurIPS23 (regression) | YES (dMMSE + ridge) | YES | no | MSE | appendix (4 seeds) |
| A5 | Lu+ PNAS25 (regression) | per abstract | YES | - | MSE | not checked |
| A6 | Panda ICLR26 (chaos) | no | YES (#systems scaling) | no | sMAPE/MAE | no |
| B1 | Sander+ ICML24 (AR, noiseless) | no | no | GD | MSE | no |
| B2 | Zheng+ NeurIPS24 (AR, noiseless) | no | no | OLS (target) | MSE | not found |
| B4 | Cole+ NeurIPS25 (noisy 1-D LDS) | no | no | LS (theory) | L2 | no |
| B5 | Zhou+ 2025 (AR(p)) | oracle known-coef | no | OLS | MSE | YES (7 seeds, SEM) |
| B6 | Tseran & Imaizumi NeurIPS26 (AR(1)) | ? | ? | moment estimator | ? | ? |
| C2 | Balim/Du+ LCSYS23 (KF) | oracle KF | no (M=20000, not varied) | RLS | L2 | no |
| C3 | Akram & Vikalo (KF) | oracle KF | no (fresh) | OLS/ridge/SGD | MSE/MSPD | no |
| D1 | Edelman+ NeurIPS24 (Markov) | YES (Dirichlet) | no | n-gram | KL | not found |
| D4 | Zhou, Tian, Diggavi AISTATS26 | YES (CTW) | ? | PPM | log-loss | not checked |
| E1 | Zhang & Gilpin ICLR25 | no | no | controls | sMAPE/VPT | ICs only |
| E2 | Zhang & Gilpin ICLR26 | no | no | YES (parroting) | point | no |
| E3 | Bao, Lai, Gilpin 2026 | derived only | no | Ulam / k-Markov | CE | 100 replicates |
| E4 | Liu+ EMNLP24 | oracle density | no | AR, n-gram | Bhattacharyya | 10 seeds, no CI |
| F1 | Forgione+ LCSYS23 | no | no (infinite stream) | YES (subspace ID / NLSQ) | RMSE | no |

## Gap statement (DERIVED from the table above; limited to papers retrieved here)
No retrieved paper on **continuous-state** AR or linear-Gaussian or Kalman ICL compares a trained model against a **population-prior (matched) Bayes posterior predictive**. Comparators are oracle known-parameter predictors (KF with true matrices, AR with true coefficients) or least squares/OLS. None uses a **finite-library posterior** reference, and none scores with **log score / CRPS**: all use MSE, L2, sMAPE or RMSE. Finite-pool vs continuous-prior Bayes comparisons with log-loss and multi-seed variance exist only for **discrete Markov chains** (A1, A2, D1) and **linear regression** (A4, A5). Seed-to-seed variance is rarely reported (A1, B5, partly E3/E4/A4).

---

## NOT VERIFIED (excluded)

| Item | Reason |
|---|---|
| Wu et al. 2025, "transformers approximate least squares for (possibly more complex) dynamical systems" (cited in Cole+ 2025) | Not identified or retrieved. |
| Guo et al. 2023 (cited in Cole+ as approximating LS for dynamical systems) | Not retrieved. |
| Huang et al. 2024, non-IID next-token convergence (cited in Cole+) | Not retrieved. |
| von Oswald et al., "Transformers learn in-context by gradient descent" (ICML 2023, arXiv:2212.07677) | Only seen in search results. Page not fetched (and it is IID regression, off-topic). |
| Berkeley EECS tech reports "Transformers on Dynamical Systems - An Exploration of In-context Learning" (EECS-2023-287, EECS-2024-40) | Search snippet only. Pages not fetched. |
| Zekri et al., "Large Language Models as Markov Chains" (arXiv:2410.02724) | Search snippet only. Not fetched. |
| Kiruluta, "Filtering Beats Fine-Tuning: A Bayesian Kalman View of In-Context Learning in LLMs" (arXiv:2601.06100) | Search snippet only. Not fetched. |
| "Kalman Linear Attention" (arXiv:2602.10743) | Search snippet only. Architecture paper, not fetched. |
| "Continuum Transformers Perform In-Context Learning by Operator Gradient Descent" (arXiv:2505.17838) | Search snippet only. Not fetched. |
| "Transformers Can Learn Posterior Predictive Distributions In-Context" (arXiv:2605.26713); "Can Transformers Learn Full Bayesian Inference In Context?" (arXiv:2501.16825); "In-Context Learning Is Provably Bayesian Inference" (arXiv:2510.10981); "How many pretraining tasks are needed for in-context learning of linear regression?" (arXiv:2310.08391) | Search results only. Not fetched (general ICL-Bayes, not dynamics; likely covered by another hunt). |
| Foundation Inference Models for Markov Jump Processes; FIM-ODE (Mauel et al.) | Mentioned in a search summary only. Not fetched. |
| AutoTimes (arXiv:2402.02370); arXiv:2512.07705 (LLM few-shot forecasting) | Search results only. Not fetched. |
| Akram & Vikalo claim "smaller models or shorter contexts emulate linear regression or SGD … larger models with longer contexts converge toward optimal filtering" | From a search-engine summary. NOT found in the v1 or v3 abstracts fetched. Excluded as a claim (the paper itself is verified, C3). |
| Rajaraman et al. arXiv id | Not found. The paper is verified via NeurIPS proceedings only. |
| Tseran & Imaizumi arXiv version / full abstract | No arXiv listing found, and OpenReview was blocked. Only the NeurIPS 2026 poster abstract was verified. |
