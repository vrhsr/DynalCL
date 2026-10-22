# Phase D (pilot) tooling: NOT part of the frozen file set

Everything under `phase_d_pilot/` and `colab/pilot/` is pilot-only. None of it is listed in `docs/FREEZE_MANIFEST_STAGE06.json`
and none of it may be used to launch the confirmatory run.

| File | Purpose |
|---|---|
| `pilot_common.py` | hashing, environment report, peak-RSS, process control, the pilot-seed guard (`assert_pilot_config`) |
| `pilot_child.py` | child processes: crash injection, per-unit profiling, launch-guard stubs, synthetic analysis cost |
| `pilot_harness.py` | the tasks (integrity, env, ref-run, interrupt-tests, corruption-tests, ...), same code locally and on Colab |
| `build_phase_d_notebook.py` | builds `dist/phase_d_pilot_bundle.zip` and `colab/pilot/DynaICL_Stage06_PhaseD_PILOT.ipynb` |
| `config/PILOT_*.yaml` | pilot-labelled config variants (pilot seeds; sizes N = 50 / 100 / 400 / 4000; mode `test` copies used only to take the full analysis branch). The frozen runner REFUSES them (not frozen); they are used only through direct calls to frozen functions |
| `reports/`, `work/` | outputs (run kind PILOT) |
| `PILOT_ONLY_do_not_open_effects.json` | pilot effect estimates written by the structural analysis. Never opened or summarised |

Pilot seeds: evaluation 62001 and 62101, bootstrap 62999 (seed manifest role `pilot`). Confirmatory seeds 64101, 64102, 64999 appear
nowhere here except in the guard that refuses them and in the seed search that looks for them.
