# Stage 0.6 seed roles

GENERATED from `config/stage06_seed_manifest.yaml` by `dynaicl.config.stage06_seed_roles.render_markdown` and checked against it by the test suite (V28). Edit the YAML, never this file.

| role | seeds | purpose |
|---|---|---|
| `validation` | 61001, 61002, 61003, 61005, 61006, 61007, 61008, 61009, 61010, 61011, 61012, 61013, 61014, 61015, 61016, 61017, 61018, 61019, 61020, 61021, 61022, 61023, 61024, 61025, 61026 | validation checks V1-V29 (one root per check), the fresh calibration-diagnostic rerun (61020), analysis checks V20-V23 (61021-61023), the runner's test-mode configuration (evaluation 61024, 61025; bootstrap 61026) |
| `design_calculation` | 61901, 61902, 61903 | prior-based noise-level verification (Fisher-information Monte Carlo, expected posterior variance) and the synthetic decision-rule dry run (61903; synthetic data only, planning variances from Stage 0.5 artifacts) |
| `pilot_evaluation` | 62001, 62101 | Phase D operational pilot data generation, replicate 1 = 62001 and replicate 2 = 62101 (runtime, memory, checkpoints, resume and structural completeness; never selection, thresholds or hypothesis tests) |
| `pilot_bootstrap` | 62999 | bootstrap root of PILOT pipeline-execution tests only. The pilot-mode runner draws no bootstrap and never uses it. The Phase D structural analysis (frozen analyze() on pilot per-item outputs, config variant of mode test) drew from it, which the v1 note 'never drawn from' did not allow for (disclosure erratum E1) |
| `selection` | 63001 | selection-data audit of noise-aware context-only alternatives (context-only predictors only) and the runner's integrity-unit disjointness check (no scores) |
| `confirmatory_evaluation` | 64101, 64102 | confirmatory replicates R1 = 64101 and R2 = 64102 (allocated, NOT used before authorization) |
| `confirmatory_bootstrap` | 64999 | cluster bootstrap for the confirmatory run (allocated, not used) |

## Allowed and forbidden uses

### `validation` (61001, 61002, 61003, 61005, 61006, 61007, 61008, 61009, 61010, 61011, 61012, 61013, 61014, 61015, 61016, 61017, 61018, 61019, 61020, 61021, 61022, 61023, 61024, 61025, 61026)

* allowed: validation checks and pytest only; runner test-mode configuration
* forbidden: any pilot or confirmatory run; any decision

### `design_calculation` (61901, 61902, 61903)

* allowed: design calculations on prior-predictive or synthetic data
* forbidden: any run on model data used for a decision

### `pilot_evaluation` (62001, 62101)

* allowed: generating pilot systems and observations through the frozen runner in pilot mode; pilot-size variants through direct calls of frozen functions; timing and memory measurement
* forbidden: bootstrap stream; any confirmatory evaluation; choosing hypotheses; thresholds; sample sizes; noise levels or baselines

### `pilot_bootstrap` (62999)

* allowed: bootstrap stream of structural or pipeline-execution analyses of PILOT per-item outputs; written only to pilot-labelled files
* forbidden: data generation; any confirmatory analysis; any use whose result informs a design choice

### `selection` (63001)

* allowed: the Phase B selection audit; disjointness checks
* forbidden: population-aware scores; confirmatory evaluation

### `confirmatory_evaluation` (64101, 64102)

* allowed: the authorized confirmatory run only
* forbidden: everything else; including tests; pilots; qualification and dry runs

### `confirmatory_bootstrap` (64999)

* allowed: the authorized confirmatory analysis only
* forbidden: everything else

