# Literature hunt C: time-series foundation models / PFNs, Bayesian filtering and scoring, training-run variance

Retrieved 2026-10-22 with WebFetch / WebSearch. **Every item under "VERIFIED" was fetched in this session** (arXiv abstract or HTML page, PMLR, NeurIPS / MLSys proceedings, Crossref API metadata, publisher or RePEc page). Quotes are copied from the fetched page as returned by the fetch tool. The fetch tool summarises pages with a small model, so treat the quotes as near-verbatim and re-check any quote before printing it in a paper.

Labels: **V** = verified (page fetched); **V-meta** = bibliographic metadata verified via Crossref because the publisher page returned HTTP 403; **X** = not verified, excluded.

---

## 0. Name-collision check: "DynaICL"

| | |
|---|---|
| **Title** | Efficient Prompting via Dynamic In-Context Learning |
| **Authors** | Wangchunshu Zhou, Yuchen Eleanor Jiang, Ryan Cotterell, Mrinmaya Sachan |
| **Year / venue** | 2023, arXiv preprint (the abs page lists no journal ref) |
| **ID** | arXiv:2305.11170 |
| **URL fetched** | https://arxiv.org/abs/2305.11170 |
| **Verified claim** | The abstract says "we propose DynaICL", a method that allocates in-context demonstrations "according to the input complexity and the computational budget". |
| **Relevance** | **This is a direct name collision**: an existing ML method is already called DynaICL. It does LLM prompting, not dynamical systems. Consider renaming the project or always qualifying the name. |

A plain web search for "DynaICL" (standard mode) found no other use. A search for variant spellings (Dyna-ICL, DynICL, DynamicICL) found nothing under those names, but it did surface related dynamical-system ICL work (see 4.2).

---

## 1. Time-series foundation models and prior-fitted networks (PFNs)

### 1.1 Chronos (and KernelSynth) [V]
- **Title:** Chronos: Learning the Language of Time Series
- **Authors:** Abdul Fatir Ansari, Lorenzo Stella, Caner Turkmen, et al. (18 authors; last author Yuyang Wang)
- **Year / venue:** 2024, Transactions on Machine Learning Research (TMLR). The venue is verified on mlanthology (https://mlanthology.org/tmlr/2024/ansari2024tmlr-chronos), which links OpenReview forum gerNCVqqtR. The OpenReview page itself showed only a bot-check screen.
- **ID:** arXiv:2403.07815 (v3, 4 Nov 2024)
- **URLs fetched:** https://arxiv.org/abs/2403.07815 ; https://arxiv.org/html/2403.07815v3 ; mlanthology page above
- **Verified claims:**
  - Pretraining includes "a synthetic dataset that we generated via Gaussian processes to improve generalization".
  - **KernelSynth** (in the HTML paper): "randomly compose GP kernels to generate new time series". The kernel bank holds "linear kernels for trend, RBF kernels for smooth local variation, and periodic kernels for seasonalities", combined with + or x. The paper also proposes TSMixup.
  - It analyses autoregressive processes: Chronos-T5 (Base) is compared with the ground-truth AR model, an AR model of the correct order and AutoARIMA. For AR(4), Chronos "performs on par with the fitted AR model with correct order".
  - No comparison to a Bayes-optimal predictor is mentioned (checked in the first 100k characters of the HTML only).
- **Relevance:** This is the closest foundation-model precedent for testing on AR processes against a known-model reference. The reference there is a known or fitted AR model, not the Bayes posterior predictive under a population prior. DynaICL's matched Bayes reference is a stricter benchmark.

### 1.2 TimesFM [V]
- **Title:** A decoder-only foundation model for time-series forecasting
- **Authors:** Abhimanyu Das, Weihao Kong, Rajat Sen, Yichen Zhou
- **Year / venue:** 2024, ICML (PMLR 235:10148-10167)
- **ID:** arXiv:2310.10688
- **URLs fetched:** https://arxiv.org/abs/2310.10688 ; https://proceedings.mlr.press/v235/das24c.html ; https://arxiv.org/html/2310.10688v4
- **Verified claims:** Pretrained on "a large time-series corpus comprising both real-world and synthetic datasets" (PMLR abstract). The HTML paper says the authors "create generators for ARMA processes", plus seasonal patterns, trends and step functions, and that "The training loader samples 80% real data and 20% synthetic" (3M synthetic series of length 2048).
- **Relevance:** Synthetic ARMA data forms part of the pretraining mix. No Bayes-optimal comparison was seen on the pages fetched.

### 1.3 Lag-Llama [V]
- **Title:** Lag-Llama: Towards Foundation Models for Probabilistic Time Series Forecasting
- **Authors:** Kashif Rasul, Arjun Ashok, Andrew Robert Williams, et al. (18 authors)
- **Year / venue:** 2023 (v1 12 Oct 2023; v3 Feb 2024), arXiv preprint (no venue listed on the abs page)
- **ID:** arXiv:2310.08278
- **URL fetched:** https://arxiv.org/abs/2310.08278
- **Verified claim:** "a general-purpose foundation model for univariate probabilistic time series forecasting".
- **Relevance:** A probabilistic (distributional) forecaster, so it is compatible with log-score / CRPS evaluation. Its training data are real series. No Bayes reference was seen.

### 1.4 Moirai [V]
- **Title:** Unified Training of Universal Time Series Forecasting Transformers
- **Authors:** Gerald Woo, Chenghao Liu, Akshat Kumar, Caiming Xiong, Silvio Savarese, Doyen Sahoo
- **Year / venue:** 2024, ICML (PMLR 235:53140-53164)
- **ID:** arXiv:2402.02592
- **URLs fetched:** https://arxiv.org/abs/2402.02592 ; https://proceedings.mlr.press/v235/woo24a.html
- **Verified claims:** Trained on the "Large-scale Open Time Series Archive (LOTSA)" (over 27B observations, nine domains). "Moirai achieves competitive or superior performance as a zero-shot forecaster when compared to full-shot models."
- **Relevance:** A real-data foundation model, so it is not a synthetic-prior design.

### 1.5 TimeGPT [V]
- **Title:** TimeGPT-1
- **Authors:** Azul Garza, Cristian Challu, Max Mergenthaler-Canseco
- **Year / venue:** 2023 (v3 May 2024), arXiv preprint (no venue shown)
- **ID:** arXiv:2310.03589
- **URL fetched:** https://arxiv.org/abs/2310.03589
- **Verified claim:** It presents TimeGPT as "the first foundation model for time series".
- **Relevance:** Background only (a proprietary, real-data model).

### 1.6 ForecastPFN [V]
- **Title:** ForecastPFN: Synthetically-Trained Zero-Shot Forecasting
- **Authors:** Samuel Dooley, Gurnoor Singh Khurana, Chirag Mohapatra, Siddartha V. Naidu, Colin White
- **Year / venue:** 2023, NeurIPS 36 (Main Conference Track)
- **ID:** arXiv:2311.01933
- **URLs fetched:** https://arxiv.org/abs/2311.01933 ; https://papers.neurips.cc/paper_files/paper/2023/hash/0731f0e65559059eb9cd9d6f44ce2dd8-Abstract-Conference.html ; https://ar5iv.labs.arxiv.org/html/2311.01933
- **Verified claims:**
  - Abstract: "a prior-data fitted network, trained to approximate Bayesian inference", "trained purely on a novel synthetic data distribution".
  - Its prior has a linear x exponential trend, week / month / year sinusoidal seasonality and multiplicative Weibull noise.
  - It is trained with MSE and "makes pointwise predictions".
  - **It does not measure the gap to the true posterior predictive of its own prior.** The paper states only that MSE training "trains the model to predict the mean of the posterior distribution".
- **Relevance:** This is the direct PFN-for-forecasting precedent. Because it is point-only, it cannot be scored with log score or CRPS (see DynaICL invariant on `PointPredictor`). The missing Bayes-gap check is exactly what DynaICL would supply.

### 1.7 Mamba4Cast [V]
- **Title:** Mamba4Cast: Efficient Zero-Shot Time Series Forecasting with State Space Models
- **Authors:** Sathya Kamesh Bhethanabhotla, Omar Swelam, Julien Siems, David Salinas, Frank Hutter
- **Year / venue:** 2024, arXiv preprint (no venue on the abs page or in v1 HTML)
- **ID:** arXiv:2410.09385
- **URLs fetched:** https://arxiv.org/abs/2410.09385 ; https://arxiv.org/html/2410.09385v1
- **Verified claims:**
  - "inspired by Prior-data Fitted Networks (PFNs)" and "Trained solely on synthetic data".
  - The prior mixes 70% GP (composite Linear / Polynomial / Matern / Periodic kernels, "inspired by" KernelSynth) and 30% ForecastPFN prior.
  - The decoder outputs "point forecasts" and is trained with MSE.
- **Relevance:** A synthetic-prior state-space (non-transformer) forecaster. It is point-only, and no Bayes-optimal comparison was seen.

### 1.8 TabPFN-TS [V]
- **Title (current, v4):** From Tables to Time: Extending TabPFN-v2 to Time Series Forecasting. **v1 title:** "The Tabular Foundation Model TabPFN Outperforms Specialized Time Series Forecasting Models Based on Simple Features".
- **Authors:** Shi Bin Hoo, Samuel Müller, David Salinas, Frank Hutter
- **Year / venue:** 2025 (v4 revised Jan 2026), arXiv preprint (no venue listed)
- **ID:** arXiv:2501.02945
- **URLs fetched:** https://arxiv.org/abs/2501.02945 ; https://arxiv.org/abs/2501.02945v1
- **Verified claim:** It "treats forecasting as a tabular regression problem".
- **Relevance:** Shows that a synthetically pretrained PFN can forecast through features, without being a sequence model.

### 1.9 LLMTime (Gruver et al.) [V]
- **Title:** Large Language Models Are Zero-Shot Time Series Forecasters
- **Authors:** Nate Gruver, Marc Finzi, Shikai Qiu, Andrew Gordon Wilson
- **Year / venue:** 2023, NeurIPS 2023 (stated in the arXiv comments)
- **ID:** arXiv:2310.07820
- **URL fetched:** https://arxiv.org/abs/2310.07820
- **Verified claim:** LLMs "can surprisingly zero-shot extrapolate time series at a level comparable to or exceeding the performance" of purpose-built models.
- **Relevance:** Background for the claim that general-purpose sequence models do ICL on numeric series.

### 1.10 PFNs, the original (Müller et al.) [V]
- **Title:** Transformers Can Do Bayesian Inference
- **Authors:** Samuel Müller, Noah Hollmann, Sebastian Pineda Arango, Josif Grabocka, Frank Hutter
- **Year / venue:** 2022, ICLR 2022 (arXiv comments: "Published at ICLR 2022")
- **ID:** arXiv:2112.10510
- **URLs fetched:** https://arxiv.org/abs/2112.10510 ; https://arxiv.org/html/2112.10510v7
- **Verified claims:**
  - "PFNs leverage in-context learning ... to approximate a large set of posteriors".
  - Against the exact GP posterior predictive: "While the PPD of the GP is exact, we can see that our approximations get very close to it". The GP likelihood is "approximated very closely, and increasingly better so the more meta-train datasets we train the PFN for".
  - The comparison is qualitative or by likelihood curves. No nats-level tolerance like DynaICL's was seen.
- **Relevance:** This is the methodological ancestor of comparing a network with the Bayes-optimal predictor of its training prior. The gap-vs-meta-training-size curve is a design template for DynaICL Stage 1.

### 1.11 The Simulacrum (closest recent hit on "near-optimal under the generating prior") [V, metadata and abstract only]
- **Title:** The Simulacrum: Decision-Theoretic Pretraining for Near-Optimal Time-Series Forecasting and Inference
- **Authors:** Pablo Montero-Manso, Marcel Scharth
- **Year / venue:** 2026 (v1 26 Jun 2026), arXiv preprint
- **ID:** arXiv:2606.27711
- **URL fetched:** https://arxiv.org/abs/2606.27711
- **Verified claims:** The network "approximates the corresponding optimal decision rule" for "a distribution over data-generating processes". The authors claim control of "near-optimal risk, bias control, minimax performance, and uniform calibration".
- **Relevance:** This is potentially the most directly overlapping recent work (simulation-pretrained forecasters judged against the optimal rule for the generating world). **The results were NOT read**; only the abstract was. Read the full paper before positioning DynaICL.

**Answer to "is anyone comparing against the Bayes-optimal predictor of the generating prior?"** Among the pages fetched:
- The original PFN paper does this qualitatively for GP regression.
- Chronos compares against the true or fitted AR model, not a Bayes posterior predictive.
- ForecastPFN and Mamba4Cast do not measure their gap to their own prior's posterior.
- The Simulacrum (2026) claims a near-optimality framework (results unread).

No fetched paper reports a nats-level gap between a pretrained forecaster and the matched Bayes posterior predictive for an AR(1) population prior. This is a search-based negative, not proof of absence. An extended web search also returned no such head-to-head study.

---

## 2. Bayesian filtering, proper scoring, Bayesian AR(1)

### 2.1 Kalman (1960) [V-meta]
- **Title:** A New Approach to Linear Filtering and Prediction Problems
- **Author:** R. E. Kalman
- **Year / venue:** 1960, Journal of Basic Engineering 82(1):35-45
- **DOI:** 10.1115/1.3662552
- **URL fetched:** https://api.crossref.org/works/10.1115/1.3662552 (the ASME landing page returned 403)
- **Verified:** Title, author, journal, volume, issue, pages and year, from the Crossref record.
- **Relevance:** The canonical citation for the Stage 0.6 Kalman likelihood reference.

### 2.2 Särkkä, Bayesian Filtering and Smoothing [V]
- **Author:** Simo Särkkä
- **Publisher / series:** Cambridge University Press, Institute of Mathematical Statistics Textbooks (vol. 3)
- **Year:** The page shows two dates, 05 Sep 2013 and 05 Jun 2014 (edition or format not stated). Cite as 2013.
- **DOI:** 10.1017/CBO9781139344203
- **URL fetched:** https://www.cambridge.org/core/product/identifier/9781139344203/type/book
- **Relevance:** A textbook reference for Kalman prediction and the marginal likelihood used in the noisy-observation reference.

### 2.3 Gneiting & Raftery (2007) [V-meta]
- **Title:** Strictly Proper Scoring Rules, Prediction, and Estimation
- **Authors:** Tilmann Gneiting, Adrian E. Raftery
- **Year / venue:** 2007, Journal of the American Statistical Association 102(477):359-378
- **DOI:** 10.1198/016214506000001437
- **URL fetched:** https://api.crossref.org/works/10.1198/016214506000001437 (Taylor & Francis returned 403)
- **Relevance:** The justification for log score and CRPS as strictly proper scores.

### 2.4 Gneiting, Balabdaoui & Raftery (2007) [V]
- **Title:** Probabilistic Forecasts, Calibration and Sharpness
- **Authors:** Tilmann Gneiting, Fadoua Balabdaoui, Adrian E. Raftery
- **Year / venue:** 2007, JRSS Series B 69(2):243-268
- **DOI:** 10.1111/j.1467-9868.2007.00587.x
- **URL fetched:** https://academic.oup.com/jrsssb/article/69/2/243/7109375
- **Verified claim:** The paradigm of "maximizing the sharpness of the predictive distributions subject to calibration".
- **Relevance:** The basis for DynaICL's PIT / coverage calibration checks.

### 2.5 Talts et al., Simulation-Based Calibration [V]
- **Title:** Validating Bayesian Inference Algorithms with Simulation-Based Calibration
- **Authors:** Sean Talts, Michael Betancourt, Daniel Simpson, Aki Vehtari, Andrew Gelman
- **Year / venue:** 2018 (v2 Oct 2020), arXiv preprint (no journal ref on the abs page)
- **ID:** arXiv:1804.06788
- **URL fetched:** https://arxiv.org/abs/1804.06788
- **Verified claim:** SBC is "a general procedure for validating inferences from Bayesian algorithms capable of generating posterior samples".
- **Relevance:** The basis of the SBC tests (E) for the matched reference.

### 2.6 Sims & Uhlig (1991) [V, no DOI verified]
- **Title:** Understanding Unit Rooters: A Helicopter Tour
- **Authors:** Christopher A. Sims, Harald Uhlig
- **Year / venue:** 1991, Econometrica 59(6):1591-1599
- **URL fetched:** https://ideas.repec.org/a/ecm/emetrp/v59y1991i6p1591-99.html
- **Verified claim:** The study covers the "first-order univariate autoregression without constant term" and warns against "treating classical significance levels as if they were Bayesian posterior probabilities" (flat prior on the coefficient).
- **DOI note:** The DOI recalled before the search (10.2307/2938223) was **wrong**: Crossref resolves it to Gul, "A Theory of Disappointment Aversion". A web-search summary gave JSTOR stable 2938280, which was **not fetched**. Cite it via Econometrica volume and pages, or check the JSTOR id first.
- **Relevance:** Bayesian vs classical inference for the AR(1) coefficient. This supports conditioning on x_0 and using a flat-prior or likelihood-based AR(1) posterior.

### 2.7 Phillips (1991) [V-meta]
- **Title:** To criticize the critics: An objective Bayesian analysis of stochastic trends
- **Author:** P. C. B. Phillips
- **Year / venue:** 1991, Journal of Applied Econometrics 6(4):333-364
- **DOI:** 10.1002/jae.3950060402
- **URL fetched:** https://api.crossref.org/works/10.1002/jae.3950060402 (the Wiley page was not fetched)
- **Relevance:** The prior-sensitivity debate for the AR root (flat vs Jeffreys-type priors). This matters for DynaICL's "generic-stability" context-only prior.

---

## 3. Training-run variance, seeds, statistical power

### 3.1 Bouthillier et al. (2021) [V]
- **Title:** Accounting for Variance in Machine Learning Benchmarks
- **Authors:** Xavier Bouthillier, Pierre Delaunay, Mirko Bronzi, et al. (16 authors on the proceedings page; 17 on arXiv)
- **Year / venue:** 2021, Proceedings of Machine Learning and Systems 3 (MLSys 2021)
- **ID:** arXiv:2103.03098
- **URLs fetched:** https://arxiv.org/abs/2103.03098 ; https://proceedings.mlsys.org/paper_files/paper/2021/hash/0184b0cd3cfb185989f858a1d9f5c1eb-Abstract.html
- **Verified claim:** "variance due to data sampling, parameter initialization and hyperparameter choice impact markedly the results". It "leads us to propose recommendations for future performance comparisons".
- **Relevance:** Supports randomising every source of variation (init, data order, data sample) across neural replicates, not only the init seed.

### 3.2 Dodge et al. (2020) [V]
- **Title:** Fine-Tuning Pretrained Language Models: Weight Initializations, Data Orders, and Early Stopping
- **Authors:** Jesse Dodge, Gabriel Ilharco, Roy Schwartz, Ali Farhadi, Hannaneh Hajishirzi, Noah Smith
- **Year / venue:** 2020, arXiv preprint (no venue on the abs page)
- **ID:** arXiv:2002.06305
- **URL fetched:** https://arxiv.org/abs/2002.06305
- **Verified claim:** "distinct random seeds can lead to substantially different results" with fixed hyperparameters.
- **Relevance:** Shows that init and data-order seeds should be treated as separate variance components.

### 3.3 Picard (2021) [V]
- **Title:** Torch.manual_seed(3407) is all you need: On the influence of random seeds in deep learning architectures for computer vision
- **Author:** David Picard
- **Year / venue:** 2021 (v2 2023), arXiv preprint
- **ID:** arXiv:2109.08203
- **URL fetched:** https://arxiv.org/abs/2109.08203
- **Verified claim:** "it is surprisingly easy to find an outlier that performs much better or much worse than the average".
- **Relevance:** A warning against single-seed or best-seed reporting when the effects are around 0.04 nats.

### 3.4 Agarwal et al. (2021) [V]
- **Title:** Deep Reinforcement Learning at the Edge of the Statistical Precipice
- **Authors:** Rishabh Agarwal, Max Schwarzer, Pablo Samuel Castro, Aaron Courville, Marc G. Bellemare
- **Year / venue:** 2021, NeurIPS 2021 (Outstanding Paper Award, per the arXiv comments)
- **ID:** arXiv:2108.13264
- **URLs fetched:** https://arxiv.org/abs/2108.13264 ; https://arxiv.org/html/2108.13264v4
- **Verified claims:**
  - "we propose using bootstrap CIs with stratified sampling for aggregate performance", re-sampling "runs with replacement independently for each task".
  - "percentile CIs provide good interval estimates for as few as N=10 runs".
  - "3-10 runs are prevalent in deep RL".
- **Relevance:** A template for seed-level (run-level) stratified bootstrap across DynaICL cells (stratified by n, h, r), as a complement to the existing item-level cluster bootstrap.

### 3.5 Madaan et al. (2024) [V]
- **Title:** Quantifying Variance in Evaluation Benchmarks
- **Authors:** Lovish Madaan, Aaditya K. Singh, Rylan Schaeffer, et al. (8 authors)
- **Year / venue:** 2024, arXiv preprint (no venue on the abs page)
- **ID:** arXiv:2406.10229
- **URL fetched:** https://arxiv.org/abs/2406.10229
- **Verified claim:** It measures "seed variance across initialisations".
- **Relevance:** Shows that seed variance should be estimated and reported alongside evaluation-sample variance.

### 3.6 The MultiBERTs (Sellam et al.) [V]
- **Title:** The MultiBERTs: BERT Reproductions for Robustness Analysis
- **Authors:** Thibault Sellam, Steve Yadlowsky, Jason Wei, et al. (12 authors)
- **Year / venue:** 2022, ICLR 2022 ("ICLR'22" in the arXiv comments)
- **ID:** arXiv:2106.16163
- **URL fetched:** https://arxiv.org/abs/2106.16163
- **Verified claims:** It releases 25 checkpoints varying "random weight initialization and shuffling of training data", and it introduces the Multi-Bootstrap, "a non-parametric bootstrap method for statistical inference" over multiple pretrained models and limited test data.
- **Relevance:** **The most directly usable method.** The Multi-Bootstrap resamples both seeds and test items, which matches DynaICL's two-level design (training seeds x evaluation items).

### 3.7 Henderson et al. (2018) [V]
- **Title:** Deep Reinforcement Learning that Matters
- **Authors:** Peter Henderson, Riashat Islam, Philip Bachman, Joelle Pineau, Doina Precup, David Meger
- **Year / venue:** 2018, AAAI-18 (stated in the arXiv comments)
- **ID:** arXiv:1709.06560
- **URL fetched:** https://arxiv.org/abs/1709.06560
- **Verified claim:** Results are hard to interpret because of "non-determinism in standard benchmark environments, combined with variance intrinsic to the methods".
- **Relevance:** Background on reporting variance across trials.

### 3.8 Colas, Sigaud & Oudeyer (2018) [V]
- **Title:** How Many Random Seeds? Statistical Power Analysis in Deep Reinforcement Learning Experiments
- **Authors:** Cédric Colas, Olivier Sigaud, Pierre-Yves Oudeyer
- **Year / venue:** 2018, arXiv preprint (no venue on the abs page)
- **ID:** arXiv:1806.08295
- **URL fetched:** https://arxiv.org/abs/1806.08295
- **Verified claim:** It explains "how the number of random seeds relates to the probabilities of statistical errors".
- **Relevance:** A power-analysis recipe for choosing the number of training seeds in Stage 1, given a pilot estimate of seed-to-seed SD. (DynaICL's rule applies: pilot SDs may set N, pilot effects may not.)

---

## 4. Additional hits

### 4.1 Verified (fetched) dynamical-system ICL papers (outside the requested groups, but relevant)
- **Transformers as Implicit State Estimators: In-Context Learning in Dynamical Systems.** Usman Akram, Haris Vikalo. arXiv:2410.16546 (v3 Mar 2026), no venue listed. Fetched https://arxiv.org/abs/2410.16546. Transformers "can implicitly infer hidden states" to predict system outputs. Relevance: a Kalman-filter-style comparison for in-context state estimation (DynaICL Stage 0.6 analogue).
- **On learning linear dynamical systems in context with attention layers.** Maria-Luiza Vlǎdǎrean, Xuhui Zhang, Suvrit Sra. ICLR 2026. Fetched https://proceedings.iclr.cc/paper_files/paper/2026/hash/0edcce16f918256cd3992c8a6f4afd79-Abstract-Conference.html. "We provide the optimal weight construction for a single linear-attention layer". Relevance: theory for linear-attention ICL of linear dynamical systems with noisy observations.

### 4.2 NOT VERIFIED (excluded): seen only as search-result titles or snippets, never fetched
| Item | Reason excluded |
|---|---|
| LaT-PFN (arXiv 2405.10093), TempoPFN, ApolloPFN / "Time-Aware Prior Fitted Networks" (arXiv 2603.15802), SarSim0 | Search-result titles and summaries only; not fetched |
| "Position: The Future of Bayesian Prediction Is Prior-Fitted" (arXiv 2505.23947) | Search result only; not fetched |
| Liu et al., "LLMs learn governing principles of dynamical systems..." (arXiv 2402.00795) | Search result only; not fetched |
| Rufolo et al., "Enhanced Transformer architecture for in-context learning of dynamical systems" (arXiv 2410.03291) | Search result only; not fetched |
| Zellner (Bayesian AR / econometrics book) | Not searched or retrieved in this session |
| Sims & Uhlig DOI 10.2307/2938223 | **Wrong**: Crossref resolves it to Gul (1991). The paper itself is verified via RePEc; its DOI / JSTOR id is unverified |
| Agarwal et al., NeurIPS proceedings page | Venue taken from the arXiv comments only (Outstanding Paper Award at NeurIPS 2021); proceedings page not fetched |
| Lag-Llama, TimeGPT, Mamba4Cast, TabPFN-TS, Talts (SBC), Dodge, Colas, Madaan: peer-reviewed venues | No venue was found on the pages fetched; cite as arXiv unless a venue is confirmed |
| Chronos OpenReview forum page | Bot-check screen; the TMLR venue was confirmed only through mlanthology |
