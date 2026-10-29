# Relay prompt for the box: Stage 2 CPU batch 3 (CPU only, no GPU, no torch; about 2-3 h). Run after batch 2.

Two F2 validation jobs (task B2), one after the other, at most 16 worker processes:
1. **F2-V11 mutation matrix** (`scripts/stage2_f2_mutation_matrix.py`, 4 parallel rows): 7 mutations + clean, each row runs
   `tests_stage2/test_f2_references.py` (unedited) under the mutation plugin and the extra detectors. About 1-1.5 h.
2. **F2 validation report** (`scripts/stage2_f2_validation.py`, seed role f2_validation used for the first time):
   calibration and optimality in 9 cells, 117 tests. About 1-2 h at 16 workers.

```
Task: Stage 2 CPU batch 3 (CPU only: no GPU, no torch). Stop and report if anything fails or a permission is denied.
Never open, print, add or push anything under results_stage1/pilot/. At most 16 worker processes in total.
1. cd /home/rama_11187/projects/dynacl && git status --porcelain --untracked-files=no   (must print nothing)
   git fetch origin && git checkout stage1-planning && git pull --ff-only && git log --oneline -1
2. tmux new -d -s s2cpu3 "export OMP_NUM_THREADS=1; mkdir -p results_stage2; \
     (.venv/bin/python scripts/stage2_f2_mutation_matrix.py --out results_stage2/f2_mutation_matrix --jobs 4 > results_stage2/f2mm.log 2>&1; echo \$? > results_stage2/f2mm.rc); \
     (.venv/bin/python scripts/stage2_f2_validation.py --out results_stage2/f2_validation --workers 16 > results_stage2/f2val.log 2>&1; echo \$? > results_stage2/f2val.rc); \
     date -u +%FT%TZ > results_stage2/BATCH3_DONE"
3. Wait with ONE background waiter until results_stage2/BATCH3_DONE exists; do not poll in a loop.
4. When BATCH3_DONE exists:
   git checkout -b results-stage2-cpu-batch3
   git add -f results_stage2/BATCH3_DONE results_stage2/f2mm.rc results_stage2/f2mm.log results_stage2/f2val.rc results_stage2/f2val.log results_stage2/f2_mutation_matrix results_stage2/f2_validation
   git diff --cached --name-only | grep -E "results_stage1/|\.pt$" && echo "STOP: forbidden file staged"   (must print nothing)
   find results_stage2 -type f -size +2M -newer results_stage2/f2mm.rc   (list; unstage anything listed)
   git commit -m "Stage 2 CPU batch 3: F2 mutation matrix and F2 validation (box CPU)" && git push -u origin results-stage2-cpu-batch3   (never main, never --force)
   git checkout stage1-planning
5. Report: both .rc files, results_stage2/f2_mutation_matrix/f2_mutation_matrix.md, results_stage2/f2_validation/f2_validation.md, start and end times, and the commit hash.
```
