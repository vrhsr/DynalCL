# Literature review (Phase 2)

Produced 2026-10-31 by a literature sub-agent (read-only; primary records: arXiv API, OpenReview API, NeurIPS proceedings BibTeX, PMLR, Crossref; DBLP was blocked). Kept verbatim below. Audit notes (mine):

* Two items in its section 5 must be fixed before use, as it says: Rissanen's given name (Crossref gives only J.) and the Chronos entry type.
* Section 3e (model discrimination, Clarke-Barron) is metadata-only: the content claims this audit relies on (chain rule of KL; Clarke-Barron asymptotics) are DERIVED in STATISTICAL_AUDIT.md section 6, not taken from those papers; the papers must be read before the manuscript cites them for specific statements.
* Reviewers 1 and 3 independently confirmed the Wurgaft et al. miscitation (Markov chains) on the arXiv HTML.

---

# Literature map for the DynaICL paper (TMLR): verification of the 18 references.bib entries, gap search, matrix, five closest works

All lookups ran on 2026-10-31. I did not create or change any project file. Scratch files (raw API responses and three small parsers) are in `C:\Users\Ramana\AppData\Local\Temp\claude\e--study-buddy-DynaICL\bd3df7a4-8736-46d2-9c91-75fbaf70608c\scratchpad\lit\`.

**Status labels:**
- **VERIFIED** means the field came from a primary record I retrieved: the arXiv API record, the OpenReview API, a NeurIPS proceedings BibTeX file, a PMLR page, or a Crossref record.
- **S2** means the field came only from the Semantic Scholar Graph API. I treat that as secondary and say so wherever it is used.
- **UNVERIFIED** means I could not confirm it.

DBLP blocked automated access (an anti-bot page, then HTTP 429), so no field here comes from DBLP directly.

---

## 1. The 18 references.bib entries: corrected BibTeX and discrepancies

### Discrepancies found (most important first)

1. **sellam2022: wrong author order for the venue cited.** The bib order (Sellam, Yadlowsky, Wei, ...) follows arXiv. The ICLR 2022 version on OpenReview (forum K0E_F0gFDgA, "ICLR 2022 Spotlight") puts **Ian Tenney third**: Sellam, Yadlowsky, Tenney, Wei, Saphra, D'Amour, Linzen, Bastings, Iulia Raluca Turc, Eisenstein, Das, Pavlick. Since the bib cites ICLR, use the ICLR order and list every author, not "others".
2. **cole2025: title capitalisation differs from the proceedings.** The NeurIPS proceedings and OpenReview title is "In-context Learning of Linear Dynamical Systems with Transformers: Approximation Bounds and Depth-separation". The bib copies the arXiv v3 casing ("In-Context ... Depth-Separation"). The arXiv comment says earlier versions had a slightly different title and author order, so cite the camera-ready (v3 / proceedings).
3. **koshelev2023: also exists as an SSRN working paper.** Crossref has DOI 10.2139/ssrn.4520621 as type "posted-content", titled "Amortized Neural Networks for Agent-Based Model Forecasting". I found no peer-reviewed venue. The arXiv v1 abstract does not mention AR(1). The AR(1) material is in the body (Appendix B.1, PDF-checked in BIBLIOGRAPHY.md), so do not cite it as an abstract claim.
4. **All entries use surnames only.** The given names are fixed below.
5. **Missing pages, volumes and DOIs** that the venue records give:
   - raventos2023: vol 36, pp. 14228–14246, DOI 10.52202/075280-0626.
   - wurgaft2025: vol 38, pp. 118425–118485, DOI 10.52202/085713-3950.
   - cole2025: vol 38, pp. 169441–169479, DOI 10.52202/085713-5641.
   - agarwal2021: vol 34, pp. 29304–29320.
   - wakayama2026: pp. 124318–124351.
   - bertinetto2021: pp. i–i.
6. **panwar2024: order confirmed; one secondary source is wrong.** The order Panwar, Ahuja, Goyal is correct (arXiv and OpenReview HX5ujdsSon, "ICLR 2024 poster"). Semantic Scholar lists Ahuja first, which is wrong. Do not take metadata from it.
7. **aswadi2026: the given/family split is unclear.** arXiv gives "Afiq Abdillah Effiezal Aswadi". I could not verify which part is the family name; the bib's choice of "Aswadi" is plausible but **UNVERIFIED**.
8. **gneiting2007: journal name.** Crossref gives the full name "Journal of the Royal Statistical Society Series B: Statistical Methodology". Everything else matches.
9. **raventos2023: diacritic.** OpenReview spells it "Raventos"; arXiv and the NeurIPS proceedings spell it "Raventós". Keep "Ravent{\'o}s".
10. **wurgaft2025: name variant.** The arXiv comment still says "Preprint", but the NeurIPS 2025 proceedings entry is verified. The last author is "Noah D. Goodman" on arXiv and "Noah Goodman" in the proceedings.
11. **Six entries are arXiv-only (no peer-reviewed venue found).** These are gibson2026, aswadi2026, talts2018, zhou2023dynaicl, cao2026 and koshelev2023 (koshelev2023 is also on SSRN). For each, OpenReview search found no conference record, the arXiv record has no journal-ref, and Semantic Scholar says "arXiv". Cao et al. appears on OpenReview only as a DBLP "CoRR 2026" record.

Everything else matches (title, year, venue). Venue status for all 18:

| Key | Venue status | Source used |
|---|---|---|
| raventos2023 | NeurIPS 2023 main proceedings, VERIFIED | proceedings.neurips.cc …/2023/hash/2e10b2c2e1aa4f8083c37dfe269873f8-Abstract-Conference.html; OpenReview BtAz4a5xDg "NeurIPS 2023 poster" |
| wurgaft2025 | NeurIPS 2025 main proceedings, VERIFIED | …/2025/hash/abb22b1e4b4ab2988862be9d7ed083f9-Abstract-Conference.html; OpenReview bBUUOQI0N6 |
| lu2025 | PNAS 122(28) e2502599122, 2025, VERIFIED | api.crossref.org/works/10.1073/pnas.2502599122; arXiv journal-ref |
| gibson2026 | arXiv only (2604.12151) | arxiv.org/abs/2604.12151 |
| panwar2024 | ICLR 2024 poster, VERIFIED | openreview.net/forum?id=HX5ujdsSon |
| aswadi2026 | arXiv only (2607.17060) | arxiv.org/abs/2607.17060 |
| muller2022 | ICLR 2022 poster, VERIFIED | openreview.net/forum?id=KSugKcbNf9 |
| cole2025 | NeurIPS 2025 main proceedings, VERIFIED | …/2025/hash/f7ae4fe91d96f50abc2211f09b6a7e49-Abstract-Conference.html; OpenReview TVD7cVIPCp |
| zhang2026parroting | ICLR 2026 poster, VERIFIED | openreview.net/forum?id=EUAXc9Hlvm; arXiv comment |
| gneiting2007 | JRSS B 69(2):243–268, VERIFIED | api.crossref.org/works/10.1111/j.1467-9868.2007.00587.x |
| talts2018 | arXiv only (1804.06788; v2 2020) | arxiv.org/abs/1804.06788 |
| agarwal2021 | NeurIPS 2021 proceedings, VERIFIED (Outstanding Paper Award per arXiv comment) | …/2021/hash/f514cec81cb148559cf475e7426eed5e-Abstract.html |
| sellam2022 | ICLR 2022 spotlight, VERIFIED | openreview.net/forum?id=K0E_F0gFDgA |
| zhou2023dynaicl | arXiv only | arxiv.org/abs/2305.11170 |
| koshelev2023 | arXiv and SSRN working paper | arxiv.org/abs/2308.05753; api.crossref.org/works/10.2139/ssrn.4520621 |
| cao2026 | arXiv only | arxiv.org/abs/2603.18564 |
| wakayama2026 | ICML 2026, PMLR 306:124318–124351, VERIFIED | proceedings.mlr.press/v306/wakayama26b.html |
| bertinetto2021 | PMLR 148, pp. i–i, VERIFIED | proceedings.mlr.press/v148/bertinetto21a.html |

### Corrected BibTeX (each entry VERIFIED from the URLs in the table above)

```bibtex
@inproceedings{raventos2023,
  author    = {Ravent{\'o}s, Allan and Paul, Mansheej and Chen, Feng and Ganguli, Surya},
  title     = {Pretraining task diversity and the emergence of non-{B}ayesian in-context learning for regression},
  booktitle = {Advances in Neural Information Processing Systems},
  volume    = {36}, pages = {14228--14246}, year = {2023},
  doi       = {10.52202/075280-0626}, note = {arXiv:2306.15063}}

@inproceedings{wurgaft2025,
  author    = {Wurgaft, Daniel and Lubana, Ekdeep Singh and Park, Core Francisco and Tanaka, Hidenori and Reddy, Gautam and Goodman, Noah D.},
  title     = {In-Context Learning Strategies Emerge Rationally},
  booktitle = {Advances in Neural Information Processing Systems},
  volume    = {38}, pages = {118425--118485}, year = {2025},
  doi       = {10.52202/085713-3950}, note = {arXiv:2506.17859}}

@article{lu2025,
  author  = {Lu, Yue M. and Letey, Mary I. and Zavatone-Veth, Jacob A. and Maiti, Anindita and Pehlevan, Cengiz},
  title   = {Asymptotic theory of in-context learning by linear attention},
  journal = {Proceedings of the National Academy of Sciences},
  volume  = {122}, number = {28}, pages = {e2502599122}, year = {2025},
  doi     = {10.1073/pnas.2502599122}, note = {arXiv:2405.11751}}

@misc{gibson2026,
  author = {Gibson, Cole and Cui, Wenping and Reddy, Gautam},
  title  = {Distinct mechanisms underlying in-context learning in transformers},
  year   = {2026}, eprint = {2604.12151}, archivePrefix = {arXiv}, note = {arXiv preprint}}

@inproceedings{panwar2024,
  author    = {Panwar, Madhur and Ahuja, Kabir and Goyal, Navin},
  title     = {In-Context Learning through the {B}ayesian Prism},
  booktitle = {International Conference on Learning Representations (ICLR)}, year = {2024},
  url       = {https://openreview.net/forum?id=HX5ujdsSon}, note = {arXiv:2306.04891}}

@misc{aswadi2026,
  author = {Aswadi, Afiq Abdillah Effiezal and Ma, Haotong and Wei, Susan},  % given/family split of the first author UNVERIFIED
  title  = {What does a {B}ayes-filtered transformer believe? {A} predictive {M}onte {C}arlo approach},
  year   = {2026}, eprint = {2607.17060}, archivePrefix = {arXiv}, note = {arXiv preprint}}

@inproceedings{muller2022,
  author    = {M{\"u}ller, Samuel and Hollmann, Noah and Pineda Arango, Sebastian and Grabocka, Josif and Hutter, Frank},
  title     = {Transformers Can Do {B}ayesian Inference},
  booktitle = {International Conference on Learning Representations (ICLR)}, year = {2022},
  url       = {https://openreview.net/forum?id=KSugKcbNf9}, note = {arXiv:2112.10510}}

@inproceedings{cole2025,
  author    = {Cole, Frank and Zhao, Yuxuan and Lu, Yulong and Zhang, Tianhao},
  title     = {In-context Learning of Linear Dynamical Systems with Transformers: Approximation Bounds and Depth-separation},
  booktitle = {Advances in Neural Information Processing Systems},
  volume    = {38}, pages = {169441--169479}, year = {2025},
  doi       = {10.52202/085713-5641}, note = {arXiv:2502.08136}}

@inproceedings{zhang2026parroting,
  author    = {Zhang, Yuanzhao and Gilpin, William},
  title     = {Context parroting: A simple but tough-to-beat baseline for foundation models in scientific machine learning},
  booktitle = {International Conference on Learning Representations (ICLR)}, year = {2026},
  url       = {https://openreview.net/forum?id=EUAXc9Hlvm}, note = {arXiv:2505.11349}}

@article{gneiting2007,
  author  = {Gneiting, Tilmann and Balabdaoui, Fadoua and Raftery, Adrian E.},
  title   = {Probabilistic Forecasts, Calibration and Sharpness},
  journal = {Journal of the Royal Statistical Society Series B: Statistical Methodology},
  volume  = {69}, number = {2}, pages = {243--268}, year = {2007},
  doi     = {10.1111/j.1467-9868.2007.00587.x}}

@misc{talts2018,
  author = {Talts, Sean and Betancourt, Michael and Simpson, Daniel and Vehtari, Aki and Gelman, Andrew},
  title  = {Validating {B}ayesian Inference Algorithms with Simulation-Based Calibration},
  year   = {2018}, eprint = {1804.06788}, archivePrefix = {arXiv}, note = {arXiv preprint}}

@inproceedings{agarwal2021,
  author    = {Agarwal, Rishabh and Schwarzer, Max and Castro, Pablo Samuel and Courville, Aaron and Bellemare, Marc G.},
  title     = {Deep Reinforcement Learning at the Edge of the Statistical Precipice},
  booktitle = {Advances in Neural Information Processing Systems},
  volume    = {34}, pages = {29304--29320}, year = {2021}, note = {arXiv:2108.13264}}

@inproceedings{sellam2022,
  author    = {Sellam, Thibault and Yadlowsky, Steve and Tenney, Ian and Wei, Jason and Saphra, Naomi and D'Amour, Alexander and Linzen, Tal and Bastings, Jasmijn and Turc, Iulia Raluca and Eisenstein, Jacob and Das, Dipanjan and Pavlick, Ellie},
  title     = {The {MultiBERTs}: {BERT} Reproductions for Robustness Analysis},
  booktitle = {International Conference on Learning Representations (ICLR)}, year = {2022},
  url       = {https://openreview.net/forum?id=K0E_F0gFDgA}, note = {arXiv:2106.16163}}

@misc{zhou2023dynaicl,
  author = {Zhou, Wangchunshu and Jiang, Yuchen Eleanor and Cotterell, Ryan and Sachan, Mrinmaya},
  title  = {Efficient Prompting via Dynamic In-Context Learning},
  year   = {2023}, eprint = {2305.11170}, archivePrefix = {arXiv}, note = {arXiv preprint}}

@misc{koshelev2023,
  author = {Koshelev, Denis and Ponomarenko, Alexey and Seleznev, Sergei},
  title  = {Amortized neural networks for agent-based model forecasting},
  year   = {2023}, eprint = {2308.05753}, archivePrefix = {arXiv},
  note   = {arXiv preprint; also SSRN working paper, doi:10.2139/ssrn.4520621}}

@misc{cao2026,
  author = {Cao, Hoang T. H. and Trinh, Hai D. V. and Quan, Tho and Truong, Lan V.},
  title  = {Transformers Learn Robust In-Context Regression under Distributional Uncertainty},
  year   = {2026}, eprint = {2603.18564}, archivePrefix = {arXiv}, note = {arXiv preprint}}

@inproceedings{wakayama2026,
  author    = {Wakayama, Tomoya and Suzuki, Taiji},
  title     = {In-Context Learning Is Provably {B}ayesian Inference: A Generalization Theory for Meta-Learning},
  booktitle = {Proceedings of the 43rd International Conference on Machine Learning},
  series    = {Proceedings of Machine Learning Research}, volume = {306}, pages = {124318--124351},
  year      = {2026}, publisher = {PMLR}, note = {arXiv:2510.10981}}

@inproceedings{bertinetto2021,
  author    = {Bertinetto, Luca and Henriques, Jo{\~a}o F. and Albanie, Samuel and Paganini, Michela and Varol, G{\"u}l},
  title     = {Preface},
  booktitle = {NeurIPS 2020 Workshop on Pre-registration in Machine Learning},
  series    = {Proceedings of Machine Learning Research}, volume = {148}, pages = {i--i},
  year      = {2021}, publisher = {PMLR}}
```

### Venue updates that BIBLIOGRAPHY.md needs (not in references.bib)

These were found by OpenReview API venue lookups (the forum ids are in brackets).
- Entry 6, Nguyen & Reddy: **ICLR 2025 Spotlight** [INyi7qUdjZ]. BIBLIOGRAPHY.md says arXiv preprint.
- Entry 17, Lin & Lee: **ICML 2024 Poster** [ElVHUWyL3n]. BIBLIOGRAPHY.md says arXiv preprint.
- Entry 33, Pathak et al.: **ICLR 2024 poster** [sLkj91HIZU]. BIBLIOGRAPHY.md says arXiv preprint.
- Entry 72, TabPFN-TS: **"Accepted by TMLR"** [KIkQj8VOUY]. BIBLIOGRAPHY.md says arXiv preprint.
- Entry 65, Chronos: TMLR confirmed [gerNCVqqtR].
- Entry 46, Akram & Vikalo: TMLR confirmed [hIMK5MvGkP].

---

## 2. Search log (all on 2026-10-31)

### Tools and what each one counted for

- **arXiv API** (`export.arxiv.org/api/query?id_list=`; plain http returned an empty body, https worked). Four batches:
  - b1: the 16 arXiv ids in references.bib.
  - b2: 32 ids, including 2111.02080, 2208.01066, 2211.15661, 2212.07677, 2306.04637, 2312.06937, 2308.08536, 2301.07067, 2402.05787, 2403.07815, 2310.10688, 2310.08278, 2402.02592, 2311.01933, 2501.02945, 2406.00793, 2103.03098, 1709.06560, 2003.12206, 2205.13504, 2507.11768, 2410.16546, 2510.09776, 2412.00104, 2501.17745, 2506.05574, 2310.08391, 2412.01003, 2509.26551, 2606.06814, 2406.16964, 2501.10216.
  - b3: 2401.15530, 2306.09927, 2410.10393, 2405.19162, 2606.27711, 2311.08362, 2402.18819, 2602.17744, 2604.23818, 2510.25502.
  - b4: 2605.18281.
  - Abstracts were read from these records.
- **Semantic Scholar Graph API** (`/paper/batch`): venue cross-check only, treated as secondary.
- **OpenReview API** (v1 `api.openreview.net/notes/search`, v2 `api2.openreview.net/notes/search`): accepted-venue strings and author order. The v1 endpoint hit HTTP 429 several times, so I retried after pauses.
- **NeurIPS proceedings** (`papers.nips.cc/paper_files/paper/{2021,2022,2023,2024,2025/vol38-main-conference}` index pages, then the `-Bibtex*.bib` files): pages and DOIs.
- **PMLR pages** (curl): v306/wakayama26b, v235/jeon24a, v235/falck24a, v235/sander24a, v235/das24c, v235/woo24a, v202/von-oswald23a, v202/li23l, v242/goel24a. WebFetch was used for v148/bertinetto21a.
- **Crossref REST API.** Direct DOI lookups: 10.1111/j.1467-9868.2007.00587.x, 10.1073/pnas.2502599122, 10.2139/ssrn.4520621, 10.1198/016214506000001437, 10.1109/18.720554, 10.1111/j.2517-6161.1979.tb01066.x, 10.1609/aaai.v37i9.26317, 10.1109/LCSYS.2023.3335318. Bibliographic queries (several retried after 429s):
  - "Box Hill 1967 Discrimination among mechanistic models Technometrics"
  - "Atkinson Fedorov 1975 design of experiments for discriminating between two rival models Biometrika"
  - "Lopez-Fidalgo Tommasi Trandafir 2007 ..."
  - "Chaloner Verdinelli 1995 Bayesian experimental design: a review"
  - "Rainforth Foster Ivanova Smith Modern Bayesian experimental design"
  - "Clarke Barron 1990 Information-theoretic asymptotics of Bayes methods"
  - "Clarke Barron 1994 Jeffreys prior is asymptotically least favorable under entropy risk"
  - "Henderson Islam Bachman Pineau Precup Meger Deep reinforcement learning that matters"
  - "Pineau ... reproducibility" (rate-limited, never returned; Pineau was checked with WebSearch and Semantic Scholar instead).
- **DBLP API:** blocked (bot page, then 429). Nothing was taken from it.

### WebSearch queries (summaries were used only to find items; nothing was counted as read from a summary)

| # | Mode | Query | Result |
|---|---|---|---|
| W1 | std | `"Pretraining task diversity and the emergence of non-Bayesian in-context learning for regression" proceedings.neurips.cc` | neurips.cc poster 72459 |
| W2 | std | `"Deep Reinforcement Learning at the Edge of the Statistical Precipice" proceedings.neurips.cc 2021` | virtual page; proceedings found via the index instead |
| W3 | std | `"In-Context Learning Strategies Emerge Rationally" NeurIPS 2025 proceedings` | poster 117195 |
| W4 | std | `"In-context Learning of Linear Dynamical Systems with Transformers" NeurIPS 2025 proceedings papers.nips.cc` | proceedings hash f7ae4fe9... |
| W5 | std | `"In-Context Learning Is Provably Bayesian Inference" Wakayama Suzuki proceedings.mlr.press v306` | PMLR page |
| W6 | std | `transformers in-context learning not Bayesian deviation from Bayesian inference arXiv 2024 2025` | 2507.11768 (Chlon et al.), 2406.00793 |
| W7 | ext | `task diversity in-context learning memorization generalization transition follow-up Raventós 2024 2025 linear regression transformer` | items already known; 2606.06814 |
| W8 | std | `simple baselines rival time series foundation models zero-shot forecasting Chronos TimesFM evaluation 2024 2025` | 2501.00889 (already entry 107); 2609.25788 seen, not opened |
| W9 | std | `Pineau "Improving reproducibility in machine learning research" JMLR 2021 NeurIPS 2019 reproducibility program` | 2003.12206; JMLR v22/20-303 |
| W10 | ext | `transformer in-context learning Kalman filter linear dynamical system unknown parameters 2024 2025 arXiv "in-context" state estimation` | 2410.16546, 2308.08536, 2312.06937 |
| W11 | std | `"Are Language Models Actually Useful for Time Series Forecasting" OR "Are Transformers Effective for Time Series Forecasting" simple linear baseline` | 2205.13504; 2406.16964 found via arXiv |
| W12 | ext | `identifiability distinguishing in-context learning algorithms Bayes predictors before training separability ridge vs discrete prior meta-learning` | nothing new that maps separability before training |
| W13 | std | `statistical ensemble baseline outperforms Chronos zero-shot foundation model Nixtla benchmark arXiv` | 2501.10216 (opened). The Nixtla claim is only a blog/GitHub commit and is **not cited** |
| W14 | ext | `in-context learning dynamical systems transformer Bayes-optimal predictor comparison log-likelihood finite set of training systems memorization 2025 2026 arXiv` | known items (2604.12151, 2506.17859, 2510.10981, 2602.18679) |
| W15 | std | `"Trained Transformers Learn Linear Models In-Context" Zhang Frei Bartlett JMLR` | 2306.09927; JMLR v25/23-1042 |
| W16 | std | `Bayesian model discrimination expected KL divergence between posterior predictive distributions prior sensitivity sample size when do priors matter` | 2001.10664 and 1405.2818 seen, **not opened, not cited** |
| W17 | std | `GIFT-Eval benchmark general time series forecasting model evaluation statistical baselines foundation models arXiv` | 2410.10393 |
| W18 | std | `Jeon Lee Lei Van Roy "An Information-Theoretic Analysis of In-Context Learning" ICML 2024` | PMLR v235/jeon24a |
| W19 | std | `Kalman filter transformer in-context learning linear attention optimal filtering 2025 2026 arXiv unknown dynamics meta-learning Bayes posterior over system parameters` | nothing new (Vlădărean et al. ICLR 2026 is already entry 43) |
| W20 | std | `"registered report" OR "pre-registered" machine learning experiment transformer in-context learning TMLR 2025 2026 confirmatory` | **no pre-registered ICL study found** |
| W21 | ext | `choose synthetic task regime where memorizing and generalizing Bayesian predictors differ before training transformer "dMMSE" ridge gap context length task diversity analysis` | 2605.18281 (new) |
| W22 | std | `transformer in-context learning vector autoregression VAR multivariate time series Bayes optimal predictor in-context 2025 2026 arXiv` | **no VAR-specific Bayes-reference ICL study** |

### Overlap check

No paper found here builds validated Bayes references for AR, Kalman or VAR families, compares population vs finite-library vs context-only predictors by log score, maps where they differ by δ before any training, and pre-registers the study. This agrees with the 2026-10-27 log. Limits: one day; WebSearch summaries can miss items; DBLP was not reachable; this is not proof that no such paper exists.

---

## 3. Literature matrix

What I read is shown as **[A]** = abstract from the arXiv API record this session, **[M]** = metadata record only (Crossref, PMLR, proceedings or OpenReview), **[B]** = relies on a PDF check already recorded in BIBLIOGRAPHY.md. For [M] rows I state no findings, because I did not read the content in this task.

### 3a. Finite library vs continuous prior; task diversity

| Paper | Year | Venue | Method / setting | Main finding (as read) | Limitation | Difference from this project | Read |
|---|---|---|---|---|---|---|---|
| Raventós, Paul, Chen, Ganguli | 2023 | NeurIPS (peer-reviewed) | Train transformers on linear regression; vary the number of pretraining tasks | Below a task-diversity threshold the model behaves like Bayes with the discrete pretraining-task prior; above it, like ridge (Gaussian prior over all tasks) | i.i.d. regression; MSE; ridge is both the population predictor and the context-only predictor there | AR/state-space families; log score; separability map before training; library on held-out systems | [A] |
| Wurgaft, Lubana, Park, Tanaka, Reddy, Goodman | 2025 | NeurIPS | Hierarchical Bayesian "rational analysis" of memorising vs generalising predictors | The framework "almost perfectly predicts Transformer next-token predictions throughout training" | Fitted after training; task mixtures | We fix the references and their separability before training | [A] |
| Lu, Letey, Zavatone-Veth, Maiti, Pehlevan | 2025 | PNAS | Exactly solvable linear-attention model | Phase transition: low task diversity tends to memorisation | Asymptotic regime; MSE | Finite-n exact references; dependent (AR) data | [A] |
| Gibson, Cui, Reddy | 2026 | arXiv | Transformers trained on a finite set of K discrete Markov chains | Four algorithmic phases (memorise/generalise × 1-point/2-point statistics); boundaries K₁*, K₂* | Discrete states | Continuous-state linear families; maps before training | [A], [B] |
| Panwar, Ahuja, Goyal | 2024 | ICLR | Hierarchical meta-ICL with mixed function families | "A model with unlimited training data and compute is a Bayesian predictor"; deviations found | Regression | Dynamical families; pre-registered | [A] |
| Nguyen, Reddy | 2024/25 | ICLR 2025 Spotlight (OpenReview) | Small transformer, synthetic ICL task | Relative learning rates of sub-circuits explain the memorisation→generalisation transition; memorisation scaling law | Mechanistic; one task | No mechanism claims | [A] |
| Carroll, Hoogland, Farrugia-Roberts, Murfet | 2025 | arXiv | Linear regression at intermediate diversity | Models behave like ridge first, then specialise ("transient ridge") | Training-time dependence | Supports fixing a checkpoint in advance | [A] |
| Goddard, Smith, Ngampruetikorn, Schwab | 2025 | ICML, PMLR 267:19585–19599 (arXiv jref) | Task diversity as coverage of task space | Transition from a specialised to an OOD-generalising solution; phase diagram | Regression | Held-out systems in our library tests | [A] |
| Wu, Zou, Chen, Braverman, Gu, Bartlett | 2024 | ICLR (arXiv comment) | One-layer linear attention theory | Few tasks suffice; matches optimally tuned ridge | Gaussian prior only | Discrete-vs-continuous prior contrast | [A] |
| Letey, Zavatone-Veth, Lu, Pehlevan | 2025 | arXiv | Solvable model with pretrain/test covariance mismatch | Alignment measure; diversity can help or hurt | Regression | Held-out vs in-library evaluation | [A] |
| Kwon, Xu, Yaras, Song, Balzano, Qu | 2026 | arXiv | Mixture of low-rank Gaussians | Subspace-based diversity explains plateau shortening and OOD generalisation | Theory | — | [A] |
| Aswadi, Britton, Baker, Farrugia-Roberts | 2026 | ICML 2026 FoGen **workshop** poster (OpenReview tkZDIomP4W); TAIS 2026 | Task distribution diversified over training time | Temporal diversity increases bias toward generalisation | Workshop paper | New Raventós follow-up (2026) | [A] |
| Park, Lubana, Pres, Tanaka | 2025 | ICLR 2025 (arXiv jref) | Finite mixture of Markov chains | Four competing algorithms (retrieval vs inference) | Discrete | — | [A] |
| Lin, Lee | 2024 | ICML 2024 (OpenReview) | Closed-form task posterior; retrieval vs learning | Explains the dual operating modes | Squared loss | — | [A] |
| Pathak, Sen, Kong, Das | 2023/24 | ICLR 2024 (OpenReview) | Mixture of regressions | Optimal = exponential weights over a finite parameter set; transformers come close | MSE | A finite-library analogue in regression | [A] |

### 3b. Bayesian readings of ICL, and challenges to them

| Paper | Year | Venue | Method / setting | Main finding (as read) | Limitation | Difference from this project | Read |
|---|---|---|---|---|---|---|---|
| Xie, Raghunathan, Liang, Ma | 2022 | ICLR (OpenReview RdJVFCHjUMI) | Mixture-of-HMMs theory; GINC data | ICL as implicit Bayesian inference over a latent concept | Synthetic language | Continuous dynamics | [A] |
| Müller, Hollmann, Pineda Arango, Grabocka, Hutter | 2022 | ICLR | Prior-data fitted networks (PFNs) | Networks approximate the posterior predictive (PPD) | Not time series | Same NLL-to-reference logic | [A] |
| Falck, Wang, Holmes | 2024 | ICML, PMLR 235:12784–12805 | Martingale property tests | Violations "falsify" that LLM ICL is Bayesian | Assumes exchangeability (AR data is not) | **Challenges the premise** | [A] |
| Chlon et al. | 2025 | arXiv | Prequential code length vs Bayes reference | Order sensitivity "priced by log loss"; Bayes-competitive in expectation | LLMs; arXiv only | Supports log-score comparison to Bayes references | [A] |
| Mittal, Elmoznino, Gagnon, Bhardwaj, Marty, Sridhar, Lajoie | 2024/25 | ICML 2025 poster (OpenReview) | Bottleneck to force task-latent inference | "Little discernible difference" | Regression and similar tasks | Challenge: optimal-latent behaviour need not help | [A] |
| Jeon, Lee, Lei, Van Roy | 2024 | ICML, PMLR 235:21522–21554 | Information-theoretic error decomposition | Irreducible, meta-learning and intra-task error | Theory | Theory of where population knowledge pays | [A] |
| Wakayama, Suzuki | 2026 | ICML, PMLR 306 | Bayes Gap / Posterior Variance decomposition | Task-mixture uncertainty "vanishes exponentially fast with only a few in-context examples" | Regression mixtures | Matches our short-context-only finding | [A], [B] |
| Aswadi, Ma, Wei | 2026 | arXiv | Predictive Monte Carlo on Bayes-filtered transformers | Prediction-space comparison is fragile ("different posteriors can share the same posterior-mean predictions") | — | Supports full-predictive log score over MSE | [A] |
| Cao, Trinh, Quan, Truong | 2026 | arXiv | Regression under distribution shifts | Transformers match or beat classical baselines | Context-only baselines only; MSE | — | [A] |
| Koshelev, Ponomarenko, Seleznev | 2023 | arXiv + SSRN | Amortised network trained on a Bayesian AR(1) prior | Beats a per-series AR(1) fit in MSFE/LPS (body, App. B.1) | Toy example; no library; no seeds | **Closest AR precedent** | [A], [B] |
| Garg, Tsipras, Liang, Valiant | 2022 | NeurIPS, vol 35, pp. 30583–30598 | Train on function classes | Comparable to optimal least squares | MSE | Context-only comparator | [A] |
| Akyürek, Schuurmans, Andreas, Ma, Zhou | 2023 | ICLR (notable top 5%, OpenReview) | Linear models | Matches GD/ridge/OLS; converges to Bayes estimators at large width and depth | — | — | [A] |
| von Oswald et al. | 2023 | ICML, PMLR 202:35151–35174 | Linear self-attention ≈ GD | Mesa-optimisation | Mechanistic | — | [A] |
| Bai, Chen, Wang, Xiong, Mei | 2023 | NeurIPS, vol 36, pp. 57125–57211 | Constructions | In-context algorithm selection; near-Bayes-optimal under mixed noise levels | Theory | A Bayes mixture can look like algorithm selection | [A] |
| Zhang, Frei, Bartlett | 2024 | JMLR 25(49):1–55 (from the Semantic Scholar record; JMLR page seen only in search) | Gradient-flow theory | Reaches the global minimum; competitive with the best linear predictor; brittle under covariate shift | One linear attention layer | — | [A] |

### 3c. ICL of AR processes, linear dynamical systems and Kalman filtering

| Paper | Year | Venue | Method / setting | Main finding (as read) | Limitation | Difference from this project | Read |
|---|---|---|---|---|---|---|---|
| Li, Ildiz, Papailiopoulos, Oymak | 2023 | ICML, PMLR 202:19565–19594 | Generalisation bounds incl. dynamical-system prompts | Near-optimal on i.i.d. and dynamic data | Bounds only | — | [A] |
| Sander, Giryes, Suzuki, Blondel, Peyré | 2024 | ICML, PMLR 235:43235–43254 | s_{t+1} = W s_t, orthogonal W | One linear layer = one GD step | Noiseless | No Bayes reference | [A] |
| Goel, Bartlett | 2024 | L4DC, PMLR 242:1502–1512 | Construction | A transformer can represent the Kalman filter | Known system | Representability only | [A] |
| Du, Balim, Oymak, Ozay | 2023 | IEEE Control Systems Letters 7:3525–3530 (Crossref; arXiv lists Balim first) | Train on many systems | Matches the Kalman filter for linear systems | Oracle KF reference | Not a Bayes posterior over systems | [A] |
| Akram, Vikalo | 2024–26 | TMLR (OpenReview) | Transformer state estimation | Close to the Kalman filter in linear-Gaussian settings; degrades gracefully without the transition matrix | MSE; oracle KF | — | [A] |
| Cole, Zhao, Lu, Zhang | 2025 | NeurIPS | Approximation theory | Log-depth error comparable to least squares; depth separation | L2; no Bayes reference | Nearest setting (noisy linear dynamics) | [A] |
| Zhou, Wang, Goel, Zhang | 2025 | arXiv | Linear self-attention (LSA) on AR(p) | LSA cannot beat classical linear models in expected MSE; recovers them as n→∞ | MSE | Same direction as our vanishing long-context gap | [A] |
| Zhang, Xing | 2026 | arXiv | Selective SSM on linear-Gaussian SSMs | Asymptotically Bayes-optimal | Asymptotic | — | [A] |
| Tang, Ildiz, Kurt, Oymak, Ozay | 2026 | CDC 2026 (arXiv comment) | SSM trained on a set of systems | Generalisation bounds | Oracle KF reference | — | [A] |

### 3d. Forecasting foundation models and simple baselines

| Paper | Year | Venue | Method / setting | Main finding (as read) | Limitation | Difference from this project | Read |
|---|---|---|---|---|---|---|---|
| Ansari et al. (Chronos) | 2024 | TMLR (OpenReview) | Tokenised language-model forecaster | Strong zero-shot results on 42 datasets | No Bayes reference | Candidate pretrained model to score against our references | [A] |
| Das, Kong, Sen, Zhou (TimesFM) | 2024 | ICML, PMLR 235:10148–10167 | Patched decoder | Zero-shot close to supervised SOTA | — | — | [A] |
| Rasul et al. (Lag-Llama) | 2023 | arXiv | Probabilistic decoder | Strong zero-shot | — | — | [A] |
| Woo et al. (Moirai) | 2024 | ICML, PMLR 235:53140–53164 | Trained on LOTSA | Competitive zero-shot | — | — | [A] |
| Dooley et al. (ForecastPFN) | 2023 | NeurIPS, vol 36, pp. 2403–2426 | PFN on synthetic series | Accurate zero-shot | Point forecasts | — | [A] |
| Hoo, Müller, Salinas, Hutter (TabPFN-TS) | 2025/26 | TMLR (OpenReview) | Tabular PFN for forecasting | Competitive univariate | — | — | [A] |
| Zeng, Chen, Zhang, Xu | 2023 | AAAI 37(9):11121–11128 | One-layer linear baselines | Beat transformer long-term forecasters | Real data | A simple estimator rivals a complex one | [A] |
| Tan, Merrill, Gupta, Althoff, Hartvigsen | 2024 | NeurIPS, vol 37, pp. 60162–60191 | Ablations of LLM forecasters | Removing the LLM does not hurt | — | — | [A] |
| Zhang, Gilpin | 2026 | ICLR | Context parroting baseline | Beats foundation models on dynamical systems | Point metrics | Context-only explanation of pretrained models | [A] |
| Aksu et al. (GIFT-Eval) | 2024 | arXiv (workshop venue UNVERIFIED) | Benchmark | 17 baselines incl. statistical models | — | — | [A] |
| Montero-Manso, Scharth | 2026 | arXiv | Decision-theoretic pretraining on simulated AR worlds | Beats MLE and AICc model selection | No Bayes PPD, no library, no seeds ([B]) | Closest forecasting paper | [A], [B] |
| Baron, Karpinski | 2025 | arXiv | Chronos vs ARIMA/Prophet | Chronos better at longer horizons | Single domain | Low relevance | [A] |

### 3e. Model discrimination and design; prior sensitivity; scoring rules

These rows are metadata-only (Crossref); findings are not stated because I did not read the papers here.

| Paper | Venue | Record (VERIFIED, Crossref) | Why it matters here |
|---|---|---|---|
| Box, Hill 1967, "Discrimination Among Mechanistic Models" | Technometrics 9(1):57–71 | DOI 10.1080/00401706.1967.10490441 | Classical model discrimination |
| Atkinson, Fedorov 1975, "The design of experiments for discriminating between two rival models" | Biometrika 62(1):57–70 | DOI 10.1093/biomet/62.1.57 | T-optimality |
| Atkinson, Fedorov 1975, "Optimal design: Experiments for discriminating between several models" | Biometrika 62(2):289–303 | DOI 10.1093/biomet/62.2.289 | Several-model case |
| López-Fidalgo, Tommasi, Trandafir 2007, "An Optimal Experimental Design Criterion for Discriminating Between Non-Normal Models" | JRSS B 69(2):231–242 | DOI 10.1111/j.1467-9868.2007.00586.x | KL-optimality, the nearest classical analogue of a δ-separability map |
| Chaloner, Verdinelli 1995, "Bayesian Experimental Design: A Review" | Statistical Science 10(3):273–304 | DOI 10.1214/ss/1177009939 | Bayesian design review |
| Rainforth, Foster, Ivanova, Bickford Smith 2024, "Modern Bayesian Experimental Design" | Statistical Science 39(1):100–114 | DOI 10.1214/23-STS915 | Modern design review |
| Clarke, Barron 1990, "Information-theoretic asymptotics of Bayes methods" | IEEE Trans. Inf. Theory 36(3):453–471 | DOI 10.1109/18.54897 | Cumulative Bayes risk and the prior's role |
| Clarke, Barron 1994, "Jeffreys' prior is asymptotically least favorable under entropy risk" | J. Stat. Plann. Inference 41(1):37–60 | DOI 10.1016/0378-3758(94)90153-8 | Same |
| Barron, Rissanen, Yu 1998, "The minimum description length principle in coding and modeling" | IEEE Trans. Inf. Theory 44(6):2743–2760 | DOI 10.1109/18.720554 | MDL / prequential view |
| Bernardo 1979, "Reference Posterior Distributions for Bayesian Inference" | JRSS B 41(2):113–128 | DOI 10.1111/j.2517-6161.1979.tb01066.x | Reference priors (the vague-prior comparator) |
| Gneiting, Raftery 2007, "Strictly Proper Scoring Rules, Prediction, and Estimation" | JASA 102(477):359–378 | DOI 10.1198/016214506000001437 | Log score as a proper score |

Whether these classical results give the paper's δ-separability map a closed form (for example, as an expected KL between predictives) is **UNVERIFIED** here. The papers would need to be read.

### 3f. Reproducibility and pre-registration

| Paper | Year | Venue | Main point (as read) | Read |
|---|---|---|---|---|
| Pineau, Vincent-Lamarre, Sinha, Larivière, Beygelzimer, d'Alché-Buc, Fox, Larochelle | 2021 | JMLR 22(164):1–20 (from Semantic Scholar plus the JMLR page seen only in search; arXiv comment "To appear at JMLR") | NeurIPS 2019 reproducibility program: code policy, challenge, checklist | [A] |
| Bouthillier et al. | 2021 | MLSys (Semantic Scholar only; arXiv says "Submitted to MLSys2021"; venue **UNVERIFIED**) | Variance from data sampling, initialisation and hyperparameters | [A] |
| Henderson, Islam, Bachman, Pineau, Precup, Meger | 2018 | AAAI 32(1) (Crossref, DOI 10.1609/aaai.v32i1.11694) | Variance makes deep RL results hard to interpret | [A] |
| Agarwal et al. | 2021 | NeurIPS | Interval estimates for few runs | [A] |
| Sellam et al. | 2022 | ICLR | Multi-Bootstrap over seeds × test items | [A] |
| Bertinetto et al. | 2021 | PMLR 148 | ML pre-registration workshop | [M], [B] |

---

## 4. The five closest works

1. **Raventós et al. 2023 (NeurIPS).**
   - *Better than this project:* trained networks show the finite-pool to ridge transition empirically, at scale, with released code. It became the field's reference result. This project's own neural pilot was not resolvable.
   - *This project does that they do not:* AR and state-space families with dependent contexts, unknown noise, observation noise (Kalman) and VAR. Full predictive log score instead of MSE; in their setting the population and context-only predictors coincide (both ridge), while here they are separate. A pre-training map of where the predictors differ by more than δ. Library vs continuous on held-out systems. Pre-registration.
2. **Wurgaft et al. 2025 (NeurIPS).**
   - *Better:* a quantitative model of which strategy a trained transformer uses throughout training, which the authors say "almost perfectly predicts" next-token behaviour.
   - *This project:* asks earlier, before any model, whether the memorising and generalising predictors differ at all in a given (n, family) cell. If they do not, a fit like theirs cannot tell them apart in that cell.
3. **Gibson, Cui & Reddy 2026 (arXiv).**
   - *Better:* a complete mechanistic account with explicit memorising and generalising Bayes predictors, a K sweep and phase boundaries.
   - *This project:* continuous-state linear-Gaussian families with exact, validated references (conjugate, quadrature and Kalman), δ thresholds, a pre-registered decision procedure, and a context-only third reference.
4. **Koshelev, Ponomarenko & Seleznev 2023 (arXiv/SSRN).**
   - *Better:* actually trains an amortised network on a Bayesian AR(1) prior, checks it against MCMC, and reports MSFE and log predictive score against a per-series AR(1) fit.
   - *This project:* adds a finite-library posterior, a separability map over n and families, seeds and power analysis, and pre-registration. Their AR(1) work is a toy proof of concept inside an agent-based-model paper.
5. **Wakayama & Suzuki 2026 (ICML).**
   - *Better:* non-asymptotic theory (Bayes Gap / Posterior Variance), with a result that task-mixture uncertainty vanishes exponentially fast in the number of in-context examples.
   - *This project:* measures empirically, with exact AR, Kalman and VAR references and a δ in nats, at which context lengths the prior still matters. That is the finite-n, dependent-data counterpart of their asymptotic claim.

Runners-up worth discussing in the paper:
- Cole et al. 2025: nearest setting, but L2 approximation theory with a least-squares reference.
- Montero-Manso & Scharth 2026: simulated AR worlds with decision-theoretic pretraining, but no Bayes predictive, no library and no seeds (per BIBLIOGRAPHY.md).
- Zhang & Gilpin 2026: a context-only predictor explains foundation models.
- Panwar et al. 2024: Bayesian prism with three kinds of predictors.
- Falck et al. 2024: the main premise challenge, though it assumes exchangeable data, which AR data is not.

---

## 5. New BibTeX for the most important missing works (VERIFIED only; source given as a comment on each entry)

```bibtex
@inproceedings{xie2022,  % OpenReview RdJVFCHjUMI "ICLR 2022 Poster"; arXiv 2111.02080
  author = {Xie, Sang Michael and Raghunathan, Aditi and Liang, Percy and Ma, Tengyu},
  title = {An Explanation of In-context Learning as Implicit {B}ayesian Inference},
  booktitle = {International Conference on Learning Representations (ICLR)}, year = {2022}}

@inproceedings{garg2022,  % NeurIPS proceedings BibTeX, hash c529dba08a146ea8d6cf715ae8930cbe
  author = {Garg, Shivam and Tsipras, Dimitris and Liang, Percy and Valiant, Gregory},
  title = {What Can Transformers Learn In-Context? {A} Case Study of Simple Function Classes},
  booktitle = {Advances in Neural Information Processing Systems}, volume = {35}, pages = {30583--30598},
  year = {2022}, doi = {10.52202/068431-2217}}

@inproceedings{akyurek2023,  % OpenReview 0g0X4H8yN4I "ICLR 2023 notable top 5%"; arXiv 2211.15661
  author = {Aky{\"u}rek, Ekin and Schuurmans, Dale and Andreas, Jacob and Ma, Tengyu and Zhou, Denny},
  title = {What learning algorithm is in-context learning? {I}nvestigations with linear models},
  booktitle = {International Conference on Learning Representations (ICLR)}, year = {2023}}

@inproceedings{vonoswald2023,  % proceedings.mlr.press/v202/von-oswald23a.html
  author = {von Oswald, Johannes and Niklasson, Eyvind and Randazzo, Ettore and Sacramento, Jo{\~a}o and Mordvintsev, Alexander and Zhmoginov, Andrey and Vladymyrov, Max},
  title = {Transformers Learn In-Context by Gradient Descent},
  booktitle = {Proceedings of the 40th International Conference on Machine Learning}, series = {PMLR},
  volume = {202}, pages = {35151--35174}, year = {2023}}

@inproceedings{bai2023,  % NeurIPS proceedings BibTeX, hash b2e63e36c57e153b9015fece2352a9f9
  author = {Bai, Yu and Chen, Fan and Wang, Huan and Xiong, Caiming and Mei, Song},
  title = {Transformers as Statisticians: Provable In-Context Learning with In-Context Algorithm Selection},
  booktitle = {Advances in Neural Information Processing Systems}, volume = {36}, pages = {57125--57211},
  year = {2023}, doi = {10.52202/075280-2498}}

@inproceedings{li2023algorithms,  % proceedings.mlr.press/v202/li23l.html
  author = {Li, Yingcong and Ildiz, M. Emrullah and Papailiopoulos, Dimitris and Oymak, Samet},
  title = {Transformers as Algorithms: Generalization and Stability in In-context Learning},
  booktitle = {Proceedings of the 40th International Conference on Machine Learning}, series = {PMLR},
  volume = {202}, pages = {19565--19594}, year = {2023}}

@inproceedings{sander2024,  % proceedings.mlr.press/v235/sander24a.html
  author = {Sander, Michael E. and Giryes, Raja and Suzuki, Taiji and Blondel, Mathieu and Peyr{\'e}, Gabriel},
  title = {How do Transformers Perform In-Context Autoregressive Learning?},
  booktitle = {Proceedings of the 41st International Conference on Machine Learning}, series = {PMLR},
  volume = {235}, pages = {43235--43254}, year = {2024}}

@inproceedings{goel2024kalman,  % proceedings.mlr.press/v242/goel24a.html
  author = {Goel, Gautam and Bartlett, Peter},
  title = {Can a Transformer Represent a {K}alman Filter?},
  booktitle = {Proceedings of the 6th Annual Learning for Dynamics \& Control Conference}, series = {PMLR},
  volume = {242}, pages = {1502--1512}, year = {2024}}

@article{du2023filtering,  % api.crossref.org/works/10.1109/LCSYS.2023.3335318 (journal order: Du first)
  author = {Du, Zhe and Balim, Haldun and Oymak, Samet and Ozay, Necmiye},
  title = {Can Transformers Learn Optimal Filtering for Unknown Systems?},
  journal = {IEEE Control Systems Letters}, volume = {7}, pages = {3525--3530}, year = {2023},
  doi = {10.1109/LCSYS.2023.3335318}}

@article{akram2026,  % OpenReview hIMK5MvGkP "Accepted by TMLR"; year (03/2026) from the PDF header per BIBLIOGRAPHY.md; arXiv 2410.16546
  author = {Akram, Usman and Vikalo, Haris},
  title = {Transformers as Implicit State Estimators: In-Context Learning in Dynamical Systems},
  journal = {Transactions on Machine Learning Research}, year = {2026}}

@inproceedings{falck2024,  % proceedings.mlr.press/v235/falck24a.html
  author = {Falck, Fabian and Wang, Ziyu and Holmes, Christopher C.},
  title = {Is In-Context Learning in Large Language Models {B}ayesian? {A} Martingale Perspective},
  booktitle = {Proceedings of the 41st International Conference on Machine Learning}, series = {PMLR},
  volume = {235}, pages = {12784--12805}, year = {2024}}

@inproceedings{jeon2024,  % proceedings.mlr.press/v235/jeon24a.html
  author = {Jeon, Hong Jun and Lee, Jason D. and Lei, Qi and Van Roy, Benjamin},
  title = {An Information-Theoretic Analysis of In-Context Learning},
  booktitle = {Proceedings of the 41st International Conference on Machine Learning}, series = {PMLR},
  volume = {235}, pages = {21522--21554}, year = {2024}}

@inproceedings{nguyen2025,  % OpenReview INyi7qUdjZ "ICLR 2025 Spotlight"; arXiv 2412.00104
  author = {Nguyen, Alex and Reddy, Gautam},
  title = {Differential learning kinetics govern the transition from memorization to generalization during in-context learning},
  booktitle = {International Conference on Learning Representations (ICLR)}, year = {2025}}

@inproceedings{goddard2025,  % arXiv 2506.05574 journal-ref
  author = {Goddard, Chase and Smith, Lindsay M. and Ngampruetikorn, Vudtiwat and Schwab, David J.},
  title = {When can in-context learning generalize out of task distribution?},
  booktitle = {Proceedings of the 42nd International Conference on Machine Learning}, series = {PMLR},
  volume = {267}, pages = {19585--19599}, year = {2025}}

@inproceedings{ansari2024chronos_note, % NOTE: Chronos is in TMLR (OpenReview gerNCVqqtR); TMLR has no volume or pages; year 2024 comes from Semantic Scholar's DBLP key (secondary)
  author = {Ansari, Abdul Fatir and Stella, Lorenzo and Turkmen, Caner and Zhang, Xiyuan and Mercado, Pedro and Shen, Huibin and Shchur, Oleksandr and Rangapuram, Syama Sundar and Pineda Arango, Sebastian and Kapoor, Shubham and Zschiegner, Jasper and Maddix, Danielle C. and Wang, Hao and Mahoney, Michael W. and Torkkola, Kari and Wilson, Andrew Gordon and Bohlke-Schneider, Michael and Wang, Yuyang},
  title = {Chronos: Learning the Language of Time Series},
  booktitle = {Transactions on Machine Learning Research}, year = {2024}}
% Use @article{..., journal={Transactions on Machine Learning Research}} in the final bib.

@inproceedings{das2024timesfm,  % proceedings.mlr.press/v235/das24c.html
  author = {Das, Abhimanyu and Kong, Weihao and Sen, Rajat and Zhou, Yichen},
  title = {A decoder-only foundation model for time-series forecasting},
  booktitle = {Proceedings of the 41st International Conference on Machine Learning}, series = {PMLR},
  volume = {235}, pages = {10148--10167}, year = {2024}}

@inproceedings{woo2024moirai,  % proceedings.mlr.press/v235/woo24a.html
  author = {Woo, Gerald and Liu, Chenghao and Kumar, Akshat and Xiong, Caiming and Savarese, Silvio and Sahoo, Doyen},
  title = {Unified Training of Universal Time Series Forecasting Transformers},
  booktitle = {Proceedings of the 41st International Conference on Machine Learning}, series = {PMLR},
  volume = {235}, pages = {53140--53164}, year = {2024}}

@inproceedings{dooley2023forecastpfn,  % NeurIPS proceedings BibTeX, hash 0731f0e65559059eb9cd9d6f44ce2dd8
  author = {Dooley, Samuel and Khurana, Gurnoor Singh and Mohapatra, Chirag and Naidu, Siddartha V. and White, Colin},
  title = {{ForecastPFN}: Synthetically-Trained Zero-Shot Forecasting},
  booktitle = {Advances in Neural Information Processing Systems}, volume = {36}, pages = {2403--2426},
  year = {2023}, doi = {10.52202/075280-0112}}

@inproceedings{tan2024lms,  % NeurIPS proceedings BibTeX, hash 6ed5bf446f59e2c6646d23058c86424b
  author = {Tan, Mingtian and Merrill, Mike A. and Gupta, Vinayak and Althoff, Tim and Hartvigsen, Thomas},
  title = {Are Language Models Actually Useful for Time Series Forecasting?},
  booktitle = {Advances in Neural Information Processing Systems}, volume = {37}, pages = {60162--60191},
  year = {2024}, doi = {10.52202/079017-1922}}

@article{zeng2023,  % Crossref 10.1609/aaai.v37i9.26317
  author = {Zeng, Ailing and Chen, Muxi and Zhang, Lei and Xu, Qiang},
  title = {Are Transformers Effective for Time Series Forecasting?},
  journal = {Proceedings of the AAAI Conference on Artificial Intelligence}, volume = {37}, number = {9},
  pages = {11121--11128}, year = {2023}, doi = {10.1609/aaai.v37i9.26317}}

@article{boxhill1967,  % Crossref
  author = {Box, G. E. P. and Hill, W. J.}, title = {Discrimination Among Mechanistic Models},
  journal = {Technometrics}, volume = {9}, number = {1}, pages = {57--71}, year = {1967},
  doi = {10.1080/00401706.1967.10490441}}

@article{atkinson1975,  % Crossref
  author = {Atkinson, A. C. and Fedorov, V. V.},
  title = {The design of experiments for discriminating between two rival models},
  journal = {Biometrika}, volume = {62}, number = {1}, pages = {57--70}, year = {1975}, doi = {10.1093/biomet/62.1.57}}

@article{lopezfidalgo2007,  % Crossref
  author = {L{\'o}pez-Fidalgo, J. and Tommasi, C. and Trandafir, P. C.},
  title = {An Optimal Experimental Design Criterion for Discriminating Between Non-Normal Models},
  journal = {Journal of the Royal Statistical Society Series B: Statistical Methodology}, volume = {69}, number = {2},
  pages = {231--242}, year = {2007}, doi = {10.1111/j.1467-9868.2007.00586.x}}

@article{chaloner1995,  % Crossref
  author = {Chaloner, Kathryn and Verdinelli, Isabella}, title = {Bayesian Experimental Design: A Review},
  journal = {Statistical Science}, volume = {10}, number = {3}, pages = {273--304}, year = {1995}, doi = {10.1214/ss/1177009939}}

@article{rainforth2024,  % Crossref
  author = {Rainforth, Tom and Foster, Adam and Ivanova, Desi R. and Bickford Smith, Freddie},
  title = {Modern {B}ayesian Experimental Design}, journal = {Statistical Science}, volume = {39}, number = {1},
  pages = {100--114}, year = {2024}, doi = {10.1214/23-STS915}}

@article{clarke1990,  % Crossref
  author = {Clarke, Bertrand S. and Barron, Andrew R.}, title = {Information-theoretic asymptotics of {B}ayes methods},
  journal = {IEEE Transactions on Information Theory}, volume = {36}, number = {3}, pages = {453--471}, year = {1990},
  doi = {10.1109/18.54897}}

@article{clarke1994,  % Crossref
  author = {Clarke, Bertrand S. and Barron, Andrew R.},
  title = {Jeffreys' prior is asymptotically least favorable under entropy risk},
  journal = {Journal of Statistical Planning and Inference}, volume = {41}, number = {1}, pages = {37--60}, year = {1994},
  doi = {10.1016/0378-3758(94)90153-8}}

@article{barron1998mdl,  % Crossref (third author recorded as "Bin Yu")
  author = {Barron, Andrew and Rissanen, Jorma and Yu, Bin},
  title = {The minimum description length principle in coding and modeling},
  journal = {IEEE Transactions on Information Theory}, volume = {44}, number = {6}, pages = {2743--2760}, year = {1998},
  doi = {10.1109/18.720554}}
% Rissanen's given name "Jorma" is NOT in the Crossref record (it has only "J."). Use "J." unless checked elsewhere.

@article{bernardo1979,  % Crossref
  author = {Bernardo, Jos{\'e} M.}, title = {Reference Posterior Distributions for {B}ayesian Inference},
  journal = {Journal of the Royal Statistical Society Series B: Statistical Methodology}, volume = {41}, number = {2},
  pages = {113--128}, year = {1979}, doi = {10.1111/j.2517-6161.1979.tb01066.x}}

@article{gneiting2007scoring,  % Crossref
  author = {Gneiting, Tilmann and Raftery, Adrian E.}, title = {Strictly Proper Scoring Rules, Prediction, and Estimation},
  journal = {Journal of the American Statistical Association}, volume = {102}, number = {477}, pages = {359--378},
  year = {2007}, doi = {10.1198/016214506000001437}}

@inproceedings{henderson2018,  % Crossref DOI; pages 3207-3214 from Semantic Scholar only
  author = {Henderson, Peter and Islam, Riashat and Bachman, Philip and Pineau, Joelle and Precup, Doina and Meger, David},
  title = {Deep Reinforcement Learning That Matters},
  booktitle = {Proceedings of the AAAI Conference on Artificial Intelligence}, volume = {32}, number = {1}, year = {2018},
  doi = {10.1609/aaai.v32i1.11694}}

@article{pineau2021,  % arXiv 2003.12206 ("To appear at JMLR"); vol 22, no 164, pp. 1-20 from Semantic Scholar + JMLR page seen in search, not fetched
  author = {Pineau, Joelle and Vincent-Lamarre, Philippe and Sinha, Koustuv and Larivi{\`e}re, Vincent and Beygelzimer, Alina and d'Alch{\'e}-Buc, Florence and Fox, Emily and Larochelle, Hugo},
  title = {Improving Reproducibility in Machine Learning Research (A Report from the {NeurIPS} 2019 Reproducibility Program)},
  journal = {Journal of Machine Learning Research}, volume = {22}, number = {164}, pages = {1--20}, year = {2021}}
```

### Fix before use

1. In `barron1998mdl`, Crossref gives Rissanen only as "J.". I wrote "Jorma" from memory, which breaks the no-memory rule: change it to "J." or verify it.
2. In `ansari2024chronos_note`, change the entry type to `@article` with `journal = {Transactions on Machine Learning Research}`.

### Not added (arXiv-only or venue not verified; cite as preprints if wanted)

- Chlon et al. 2025 (2507.11768)
- Carroll et al. 2025 (2501.17745)
- Letey et al. 2025 (2509.26551)
- Kwon et al. 2026 (2606.06814)
- Aswadi, Britton, Baker, Farrugia-Roberts 2026 (2605.18281; ICML 2026 FoGen workshop poster per OpenReview tkZDIomP4W)
- Zhou, Wang, Goel, Zhang 2025 (2510.09776)
- Zhang & Xing 2026 (2602.17744)
- GIFT-Eval (2410.10393)
- Lag-Llama (2310.08278)
- Bouthillier et al. 2021 (MLSys venue appears only in Semantic Scholar)
