# Literature hunt A: transformers as Bayesian / Bayes-optimal in-context learners; task diversity and memorisation vs generalisation

Retrieved 2026-10-22 with WebFetch/WebSearch. **VERIFIED** means the arXiv abstract page (or the proceedings/venue page) was fetched in this session and the quoted phrase comes from that fetched text. The venue is VERIFIED only where a venue page, a journal-ref, or the arXiv "Comments" field was fetched. Otherwise it is marked. Details about setups (baselines, metrics) come from the fetched arXiv HTML full text where stated ("HTML-checked"). The fetch tool summarises pages, so short quotes are as returned by it. Re-check them against the PDF before citing verbatim in a paper.

Relevance key for DynaICL: (i) = compares against a Bayes-optimal predictor under a continuous prior; (ii) = compares against a discrete-task-pool (memorising) posterior; (iii) = compares against a context-only estimator (OLS / ridge / least squares / Kalman with known model, etc.).

---

## 1. Core: finite vs continuous pretraining task distribution (most relevant)

### 1.1 Pretraining task diversity and the emergence of non-Bayesian in-context learning for regression
- Authors: Allan Raventós, Mansheej Paul, Feng Chen, Surya Ganguli. 2023. **NeurIPS 2023** (Advances in NeurIPS 36, Main Conference Track; venue page fetched).
- arXiv:2306.15063. URLs: https://arxiv.org/abs/2306.15063 ; https://proceedings.neurips.cc/paper_files/paper/2023/hash/2e10b2c2e1aa4f8083c37dfe269873f8-Abstract-Conference.html ; HTML https://arxiv.org/html/2306.15063v2
- Verified claim: "We empirically demonstrate a task diversity threshold for the emergence of ICL." Below the threshold the transformer behaves like the Bayes estimator with the finite pretraining pool as its prior. Above it, it behaves like ridge regression. The abstract says ICL on new tasks "hinges on it deviating from the Bayes optimal estimator with the pretraining distribution as the prior".
- Setup (HTML-checked): the pool is a "uniform distribution over a finite set of" M tasks drawn i.i.d. from N(0, I_D). The baselines are dMMSE ("discrete minimum mean squared error", the Bayes posterior mean under the M-task prior) and Ridge "with the ridge parameter set to the noise scale" (Bayes under the Gaussian prior). D = 8, K up to 16 in-context examples, sigma^2 = 0.25. **Metric: MSE** (normalised by D) plus mean-squared prediction difference Delta. No NLL. The main experiments do not state a seed count (only an appendix study uses 4 seeds).
- Relevance: the closest template to DynaICL's (a)/(b)/(c) question. Covers (i) ridge = continuous-prior Bayes and (ii) dMMSE. Note: here (i) and (iii) coincide, because ridge is both continuous-prior Bayes and a context-only estimator. DynaICL separates them (continuous-prior Bayes vs a context-only estimator without the population prior). Point-prediction MSE only, i.i.d. regression, not AR.

### 1.2 In-Context Learning Strategies Emerge Rationally
- Authors: Daniel Wurgaft, Ekdeep Singh Lubana, Core Francisco Park, Hidenori Tanaka, Gautam Reddy, Noah D. Goodman. 2025. **NeurIPS 2025 (poster)** (neurips.cc page fetched). arXiv:2506.17859 (comment there: "Preprint").
- URLs: https://arxiv.org/abs/2506.17859 ; https://neurips.cc/virtual/2025/poster/117195 ; HTML https://arxiv.org/html/2506.17859v2
- Verified claim: the abstract describes "a memorizing predictor, which assumes a discrete prior on the set of seen tasks" and "a generalizing predictor, where the prior matches the underlying task distribution". It also says "a model's preference towards implementing a strategy is dictated by its complexity".
- Setup (HTML-checked): Balls & Urns (Dirichlet), linear regression (dMMSE = M vs ridge = G), and classification. The comparison distance is symmetrised KL or Euclidean, reported as a relative distance between G and M. Fit quality is reported as R^2, agreement, or Spearman.
- Relevance: explicitly (i) + (ii), framed as Bayesian model selection between memorising and generalising posteriors over training time and task diversity. Not time series. On the categorical tasks the metric is distributional (KL), not just MSE.

### 1.3 Asymptotic theory of in-context learning by linear attention
- Authors: Yue M. Lu, Mary I. Letey, Jacob A. Zavatone-Veth, Anindita Maiti, Cengiz Pehlevan. **PNAS 122(28) e2502599122 (2025)** (journal-ref on the arXiv page). arXiv:2405.11751.
- URL: https://arxiv.org/abs/2405.11751 ; HTML https://arxiv.org/html/2405.11751v3
- Verified claim: "In the low diversity regime, the model tends toward memorization of training tasks". At high diversity "it achieves genuine in-context learning and generalization beyond the scope of pretrained tasks".
- Setup (HTML-checked): k task vectors drawn once from N(0, I_d), with kappa = k/d. Ridge is the Bayes-optimal within-context estimator. dMMSE is the "pure memorizer". Metric: MSE (ICL error on fresh tasks vs IDG error on training tasks).
- Relevance: exactly solvable theory of the (i) vs (ii) transition. MSE only. i.i.d. regression.

### 1.4 Pretrain-Test Task Alignment Governs Generalization in In-Context Learning
- Authors: Mary I. Letey, Jacob A. Zavatone-Veth, Yue M. Lu, Cengiz Pehlevan. 2025. arXiv preprint 2509.26551 (v1, no venue listed).
- URL: https://arxiv.org/abs/2509.26551
- Verified claim: "Our analysis further reveals a tradeoff between specialization and generalization in ICL".
- Relevance: pretrain/test mismatch. This is the analogue of DynaICL's held-out-system vs in-pool evaluation.

### 1.5 Dynamics of Transient Structure in In-Context Linear Regression Transformers
- Authors: Liam Carroll, Jesse Hoogland, Matthew Farrugia-Roberts, Daniel Murfet. 2025. arXiv preprint 2501.17745 (no venue listed).
- URL: https://arxiv.org/abs/2501.17745
- Verified claim: at intermediate task diversity, transformers "initially behave like ridge regression before specializing to the tasks in their training distribution".
- Relevance: (i) then (ii) over training time, so training-time checkpoints matter when you classify a model as continuous-Bayes or library-Bayes.

### 1.6 Differential learning kinetics govern the transition from memorization to generalization during in-context learning
- Authors: Alex Nguyen, Gautam Reddy. 2024. arXiv preprint 2412.00104 (v2 Dec 2024, no venue listed).
- URL: https://arxiv.org/abs/2412.00104
- Verified claim: "The relative rates at which these sub-circuits learn explains the transition from memorization to generalization".
- Relevance: mechanistic account of the (ii)→(i) transition.

### 1.7 Distinct mechanisms underlying in-context learning in transformers
- Authors: Cole Gibson, Wenping Cui, Gautam Reddy. 2026. arXiv preprint 2604.12151 (v1, 14 Apr 2026).
- URL: https://arxiv.org/abs/2604.12151 ; HTML https://arxiv.org/html/2604.12151v1
- Verified claim: "The transformer displays four algorithmic phases". "Memorization and generalization phases are delineated by two boundaries that depend on data diversity."
- Setup (HTML-checked): K Markov chains (10 states) drawn once from a Dirichlet prior. Four Bayes-style predictors (1-/2-point statistics × memorising/generalising). Metric: autoregressive KL averaged over positions.
- Relevance: **sequential (Markov) data** with explicit (i) vs (ii) Bayes references and a **distributional (KL) metric**. Closest in spirit to DynaICL among the memorisation papers, but discrete-state.

### 1.8 Competition Dynamics Shape Algorithmic Phases of In-Context Learning
- Authors: Core Francisco Park, Ekdeep Singh Lubana, Itamar Pres, Hidenori Tanaka. 2024/2025. **ICLR 2025 (Spotlight)** (arXiv comment and journal-ref). arXiv:2412.01003.
- URL: https://arxiv.org/abs/2412.01003
- Verified claim: "learning to simulate a finite mixture of Markov chains". Strategies "combine a fuzzy retrieval vs. inference approach with either unigram or bigram statistics of the context".
- Relevance: retrieval (≈ library posterior) vs inference (≈ generalising) on sequential data.

### 1.9 In-Context Learning through the Bayesian Prism
- Authors: Madhur Panwar, Kabir Ahuja, Navin Goyal. 2023. **ICLR 2024** (arXiv Comments). arXiv:2306.04891.
- URL: https://arxiv.org/abs/2306.04891 ; HTML https://arxiv.org/html/2306.04891v2
- Verified claim: "A model with unlimited training data and compute is a Bayesian predictor: it learns the pretraining distribution."
- Setup (HTML-checked): Gaussian-mixture task priors ("Transformer's errors almost exactly align with those of the PME of the mixture"). Revisits Raventós with dMMSE vs ridge: small task diversity agrees with dMMSE, from 2^12 on with ridge. Intermediate diversities "agree with neither of the two" and show generalise-then-forget. Metric: squared error, 1280 prompts, 90% bootstrap CIs.
- Relevance: (i) + (ii) + (iii) (OLS/Lasso). MSE. Reports bootstrap CIs.

### 1.10 When can in-context learning generalize out of task distribution?
- Authors: Chase Goddard, Lindsay M. Smith, Vudtiwat Ngampruetikorn, David J. Schwab. 2025. **ICML 2025, PMLR 267:19585-19599** (arXiv Comments). arXiv:2506.05574.
- URL: https://arxiv.org/abs/2506.05574
- Verified claim: "as task diversity increases, transformers undergo a transition from a specialized solution" to one that generalises over the whole task space.
- Relevance: task diversity measured as the coverage of the task space, not just the count. This matters for DynaICL's choice of library support.

### 1.11 How Many Pretraining Tasks Are Needed for In-Context Learning of Linear Regression?
- Authors: Jingfeng Wu, Difan Zou, Zixiang Chen, Vladimir Braverman, Quanquan Gu, Peter L. Bartlett. 2023. **ICLR 2024** (arXiv Comments "ICLR 2024 Camera Ready"). arXiv:2310.08391.
- URL: https://arxiv.org/abs/2310.08391 ; HTML https://arxiv.org/html/2310.08391v2
- Verified claim: "effective pretraining only requires a small number of independent tasks". "the pretrained model closely matches the Bayes optimal algorithm, i.e., optimally tuned ridge regression".
- Setup (HTML-checked): Gaussian task prior. The metric is average regression risk (squared loss). It does **not** compare to a finite-pool memorising posterior (T tasks enter only through the bounds).
- Relevance: (i)/(iii) (ridge). Single-layer linear attention theory. MSE.

### 1.12 General-Purpose In-Context Learning by Meta-Learning Transformers
- Authors: Louis Kirsch, James Harrison, Jascha Sohl-Dickstein, Luke Metz. 2022. NeurIPS 2022 Workshop on Meta-Learning (arXiv Comments, "Full version currently under review"; no later venue confirmed). arXiv:2212.04458.
- URL: https://arxiv.org/abs/2212.04458
- Verified claim: "We characterize transitions between algorithms that generalize, algorithms that memorize, and algorithms that fail to meta-train at all, induced by changes in model size, number of tasks, and meta-optimization."
- Relevance: an early statement of the memorise/generalise transition as a function of the number of tasks.

### 1.13 Data Distributional Properties Drive Emergent In-Context Learning in Transformers
- Authors: Stephanie C.Y. Chan, Adam Santoro, Andrew K. Lampinen, Jane X. Wang, Aaditya Singh, Pierre H. Richemond, Jay McClelland, Felix Hill. 2022. **NeurIPS 2022 (Oral)** (arXiv Comments). arXiv:2205.05055.
- URL: https://arxiv.org/abs/2205.05055
- Verified claim: "In-context learning emerges when the training data exhibits particular distributional properties such as burstiness".
- Relevance: in-weights vs in-context learning on few-shot classification. Background for the memorisation axis. No Bayes references.

### 1.14 The Transient Nature of Emergent In-Context Learning in Transformers
- Authors: Aaditya K. Singh, Stephanie C.Y. Chan, Ted Moskovitz, Erin Grant, Andrew M. Saxe, Felix Hill. 2023. **NeurIPS 2023 (poster)** (neurips.cc page fetched). arXiv:2311.08360.
- URL: https://arxiv.org/abs/2311.08360 ; https://neurips.cc/virtual/2023/poster/71806
- Verified claim: "We find that ICL first emerges, then disappears and gives way to IWL".
- Relevance: ICL can be transient over training. Any DynaICL Stage-1 verdict must be stated per checkpoint.

### 1.15 The mechanistic basis of data dependence and abrupt learning in an in-context classification task
- Author: Gautam Reddy. 2023. **ICLR 2024 (poster)** (iclr.cc page fetched; listed as "Gautam Reddy Nallamala"). arXiv:2312.03002.
- URL: https://arxiv.org/abs/2312.03002 ; https://iclr.cc/virtual/2024/poster/18368
- Verified claim: "In-context learning (ICL) is driven by the abrupt emergence of an induction head".
- Relevance: mechanism background. Classification, no Bayes references.

### 1.16 What does a Bayes-filtered transformer believe? A predictive Monte Carlo approach
- Authors: Afiq Abdillah Effiezal Aswadi, Haotong Ma, Susan Wei. 2026. arXiv preprint 2607.17060 (v1, 19 Jul 2026).
- URL: https://arxiv.org/abs/2607.17060 ; HTML https://arxiv.org/html/2607.17060v1
- Verified claim: "This prediction-space comparison is fragile: different posteriors can share the same posterior-mean predictions." "PMC returns an approximation to the implicit prior and posterior over the latent task".
- Setup (HTML-checked): Balls-and-urns, linear regression, and Markov chains. The training pool Pi_M (M tasks drawn once) is the "memorizing" reference and the population prior Pi_inf is the "generalizing" reference, both closed form. Metrics: Delta-MSE (regression) or symmetrised KL in prediction space, plus energy distance / sliced Wasserstein in latent space. At M = 8 the implicit prior concentrates near the pool. As M grows it moves toward the generalising baseline, with "transient generalization" at intermediate M. Not AR/time series.
- Relevance: **highly relevant methodologically.** It argues directly that MSE/posterior-mean comparisons cannot distinguish (i) from (ii). That supports DynaICL's use of log score and CRPS on full predictives.

### 1.17 Dual Operating Modes of In-Context Learning
- Authors: Ziqian Lin, Kangwook Lee. 2024. arXiv preprint 2402.18819 (v2 Aug 2024, no venue on the arXiv page).
- URL: https://arxiv.org/abs/2402.18819
- Verified claim: "a limited number of in-context samples may lead to the retrieval of an incorrect skill". "we derive the closed-form expression of the task posterior distribution".
- Relevance: task retrieval (≈ library posterior) vs task learning under a Gaussian-mixture task prior. Closed-form posterior as the reference.

---

## 2. Bayesian ICL theory and PFN-style amortised Bayes (posterior predictive as target)

### 2.1 An Explanation of In-context Learning as Implicit Bayesian Inference
- Authors: Sang Michael Xie, Aditi Raghunathan, Percy Liang, Tengyu Ma. 2021. **ICLR 2022** (arXiv Comments). arXiv:2111.02080.
- URL: https://arxiv.org/abs/2111.02080
- Verified claim: "we generate a small-scale synthetic dataset (GINC) where Transformers and LSTMs both exhibit in-context learning."
- Relevance: the foundational "ICL = implicit Bayesian inference over a latent concept" framing (HMM-mixture pretraining). A discrete latent-concept prior.

### 2.2 Transformers Can Do Bayesian Inference (PFNs)
- Authors: Samuel Müller, Noah Hollmann, Sebastian Pineda Arango, Josif Grabocka, Frank Hutter. 2021. **ICLR 2022** (arXiv Comments). arXiv:2112.10510 (v7 Aug 2024).
- URL: https://arxiv.org/abs/2112.10510 ; HTML https://arxiv.org/html/2112.10510v7
- Verified claim: PFNs "make probabilistic predictions for arbitrary other data points in a single forward propagation" and learn "to approximate Bayesian inference".
- Setup (HTML-checked): compares against the exact GP PPD ("the tractability of their PPD allows us to assess how close our approximation is to the exact PPD"). Metric: **Prior-Data NLL**, which the paper says "is equal to the KL-Divergence between the exact PPD and the approximation" up to a constant. 95% CIs. No time series.
- Relevance: (i) with **log-likelihood scoring**. This is the methodological precedent for DynaICL's log-score comparison against a matched Bayes reference.

### 2.3 TabPFN: A Transformer That Solves Small Tabular Classification Problems in a Second
- Authors: Noah Hollmann, Samuel Müller, Katharina Eggensperger, Frank Hutter. 2022. **ICLR 2023 (poster, top 25%)** (iclr.cc page fetched). arXiv:2207.01848.
- URL: https://arxiv.org/abs/2207.01848 ; https://iclr.cc/virtual/2023/poster/12113
- Verified claim: TabPFN is "trained offline once, to approximate Bayesian inference on synthetic datasets".
- Relevance: a PFN trained on a synthetic prior. Shows that a "pretraining prior = population" design is practical.

### 2.4 Accurate predictions on small data with a tabular foundation model (TabPFN v2)
- Authors: Noah Hollmann, Samuel Müller, Lennart Purucker, Arjun Krishnakumar, Max Körfer, Shi Bin Hoo, Robin Tibor Schirrmeister, Frank Hutter. **Nature 637(8045):319–326, 2025** (Epub 8 Jan 2025). DOI 10.1038/s41586-024-08328-6.
- URL fetched: https://pmc.ncbi.nlm.nih.gov/articles/PMC11711098/ (nature.com redirected to a login page; PubMed returned a cookie wall).
- Verified claim: "TabPFN is a learning algorithm that is itself learned across millions of synthetic datasets."
- Relevance: a large-scale PFN. Background only.

### 2.5 ForecastPFN: Synthetically-Trained Zero-Shot Forecasting
- Authors: Samuel Dooley, Gurnoor Singh Khurana, Chirag Mohapatra, Siddartha Naidu, Colin White. 2023. **NeurIPS 2023** (stated on the arXiv page). arXiv:2311.01933.
- URL: https://arxiv.org/abs/2311.01933
- Verified claim: "ForecastPFN is a prior-data fitted network, trained to approximate Bayesian inference".
- Relevance: a PFN for **time series**. The closest PFN precedent for DynaICL's AR setting. (Its evaluation metrics were not checked here.)

### 2.6 Can Transformers Learn Full Bayesian Inference in Context?
- Authors: Arik Reuter, Tim G. J. Rudner, Vincent Fortuin, David Rügamer. 2025. **ICML 2025** (arXiv Comments). arXiv:2501.16825.
- URL: https://arxiv.org/abs/2501.16825
- Verified claim: "transformers can perform full Bayesian inference for commonly used statistical models in context". Posterior samples are "similar in quality to state-of-the-art MCMC or variational inference methods".
- Relevance: posterior (not just predictive) matching for GLMs and latent factor models.

### 2.7 Multi-Task Bayesian In-Context Learning
- Authors: Qingyang Zhu, Eric Karl Oermann, Kyunghyun Cho. 2026. **ICML 2026** (arXiv Comments). arXiv:2606.20538.
- URL: https://arxiv.org/abs/2606.20538
- Verified claim: "our method matches oracle Bayesian predictors while being orders of magnitude faster". It "explicitly represents prior information as a prefix of in-context datasets."
- Relevance: the prior is passed in context, so one model can match different oracle Bayes predictors. This relates to DynaICL's matched-prior design.

### 2.8 Transformers Can Learn Posterior Predictive Distributions In-Context
- Authors: Gyeonghun Kang, Changwoo J. Lee, Xiang Cheng. 2026. arXiv preprint 2605.26713.
- URL: https://arxiv.org/abs/2605.26713
- Verified claim: "transformers can implement a gradient descent algorithm targeting the posterior predictive mean and variance".
- Relevance: a construction for full-PPD (mean and variance) learning in GP regression. Theory only.

### 2.9 Uncertainty Decomposition for Bayes-Filtered Transformers via Bayesian Predictive Inference
- Authors: Sandra Fortini, Kenyon Ng, Sonia Petrone, Judith Rousseau, Susan Wei. 2026. arXiv preprint 2602.04596 (v2 Jul 2026, retitled).
- URL: https://arxiv.org/abs/2602.04596
- Verified claim: Bayes-filtered transformers "output total predictive uncertainty in a single forward pass but never explicitly represent a posterior distribution". "epistemic uncertainty shrinks with context length".
- Relevance: predictive-inference (martingale-type) view of trained transformers.

### 2.10 Is In-Context Learning in Large Language Models Bayesian? A Martingale Perspective
- Authors: Fabian Falck, Ziyu Wang, Chris Holmes. 2024. **ICML 2024** (arXiv Comments). arXiv:2406.00793.
- URL: https://arxiv.org/abs/2406.00793 ; HTML https://arxiv.org/html/2406.00793v1
- Verified claim: "the martingale property is a necessary condition for unambiguous predictions in such scenarios". It is "a fundamental requirement of a Bayesian learning system for exchangeable data".
- Setup (HTML-checked): pretrained LLMs (Llama-2-7B, Mistral-7B, GPT-3/3.5/4) on Bernoulli/Gaussian exchangeable data. Reference Bayes models Beta(1,1) and N(0,100). The tests are on martingale property and uncertainty scaling with n. Reported violations "falsify" the Bayesian hypothesis in the tested settings.
- Relevance: a diagnostic for Bayesian coherence that needs no ground-truth prior. It assumes exchangeability, so it does not apply directly to AR data.

### 2.11 Exchangeable Sequence Models Quantify Uncertainty Over Latent Concepts
- Authors: Naimeng Ye, Hongseok Namkoong. 2024. arXiv preprint 2408.03307 (v3 Nov 2024).
- URL: https://arxiv.org/abs/2408.03307
- Verified claim: "epistemic uncertainty over latent environments is captured by variation in predicted future observations."
- Note: I searched for this under a remembered title ("Pre-training and in-context learning IS Bayesian inference a la De Finetti"). The arXiv page fetched shows the title above. The earlier title was NOT verified.

### 2.12 Bayesian scaling laws for in-context learning
- Authors: Aryaman Arora, Dan Jurafsky, Christopher Potts, Noah D. Goodman. 2024. **COLM 2025** (arXiv Comments). arXiv:2410.16531.
- URL: https://arxiv.org/abs/2410.16531
- Verified claim: the paper explains ICL accuracy curves by "showing that ICL approximates a Bayesian learner".
- Relevance: a Bayesian-learner model for how performance scales with the number of shots.

---

## 3. Algorithmic ICL on regression (context-only estimators as comparators)

### 3.1 What Can Transformers Learn In-Context? A Case Study of Simple Function Classes
- Authors: Shivam Garg, Dimitris Tsipras, Percy Liang, Gregory Valiant. 2022. **NeurIPS 2022 (poster)** (neurips.cc page fetched). arXiv:2208.01066.
- URL: https://arxiv.org/abs/2208.01066 ; https://neurips.cc/virtual/2022/poster/53586
- Verified claim: "the trained model is able to learn unseen linear functions from in-context examples".
- Relevance: (iii) least squares (which equals Bayes in the noiseless isotropic setting). Squared error. i.i.d. regression. (The "close to the optimal least squares estimator" wording appeared only in a search summary, not in a fetched page.)

### 3.2 What learning algorithm is in-context learning? Investigations with linear models
- Authors: Ekin Akyürek, Dale Schuurmans, Jacob Andreas, Tengyu Ma, Denny Zhou. 2022. **ICLR 2023** (arXiv Comments "ICLR2023 Camera Ready"). arXiv:2211.15661.
- URL: https://arxiv.org/abs/2211.15661
- Verified claim: trained ICL predictors match "the predictors computed by gradient descent, ridge regression, and exact least-squares regression", "converging to Bayesian estimators for large widths and depths".
- Relevance: (i)/(iii) via ridge and least squares.

### 3.3 Transformers learn in-context by gradient descent
- Authors: Johannes von Oswald, Eyvind Niklasson, Ettore Randazzo, João Sacramento, Alexander Mordvintsev, Andrey Zhmoginov, Max Vladymyrov. 2022. **ICML 2023, PMLR 202:35151–35174** (PMLR page fetched). arXiv:2212.07677.
- URL: https://arxiv.org/abs/2212.07677 ; https://proceedings.mlr.press/v202/von-oswald23a.html
- Verified claim: "trained Transformers become mesa-optimizers i.e. learn models by gradient descent in their forward pass."
- Relevance: (iii)-type mechanism (in-context GD). Squared loss.

### 3.4 Transformers as Statisticians: Provable In-Context Learning with In-Context Algorithm Selection
- Authors: Yu Bai, Fan Chen, Huan Wang, Caiming Xiong, Song Mei. 2023. **NeurIPS 2023 (oral)** (neurips.cc poster page fetched). arXiv:2306.04637.
- URL: https://arxiv.org/abs/2306.04637 ; https://neurips.cc/virtual/2023/poster/70583
- Verified claim: "A single transformer can adaptively select different base ICL algorithms".
- Relevance: algorithm selection. A Bayes-mixture predictor can look like a selector between context-only estimators.

### 3.5 Transformers can optimally learn regression mixture models
- Authors: Reese Pathak, Rajat Sen, Weihao Kong, Abhimanyu Das. 2023. arXiv preprint 2311.08362 (no venue on the arXiv page).
- URL: https://arxiv.org/abs/2311.08362
- Verified claim: "transformers achieve low mean-squared error on data generated via this process". The authors prove "the decision-theoretic optimal procedure is indeed implementable by a transformer".
- Relevance: (ii)-like discrete-mixture Bayes reference. MSE.

### 3.6 Transformers as Algorithms: Generalization and Stability in In-context Learning
- Authors: Yingcong Li, M. Emrullah Ildiz, Dimitris Papailiopoulos, Samet Oymak. 2023. arXiv preprint 2301.07067 (v2 Feb 2023; no venue listed on the arXiv page).
- URL: https://arxiv.org/abs/2301.07067
- Verified claim: prompts can be "a trajectory arising from a dynamical system". "transformers can indeed implement near-optimal algorithms on classical regression problems".
- Relevance: one of the few ICL-theory papers that explicitly includes **dynamical-system trajectories** (non-i.i.d. prompts).

---

## 4. ICL on autoregressive / dynamical-system data

### 4.1 How do Transformers perform In-Context Autoregressive Learning?
- Authors: Michael E. Sander, Raja Giryes, Taiji Suzuki, Mathieu Blondel, Gabriel Peyré. 2024. **ICML 2024** (arXiv Comments). arXiv:2402.05787.
- URL: https://arxiv.org/abs/2402.05787
- Verified claim: "a trained Transformer predicts the next token by first learning" the AR matrix in context, then applying a prediction mapping.
- Relevance: an AR(1)-type process x_{t+1} = W x_t with W varying across sequences. Mechanistic, not Bayes-scored.

### 4.2 Why Do Transformers Fail to Forecast Time Series In-Context?
- Authors: Yufa Zhou, Yixiao Wang, Surbhi Goel, Anru R. Zhang. 2025. arXiv preprint 2510.09776 (v1).
- URL: https://arxiv.org/abs/2510.09776 ; HTML https://arxiv.org/html/2510.09776v1
- Verified claim: linear self-attention models "cannot achieve lower expected MSE than classical linear models for in-context forecasting". As context grows "LSA asymptotically recovers the optimal linear predictor".
- Setup (HTML-checked): AR data. Main empirical baseline OLS. Metric MSE / cumulative MSE. The coefficient prior was not found in the portion read.
- Relevance: **AR data with a (iii) context-only comparator.** Consistent in direction with DynaICL's finding that the population advantage vanishes at long context. MSE only.

### 4.3 Can Transformers Learn Optimal Filtering for Unknown Systems?
- Authors: Haldun Balim, Zhe Du, Samet Oymak, Necmiye Ozay. 2023. arXiv preprint 2308.08536 (v3 Jun 2024; no venue listed on the arXiv page).
- URL: https://arxiv.org/abs/2308.08536
- Verified claim: the trained transformer "even matches the optimal performance given by the Kalman filter for linear systems".
- Relevance: the comparator is a **known-system** Kalman filter (an oracle, not the population-prior Bayes predictor). Related to DynaICL's noisy-observation variant.

### 4.4 Can a Transformer Represent a Kalman Filter?
- Authors: Gautam Goel, Peter Bartlett. 2023. arXiv preprint 2312.06937 (v3 May 2024).
- URL: https://arxiv.org/abs/2312.06937
- Verified claim: "for any observable LTI system we construct an explicit causally-masked Transformer which implements the Kalman Filter".
- Relevance: representational result for Kalman filtering. Theory only.

### 4.5 Transformers as Implicit State Estimators: In-Context Learning in Dynamical Systems
- Authors: Usman Akram, Haris Vikalo. 2024. arXiv preprint 2410.16546 (v3 7 Mar 2026; the HTML says "Reviewed on OpenReview". A search snippet said "Published in TMLR (03/2026)", but no fetched page confirmed it, so treat the venue as UNVERIFIED).
- URL: https://arxiv.org/abs/2410.16546 ; HTML https://arxiv.org/html/2410.16546v3
- Verified claim: "In linear-Gaussian regimes, its predictions closely match those of the Kalman filter."
- Setup (HTML-checked): trains on randomly sampled systems. Metrics: mean-squared prediction difference vs the KF, and MSE vs the truth.
- Relevance: a trained transformer vs a Kalman filter on linear-Gaussian state-space data. MSE only. It does not separate (i) from (iii).

### 4.6 Bayesian Optimality of In-Context Learning with Selective State Spaces
- Authors: Di Zhang, Jiaqi Xing. 2026. arXiv preprint 2602.17744 (v1).
- URL: https://arxiv.org/abs/2602.17744
- Verified claim: a meta-trained selective SSM "asymptotically implements the Bayes-optimal predictor" for linear Gaussian state-space tasks.
- Relevance: (i) for LG-SSM tasks. Theory. Asymptotic, so it says nothing about the short-context regime where DynaICL finds the advantage.

### 4.7 From system models to class models: An in-context learning paradigm
- Authors: Marco Forgione, Filippo Pura, Dario Piga. 2023. arXiv:2308.13380 (v3 Jul 2026). The arXiv page lists related DOI 10.1109/LCSYS.2023.3335036. The venue name is not shown, and the DOI was not resolved here.
- URL: https://arxiv.org/abs/2308.13380
- Verified claim: they "learn a meta model that represents a class of dynamical systems".
- Relevance: ICL for system identification over a class of dynamical systems (the control community's framing).

### 4.8 LLMs learn governing principles of dynamical systems, revealing an in-context neural scaling law
- Authors: Toni J.B. Liu, Nicolas Boullé, Raphaël Sarfati, Christopher J. Earls. 2024. **EMNLP 2024** (journal-ref on arXiv; DOI 10.18653/v1/2024.emnlp-main.842). arXiv:2402.00795.
- URL: https://arxiv.org/abs/2402.00795
- Verified claim: LLaMA 2 "achieves accurate predictions of dynamical system time series without fine-tuning or prompt engineering". Accuracy "increases with the length of the input context window".
- Relevance: pretrained LLMs on dynamical-system time series, including stochastic ones. No Bayes reference.

---

## 5. Comparison table: which verified papers compare a trained model with (i)/(ii)/(iii)

| Paper | (i) continuous-prior Bayes | (ii) discrete-pool (memorising) posterior | (iii) context-only estimator | Metric | AR / time series? |
|---|---|---|---|---|---|
| Raventós et al. 2023 | yes (ridge) | yes (dMMSE) | ridge = (i) here | MSE, prediction Delta | no |
| Wurgaft et al. 2025 | yes (G) | yes (M) | — | sym. KL / Euclidean; R^2 fits | no (categorical + regression) |
| Lu et al. 2025 (PNAS) | yes (ridge) | yes (dMMSE) | ridge = (i) | MSE | no |
| Panwar et al. 2024 | yes (PME, GMM, ridge) | yes (dMMSE) | OLS, Lasso | squared error, bootstrap CI | no |
| Carroll et al. 2025 | yes (ridge) | yes (dMMSE setup) | — | not checked | no |
| Gibson, Cui, Reddy 2026 | yes (generalising) | yes (memorising) | — | autoregressive KL | Markov chains (discrete) |
| Aswadi, Ma, Wei 2026 | yes (Pi_inf) | yes (Pi_M) | — | Delta-MSE / sym. KL + latent-space distances | Markov chains (discrete) |
| Park et al. 2025 | inference strategy | retrieval strategy | — | not checked | Markov chains (discrete) |
| Lin & Lee 2024 | Gaussian-mixture Bayes | task retrieval | — | not checked | no |
| Wu et al. 2024 | yes (tuned ridge) | **no** | ridge = (i) | squared risk | no |
| Müller et al. 2022 (PFN) | yes (exact GP PPD) | — | — | **NLL (= KL to the PPD)** | no |
| Falck et al. 2024 | Bayes ref. models (Beta, N(0,100)) | — | — | martingale tests | no (exchangeable) |
| Garg 2022, Akyürek 2023 | Akyürek: Bayes at large width | — | OLS / ridge / GD | squared error | no |
| Zhou et al. 2025 | — | — | OLS / optimal linear predictor | MSE | **yes (AR)** |
| Sander et al. 2024 | — | — | — (mechanistic) | squared loss | **yes (AR)** |
| Balim et al. 2023; Akram & Vikalo 2024 | — | — | known-system Kalman filter (oracle) | MSE / MSPD | **yes (LDS)** |
| Zhang & Xing 2026 | yes (theory, LG-SSM) | — | — | theory | **yes (LG-SSM)** |

**Gaps relevant to DynaICL (DERIVED from the table above; limited to the papers verified here):**
1. None of the verified papers combines all four of: AR/state-space data, a continuous-prior Bayes reference, a discrete-pool posterior, and a context-only estimator that is distinct from continuous-prior Bayes. In the regression papers (Raventós, Lu, Wu, Panwar) "ridge" plays both roles (i) and (iii), because ridge with lambda = sigma^2/tau^2 *is* the Bayes estimator under the Gaussian prior. DynaICL's separation of population-aware Bayes from a strong context-only Bayes (generic-stability prior) has no direct counterpart in the verified set.
2. Most memorisation-vs-generalisation papers score in **MSE / point-prediction space**. Aswadi, Ma & Wei (2026) argue explicitly that prediction-space comparison is "fragile" because different posteriors can share posterior-mean predictions. Distributional scoring (KL in Gibson et al. 2026 and Wurgaft et al. 2025; NLL in Müller et al. 2022) is the exception.
3. The time-series papers (Zhou 2025, Sander 2024, Balim 2023, Akram & Vikalo 2024) compare against OLS or a known-system Kalman oracle, not against a population-prior Bayes predictor, and they use MSE.
4. Seeds/variance reporting is thin: Raventós does not state a seed count for its main results. Panwar reports 90% bootstrap CIs over prompts. Müller reports 95% CIs.

---

## 6. NOT VERIFIED (excluded or partially excluded)

- "Pre-training and in-context learning IS Bayesian inference a la De Finetti" (Ye & Namkoong). This title was not found. The arXiv id 2408.03307 shows the title "Exchangeable Sequence Models Quantify Uncertainty Over Latent Concepts" (listed in 2.11 under that title).
- "Filtering Beats Fine-Tuning: A Bayesian Kalman View of In-Context Learning in LLMs" (arXiv 2601.06100). Seen only in a search result. Not fetched, so excluded.
- Akram & Vikalo TMLR venue. Seen only in a search snippet (the PDF fetch was unreadable and the HTML header did not show it), so the venue is unverified. The paper itself is verified.
- Raventós et al. earlier ICLR 2023 ME-FoMo workshop version ("The Effects of Pretraining Task Diversity on In-Context Learning of Ridge Regression"). Seen only via a search summary (mlanthology). Not fetched.
- Kirsch et al. final archival venue. The arXiv page says only "NeurIPS 2022 Workshop on Meta-Learning … Full version currently under review". No later venue was verified.
- Forgione et al. venue. The DOI 10.1109/LCSYS.2023.3335036 is listed on arXiv but was not resolved.
- Garg et al. phrase "error close to the optimal least squares estimator". Seen only in a search summary, not in a fetched abstract. Not used as evidence.
- Wrong id tried: arXiv 2502.05787 resolved to an unrelated paper (TAP-CAM). Goddard et al. was then verified at 2506.05574.
- Not searched or verified in this pass, so not included: Edelman et al. on Markov-chain statistical induction heads; Zhang & Gilpin on zero-shot chaotic forecasting; "Trained Transformers Learn Linear Models In-Context" (Zhang, Frei, Bartlett); Chronos / other time-series foundation models.

**Counts:** 43 papers verified (abstract page fetched; 2 TabPFN entries counted separately). Excluded or not verified: 2 papers (the De Finetti-titled Ye & Namkoong item and "Filtering Beats Fine-Tuning"), plus 5 unverified venue/version/phrase details listed above. 1 wrong arXiv id was corrected.
