# Annotated bibliography (workstream B, 2026-10-22)

**How this was verified.** Every entry was retrieved in this session by web fetch (arXiv abstract or HTML page, proceedings page, journal
landing page, or the Crossref record where the publisher returned 403). Three search agents did most of the fetching; their full reports,
with the exact URLs fetched and longer quotes, are in [raw/](raw/). I re-fetched two items myself (marked **[main]**): Gibson et al. 2026 and
Montero-Manso & Scharth 2026. **Quotes passed through the fetch tool's summariser, so they are near-verbatim. Re-check any quote against the
PDF before it goes into the paper.** Nothing here was written from memory; items that could not be fetched are listed at the end and excluded.

Columns: **ID** is the arXiv id (fetched URL `https://arxiv.org/abs/<id>` unless noted) or DOI. **Venue** is VERIFIED from a venue page,
a journal-ref, or the arXiv comments; "venue unverified" otherwise. **Claim** is one claim checked in the fetched text.
**Use** says how the item bears on DynaICL. Legend: (i) continuous-prior Bayes reference, (ii) finite-pool (memorising) posterior,
(iii) context-only estimator.

## 0. Quote check against the PDFs (2026-10-22, after review)

The quotes that `GAP_AND_NOVELTY.md` relies on were re-checked against the **raw PDF text**, not the fetch summariser: each arXiv PDF was
downloaded with curl, converted with `pdftotext`, and searched for the exact phrase after whitespace and line-break hyphen normalisation
(script `quote_check.py`, kept outside the repo in the session scratchpad; it runs nothing from the downloads). **21 of 21 papers, every
quote FOUND verbatim:**
entries 1, 2, 3, 7, 8, 9, 11, 16, 19, 39, 40, 45, 46, 51, 57, 65, 70, 73, 84, 86, 89 (for entry 51 only the phrase "statistical induction
heads" was searched; its other quoted claims were not PDF-checked).

* **Entry 39 (Cole et al.), the point you raised:** the abstract says "a family of noisy linear dynamical systems". The phrase "noisy
  one-dimensional linear dynamical systems" is **in the body**, in the experiments section ("we train transformers of varying depth to
  in-context learn noisy one-dimensional linear dynamical systems of the form (2)"). The one-dimensional analysis case is x_t = w x_{t-1} + xi_t with x_0 = 0.
  The bibliography entry is correct as a body quote; it must not be cited as an abstract quote.
* Entry 84 (Agarwal et al.): the PDF reads "as few as N = 10 runs" (with spaces); corrected below.
* Entry 7 (Gibson et al.): "Identification is more sample efficient than generalization (i.e., needs a shorter sequence to predict well)",
  "drawn once from a symmetric Dirichlet ensemble", and "evaluated over 16 different model seeds" are all in the PDF.
* Entry 73 (Simulacrum): "The reference AR models are correctly specified according to the simulation mechanism" and the comparator list
  (AR-BURG, AR-YW, AR-OLS, AR-MLE) are in the PDF.
* Not re-checked against PDFs (not relied on by the gap analysis): the remaining entries keep the abstract-level verification described above.

## 1. Memorisation vs generalisation, task diversity, finite vs continuous pretraining priors

| # | Reference | ID | Claim (checked) | Use |
|---|---|---|---|---|
| 1 | Raventós, Paul, Chen, Ganguli (2023). Pretraining task diversity and the emergence of non-Bayesian in-context learning for regression. NeurIPS 2023. | 2306.15063 | "a task diversity threshold for the emergence of ICL"; below it the model tracks dMMSE (finite-pool Bayes), above it ridge. | The template for (i) vs (ii). Linear regression, MSE; ridge is both (i) and (iii) there. |
| 2 | Wurgaft, Lubana, Park, Tanaka, Reddy, Goodman (2025). In-Context Learning Strategies Emerge Rationally. NeurIPS 2025 (poster page). | 2506.17859 | "a memorizing predictor, which assumes a discrete prior on the set of seen tasks" vs a generalizing predictor. | Formal (i)/(ii) mixture framework; KL / Euclidean distances. |
| 3 | Lu, Letey, Zavatone-Veth, Maiti, Pehlevan (2025). Asymptotic theory of in-context learning by linear attention. PNAS 122(28) e2502599122. | 2405.11751; DOI 10.1073/pnas.2502599122 | "In the low diversity regime, the model tends toward memorization of training tasks". | Solvable theory of the (ii) to (i) transition. MSE. |
| 4 | Letey, Zavatone-Veth, Lu, Pehlevan (2025). Pretrain-Test Task Alignment Governs Generalization in In-Context Learning. arXiv preprint. | 2509.26551 | "a tradeoff between specialization and generalization in ICL". | Pretrain/test mismatch, as in held-out vs in-library evaluation. |
| 5 | Carroll, Hoogland, Farrugia-Roberts, Murfet (2025). Dynamics of Transient Structure in In-Context Linear Regression Transformers. arXiv preprint. | 2501.17745 | Models "initially behave like ridge regression before specializing to the tasks in their training distribution". | Behaviour changes over training time: classification must be tied to a pre-registered checkpoint. |
| 6 | Nguyen, Reddy (2024). Differential learning kinetics govern the transition from memorization to generalization during in-context learning. arXiv preprint. | 2412.00104 | "The relative rates at which these sub-circuits learn explains the transition". | Mechanism of the (ii) to (i) transition. |
| 7 | Gibson, Cui, Reddy (2026). Distinct mechanisms underlying in-context learning in transformers. arXiv preprint. **[main]** | 2604.12151 | Trained on a finite set of discrete Markov chains; four algorithmic phases; memorisation/generalisation boundaries depend on the number of chains K (abstract re-read by me). Agent full-text read: memorising and generalising Bayes references, autoregressive KL in nats, 16 model seeds. | **Closest methodological twin**, but discrete-state chains, not continuous-state AR. |
| 8 | Park, Lubana, Pres, Tanaka (2025). Competition Dynamics Shape Algorithmic Phases of In-Context Learning. ICLR 2025. | 2412.01003 | "learning to simulate a finite mixture of Markov chains"; retrieval vs inference strategies. | Retrieval (about (ii)) vs inference (about (i)) on sequences; KL. |
| 9 | Panwar, Ahuja, Goyal (2024). In-Context Learning through the Bayesian Prism. ICLR 2024. | 2306.04891 | "A model with unlimited training data and compute is a Bayesian predictor". Intermediate diversities "agree with neither". | (i), (ii), (iii) on regression; bootstrap CIs; generalise-then-forget. |
| 10 | Goddard, Smith, Ngampruetikorn, Schwab (2025). When can in-context learning generalize out of task distribution? ICML 2025, PMLR 267:19585-19599. | 2506.05574 | "as task diversity increases, transformers undergo a transition from a specialized solution". | Diversity as coverage of task space, relevant to library atom placement. |
| 11 | Wu, Zou, Chen, Braverman, Gu, Bartlett (2024). How Many Pretraining Tasks Are Needed for In-Context Learning of Linear Regression? ICLR 2024. | 2310.08391 | "the pretrained model closely matches the Bayes optimal algorithm, i.e., optimally tuned ridge regression". | (i) = (iii) = ridge; no memorising baseline. |
| 12 | Kirsch, Harrison, Sohl-Dickstein, Metz (2022). General-Purpose In-Context Learning by Meta-Learning Transformers. NeurIPS 2022 Workshop on Meta-Learning (final venue unverified). | 2212.04458 | "transitions between algorithms that generalize, algorithms that memorize, and algorithms that fail to meta-train". | Early statement of the transition vs number of tasks. |
| 13 | Chan, Santoro, Lampinen, Wang, Singh, Richemond, McClelland, Hill (2022). Data Distributional Properties Drive Emergent In-Context Learning in Transformers. NeurIPS 2022. | 2205.05055 | "In-context learning emerges when the training data exhibits particular distributional properties such as burstiness". | Background (in-weights vs in-context). |
| 14 | Singh, Chan, Moskovitz, Grant, Saxe, Hill (2023). The Transient Nature of Emergent In-Context Learning in Transformers. NeurIPS 2023. | 2311.08360 | "ICL first emerges, then disappears and gives way to IWL". | Transience: report the training trajectory, decide at a fixed checkpoint. |
| 15 | Reddy (2024). The mechanistic basis of data dependence and abrupt learning in an in-context classification task. ICLR 2024. | 2312.03002 | "ICL is driven by the abrupt emergence of an induction head". | Mechanism background. |
| 16 | Aswadi, Ma, Wei (2026). What does a Bayes-filtered transformer believe? A predictive Monte Carlo approach. arXiv preprint. | 2607.17060 | "prediction-space comparison is fragile: different posteriors can share the same posterior-mean predictions." | Supports scoring full predictives (log score), not MSE. Possible implicit-prior readout. |
| 17 | Lin, Lee (2024). Dual Operating Modes of In-Context Learning. arXiv preprint. | 2402.18819 | Task retrieval vs task learning; "we derive the closed-form expression of the task posterior distribution". | Retrieval as (ii). |

## 2. Transformers as Bayesian predictors; prior-fitted networks

| # | Reference | ID | Claim (checked) | Use |
|---|---|---|---|---|
| 18 | Xie, Raghunathan, Liang, Ma (2022). An Explanation of In-context Learning as Implicit Bayesian Inference. ICLR 2022. | 2111.02080 | Synthetic GINC data on which "Transformers and LSTMs both exhibit in-context learning". | Foundational Bayesian framing. |
| 19 | Müller, Hollmann, Pineda Arango, Grabocka, Hutter (2022). Transformers Can Do Bayesian Inference. ICLR 2022. | 2112.10510 | Compared with the exact GP posterior predictive; prior-data NLL equals the KL to the exact PPD up to a constant. | **Precedent for log-score comparison to a matched Bayes reference** (i). Not time series. |
| 20 | Hollmann, Müller, Eggensperger, Hutter (2023). TabPFN. ICLR 2023. | 2207.01848 | "trained offline once, to approximate Bayesian inference on synthetic datasets". | Practicality of prior-trained networks. |
| 21 | Hollmann, Müller, Purucker, et al. (2025). Accurate predictions on small data with a tabular foundation model. Nature 637:319-326. | DOI 10.1038/s41586-024-08328-6 (fetched via PMC11711098) | "a learning algorithm that is itself learned across millions of synthetic datasets". | Background. |
| 22 | Reuter, Rudner, Fortuin, Rügamer (2025). Can Transformers Learn Full Bayesian Inference in Context? ICML 2025. | 2501.16825 | Posterior samples "similar in quality to state-of-the-art MCMC or variational inference methods". | Posterior (not only predictive) matching. |
| 23 | Zhu, Oermann, Cho (2026). Multi-Task Bayesian In-Context Learning. ICML 2026. | 2606.20538 | "matches oracle Bayesian predictors"; prior given as an in-context prefix. | Matched-prior design. |
| 24 | Kang, Lee, Cheng (2026). Transformers Can Learn Posterior Predictive Distributions In-Context. arXiv preprint. | 2605.26713 | Transformers can implement GD "targeting the posterior predictive mean and variance". | Theory of full-PPD learning. |
| 25 | Fortini, Ng, Petrone, Rousseau, Wei (2026). Uncertainty Decomposition for Bayes-Filtered Transformers via Bayesian Predictive Inference. arXiv preprint. | 2602.04596 | "epistemic uncertainty shrinks with context length". | Predictive-inference view. |
| 26 | Falck, Wang, Holmes (2024). Is In-Context Learning in Large Language Models Bayesian? A Martingale Perspective. ICML 2024. | 2406.00793 | Martingale property is "a fundamental requirement of a Bayesian learning system for exchangeable data". | Bayesian-coherence diagnostic; assumes exchangeability, so not directly for AR. |
| 27 | Ye, Namkoong (2024). Exchangeable Sequence Models Quantify Uncertainty Over Latent Concepts. arXiv preprint. | 2408.03307 | "epistemic uncertainty over latent environments is captured by variation in predicted future observations." | Background. |
| 28 | Arora, Jurafsky, Potts, Goodman (2025). Bayesian scaling laws for in-context learning. COLM 2025. | 2410.16531 | ICL "approximates a Bayesian learner". | Background. |

## 3. Algorithmic in-context learning on regression (context-only comparators)

| # | Reference | ID | Claim (checked) | Use |
|---|---|---|---|---|
| 29 | Garg, Tsipras, Liang, Valiant (2022). What Can Transformers Learn In-Context? A Case Study of Simple Function Classes. NeurIPS 2022. | 2208.01066 | "the trained model is able to learn unseen linear functions from in-context examples". | (iii) least squares; MSE. |
| 30 | Akyürek, Schuurmans, Andreas, Ma, Zhou (2023). What learning algorithm is in-context learning? Investigations with linear models. ICLR 2023. | 2211.15661 | Matches GD, ridge and least squares, "converging to Bayesian estimators for large widths and depths". | (i)/(iii). |
| 31 | von Oswald, Niklasson, Randazzo, Sacramento, Mordvintsev, Zhmoginov, Vladymyrov (2023). Transformers learn in-context by gradient descent. ICML 2023, PMLR 202:35151-35174. | 2212.07677 | "trained Transformers become mesa-optimizers". | Mechanism. |
| 32 | Bai, Chen, Wang, Xiong, Mei (2023). Transformers as Statisticians. NeurIPS 2023. | 2306.04637 | "A single transformer can adaptively select different base ICL algorithms". | A Bayes mixture can look like algorithm selection. |
| 33 | Pathak, Sen, Kong, Das (2023). Transformers can optimally learn regression mixture models. arXiv preprint. | 2311.08362 | "the decision-theoretic optimal procedure is indeed implementable by a transformer". | (ii)-like reference; MSE. |
| 34 | Ahn, Cheng, Daneshmand, Sra (2023). Transformers learn to implement preconditioned gradient descent for in-context learning. NeurIPS 2023. | 2306.00297 | Global minimum "implements a single iteration of preconditioned gradient descent". | Mechanism. |
| 35 | Li, Ildiz, Papailiopoulos, Oymak (2023). Transformers as Algorithms: Generalization and Stability in In-context Learning. ICML 2023, PMLR 202:19565-19594. | 2301.07067 | Prompts can be "a trajectory arising from a dynamical system". | ICL theory with dependent prompts. |

## 4. In-context learning of AR processes, linear dynamical systems and Kalman filtering

| # | Reference | ID | Claim (checked) | Use |
|---|---|---|---|---|
| 36 | Sander, Giryes, Suzuki, Blondel, Peyré (2024). How do Transformers perform In-Context Autoregressive Learning? ICML 2024. | 2402.05787 | "a trained one-layer linear Transformer implements one step of gradient descent". Noiseless, orthogonal W. | Mechanism for AR; no Bayes reference. |
| 37 | Zheng, Huang, Wang, Wu, Zhu, Li (2024). On Mesa-Optimization in Autoregressively Trained Transformers: Emergence and Capability. NeurIPS 2024. | 2405.16845 | Implements "one step of gradient descent to minimize an ordinary least squares (OLS) problem". | (iii) OLS; initial-state distribution matters. |
| 38 | von Oswald, Schlegel, Meulemans, et al. (2023). Uncovering mesa-optimization algorithms in Transformers. arXiv preprint (venue unverified). | 2309.05858 | "next-token prediction error minimization gives rise to a subsidiary learning algorithm". | Mechanism. |
| 39 | Cole, Zhao, Lu, Zhang (2025). In-Context Learning of Linear Dynamical Systems with Transformers: Approximation Bounds and Depth-Separation. NeurIPS 2025. | 2502.08136 | Abstract: log-depth transformers reach "error bounds comparable with those of the least-squares estimator" for "noisy linear dynamical systems". Body (experiments, PDF-checked): "noisy one-dimensional linear dynamical systems". | **Nearly our setting (d = 1, noisy)**; reference is least squares (theory); no baseline in experiments; L2. |
| 40 | Zhou, Wang, Goel, Zhang (2025). Why Do Transformers Fail to Forecast Time Series In-Context? arXiv preprint. | 2510.09776 | Linear self-attention "cannot achieve lower expected MSE than classical linear models"; gap shrinks no faster than 1/n. 7 seeds, SEM. | AR(p) with OLS and known-coefficient oracle; MSE. Direction agrees with our vanishing long-context gap. |
| 41 | Tseran, Imaizumi (2026). Optimal In-Context Learning of Autoregressive Processes under Heterogeneous Second-Order Moments of the Prompts. NeurIPS 2026 (poster abstract only; fetched https://neurips.cc/virtual/2026/poster/153067). | no arXiv id found | Convergence to an "optimal second-order moment-based AR(1) estimator" (part of this phrase came from a search summary). | Scalar AR(1) target is context-only (iii). Only the abstract verified. |
| 42 | Ziemann, Matni, Pappas (2025). State space models, emergence, and ergodicity. L4DC 2025, PMLR 283. | 2409.13421 | A "critical threshold" in parameters for non-ergodic linear systems. | Theory. |
| 43 | Vlǎdǎrean, Zhang, Sra (2026). On learning linear dynamical systems in context with attention layers. ICLR 2026 (fetched proceedings page). | proceedings.iclr.cc 2026, hash 0edcce16... | "the optimal weight construction for a single linear-attention layer". | Theory, noisy observations. |
| 44 | Goel, Bartlett (2024). Can a Transformer Represent a Kalman Filter? L4DC 2024, PMLR 242:1502-1512. | 2312.06937 | A causally-masked Transformer "which implements the Kalman Filter". | Representability only (known system). |
| 45 | Du, Balim, Oymak, Ozay (2023; arXiv order Balim first). Can Transformers Learn Optimal Filtering for Unknown Systems? IEEE Control Systems Letters 7:3525-3530. | 2308.08536; DOI 10.1109/LCSYS.2023.3335318 | "matches the optimal performance given by the Kalman filter for linear systems". | Oracle KF (known matrices) and RLS; L2; no seeds. |
| 46 | Akram, Vikalo (2024-2026). Transformers as Implicit State Estimators: In-Context Learning in Dynamical Systems. arXiv preprint (TMLR venue unverified). | 2410.16546 | "In linear-Gaussian regimes, its predictions closely match those of the Kalman filter." | Oracle KF, OLS, ridge; MSE. |
| 47 | Zhang, Xing (2026). Bayesian Optimality of In-Context Learning with Selective State Spaces. arXiv preprint. | 2602.17744 | Meta-trained selective SSM "asymptotically implements the Bayes-optimal predictor" for LG state-space tasks. | Asymptotic theory; silent on short context. |
| 48 | Forgione, Pura, Piga (2023). From system models to class models: An in-context learning paradigm. arXiv (related DOI 10.1109/LCSYS.2023.3335036; venue unverified). | 2308.13380 | "learn a meta model that represents a class of dynamical systems". | In-context system identification; RMSE. |
| 49 | Piga, Pura, Forgione (2023). On the adaptation of in-context learners for system identification. arXiv preprint. | 2312.04083 | "meta-model adaptation can enhance predictive performance". | Background. |
| 50 | Yang, Liu, Meng, Osher. In-Context Operator Learning with Data Prompts for Differential Equation Problems (ICON). PNAS (DOI listed on arXiv). | 2304.07993; DOI 10.1073/pnas.2310142120 | "training a single neural network as an operator learner". | Background (deterministic operators). |

## 5. In-context learning of Markov chains

| # | Reference | ID | Claim (checked) | Use |
|---|---|---|---|---|
| 51 | Edelman, Tsilivis, Edelman, Malach, Goel (2024). The Evolution of Statistical Induction Heads: In-Context Learning Markov Chains. NeurIPS 2024. | 2402.11004 | "rapid phase transition to the correct in-context bigram solution"; models "converge near the Bayesian optimal solution". | (i) Dirichlet posterior mean; KL. |
| 52 | Nichani, Damian, Lee (2024). How Transformers Learn Causal Structure with Gradient Descent. ICML 2024. | 2402.14735 | "we prove that transformers learn an induction head". | Mechanism. |
| 53 | Rajaraman, Bondaschi, Ramchandran, Gastpar, Makkuva (2024). Transformers on Markov data: Constant depth suffices. NeurIPS 2024 (proceedings page; arXiv id not confirmed). | NeurIPS 2024 hash f8a20700... | "a transformer with a constant number of layers can represent" the in-context conditional empirical distribution. | (iii) k-gram estimator. |
| 54 | Zhou, Tian, Diggavi (2026). An Information-Theoretic Approach to Understanding Transformers' In-Context Learning of Variable-Order Markov Chains. AISTATS 2026. | 2410.05493 | CTW "provides an optimal solution" in a Bayesian formulation. | (i) with log-loss. |
| 55 | Makkuva, Bondaschi, Girish, et al. (2025). Attention with Markov. ICLR 2025. | 2402.04161 | "global minima (bigram) and bad local minima (unigram)". | Low relevance. |

## 6. Dynamical systems, chaos, time-series foundation models and prior-trained forecasters

| # | Reference | ID | Claim (checked) | Use |
|---|---|---|---|---|
| 56 | Zhang, Gilpin (2025). Zero-shot forecasting of chaotic systems. ICLR 2025. | 2409.15771 | Identifies "context parroting as a simple mechanism". | Context-only behaviour of foundation models. |
| 57 | Zhang, Gilpin (2026). Context parroting: A simple but tough-to-beat baseline for foundation models in scientific machine learning. ICLR 2026. | 2505.11349 | The parroting baseline "scores higher than leading time-series foundation models". | **Context-only estimator explains pretrained models**, mirroring hypothesis (c). |
| 58 | Lai, Bao, Gilpin (2026). Panda: A pretrained forecast model for chaotic dynamics. ICLR 2026. | 2505.13755 | "clear scaling of zero-shot performance on unseen systems" with the number of unique systems. | Only dynamics paper varying the training-system count; point metrics. |
| 59 | Bao, Lai, Gilpin (2026). Transformers for dynamical systems learn transfer operators in-context. arXiv preprint. | 2602.18679 | "attention-based models apply a transfer-operator forecasting strategy in-context". | Bayes predictor derived but not tested. |
| 60 | Liu, Boullé, Sarfati, Earls (2024). LLMs learn governing principles of dynamical systems, revealing an in-context neural scaling law. EMNLP 2024. | 2402.00795; DOI 10.18653/v1/2024.emnlp-main.842 | Accuracy "increases with the length of the input context window". | Distributional (Bhattacharyya) evaluation vs ground truth. |
| 61 | Gilpin (2021). Chaos as an interpretable benchmark for forecasting and data-driven modelling. NeurIPS 2021 Datasets and Benchmarks. | 2110.05266 | "131 known chaotic dynamical systems". | Benchmark background. |
| 62 | Hemmer, Durstewitz (2025). True Zero-Shot Inference of Dynamical Systems Preserving Long-Term Statistics (DynaMix). NeurIPS 2025. | 2505.13192 | "the first DSR model able to generalize zero-shot to out-of-domain DS". | Background. |
| 63 | Seifner, Cvejoski, Berghaus, Ojeda, Sanchez (2025). In-Context Learning of Stochastic Differential Equations with Foundation Inference Models. NeurIPS 2025. | 2502.19049 | "robust in-context function estimation". | Amortised ICL of stochastic dynamics. |
| 64 | Gruver, Finzi, Qiu, Wilson (2023). Large Language Models Are Zero-Shot Time Series Forecasters. NeurIPS 2023. | 2310.07820 | LLMs "can surprisingly zero-shot extrapolate time series". | Background. |
| 65 | Ansari, Stella, Turkmen, et al. (2024). Chronos: Learning the Language of Time Series. TMLR (via mlanthology). | 2403.07815 | For AR(4) Chronos "performs on par with the fitted AR model with correct order"; synthetic GP data (KernelSynth). | AR test against fitted AR, not a Bayes posterior. |
| 66 | Das, Kong, Sen, Zhou (2024). A decoder-only foundation model for time-series forecasting (TimesFM). ICML 2024, PMLR 235:10148-10167. | 2310.10688 | "generators for ARMA processes"; 20% synthetic training data. | Synthetic ARMA in pretraining. |
| 67 | Rasul, Ashok, Williams, et al. (2023). Lag-Llama. arXiv preprint. | 2310.08278 | "univariate probabilistic time series forecasting". | Background. |
| 68 | Woo, Liu, Kumar, Xiong, Savarese, Sahoo (2024). Unified Training of Universal Time Series Forecasting Transformers (Moirai). ICML 2024, PMLR 235:53140-53164. | 2402.02592 | Trained on LOTSA. | Background. |
| 69 | Garza, Challu, Mergenthaler-Canseco (2023). TimeGPT-1. arXiv preprint. | 2310.03589 | "the first foundation model for time series" (authors' claim). | Background. |
| 70 | Dooley, Khurana, Mohapatra, Naidu, White (2023). ForecastPFN: Synthetically-Trained Zero-Shot Forecasting. NeurIPS 2023. | 2311.01933 | "a prior-data fitted network, trained to approximate Bayesian inference"; trained with MSE, pointwise predictions. | Point-only, no gap to its own prior's posterior is measured. |
| 71 | Bhethanabhotla, Swelam, Siems, Salinas, Hutter (2024). Mamba4Cast. arXiv preprint. | 2410.09385 | "Trained solely on synthetic data"; point forecasts, MSE. | Background. |
| 72 | Hoo, Müller, Salinas, Hutter (2025). From Tables to Time: Extending TabPFN-v2 to Time Series Forecasting. arXiv preprint. | 2501.02945 | "treats forecasting as a tabular regression problem". | Background. |
| 73 | Montero-Manso, Scharth (2026). The Simulacrum: Decision-Theoretic Pretraining for Near-Optimal Time-Series Forecasting and Inference. arXiv preprint. **[main]** | 2606.27711 | AR(5) world with coefficients from uniform partial autocorrelations; comparators "AR-MLE, AR-OLS ... AR-BURG and AR-YW"; metrics MSE, bias, pinball, coverage; no Bayes PPD reference for AR, no finite library, no seed variance (my read of the full HTML; the agent read only the abstract). | Closest recent forecasting work; differs in reference, metric and question. |

## 7. Filtering, scoring rules, calibration, Bayesian AR(1)

| # | Reference | ID | Claim (checked) | Use |
|---|---|---|---|---|
| 74 | Kalman (1960). A New Approach to Linear Filtering and Prediction Problems. J. Basic Engineering 82(1):35-45. | DOI 10.1115/1.3662552 (Crossref record) | Metadata only. | Stage 0.6 Kalman likelihood. |
| 75 | Särkkä (2013). Bayesian Filtering and Smoothing. Cambridge University Press (IMS Textbooks 3). | DOI 10.1017/CBO9781139344203 | Landing page fetched. | Textbook reference for Kalman prediction. |
| 76 | Gneiting, Raftery (2007). Strictly Proper Scoring Rules, Prediction, and Estimation. JASA 102(477):359-378. | DOI 10.1198/016214506000001437 (Crossref record) | Metadata only. | Log score and CRPS as proper scores. |
| 77 | Gneiting, Balabdaoui, Raftery (2007). Probabilistic Forecasts, Calibration and Sharpness. JRSS B 69(2):243-268. | DOI 10.1111/j.1467-9868.2007.00587.x | "maximizing the sharpness of the predictive distributions subject to calibration". | PIT / coverage checks. |
| 78 | Talts, Betancourt, Simpson, Vehtari, Gelman (2018). Validating Bayesian Inference Algorithms with Simulation-Based Calibration. arXiv preprint. | 1804.06788 | SBC validates "inferences from Bayesian algorithms capable of generating posterior samples". | Our SBC tests. |
| 79 | Sims, Uhlig (1991). Understanding Unit Rooters: A Helicopter Tour. Econometrica 59(6):1591-1599 (fetched via RePEc; **no DOI verified**). | RePEc ecm/emetrp v59y1991i6p1591-99 | Covers the "first-order univariate autoregression without constant term". | Bayesian vs classical AR(1) inference. |
| 80 | Phillips (1991). To criticize the critics: An objective Bayesian analysis of stochastic trends. J. Applied Econometrics 6(4):333-364. | DOI 10.1002/jae.3950060402 (Crossref record) | Metadata only. | Prior sensitivity for AR roots, relevant to the stability prior. |

## 8. Training-run variance, seeds and power

| # | Reference | ID | Claim (checked) | Use |
|---|---|---|---|---|
| 81 | Bouthillier, Delaunay, Bronzi, et al. (2021). Accounting for Variance in Machine Learning Benchmarks. MLSys 2021. | 2103.03098 | "variance due to data sampling, parameter initialization and hyperparameter choice impact markedly the results". | Randomise init, data order and data per replicate. |
| 82 | Dodge, Ilharco, Schwartz, Farhadi, Hajishirzi, Smith (2020). Fine-Tuning Pretrained Language Models: Weight Initializations, Data Orders, and Early Stopping. arXiv preprint. | 2002.06305 | "distinct random seeds can lead to substantially different results". | Seed components. |
| 83 | Picard (2021). Torch.manual_seed(3407) is all you need. arXiv preprint. | 2109.08203 | "it is surprisingly easy to find an outlier". | Against best-seed reporting. |
| 84 | Agarwal, Schwarzer, Castro, Courville, Bellemare (2021). Deep Reinforcement Learning at the Edge of the Statistical Precipice. NeurIPS 2021 (venue from arXiv comments). | 2108.13264 | Stratified bootstrap CIs; "percentile CIs provide good interval estimates for as few as N = 10 runs" (PDF-checked). | Run-level bootstrap. |
| 85 | Madaan, Singh, Schaeffer, et al. (2024). Quantifying Variance in Evaluation Benchmarks. arXiv preprint. | 2406.10229 | Measures "seed variance across initialisations". | Report seed variance. |
| 86 | Sellam, Yadlowsky, Wei, et al. (2022). The MultiBERTs: BERT Reproductions for Robustness Analysis. ICLR 2022. | 2106.16163 | The Multi-Bootstrap, "a non-parametric bootstrap method" over models and test data. | **Matches our seeds x items design.** |
| 87 | Henderson, Islam, Bachman, Pineau, Precup, Meger (2018). Deep Reinforcement Learning that Matters. AAAI 2018. | 1709.06560 | "variance intrinsic to the methods". | Background. |
| 88 | Colas, Sigaud, Oudeyer (2018). How Many Random Seeds? Statistical Power Analysis in Deep Reinforcement Learning Experiments. arXiv preprint. | 1806.08295 | "how the number of random seeds relates to the probabilities of statistical errors". | Seed power analysis. |

## 9. Name collision

| # | Reference | ID | Claim (checked) | Use |
|---|---|---|---|---|
| 89 | Zhou, Jiang, Cotterell, Sachan (2023). Efficient Prompting via Dynamic In-Context Learning. arXiv preprint. | 2305.11170 | "we propose DynaICL". | **The project name is taken** by an unrelated prompting method. |

## Excluded (not fetched or not verified; not cited)

* Seen only in search results: "Filtering Beats Fine-Tuning" (2601.06100), LaT-PFN (2405.10093), TempoPFN, ApolloPFN (2603.15802), SarSim0,
  "Position: The Future of Bayesian Prediction Is Prior-Fitted" (2505.23947), Rufolo et al. (2410.03291), Zekri et al. (2410.02724),
  "Kalman Linear Attention" (2602.10743), 2505.17838, "In-Context Learning Is Provably Bayesian Inference" (2510.10981), AutoTimes,
  2512.07705, Foundation Inference Models for Markov jump processes / FIM-ODE, Berkeley EECS tech reports on transformers and dynamical systems.
* Cited by Cole et al. but not retrieved: Wu et al. 2025, Guo et al. 2023, Huang et al. 2024.
* Not searched: Zellner's Bayesian econometrics.
* Wrong identifiers caught: Sims & Uhlig DOI 10.2307/2938223 resolves to a different paper; arXiv 2502.05787 is unrelated (Goddard et al. is 2506.05574).
* A remembered title for Ye & Namkoong ("... IS Bayesian inference a la De Finetti") was not found; the fetched title is entry 27.
* Claim excluded: a search-summary statement attributed to Akram & Vikalo about smaller models emulating linear regression (not in the fetched abstracts).
