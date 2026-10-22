# DynaICL Stage 0: validated reference predictors for scalar AR(1)

Reference machinery that later in-context-learning experiments will treat as ground truth: Bayes
predictors that are matched to each evaluation condition, comparison predictors, context-only
baselines, scoring, and a validation suite. CPU only, no training.

**Passing these tests establishes neither novelty nor publishability.** It establishes that the
references compute what docs/MATH.md says they compute, to stated numerical and statistical
tolerances.

## Setup

```bash
python -m pip install -r requirements.txt     # numpy, scipy, pyyaml, pytest (float64 throughout)
```

Python >= 3.11. The suite was run with Python 3.13.5, numpy 2.2.2, scipy 1.15.1 and pytest 9.0.2 on Windows 11.

## Mathematical assumptions (details and derivations in docs/MATH.md)

* x_t = a x_{t-1} + sigma eps_t. All likelihoods are **conditional on x_0**, and x_0 is drawn
  **independently of a**. The exact stationary likelihood has an a-dependent x_0 term that breaks
  conjugacy, so it is not used.
* Contexts always start at the trajectory's x_0. A context cut from mid-trajectory would make the
  conditional-likelihood posterior inexact (MATH 1.2).
* Priors: P-GAUSS (a ~ N(mu0, tau0^2), sigma known, untruncated); P-NIG (normal-inverse-gamma);
  P-STABLE (uniform or truncated normal on (-rho, rho), sigma known).
* The matched Bayes reference for a condition uses exactly that condition's prior and likelihood
  (guarded by fingerprints). Every other predictor's mismatch is measured, not forbidden.

## Exactness table

| Predictor | Prior | Horizon | Status (Section 0 terminology) | Conditions |
|---|---|---|---|---|
| Conjugate Gaussian | P-GAUSS | h = 1 | ANALYTICALLY EXACT (float64) | sigma known; x_0 ⫫ a |
| Conjugate Gaussian | P-GAUSS | h > 1 | NUMERICALLY APPROXIMATED with verified convergence: composite Gauss-Legendre over N(m_n, v_n), 128 nodes by default, more when the integrand needs them (MATH 5.2). Measured node-doubling error <= 1.7e-13 nats in the hardest regimes tested (h = 50, a ≈ 0.99, x_n = 10; wide posteriors with x_0/sigma up to 400). | window = posterior mass to e^-40 |
| Normal-inverse-gamma | P-NIG | h = 1 | ANALYTICALLY EXACT (Student-t) | cancellation-free beta_n (MATH 3.1) |
| Normal-inverse-gamma | P-NIG | h > 1 | not implemented (raises) | future work |
| Quadrature posterior | P-STABLE | any h | NUMERICALLY APPROXIMATED with verified convergence (same rule). Agrees with the closed-form truncated-normal posterior and the h = 1 predictive density (MATH 4.3) to within 10x the measured error + 1e-11. | the posterior is closed form (a spec correction, MATH 4.1); quadrature kept as primary |
| Finite library | discrete | any h | ANALYTICALLY EXACT given the library (log-space weights) | atoms and weights from the training stream only |
| Flat-prior Bayes (baseline) | improper flat | h = 1 / h > 1 | ANALYTICALLY EXACT / NUMERICALLY APPROXIMATED (as P-GAUSS) | proper fallback prior when S_xx = 0 (flagged) |
| Brute-force grid (tests only) | any | any | NUMERICALLY APPROXIMATED; raw likelihood, trapezoid rule; error measured by refinement and range widening | independent oracle |

## Running the tests

```bash
python -m pytest -q                       # everything (several minutes on a laptop CPU)
python -m pytest -q -m "not slow"         # skips the large optimality check (F)
python scripts/mutation_report.py         # mutation-detection matrix: every check under every injected bug
python scripts/mutation_report.py --pytest   # also runs the whole pytest suite under each mutation
DYNAICL_MUTATION=off_by_one_likelihood python -m pytest -q   # one mutation, whole suite
```

The test files map to Section 5: `test_a_*` algebra vs independent checks, `test_b_*` Monte Carlo,
`test_c_*` identities, `test_d_*` known-parameter behaviour, `test_e_*` calibration of the matched reference,
`test_f_*` optimality, `test_g_*` mutations, `test_h_*` numerics, `test_i_*` reproducibility,
`test_j_*` leakage, and `test_k_*` kernel validation schemes. The check logic lives in
`dynaicl/validation/checks.py`, so tests and the mutation runner execute identical code.

## Long jobs: remote pipeline

Jobs that take more than about 10 minutes are packaged to run on a remote machine. All of Stage 0 is CPU
only. The full mutation-detection matrix (every check, and the whole suite, under every injected bug) is
such a job:

```bash
bash scripts/remote_validation_pipeline.sh                      # JOBS=6; RUN_EXPERIMENT=1 also reruns the experiment
```

It writes `remote_results_<UTC>.tar.gz` (environment, baseline pytest output and junit, the mutation
matrix in `matrix.md`/`matrix.json`, and optionally the experiment run directory).

**Google Colab:** run `python scripts/build_colab_bundle.py`. It writes `dist/dynaicl_stage0_bundle.zip` and
`colab/DynaICL_Stage0_Colab.ipynb`. Upload the notebook to Colab (CPU runtime; no GPU needed), choose
`Runtime -> Run all`, and upload the zip when prompted. The notebook verifies the bundle, installs the pinned
stack, smoke-tests, runs the pipeline, and saves the archive to Drive and as a download. Rebuild the bundle after any
code change.

## Minimal experiment: reference separability map

```bash
python -m dynaicl.experiments.separability --config config/smoke.yaml --workers 1       # ~10 s smoke run
python -m dynaicl.experiments.separability --config config/separability_pilot.yaml --workers 8
python -m dynaicl.experiments.separability --config config/separability.yaml --workers 8
```

Each run writes `runs/<run_id>/`: `config.yaml`, `config_hash.txt`, `provenance.json` (git state,
package versions, platform, per-stream seeds, timestamps, runtime), `checksums.json` (SHA-256 of every
output), and `results/` (`report.md`, `summary.json`, `predictors.csv`, `paired_differences.csv`,
`g_metric.csv`, `t1_optimality.csv`, `t2_calibration.csv`, `t3_identities.csv`, `frontier_selection.json`,
`item_log_scores.npy` + index). Results are bitwise reproducible for a given config and seed,
independent of `--workers` (TESTED). The design is pre-registered in `docs/PREREG_separability.md`.

## Adding a new predictor

1. Subclass `dynaicl.references.base.Predictor`. Set `self.description = PredictorDescription(...)`,
   declaring `assumed_system_distribution` (a prior or library fingerprint, or `None` for context-only),
   `may_access` / `must_not_access`, and `uses_true_noise_scale`.
2. Implement `_predict(self, context: ContextWindow, horizon: int)` and return a `Predictive`
   (`GaussianPredictive`, `StudentTPredictive`, `GaussianMixturePredictive`, `QuadratureMixturePredictive`,
   `EmpiricalPredictive`). These expose `mean`, `variance`, `logpdf`, `cdf`, `quantile` and `sample`.
   The base class rejects anything that is not a `ContextWindow`, so the predictor cannot see ground truth.
3. A point-only model (e.g. an MSE-trained network) should be wrapped with `PointPredictor`. It
   returns a `PointForecast`, which the scoring functions refuse to log-score or CRPS-score. Score it
   with `harness.score_point_predictor`, against the target or the matched reference's posterior mean.
4. Score it with `harness.score_predictor(pred, eval_set)`, and compare paired against the matched
   reference with `harness.optimality_diagnostics`. That function refuses references that are not matched to
   the evaluation condition.
5. If it is a new *reference*, add independent checks to `dynaicl/validation/checks.py` (grid or closed
   form, Monte Carlo, identities, calibration) and a mutation that the checks must catch.

## Layout

```
dynaicl/systems      AR(1) simulator, priors, ContextWindow/GroundTruth, library, conditions, splits
dynaicl/references   Predictive classes, conjugate, quadrature, finite library, matched-reference guard
dynaicl/baselines    flat-prior Bayes, OLS (Gaussian / Student-t), kernel analog (3 schemes), persistence
dynaicl/metrics      log score, CRPS, PIT/coverage, paired differences, calibration tests
dynaicl/evaluation   harness: evaluation sets, scoring, guarded optimality diagnostics
dynaicl/validation   independent oracles, checks (A-F, J), mutations (G), kernel scheme comparison (K)
dynaicl/experiments  separability map
dynaicl/config       YAML schema;  config/  YAML files;  dynaicl/provenance.py  run records
docs/                MATH.md, DECISIONS.md, RISKS.md, PREREG_separability.md
```
