# Relay prompt for the box: Stage 2 CPU batch 1 (CPU only, no GPU, no torch; about 2.5-3.5 h)

Not frozen. Three reference-side CPU jobs in one tmux session, run one after another, at most 16 worker processes
(the user's limit while a GPU job may run):
1. **F1-V9 mutation matrix** (`scripts/stage2_f1_mutation_matrix.py`, 4 parallel rows: each row runs the frozen F1 tests,
   about 1-2 GB each; on the 16 GB laptop 7 parallel rows failed through MemoryError, disclosure S29). About 20-30 min.
2. **F3 short-context map** (`scripts/stage2_f3_map.py`, spec `docs/STAGE2_F3_MAP_SPEC.md` committed before this run;
   seed role f3_map used for the first time). Extrapolated about 21 CPU-h, so about 1.5 h at 16 workers. Resumable.
3. **F1 operating characteristics** for the DRAFT F1 neural pre-registration (`scripts/stage2_f1_operating_characteristics.py`,
   bootstrap critical value as Stage 1A v2; seed role f1_oc). Estimated 0.5-1.5 h at 16 workers (UNVERIFIED: only a
   2-setting quick run was timed).
All three only READ the frozen Stage 0.6 `.venv` (numpy 2.2.2, scipy 1.15.1, pyyaml, pytest); nothing is installed.

```
Task: Stage 2 CPU batch 1 (CPU only: no GPU, no torch). Stop and report if anything fails or a permission is denied.
Never open, print, add or push anything under results_stage1/pilot/ (pilot eval files and weights must stay untouched).
At most 16 worker processes in total.
1. cd /home/rama_11187/projects/dynacl && git status --porcelain --untracked-files=no   (must print nothing)
   git fetch origin && git checkout stage1-planning && git pull --ff-only && git log --oneline -1
   free -g ; nproc ; nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv   (report; the GPU is not used)
2. Start one tmux session that runs the three jobs in order and writes a marker at the end:
   tmux new -d -s s2cpu "export OMP_NUM_THREADS=1; mkdir -p results_stage2; \
     (.venv/bin/python scripts/stage2_f1_mutation_matrix.py --out results_stage2/f1_mutation_matrix --jobs 4 > results_stage2/f1mm.log 2>&1; echo \$? > results_stage2/f1mm.rc); \
     (.venv/bin/python scripts/stage2_f3_map.py --out results_stage2/f3_map --workers 16 > results_stage2/f3map.log 2>&1; echo \$? > results_stage2/f3map.rc); \
     (.venv/bin/python scripts/stage2_f1_operating_characteristics.py --out results_stage2/f1_oc --workers 16 > results_stage2/f1oc.log 2>&1; echo \$? > results_stage2/f1oc.rc); \
     date -u +%FT%TZ > results_stage2/BATCH1_DONE"
3. Wait with ONE background waiter until results_stage2/BATCH1_DONE exists; do not poll in a loop.
   On-demand progress only: ls results_stage2/*.rc; tail -2 results_stage2/f3map.log
4. When BATCH1_DONE exists:
   git checkout -b results-stage2-cpu-batch1
   git add -f results_stage2/BATCH1_DONE results_stage2/*.rc results_stage2/*.log results_stage2/f1_mutation_matrix results_stage2/f1_oc
   git add -f results_stage2/f3_map/MAP_REPORT.md results_stage2/f3_map/map_decisions.csv results_stage2/f3_map/map_checks.json results_stage2/f3_map/map_rows.csv.gz results_stage2/f3_map/provenance.json results_stage2/f3_map/MAP_DONE.json
   (do NOT add results_stage2/f3_map/units/: 780 unit files stay on the box)
   find results_stage2 -type f -size +2M -newer results_stage2/f1mm.rc   (list; unstage anything listed)
   git commit -m "Stage 2 CPU batch 1: F1-V9 mutation matrix, F3 short-context map, F1 operating characteristics (box CPU)" && git push -u origin results-stage2-cpu-batch1   (never main, never --force)
   git checkout stage1-planning
5. Report: the three .rc files, results_stage2/f1_mutation_matrix/f1_mutation_matrix.md, the first 25 lines of results_stage2/f3_map/MAP_REPORT.md, the last 3 lines of results_stage2/f1oc.log, the start and end times, and the commit hash.
```
