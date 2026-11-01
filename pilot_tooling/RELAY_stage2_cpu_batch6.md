# Relay prompt for the box: Stage 2 CPU batch 6, F2 neural design on CPU (head floor + Q2 operating characteristics)

Spec `docs/STAGE3_F2_DESIGN_CPU_SPEC.md` (committed before use; section A amended before any production seed was used),
code `5d23547`. Seed roles `f2n_head_floor` (83301) and `f2_oc` (83401) are used for the first time here. Estimated wall time
(ASSUMED from laptop smokes): head floor 3-4 h at 16 workers, operating characteristics under 30 min. **Run only after batches
4 and 5 have finished and been pushed** (each records the git head and source hashes at its end).

```
Task: Stage 2 CPU batch 6, F2 head floor and Q2 operating characteristics (CPU only: no GPU, no torch). Stop and report if
anything fails or a permission is denied. Do NOT write disclosure entries and do NOT commit to stage1-planning; only push the
results branch. Never open, print, add or push anything under results_stage1/pilot/. At most 16 worker processes in total.
0. Precondition: batches 4 and 5 are finished and pushed: `tmux ls` shows neither s2cpu4 nor s2cpu5;
   `git ls-remote origin results-stage2-cpu-batch4` and `git ls-remote origin results-stage2-cpu-batch5` both print a hash.
   If not, STOP and report; do not start batch 6.
1. cd /home/rama_11187/projects/dynacl && git status --porcelain --untracked-files=no   (must print nothing)
   git fetch origin && git checkout stage1-planning && git pull --ff-only && git log --oneline -1
   (`git merge-base --is-ancestor 5d23547 HEAD && echo OK` must print OK)
   free -g   (if less than 16 GB available, use --workers 8 below instead of 16)
2. tmux new -d -s s2cpu6 "export OMP_NUM_THREADS=1; \
     (.venv/bin/python scripts/stage3_f2_head_floor.py --out results_stage2/f2_head_floor --workers 16 > results_stage2/f2hf.log 2>&1; echo \$? > results_stage2/f2hf.rc); \
     (.venv/bin/python scripts/stage3_f2_operating_characteristics.py --out results_stage2/f2_oc --workers 16 > results_stage2/f2oc.log 2>&1; echo \$? > results_stage2/f2oc.rc); \
     date -u +%FT%TZ > results_stage2/BATCH6_DONE"
3. One background waiter until results_stage2/BATCH6_DONE exists, OR f2hf.rc / f2oc.rc is non-zero, OR a MemoryError /
   Traceback / FloatingPointError appears in a log, OR available memory drops below about 3 GB. If a waiter hits its time
   limit, start a new one; do not poll in a loop.
4. When BATCH6_DONE exists and both rc files are 0:
   git checkout -b results-stage2-cpu-batch6
   git add -f results_stage2/BATCH6_DONE results_stage2/f2hf.rc results_stage2/f2hf.log results_stage2/f2oc.rc \
     results_stage2/f2oc.log results_stage2/f2_head_floor/f2_head_floor.csv results_stage2/f2_head_floor/f2_head_floor_summary.json \
     results_stage2/f2_head_floor/provenance.json results_stage2/f2_oc/oc_q2_f2.csv results_stage2/f2_oc/f2_power_lookup.json \
     results_stage2/f2_oc/provenance.json
   git diff --cached --name-only | grep -E "results_stage1/|\.pt$" && echo "STOP: forbidden file staged"   (must print nothing)
   git commit -m "Stage 2 CPU batch 6: F2 head floor and Q2 operating characteristics (box CPU)" && git push -u origin results-stage2-cpu-batch6   (never main, never --force)
   git checkout stage1-planning
5. Report: both rc values, start and end times, the chosen m and worst cells from f2_head_floor_summary.json, the Q2 lookup
   from f2_power_lookup.json, and the commit hash.
```
