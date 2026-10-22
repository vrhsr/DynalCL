# Stage 0.6 Phase D report (pilot; operational qualification)

Run kind: PILOT. Seeds: 62001, 62101 (evaluation), 62999 (bootstrap). Nothing here is frozen. Machine: Windows 11, Intel i5-10310U
(4 cores / 8 threads), 16.9 GB RAM, Python 3.13.5, numpy 2.2.2, scipy 1.15.1, no GPU. **Everything below was executed on this
machine, a local rehearsal. Nothing was run on Colab** (see section 9). Outputs: `phase_d_pilot/work/reports/PILOT_*.json`.

## 1. Environment qualification (local)

* Environment fingerprint equals the frozen environment manifest (no differences). Pins in `requirements.txt` all match.
* Frozen `qualify` (pilot config): **PASS**, 177 s. V4 Tier-1 (243,216 items, max diff 9.3e-15, tolerance 1e-9 = frozen), V6
  (quadrature convergence, budget 2e-4), V11 (936 bitwise comparisons), V13 (batch = per-context, max diff 8e-15). Report bound to
  manifest `461dfec8...` and config `08d069ae...`: `PILOT_qualification_local_windows_pilotcfg.json`.
* Qualification mechanism (throwaway copy with a simulated environment difference; the real checks inside `qualify` ran,
  99 s): valid report accepted; refused when the report is missing, bound to another manifest, bound to another environment,
  bound to another config, or failed. A nonexistent report path ends in an uncaught FileNotFoundError (exit 1), not a clean REFUSED.
* float64: numpy default float64; every stored score array is float64 and every PIT array float32 by the frozen schema (checked
  by the frozen loader on every unit).

## 2. Hashes (8 verifications, all ok; bookends 0-7 in `PILOT_integrity_log.jsonl`)

| Artifact | SHA-256 |
|---|---|
| freeze manifest | `461dfec8144104f4d35a513dbf1411041494876331f8f969dda4a9cea09be0c0` |
| snapshot archive | `4114fa43cf737c643c341cccd4026d6fcb54b460bfb12ac4a8a2de8352b492e5` |
| pre-registration | `ec42214a84b1d6999acc156f2532f9d1b745debad5dfd1138458ebcb15b92e66` |
| confirmatory config file | `4d30069f2ec767cb2e2bb0c0eeaf89f29f56e4fe8623bfa889fd8f34f803c755` |
| pilot config file | `48938db45726b692233b799f26131557a5c595f97eb094f10f238bc10163822a` |
| pilot bundle (Colab harness) | `fe122d82f24154e78ffca01f008d2b66c5d3e5ac28e4eba0115ab268e06eaea6` |

All 103 manifest files and all snapshot members matched at every bookend. One slip (disclosure F8) rewrote a manifest file; it was restored
from the snapshot and re-verified.

## 3. Resources (measured, this machine, 1 thread per process)

| Quantity | Measured |
|---|---|
| Primary unit, N = 200 (24 units) | wall 7.7-9.7 s (median 8.0 s), peak RSS 298 MB |
| Primary unit, N = 4000 (2 corner cells) | wall 85-87 s in a quiet run, 105-119 s in an earlier run with other load; peak RSS 326 MB; checkpoint 7.49 MB |
| Noise-naive unit, N = 50 / 4000 | 1.5 s / 110 s; peak RSS 97 / 112 MB; checkpoint 3.84 MB (at 4000) |
| Integrity unit at N = 4000 / Tier-1 unit | 4.2 s, 127 MB / 12-18 s, 141 MB |
| Per forecast, N = 4000 (primary: 624,000 predictor-forecasts per unit; naive: 320,000) | primary 0.14-0.19 ms; naive 0.34 ms |
| Cell-type spread (24 primary cells, N = 200) | 7.7-9.7 s; no cell type is an outlier. The node set is fixed (1040 nodes), so cost depends on N and n only, not on how concentrated the posterior is (q = 0, r = 4 is not slower) |
| Frozen analysis at confirmatory scale (SYNTHETIC, N = 4000 x 2 replicates, 36 contrasts, B = 20000) | 3.8 s; peak RSS 567 MB; 20000 draws sufficed in both replicates |
| Checkpoints at confirmatory scale | 272 MB, 50 files + 50 JSON; write 1.8 s total, load + checksum 1.7 s total (local disk) |
| Local disk throughput | write 375 MB/s, read + SHA-256 251 MB/s |

Linearity (primary, quiet run, N = 50 / 100 / 200 / 400): 2.2 / 5.6 / 7.7 / 12.5 s, i.e. a fixed cost of about 1.2 s plus about 23-28 ms
per system. Extrapolating the N = 100-400 slope to N = 4000 gives about 95 s; measured 85-119 s. Naive: 1.5 / 2.9 / 11.3 s at 50 / 100 / 400 and
110 s measured at 4000 (linear).

**Extrapolation to the confirmatory workload** (24 primary + 24 noise-naive units, each at N = 4000, plus integrity and Tier-1):
24 x (85-120) s + 24 x 110 s + about 20 s = **78-92 CPU-minutes (1.3-1.5 CPU-hours)**. On this laptop with 4 workers (measured speed-up
2.2x on the 50-unit pilot; about 3x expected at full size): about **30-45 min wall**. On Colab (2 vCPU, speed per core relative to this CPU
ASSUMED 0.4-0.8x, to be measured): 2.6 to 3.7 CPU-hours / 2 workers = **about 1.3-2.5 h wall**. Memory: peak 326 MB per worker plus 567 MB for the final
analysis, below 1.5 GB in total against about 12 GB on Colab. Disk: 272 MB of checkpoints against tens of GB. Projected sessions: **1** (central), planning for
up to 3 resumes; margin about 2x on time, more than 8x on memory, more than 100x on disk. Recommended checkpoint cadence: the frozen per-unit
cadence is already right (a unit takes 1.5-4 min on Colab), so an interruption loses at most one unit.

## 4. Checkpoint and resume (frozen runner, frozen pilot config; reference = uninterrupted run)

Every scenario was resumed to completion and compared bitwise (arrays, metadata, even the raw checkpoint file bytes) with the reference.

| Failure | Units saved | Result |
|---|---|---|
| clean stop (`--max-new-units`) | 12 | identical |
| KeyboardInterrupt in the middle of a unit | 8 | identical |
| hard kill of the process tree (SIGKILL analogue), 1 worker, resumed with 4 | 6 | identical |
| hard kill, 4 workers, resumed with 1 | 16 | identical |
| hard kill, late, resumed with 2 | 41 | identical |
| self-kill halfway through writing the arrays | 6 | identical |
| self-kill before the arrays rename | 7 | identical |
| self-kill before the metadata rename (arrays present, metadata absent) | 8 | identical; the unit is recomputed (the metadata file is the commit marker) |
| LOCAL EMULATION of a runtime restart (new extraction of the snapshot, durable checkpoint directory only) | 20 | identical |

No unit was saved twice and none was skipped. Leftover `.tmp` files were overwritten on resume. Per-cell RNG streams come from cell identity
(`NamedStreams` keyed by seed, role and item), not from execution order: the 1-worker and 4-worker uninterrupted runs are bitwise identical
on all 50 units. Determinism: arrays are **bitwise** identical at 1, 2, 4 and 8 BLAS threads, repeated runs, three unit types, and the synthetic analysis
pipeline (hash of all 72 contrasts). No frozen tolerance was needed.
Checksums are verified on every load by the frozen code. Corruption (10 cases on copies): 7 clean REFUSED (truncated arrays, bit flip, zero-length file,
arrays missing, arrays swapped between units, wrong config hash, valid checksum with wrong array shape); a truncated unit JSON ends in an uncaught
JSONDecodeError traceback (exit 1: loud, not silent); a missing JSON (unit treated as not done, recomputed) and leftover tmp files are handled correctly. After the
operator deletes the bad unit, the resume reproduces the reference in every case. Nothing was silently skipped.
Atomicity on durable storage: local NTFS only (Windows refuses to replace a file another process holds open; 0 torn reads, 0 missing-file reads in 100 replacements).
**Google Drive, different-CPU resume and a real Colab restart are untested (section 9).**

## 5. Seed isolation and launch protection (throwaway copies, evaluation stubbed, temporary outputs)

| Case | Outcome |
|---|---|
| confirmatory `run`, correct manifest, **no authorization artifact** | **reached the evaluation entry point (stub)**: no authorization gate exists |
| pilot mode with confirmatory seeds (config edited in a copy, manifest re-hashed) | REFUSED (seeds not the allocation for mode pilot) |
| confirmatory mode with pilot seeds | REFUSED |
| confirmatory `analyze` given pilot checkpoints (placed under the confirmatory config-hash directory) | REFUSED (config hash mismatch) |
| same, pilot checkpoint parent directory | REFUSED (missing units) |
| confirmatory run without manifest arguments | REFUSED |

Entry points: CLI flags `--config --manifest --expected-manifest-sha256 --qualification --checkpoint-dir --runs-dir --workers --out
--max-new-units`; environment variables: only BLAS thread counts are set, none is read to select a mode; notebooks: the Phase D notebook and the
post-freeze notebook contain no run cell. The frozen functions `run_units()`/`run_unit()` can be called from Python with any config and have no guard.
Pilot outputs carry no explicit run-kind field; they are rejected through the config hash (mode is part of the config) and are named `..._pilot_...`.
This tests the guards, not the full computation path.
Seed search over all pilot outputs, logs, checkpoints, reports and pilot configs (2385 files; whole-token match for 64101 / 64102 / 64999): **0 matches**
(guard-test messages are masked and throwaway copies were deleted).
Confirmatory results location: `runs/` holds only the five Stage 0 / 0.5 directories; no Stage 0.6 run directory, no confirmatory checkpoint (config-hash directory
`8304d1ab2d37efbf` does not exist), no confirmatory per-item output.

## 6. Completeness and the frozen analysis pipeline (structural only)

Reference run: 50/50 units (2 + 24 + 24), 50 checkpoint files (2 hold no arrays), 24 primary cells x 2 replicates present, 1,689,600 array elements checked, **0 non-finite**, 0 PIT
values outside (0, 1), 0 duplicate units, every unit passes the frozen schema and checksum load. Second size (N = 50): 50/50 units, all critical-check flags True.
The frozen `analyze()` full branch (config variant mode `test`, pilot seeds, bootstrap 62999) executed successfully on the pilot outputs in 0.3 s: 2
replicates with ok flag, 72/72 contrast rows finite, a decision block and a Tier-2 block present. Estimates and labels were written to
`phase_d_pilot/PILOT_ONLY_do_not_open_effects.json` and were not read.

## 7. Failures and deviations

See disclosure log F4-F10. No frozen file changed (one accidental rewrite, F8, restored from the snapshot and verified).

## 8. Files created (all outside the frozen set)

`phase_d_pilot/` (`pilot_common.py`, `pilot_child.py`, `pilot_harness.py`, `run_queue.py`, `build_phase_d_notebook.py`, `README_PHASE_D.md`,
`PHASE_D_REPORT.md`, `config/PILOT_*.yaml`, `work/`, `PILOT_ONLY_do_not_open_effects.json`), `colab/pilot/DynaICL_Stage06_PhaseD_PILOT.ipynb`,
`dist/phase_d_pilot_bundle.zip`. Edited outside the manifest: `docs/DISCLOSURE_LOG_STAGE06.md`, `scripts/build_colab_stage06.py`,
`colab/DynaICL_Stage06_Colab.ipynb`.

## 9. Not done here (needs the user's Colab run of the Phase D notebook)

Colab package versions and the frozen-vs-Colab difference table; Colab CPU, BLAS and thread counts; `qualify` in Colab and acceptance of that report by the runner;
atomicity and throughput on Google Drive; a real runtime restart with a different CPU; Colab per-core speed and hence the Colab wall-time and session projection.

## 10. Recommendation: **REVISE**

Met: all hashes verified unchanged; only pilot seeds used; no confirmatory artifact exists; resume reproduces the uninterrupted results bitwise for every failure type;
outputs complete and checksummed; the frozen analysis executes; projected local resources fit with margin.

Not met:
1. **No authorization artifact** (disclosure F6a). A confirmatory run needs only the manifest hash and a checkpoint directory. This could be classed BLOCKED
   ('a launch guard that ... can be bypassed'); I classify it REVISE because a defined change fixes it. Treat it as BLOCKED until then if you prefer.
   Exact steps: (a) add to `stage06_probe.py` a required `--authorization FILE` for confirmatory mode, a small JSON whose SHA-256 binds the manifest hash,
   the config hash, and a statement you create, refused if absent, stale or bound to another manifest/config; pilot and test modes must refuse it; (b) add V24 cases and
   mutations (gate removed, wrong binding accepted); (c) optional in the same change: catch JSONDecodeError and a missing qualification path as REFUSED;
   (d) repeat the full validation (Stage 0.6 suite, pre-existing suite, mutation matrix on a copy), update the validation report and pre-registration section 11;
   (e) regenerate the freeze manifest, snapshot, notebooks and bundle: the manifest and snapshot hashes change; you store the new manifest hash; (f) re-run this Phase D tooling
   on the new snapshot (about 1 hour locally, plus the Colab run).
2. The Colab-specific evidence (section 9) is outstanding.
