# Relay prompt for the box: Stage 2 CPU batch 4, sensitivity analyses (CPU only; about 1-1.5 h at 16 workers)

Answers internal review 1's open items (comparator frontier, prior dependence, noisy map at ten times the precision); spec
`docs/STAGE2_SENSITIVITY_SPEC.md` committed before this run; seed roles `sensitivity` and `f3_precision` used for the first
time. About 12 CPU-hours; the high-precision noisy units hold the most memory (scored in chunks of 10 000).

```
Task: Stage 2 CPU batch 4, sensitivity analyses (CPU only: no GPU, no torch). Stop and report if anything fails or a permission is denied.
Do NOT write disclosure entries and do NOT commit to stage1-planning; only push the results branch.
Never open, print, add or push anything under results_stage1/pilot/. At most 16 worker processes in total.
1. cd /home/rama_11187/projects/dynacl && git status --porcelain --untracked-files=no   (must print nothing)
   git fetch origin && git checkout stage1-planning && git pull --ff-only && git log --oneline -1
   free -g   (if less than 12 GB available, use --workers 8 below instead of 16)
2. tmux new -d -s s2cpu4 "export OMP_NUM_THREADS=1; mkdir -p results_stage2; \
     (.venv/bin/python scripts/stage2_sensitivity.py --out results_stage2/sensitivity --workers 16 > results_stage2/sens.log 2>&1; echo \$? > results_stage2/sens.rc); \
     date -u +%FT%TZ > results_stage2/BATCH4_DONE"
3. One background waiter until results_stage2/BATCH4_DONE exists, OR sens.rc is non-zero, OR a MemoryError / Traceback appears in sens.log, OR available memory drops below about 3 GB. If a waiter hits its time limit, start a new one; do not poll in a loop. The run is resumable: if it dies, rerunning the same command skips finished units.
4. When BATCH4_DONE exists:
   git checkout -b results-stage2-cpu-batch4
   git add -f results_stage2/BATCH4_DONE results_stage2/sens.rc results_stage2/sens.log results_stage2/sensitivity/sensitivity.csv results_stage2/sensitivity/SENSITIVITY_REPORT.md results_stage2/sensitivity/provenance.json results_stage2/sensitivity/SENSITIVITY_DONE.json
   (do NOT add results_stage2/sensitivity/units/)
   git diff --cached --name-only | grep -E "results_stage1/|\.pt$|/units/" && echo "STOP: forbidden file staged"   (must print nothing)
   git commit -m "Stage 2 CPU batch 4: sensitivity analyses (box CPU)" && git push -u origin results-stage2-cpu-batch4   (never main, never --force)
   git checkout stage1-planning
5. Report: sens.rc, the start and end times, the first 40 lines of SENSITIVITY_REPORT.md, and the commit hash.
```
