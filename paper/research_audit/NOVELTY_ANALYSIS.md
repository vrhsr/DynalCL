# Novelty analysis (Phase 2)

Sources: LITERATURE_REVIEW.md (verified records), the three independent reviews (INDEPENDENT_REVIEW.md), and this audit's
derivations (STATISTICAL_AUDIT.md section 6). My judgement is labelled as such.

## The seven questions

**1. Closest five works.** Raventos et al. 2023 (NeurIPS); Wurgaft et al. 2025 (NeurIPS); Gibson, Cui, Reddy 2026 (arXiv);
Wakayama and Suzuki 2026 (ICML); Koshelev et al. 2023 (arXiv/SSRN). Runners-up: Panwar et al. 2024, Cole et al. 2025,
Du/Balim et al. 2023, Falck et al. 2024 (premise challenge), and, on the method side, classical model-discrimination design
(Box and Hill 1967; Atkinson and Fedorov 1975; Lopez-Fidalgo et al. 2007 KL-optimality) and Clarke and Barron 1990.

**2. What they do better.** They have trained networks and an empirical transition (Raventos, Gibson, Wurgaft), a predictive model
of the strategy a network uses (Wurgaft), non-asymptotic theory (Wakayama), or the classical theory that makes a separability
question answerable in closed form (Box-Hill, KL-optimal design, Clarke-Barron). Our paper has none of these.

**3. What we do better.** Exact, validated Bayes references for dependent (AR / state-space / VAR) data with measured numerical
error and mutation tests; a context-only reference that is itself Bayes (in regression, ridge is both population and
context-only predictor, so the population-specific part cannot be isolated there); a library reference evaluated on held-out
systems; full predictive log score; a pre-training separability map; pre-registered nulls. The literature search found no
pre-registered ICL study and no VAR-specific Bayes-reference ICL study (VERIFIED as "not found", search-based, not proof).

**4. Strongest defensible claim (my judgement).** "For in-context forecasting of linear-Gaussian autoregressive systems, whether
population Bayes, a finite-library posterior and a context-only Bayes predictor can be told apart is governed by two computable
quantities: the prior KL budget, spent over the context at a rate set by the Fisher information (so the per-forecast window is
short and closes earlier at large initial-state scale and later under observation noise), and the nearest-atom KL of the
library, which falls like K^(-2/p) in the number p of system parameters (so libraries stay distinguishable far longer in the
bivariate family). Validated maps over four families confirm both predictions numerically." This requires adding the theory
section and the noise-matched comparator runs (NO_GPU_ACTION_PLAN items 1-2); the 1A map already agrees with the budget to
about 3%.

**5. Weakest claims.** (a) "The window widens when the noise scale is unknown / in the bivariate family" (comparator-driven).
(b) "Observation noise shrinks population knowledge" (the budget is conserved; per-forecast gaps shrink). (c) The pre-registration
machinery as a scientific contribution (it is good practice; precedent exists). (d) The pilot as a contribution (an operational
outcome, honestly reported).

**6. A differentiating experiment.** Before any GPU work: predict, from the two closed-form quantities alone, the separability
windows of a family not yet mapped (e.g. VAR(1) with d = 3, or the d-dimensional Gaussian regression of Raventos et al.), then
run the map and test the prediction. With GPU: the F1 or F2 memorisation transition (GPU_EXPERIMENT_ROADMAP P0/P1), where the
references predict whether K* is observable by score at all.

**7. An overlooked method.** Classical KL-optimal / T-optimal design for model discrimination: the map is a design-space plot of
the expected KL between rival predictives, which that literature optimises over designs. Using it gives (i) vocabulary
("discriminability" instead of "identifiability"), (ii) a principled pooled criterion (cumulative KL over a sequence, which is
what the Stage 0 delta justification already appeals to), and (iii) credit to prior art. Also overlooked: Bernardo reference
priors / Jeffreys priors as the canonical "context-only" comparator (they remove the arbitrary scale-prior width that drives the
F1/F2 gaps; Clarke and Barron 1994 show Jeffreys is asymptotically least favourable under entropy risk, which makes it the
natural minimax context-only reference).

## Verdict (my judgement)

As written, novelty is real but narrow, and the headline patterns are predictable from classical information theory, which the
paper neither derives nor cites; all three reviewers converge on this. Reframed around the two closed-form quantities, with the
maps as their validation and noise-matched comparators, the paper has a defensible methodological contribution for TMLR ("a
predictive account of when Bayes references for in-context learners are distinguishable, validated in four families"). A
main-track contribution still needs a neural result that the account predicts in advance.
