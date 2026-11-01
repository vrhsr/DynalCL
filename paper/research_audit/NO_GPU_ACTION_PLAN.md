# No-GPU action plan (Phase 6; highest priority)

Everything below runs without a GPU. "Box" = over about 10 minutes, relayed to the user's Linux box as a CPU batch (at most 16
workers, tmux, one waiter, small result files on a new `results-*` branch). Scores 1-5 (5 = best / cheapest / lowest risk).

| Rank | Action | Sci. value | Pub. impact | Cost | Time | Risk | Box? | Notes |
|---|---|---|---|---|---|---|---|---|
| 1 | **Theory section**: KL-budget conservation (pop vs ctx) and nearest-atom limit (library), with a pinned script whose output feeds claims.yaml; overlay on the maps (Figure A/B/C) | 5 | 5 | 5 | 1-2 days | 4 | No | Converts the main rejection argument (findings predictable) into the contribution; the 1A map agrees with the budget to about 3% |
| 2 | **Noise-matched comparator maps** (F1 ctx knows sigma; F2 ctx knows Sigma) + F2 comparator sweep | 5 | 5 | 3 | spec 0.5 day; box run hours | 3 | Yes | Decides whether the F1/F2 "wider window" claims survive; affects the neural plan |
| 3 | Receive and verify batch 4; put it in the paper | 4 | 4 | 5 | hours after return | 4 | (relayed) | AB11 is false until this lands |
| 4 | Figures from pinned files (gap vs n with bands; library share vs K with prediction; cumulative gap vs budget) via a `make_figures.py` writing pgfplots data | 4 | 5 | 4 | 1 day | 5 | No | The paper has no figure |
| 5 | Wording fixes (claims class D): "identifiable" -> "separable at margin delta" (title only with approval); "worth X nats" scoped; "memorisation is visible" -> "the library reference is distinguishable"; F2 range at n = 20; tab_delta ordering sentence; "every number is a macro" (words bypass the audit); F2 context-only prior stated in Sec. 3; "four-coefficient" -> seven parameters | 3 | 4 | 5 | hours | 5 | No | Low-risk edits (Phase 9 permits after approval of the plan) |
| 6 | Numbers audit hardening: flag number words (sixteen, sixty-four, eight, ...) and add macros/claims for them; add a 1A macro for the delta = 0.01 window (fix \FoneMaxN misuse) | 3 | 3 | 5 | hours | 5 | No | Pipeline integrity |
| 7 | Expected wrong marks + Holm-adjusted Table 1 (closes 1A spec deviation; disclosure entry) | 3 | 3 | 5 | hours | 5 | No | From existing files |
| 8 | Literature: Box-Hill / T-optimality / KL-optimality; Clarke-Barron; Garg, Xie, Akyurek, von Oswald, Bai; Kalman/LDS ICL (Goel-Bartlett, Balim et al., Li et al., Sander et al.); Kirsch et al., Nguyen-Reddy, Park et al.; fix the Wurgaft miscitation; full author names | 3 | 4 | 4 | 1 day | 4 | No | Verified entries from the literature agent's report |
| 9 | Dense n grids and F2 library at K = 256/1024, n = 40 | 4 | 3 | 3 | spec + box run | 3 | Yes | Removes grid censoring; tests the F2 prediction |
| 10 | Restructure: one map protocol in the body; Stage 0/0.5/0.6/pilot history to an appendix; pre-registration machinery shortened to a reproducibility section + artefact | 3 | 4 | 4 | 1-2 days | 3 | No | Reviewers 1 and 3: reads as a project log |
| 11 | Cumulative / pooled discrimination view for F3 and Stage 0.6 (descriptive from existing files) | 3 | 3 | 4 | hours | 4 | No | Reframes "noise shrinks it" correctly |
| 12 | Bridge to Raventos et al. linear regression (reference-only map in their setting) | 4 | 4 | 2 | days | 3 | Maybe | Strong "interest" argument; new code |
| 13 | Anonymised artefact for double-blind review (TMLR), code/data DOI at camera-ready; LLM-use and author-contribution statements | 2 | 4 | 4 | hours | 5 | No | The public repo `vrhsr/DynalCL` and box paths identify the authors |
| 14 | Verify pre-registration hashes against the stored manifests in the paper build (a claims entry per freeze) | 2 | 2 | 5 | hours | 5 | No | Strengthens the methodology claim |

Not recommended: re-analysing the Stage 0.6 confirmatory data (forbidden by its own rules); opening pilot evaluation files;
any change to frozen decision rules.

Suggested order: 5, 6, 7 (no compute, low risk) in parallel with writing specs for 2 and 9 (one box batch 5); then 1 and 4 once
batch 4 and batch 5 return; then 8, 10, 13; 12 only if the user wants the stronger venue path.
