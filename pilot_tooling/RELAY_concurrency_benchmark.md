# Relay prompt for the box: concurrency benchmark before Amendment 2 (about 15 min, GPU)

Not frozen. User condition 3 (2026-10-27): measure whether more concurrent training processes on the one GPU raise
throughput, without changing any model. Uses the frozen J0 script unchanged; writes only `results_stage1/concurrency_bench/`.

```
Task: Stage 1 concurrency benchmark (about 15 min on the GPU). Stop and report if anything fails or a permission is denied.
Never open, print, summarise, add or delete anything under results_stage1/pilot/ (the pilot models and eval files must stay untouched).
1. cd /home/rama_11187/projects/dynacl && git status --porcelain --untracked-files=no   (must print nothing)
   git fetch origin && git checkout stage1-planning && git pull --ff-only && git log --oneline -1
   find results_stage1/pilot/eval -type f -name 'step*.npz' ! -name '*_controls.npz' | wc -l   (names only; must print 0 = the full evaluation at B never ran; if not 0, STOP and report)
   ls results_stage1/pilot/models/R1/CONT/M/steps100000/seed0/   (names only: confirm a 50000-step checkpoint exists; do not load anything)
   nvidia-smi   (report the processes using the GPU; the benchmark runs alongside them, as the pilot did)
2. tmux new -d -s s1bench "bash pilot_tooling/concurrency_benchmark.sh"
3. Wait with ONE background waiter (your run-in-background facility) that ends when results_stage1/concurrency_bench/BENCH_DONE.json exists; do not poll in a loop.
   On-demand progress only: tail -3 results_stage1/concurrency_bench/bench_log.txt
4. When BENCH_DONE.json exists:
   git checkout -b results-stage1-concurrency-bench
   git add -f results_stage1/concurrency_bench
   git diff --cached --name-only | grep -E "results_stage1/pilot/|\.pt$" && echo "STOP: forbidden file staged"   (must print nothing)
   find results_stage1/concurrency_bench -type f -size +2M   (must print nothing)
   git commit -m "Stage 1 concurrency benchmark (frozen J0 script, size M, concurrency 8/12/16; no models saved)" && git push -u origin results-stage1-concurrency-bench   (never main, never --force)
   git checkout stage1-planning
5. Report: the eval-file count from step 1, the checkpoint listing, BENCH_DONE.json, the "concurrency N (size M): ... aggregate steps/s" lines from bench_log.txt, any SKIPPED line, and the commit hash.
```
