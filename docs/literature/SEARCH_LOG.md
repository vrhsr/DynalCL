# Literature search log (workstream D2, 2026-10-27)

All searches below ran on **2026-10-27** (the session continued past midnight; the last venue-page downloads and quote checks ran in the
early hours of 2026-10-28). "Opened and read" means the item was retrieved in this task: the PDF was downloaded and its text extracted and
searched (**PDF**), or its arXiv API metadata record (title, authors, dates, comments, journal-ref, abstract) was retrieved (**API**), or a
web page was downloaded or fetched (**page**). Search-result snippets alone never count as read. New bibliography entries are in
[BIBLIOGRAPHY.md](BIBLIOGRAPHY.md) section 10; the D1 quote check is section 0b there; venues are in [VENUES.md](VENUES.md).

## Tools

* **WebSearch** (the Claude Code web-search tool), mode `standard` or `extended` as marked. It returns titles, URLs and a model-written summary.
  Summaries were used only to decide what to open.
* **curl** for PDFs (`https://arxiv.org/pdf/<id>`, proceedings PDFs) and for HTML venue pages; each download went to its own new directory in the
  session scratchpad. **pdftotext** (poppler, Git for Windows) and PyMuPDF for text extraction; a quote checker written for this task and run
  with `python -I` (nothing from a download was executed).
* **arXiv API** (`http://export.arxiv.org/api/query?id_list=...`) for metadata, parsed with Python's XML library.
* **WebFetch** (fetch plus summariser) for two pages; anything taken only from it is labelled fetch-only.

## Queries

| # | Tool / mode | Exact query | Opened and read (IDs) |
|---|---|---|---|
| 1 | WebSearch std | `Tseran Imaizumi "In-Context Learning of Autoregressive Processes" heterogeneous second-order moments` | none new (D1 check of entry 41; only the NeurIPS poster page exists; no PDF found) |
| 2 | WebSearch std | `"Transformers on Markov data: Constant depth suffices" arXiv` | NeurIPS 2024 proceedings PDF (hash f8a20700...) PDF; 2407.17686 PDF (D1, entry 53) |
| 3 | WebSearch std | `Vladarean Zhang Sra "On learning linear dynamical systems in context with attention layers"` | ICLR 2026 proceedings PDF (hash 0edcce16...) PDF (D1, entry 43) |
| 4 | WebSearch std | `Gneiting Balabdaoui Raftery "Probabilistic forecasts, calibration and sharpness" pdf` | author copy Gneiting2007jrssb.pdf PDF (D1, entry 77) |
| 5 | WebSearch ext | `in-context learning linear dynamical systems transformer Bayes optimal Kalman 2025 arXiv` | 2607.03660 PDF+API (from this result list); 2410.16546 v3 PDF (D1 venue, entry 46). Seen not opened: 2409.12293 (linear systems of equations, out of scope) |
| 6 | WebSearch ext | `transformer in-context learning autoregressive process Bayesian posterior predictive AR(1) memorization task diversity` | nothing new beyond existing entries (2501.16825, 2605.26713, 2402.05787, 2412.00104, 2604.12151, 2405.11751 already in the bibliography) |
| 7 | WebSearch ext | `arXiv 2026 in-context learning state-space models transformer Bayes-optimal filter unknown parameters meta-learned` | 2604.23818 PDF+API; 2510.10981 PDF+API; 2601.06100 PDF+API (read, not added: see below) |
| 8 | WebSearch ext | `transformers in-context learning chaotic dynamical systems 2025 2026 foundation model zero-shot Lorenz` | 2607.14937 PDF+API; 2509.21802 PDF+API (read, not added) |
| 9 | WebSearch std | `pre-registration machine learning research NeurIPS workshop preregistered papers` | PMLR v148 index page (page, curl); preface PDF bertinetto21a.pdf PDF |
| 10 | WebSearch std | `statistical power machine learning evaluation number of seeds paper` | nothing new opened (1806.08295 already entry 88). Seen not opened: 2605.00428, 2512.24145 |
| 11 | WebSearch std | `"With Little Power Comes Great Responsibility" Card statistical power NLP arXiv` | 2010.06595 PDF+API |
| 12 | WebSearch std | `time series foundation model synthetic prior pretraining 2025 arXiv TempoPFN OR "Chronos-2" OR "TiRex" zero-shot forecasting` | 2510.25502 PDF+API (+ NeurIPS 2026 poster page 155999, curl); 2510.15821 PDF+API; 2505.23719 PDF+API |
| 13 | WebSearch ext | `task diversity in-context learning memorization generalization transition 2026 arXiv finite number of pretraining tasks Bayesian` | 2606.06814 PDF+API. Seen not opened: 2406.02550 |
| 14 | WebSearch ext | `prior-fitted network time series autoregressive Bayesian posterior predictive comparison exact Bayes in-context forecasting` | 2505.23947 PDF+API. Seen not opened: 2603.15802, 2405.10093 (already excluded in the 2026-10-22 list), 2609.07257 |
| 15 | WebSearch ext | `"in-context" forecasting transformer "Bayes-optimal" "autoregressive" linear Gaussian 2026 arXiv short context sample efficiency prior` | 2603.18564 PDF+API; 2305.11097 PDF+API; 2410.01565 PDF+API. Seen not opened: 2606.31184, 2405.14982, 2604.00064, 2606.11473, 2402.03170 |
| 16 | WebSearch std | `Kalman filter baseline transformer time series forecasting in-context learning large language models filtering 2025 2026` | nothing new (2510.09776, 2410.16546 already entries 40, 46). Seen not opened: 2512.07705 |
| 17 | WebSearch std | `transformer in-context learning vector autoregression VAR(1) Bayesian reference matrix-normal prior pretraining` | nothing new opened; no VAR(1) Bayes-reference study surfaced |
| 18 | WebSearch std | `"Sequential Correlations Change In-Context Learning" effective context length` | 2607.03660 PDF+API; ICML 2026 virtual page 72425 (page, curl). Seen not opened: 2604.25858, 2601.22364, 2310.17639 |
| 19 | WebSearch std | `"Bayes gap" in-context learning transformer pretraining prior finite tasks continuous prior generalization theory meta-learning` | 2510.10981 PDF+API (body read: closed-form conjugate Bayes references in its experiments) |
| 20 | WebSearch ext | `transformer in-context learning time series "memorization" "generalization" number of training systems dynamical systems Bayes reference` | 2610.13411 PDF+API; 2410.03291 PDF+API. Seen not opened: 2405.02154, a ResearchGate item on critical transitions (no arXiv id), Berkeley tech report EECS-2023-287 (already excluded 2026-10-22) |
| 21 | WebSearch std | `arXiv 2610.13411 In-Context Learning for System Identification Probabilistic Formulation` | arXiv abs page via WebFetch (fetch-only), then PDF+API. Seen not opened: 2410.20357, 2312.04509 |
| 22 | WebSearch std | `Henriques Albanie Bertinetto pre-registration computer vision "Preregistering" machine learning results-blind review` | nothing new opened (ICCV 2019 workshop call seen only on a third-party mirror; not cited). Seen not opened: 2305.01509 |
| 23 | WebSearch ext | `time series foundation models evaluation synthetic AR processes compared to optimal predictor 2025 arXiv "ARIMA" zero-shot fail simple` | 2501.00889 PDF+API. Seen not opened: 2601.19040, 2503.11411, 2609.09586, 2510.08445, 2605.24381, 2401.13912 |
| 24 | WebSearch std | `hidden Markov model in-context learning transformer Bayes optimal filter prediction 2025 arXiv mixing` | led to query 25 |
| 25 | WebSearch std | `"Pre-trained Large Language Models Learn to Predict Hidden Markov Models In-context" arXiv` | 2506.07298 PDF+API |
| 26 | WebSearch ext | `position paper preregistration machine learning empirical research hypothesis testing 2024 2025 arXiv` | 2405.02200, 2311.18807, 2103.06944, 2407.12220, 2104.08878, 2606.11217 (all PDF+API). Seen not opened: 2510.11595, 2506.14652, 2509.00185, 2508.03289, a ScienceDirect opinion piece (Bruttel & Nithammer 2025, not retrieved) |
| 27 | WebSearch std | `distinguishing which algorithm a transformer implements in-context from its predictions identifiability behavioral equivalence ridge Bayes` | nothing new opened (2211.15661, 2306.04637, 2412.01003 already entries 30, 32, 8). Seen not opened: 2512.16902, 2603.10573 |
| 28 | WebSearch std | `"Hitchhiker's Guide to Testing Statistical Significance in Natural Language Processing" Dror` | ACL Anthology P18-1128 PDF |
| 29 | WebSearch ext | `neural network forecaster pretrained on AR(1) processes compared with Bayesian posterior predictive log score finite library of systems vs continuous prior` | 2308.05753 PDF+API (body read: Section 4.1 and Appendix B.1). Seen not opened: 2104.12119, 2209.02188, 2603.21075, 2008.08400 |
| 30 | WebSearch std | `NeurIPS 2026 workshop time series foundation models OR in-context learning call for papers` | NeurIPS 2026 workshop page 137514 and WorkshopsGuidance (pages, curl; used in VENUES.md) |
| 31 | WebSearch std | `"pre-registered" OR "preregistered" in-context learning transformer experiment Bayesian reference predictor` | nothing new; no pre-registered ICL study surfaced |
| 32 | WebSearch std | `transformer in-context learning noisy autoregressive process Kalman filter unknown parameters posterior predictive log-likelihood evaluation "observation noise" 2026` | ICML 2026 poster page 62122 (page, curl; venue of entry 24). No new study with log-score evaluation against a Bayes reference on noisy AR surfaced |

Venue pages read for VENUES.md are listed there with their URLs.

## Read but not added to the bibliography

* 2601.06100 (Kiruluta 2026, "Filtering Beats Fine Tuning: A Bayesian Kalman View of In Context Learning in LLMs"): single-author theory about
  LLM adaptation as a Kalman filter on a latent adaptation state; its own abstract says only "Minimal illustrative experiments" support it (PDF-verified).
  Not about forecasting dynamical systems; low relevance.
* 2509.21802 (ChaosNexus): chaotic-system foundation model, point accuracy and attractor statistics; adds nothing beyond entries 56-58 and 103.

## Overlap check (the most important question)

Searches 6, 7, 17, 19, 20, 29, 31 and 32 targeted work that does what this project does: validated Bayes references for AR or state-space families,
with population vs finite-library vs context-only comparisons, pre-registered. **None was found in these searches.** The closest items:

* **2308.05753 (Koshelev, Ponomarenko, Seleznev 2023), new entry 90: partial overlap.** A network trained on simulations from a Bayesian AR(1)
  prior (inverse-gamma on sigma^2, truncated normal on rho in [0, 1), stationary initial state) approximates the posterior predictive; it is compared
  with MCMC, and with the AR(1) model per series using MSFE and log predictive score (LPS). The network beats the per-series AR(1) "since the Bayesian
  model knows a little more information" (PDF-verified), which is our population-advantage idea in one sentence. No finite library, no
  separability analysis, no seeds, no pre-registration; the AR(1) case is a toy proof of concept for agent-based-model forecasting.
* 2510.10981 (Wakayama & Suzuki, ICML 2026), entry 92: closed-form conjugate Bayes references and a measured "Bayes Gap", but for a two-family
  regression mixture, not AR.
* 2603.18564 (Cao et al. 2026), entry 91: transformer beats OLS/ridge/l1 for short contexts (k <= 30), read as "implicit prior inference"; context-only
  baselines only, MSE, i.i.d. regression (plus a VAR(1)-correlated-features variant).
* 2604.23818 (Tang et al., CDC 2026), entry 94: trains on M sampled linear systems and compares with an oracle Kalman filter; RMS error.

Search limits: one day of web search; arXiv-centric; WebSearch summaries can miss items. "Not found" means not found here, not proof of absence.
