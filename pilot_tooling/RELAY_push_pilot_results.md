# Relay prompt for the box: push the Stage 1A pilot outcome files (no compute)

Not part of the frozen set. Written 2026-10-27 because the pilot finished (2026-10-24) but its small result files were never pushed.
The user pastes the block below into the box's Claude Code session.

```
Push the Stage 1A pilot outcome files only (no compute). Stop and report if anything fails or a permission is denied. Never open, print, summarise or add anything under results_stage1/pilot/eval/ or any *.pt.
cd /home/rama_11187/projects/dynacl
git checkout -b results-stage1-pilot
git add -f results_stage1/pilot/*.json results_stage1/pilot/*.txt results_stage1/pilot/CURRENT_STEP
find results_stage1/pilot/models -name train_record.json -print0 | xargs -0 git add -f
git diff --cached --name-only | grep -E "/eval/|\.pt$" && echo "STOP: forbidden file staged"   (must print nothing)
find results_stage1/pilot -maxdepth 1 -type f -size +2M   (list only; unstage anything it lists)
git commit -m "Stage 1A pilot outcome (decision, logs, training records; no eval arrays, no weights)" && git push -u origin results-stage1-pilot   (never main, never --force)
Report the commit hash and confirm the pilot checkpoints at step 50000 still exist on disk (ls only, do not load them). Do not delete any weights.
```

After the push, on the laptop: `git fetch origin results-stage1-pilot`, then verify (without opening `eval/`):
the freeze-verify line in `wrapper_log.txt` (v2 manifest `94cf1c51...`), `git_head.txt` (frozen files identical to `3a29c15`),
`git_status_tracked.txt` empty, the 32 `train_record.json` files (seeds = pilot seeds, steps, wall times),
`pilot_decision.json` (status, B, cap, why 10k and 25k did not qualify). Then append disclosure S26 to
`docs/DISCLOSURE_LOG_STAGE1.md` and write appendix A. Stop for the user's decision (CLAUDE.md section 2h-quater).
