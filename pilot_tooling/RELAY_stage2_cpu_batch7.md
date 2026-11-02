# Relay prompt for the box: Stage 2 CPU batch 7, F2 Q2 operating characteristics on batch 5's library cells

Spec `docs/STAGE3_F2_OC_B5_SPEC.md` (committed before use); seed role `f2_oc_b5` (83402) used for the first time here.
About a minute at 16 workers (batch 6 ran 256 settings in 15 s; this is 768). CPU only, synthetic models.

```
Task: Stage 2 CPU batch 7, F2 Q2 operating characteristics on the batch 5 cells (CPU only: no GPU, no torch). Stop and
report if anything fails or a permission is denied. Do NOT write disclosure entries and do NOT commit to stage1-planning; only
push the results branch. Never open, print, add or push anything under results_stage1/pilot/. At most 16 worker processes.
0. Precondition: no other batch is running (`tmux ls` shows no s2cpu4 / s2cpu5 / s2cpu6), and after `git fetch origin`,
   `git rev-parse --verify origin/results-stage2-cpu-batch6` succeeds. If not, STOP and report.
1. cd /home/rama_11187/projects/dynacl && git status --porcelain --untracked-files=no   (must print nothing)
   git checkout stage1-planning && git pull --ff-only && git log --oneline -1
   (`git merge-base --is-ancestor fb3b12a HEAD && echo OK` must print OK; fb3b12a adds `--cells batch5`)
2. .venv/bin/python scripts/stage3_f2_operating_characteristics.py --cells batch5 --out results_stage2/f2_oc_b5 --workers 16 \
     > results_stage2/f2ocb5.log 2>&1; echo $? > results_stage2/f2ocb5.rc
   (runs in about a minute; no tmux needed)
3. If f2ocb5.rc is 0:
   git checkout -b results-stage2-cpu-batch7
   git add -f results_stage2/f2ocb5.rc results_stage2/f2ocb5.log results_stage2/f2_oc_b5/oc_q2_f2.csv \
     results_stage2/f2_oc_b5/f2_power_lookup.json results_stage2/f2_oc_b5/provenance.json
   git diff --cached --name-only | grep -E "results_stage1/|\.pt$" && echo "STOP: forbidden file staged"   (must print nothing)
   git commit -m "Stage 2 CPU batch 7: F2 Q2 operating characteristics on batch 5 cells (box CPU)" && git push -u origin results-stage2-cpu-batch7   (never main, never --force)
   git checkout stage1-planning
4. Report: the rc, the "Q2" and "Q2_per_cell" entries of f2_power_lookup.json, and the commit hash.
```
