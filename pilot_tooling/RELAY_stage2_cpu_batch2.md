# Relay prompt for the box: Stage 2 CPU batch 2 (CPU only, no GPU, no torch; about 3-4 h)

Not frozen. Two reference-side CPU jobs in one tmux session, one after the other, at most 16 worker processes:
1. **F2 separability map** (`scripts/stage2_f2_map.py`; spec `docs/STAGE2_F2_MAP_SPEC.md`, committed before this run; seed role
   f2_map used for the first time). Estimated 20-25 CPU-h, about 1.5-2 h at 16 workers. Resumable.
2. **F1 head floor** (`scripts/stage2_f1_head_floor.py`; seed role f1n_head_floor used for the first time): the smallest
   Gaussian-mixture head m in {1, 2, 4, 8} that represents every F1 reference within 0.001 nats. Estimated 20 CPU-h, about 1.5 h.
Both only READ the frozen Stage 0.6 `.venv`.

```
Task: Stage 2 CPU batch 2 (CPU only: no GPU, no torch). Stop and report if anything fails or a permission is denied.
Never open, print, add or push anything under results_stage1/pilot/. At most 16 worker processes in total.
1. cd /home/rama_11187/projects/dynacl && git status --porcelain --untracked-files=no   (must print nothing)
   git fetch origin && git checkout stage1-planning && git pull --ff-only && git log --oneline -1
   free -g ; nproc
2. tmux new -d -s s2cpu2 "export OMP_NUM_THREADS=1; mkdir -p results_stage2; \
     (.venv/bin/python scripts/stage2_f2_map.py --out results_stage2/f2_map --workers 16 > results_stage2/f2map.log 2>&1; echo \$? > results_stage2/f2map.rc); \
     (.venv/bin/python scripts/stage2_f1_head_floor.py --out results_stage2/f1_head_floor --contexts 100 --workers 16 > results_stage2/f1hf.log 2>&1; echo \$? > results_stage2/f1hf.rc); \
     date -u +%FT%TZ > results_stage2/BATCH2_DONE"
3. Wait with ONE background waiter until results_stage2/BATCH2_DONE exists; do not poll in a loop.
   On-demand progress only: ls results_stage2/*.rc; tail -2 results_stage2/f2map.log
4. When BATCH2_DONE exists:
   git checkout -b results-stage2-cpu-batch2
   git add -f results_stage2/BATCH2_DONE results_stage2/f2map.rc results_stage2/f2map.log results_stage2/f1hf.rc results_stage2/f1hf.log results_stage2/f1_head_floor
   git add -f results_stage2/f2_map/MAP_REPORT.md results_stage2/f2_map/map_decisions.csv results_stage2/f2_map/map_checks.json results_stage2/f2_map/map_rows.csv.gz results_stage2/f2_map/provenance.json results_stage2/f2_map/MAP_DONE.json
   (do NOT add results_stage2/f2_map/units/)
   git diff --cached --name-only | grep -E "results_stage1/|\.pt$|/units/" && echo "STOP: forbidden file staged"   (must print nothing)
   find results_stage2 -type f -size +2M -newer results_stage2/f2map.rc   (list; unstage anything listed)
   git commit -m "Stage 2 CPU batch 2: F2 separability map, F1 head floor (box CPU)" && git push -u origin results-stage2-cpu-batch2   (never main, never --force)
   git checkout stage1-planning
5. Report: both .rc files, the first 30 lines of results_stage2/f2_map/MAP_REPORT.md, results_stage2/f1_head_floor/f1_head_floor_summary.json (the "chosen_m" and "max_mass_err" fields), the start and end times, and the commit hash.
```
