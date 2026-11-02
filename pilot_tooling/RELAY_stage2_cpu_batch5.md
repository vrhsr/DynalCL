# Relay prompt for the box: Stage 2 CPU batch 5 (CPU only; about 4-5 h wall at 16 workers, ASSUMED from smoke timing)

Splits the held-out population gap into a noise-level part and a dynamics part (F1, F2), maps F2 at longer contexts and larger
libraries and F1 libraries at long contexts, and estimates cumulative (sequence-level) gaps (1A, F1, F3). Spec
`docs/STAGE2_BATCH5_SPEC.md` (commit `6d8a9fd`) committed before the run; code `a5b969e`; the local theory part (section E) is
already committed (`cd2759f`). Seed roles `b5_f1_split`, `b5_f2`, `b5_cumulative` are used for the first time here.
**Run only after batch 4 has finished and been pushed** (batch 4 records the git head and source hashes at its end; pulling
during its run would corrupt that record).

```
Task: Stage 2 CPU batch 5 (CPU only: no GPU, no torch). Stop and report if anything fails or a permission is denied.
Do NOT write disclosure entries and do NOT commit to stage1-planning; only push the results branch.
Never open, print, add or push anything under results_stage1/pilot/. At most 16 worker processes in total on the machine.
0. Precondition: batch 4 is finished and pushed: `tmux ls` shows no session s2cpu4, and
   `git ls-remote origin results-stage2-cpu-batch4` prints a hash (equivalently, after `git fetch origin`,
   `git rev-parse --verify origin/results-stage2-cpu-batch4` succeeds). If not, STOP and report; do not start batch 5.
   (Corrected 2026-11-02, disclosure S46: the first version also required results_stage2/BATCH4_DONE in the working tree,
   which is tracked only on the results branch and is gone after switching back to stage1-planning.)
1. cd /home/rama_11187/projects/dynacl && git status --porcelain --untracked-files=no   (must print nothing)
   git fetch origin && git checkout stage1-planning && git pull --ff-only && git log --oneline -1
   (HEAD must be cd2759f or later; `git merge-base --is-ancestor cd2759f HEAD && echo OK` must print OK)
   free -g   (if less than 16 GB available, use --workers 8 below instead of 16)
2. tmux new -d -s s2cpu5 "export OMP_NUM_THREADS=1; \
     (.venv/bin/python scripts/stage2_batch5.py --out results_stage2/batch5 --workers 16 > results_stage2/b5.log 2>&1; echo \$? > results_stage2/b5.rc); \
     date -u +%FT%TZ > results_stage2/BATCH5_DONE"
3. One background waiter until results_stage2/BATCH5_DONE exists, OR b5.rc is non-zero, OR a MemoryError / Traceback appears
   in b5.log, OR available memory drops below about 3 GB. If a waiter hits its time limit, start a new one; do not poll in a
   loop. The run is resumable: if it dies, rerunning the same command skips finished units.
4. When BATCH5_DONE exists and b5.rc is 0:
   git checkout -b results-stage2-cpu-batch5
   git add -f results_stage2/BATCH5_DONE results_stage2/b5.rc results_stage2/b5.log results_stage2/batch5/BATCH5_DONE.json \
     results_stage2/batch5/BATCH5_REPORT.md results_stage2/batch5/provenance.json results_stage2/batch5/split.csv \
     results_stage2/batch5/f2_library.csv results_stage2/batch5/f2_library_draws.csv results_stage2/batch5/f1_library_long.csv \
     results_stage2/batch5/f1_library_long_draws.csv results_stage2/batch5/cumulative.csv
   (do NOT add results_stage2/batch5/units/)
   git diff --cached --name-only | grep -E "results_stage1/|\.pt$|/units/" && echo "STOP: forbidden file staged"   (must print nothing)
   git commit -m "Stage 2 CPU batch 5: gap split, longer contexts, larger libraries, cumulative gaps (box CPU)" && git push -u origin results-stage2-cpu-batch5   (never main, never --force)
   git checkout stage1-planning
5. Report: b5.rc, start and end times, `free -g` at the end, the first 40 lines of BATCH5_REPORT.md, and the commit hash.
```
