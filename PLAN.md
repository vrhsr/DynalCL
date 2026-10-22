# PLAN — Stage 0: trustworthy reference-predictor foundation

Status labels used throughout: DERIVED (see docs/MATH.md), TESTED (named test), ASSUMED, UNVERIFIED.

## 1. Workspace findings (Task 1)

| Item | Finding |
|---|---|
| Repository | `E:\study-buddy\DynaICL` was **empty**. Not a git repository. |
| Python | CPython 3.13.5 (Windows 11, 8 logical cores) |
| Installed | numpy 2.2.2, scipy 1.15.1, pytest 9.0.2, pyyaml 6.0.2 (also jsonschema, pandas, matplotlib, **not used**) |
| Existing code/tests | none, so nothing to preserve |

Consequences:
- No dependencies are added beyond the default stack (numpy, scipy, pytest, pyyaml). The YAML schema is
  implemented as strict, typed dataclasses, so `jsonschema` is not needed.
- **Provenance:** with no git repository, `git commit` and `dirty` cannot be recorded. The provenance module
  records `{"available": false, "reason": ...}` instead of failing. I am **not** running `git init`
  or creating commits without being asked. Recommended action for you: `git init` and commit, so later runs
  record a real commit hash.

## 2. Assumptions (all ASSUMED unless stated)

1. Likelihoods are conditional on x_0. x_0 is drawn independently of `a` (x_0 ~ N(m0, s0^2), config-fixed;
   s0 = 0 means a fixed value). Contexts **always start at the trajectory's x_0**. A context cut from the
   middle of a trajectory would have a first state that depends on `a`, which would invalidate the
   conditional-likelihood posterior. This is enforced in code.
2. Under P-GAUSS and P-STABLE, sigma is known and shared by all systems. It is part of the system
   distribution's fingerprint.
3. Package layout: everything lives under the `dynaicl/` package (`dynaicl/systems`, `dynaicl/references`, ...),
   with YAML in top-level `config/`. This avoids top-level module names such as `metrics` and `config` colliding
   with other installed packages. The deviation from the suggested layout is recorded in docs/DECISIONS.md.
4. "Flat-prior Bayes (known sigma)" is given the true sigma as a config hyperparameter, which is information about
   the population. Each predictor is flagged `uses_true_noise_scale`, and I report two frontiers: one over all
   members, and a strict one that excludes sigma-informed members.
5. Library atoms are built from a `library_systems` stream. Their training trajectories are simulated from a
   separate `library_noise` stream, so leakage tests have real training trajectories to compare against.
6. P-STABLE for the experiment: truncated normal, mu0 = 0.4, tau0 = 0.3, on (-0.95, 0.95). I chose this before
   seeing any result and record it in the pre-registration. Both the uniform and truncated-normal shapes
   are implemented and tested.
7. P-NIG: implemented for h = 1 only, as specified. h > 1 raises `NotImplementedError` and is listed as future work.

## 3. Spec issues found while re-deriving (details in docs/MATH.md)

- **P-STABLE is conjugate in a precise sense.** Truncated-normal (or uniform) prior × Gaussian-in-`a`
  conditional likelihood gives a truncated-normal posterior. The h = 1 predictive *density* is closed form
  (a Gaussian times a ratio of normal-CDF differences). Quadrature remains the primary implementation as
  specified. The closed form becomes an independent test oracle.
- NIG `beta_n`: the spec's form `S_yy + lambda0 mu0^2 - lambda_n mu_n^2` is algebraically correct but can lose
  all precision to cancellation. I implement the equivalent non-negative form
  `RSS(mu_n) + lambda0 (mu_n - mu0)^2` and test that it matches the spec form where the spec form is well conditioned.
- Coverage is computed from the PIT (y is inside the central c-interval iff |F(y) - 1/2| <= c/2, for continuous F),
  so no quantile root-finding is needed.

## 4. File list

```
PLAN.md  README.md  pyproject.toml  requirements.txt
config/                      YAML: separability_pilot.yaml, separability.yaml, smoke.yaml
dynaicl/
  rng.py                     NamedStreams: name-keyed SeedSequence streams, per-item children
  provenance.py              runs/<run_id>/: config, hash, git, versions, platform, seeds, timestamps, checksums
  config/schema.py           strict typed schema + loader + canonical hash
  systems/ar1.py             simulator, transition pairs, sufficient statistics, horizon variance (sum form)
  systems/priors.py          GaussianCoefficientPrior, NormalInverseGammaPrior, StableCoefficientPrior
  systems/context.py         ContextWindow (immutable, float64-only), GroundTruth (evaluator-private)
  systems/library.py         SystemLibrary (atoms, weights, fingerprint)
  systems/conditions.py      EvaluationCondition: ContinuousPriorCondition (E-CONT), LibraryCondition (E-LIB)
  systems/splits.py          DataSplit with role tags, overlap / disjointness assertions
  references/predictive.py   Gaussian, StudentT, GaussianMixture, QuadratureMixture, Empirical, PointForecast
  references/base.py         Predictor base with interface enforcement and information-access declaration
  references/conjugate.py    ConjugateGaussianAr1Predictor, NormalInverseGammaAr1Predictor
  references/quadrature.py   CoefficientPosteriorQuadrature, StablePriorQuadraturePredictor
  references/library.py      FiniteLibraryPredictor
  references/known.py        KnownSystemPredictor (oracle, used only in tests)
  references/matched.py      continuous_prior_predictor, matched_reference_for, MatchedBayesReference guard
  baselines/                 flat_prior.py, ols.py, kernel.py, persistence.py, family.py (+ frontier)
  metrics/scoring.py         log score, CRPS (Gaussian closed form, numerical, mixture closed form), PIT, paired diffs
  metrics/calibration.py     uniformity tests, SBC ranks, binomial coverage tests, Bonferroni
  evaluation/harness.py      item generation, private ground truth, scoring, guarded optimality diagnostics
  validation/                brute_force.py (test-only grid oracle), checks.py, mutations.py
  experiments/separability.py  the separability map (CLI)
scripts/mutation_report.py   runs every check and the full pytest suite under each mutation, prints the matrix
tests/                       test_a ... test_k + config/provenance tests
docs/MATH.md  docs/DECISIONS.md  docs/RISKS.md  docs/PREREG_separability.md
```

## 5. Order of work

1. Core math modules (systems, references), then the Predictive interface.
2. Brute-force oracle and validation checks A, B, C, D. Fix the references until green.
3. Calibration (E), optimality (F), mutations (G), numerics (H), reproducibility (I), leakage (J), kernel schemes (K).
4. Config, provenance, harness, experiment. Pilot first, then fill in and freeze the pre-registration, then the main run.
5. Docs, README, and the final report. **No reference output is used as ground truth until A, B, E, G are green.**

## 6. Risks identified up front

| Risk | Mitigation |
|---|---|
| Quadrature under-resolves narrow posteriors, or integrands that are sharp in `a` (large h, abs(a) near 1, large x_n) | Window derived from the exact Gaussian-in-a log-likelihood. Composite Gauss-Legendre. Node-doubling error estimate recorded per run. |
| Quadrature predictive logpdf in far tails (dominant `a` outside the posterior window) | Documented limitation. Convergence tested at realistic targets plus a tail probe. |
| Catastrophic cancellation in sufficient statistics (explosive trajectories) | Direct residual sums for library and NIG `beta_n`. Completed-square log-likelihood. |
| Statistical tests flaky or underpowered | Fixed seeds, Bonferroni across the family, tolerances derived from MC SE. Power is checked by the mutation tests. |
| Runtime of the experiment | Coverage from PIT, vectorised kernel CV, scipy.special instead of scipy.stats, process pool over cells (results do not depend on the worker count). |
| No git, so incomplete provenance | Recorded explicitly as unavailable, and flagged in the report. |

## 7. Outcome (end of session, 2026-10-09)

The plan was executed in order. Departures and findings, all recorded in docs/DECISIONS.md:
- Quadrature needed integrand-adaptive panels (D-08). The first version was found inadequate by A3, the
  second by the independent audit. Fixed, and the audit's regimes were added to A3.
- The kernel's bandwidth scale had to be computed causally per validation row (D-09), found while writing J4.
- scipy's truncnorm moments were inaccurate in deep tails, so that oracle got a floor (D-07).
- Timing data moved out of results/ for bitwise reproducibility (D-16).
- The full mutation matrix exceeds the local 10-minute compute budget, so it was packaged as
  `scripts/remote_validation_pipeline.sh` for the user's remote machine.

Current status, results and next steps: **CLAUDE.md** (sections 2, 7, 8).
