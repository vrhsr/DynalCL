#!/usr/bin/env bash
# Concurrency benchmark before Amendment 2 (user condition 3, 2026-10-27). NOT part of any frozen set: orchestration only.
# Calls the FROZEN J0 script (scripts/stage1_j0_benchmark.py) unchanged, size M only, once per concurrency level, so an
# out-of-memory failure at a high level cannot lose the lower levels. Random UNIF training sequences only (seed role
# j0_benchmark), no model is saved (out_dir None), nothing is evaluated, no pilot file is read or written.
# Usage (box, repository root, inside tmux):  bash pilot_tooling/concurrency_benchmark.sh
# Output: results_stage1/concurrency_bench/  (c<N>/j0.json, bench_log.txt, gpu_telemetry.txt, BENCH_DONE.json)
# Expected runtime: about 12-15 min on the shared A4000.
set -u
OUT=results_stage1/concurrency_bench
PY=.venv-stage1/bin/python
STEPS=1500
LEVELS="8 12 16"
MIB_PER_PROCESS=600          # pilot: 8 processes used about 3.6 GB (about 450 MiB each); 600 leaves headroom
MARGIN_MIB=500
mkdir -p "$OUT"
log() { echo "$(date -u +%FT%TZ) $*" | tee -a "$OUT/bench_log.txt"; }
free_mib() { nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits | head -1 | tr -d ' '; }

( while true; do
    echo "$(date -u +%FT%TZ) gpu $(nvidia-smi --query-gpu=temperature.gpu,utilization.gpu,memory.used,power.draw --format=csv,noheader 2>&1)" >> "$OUT/gpu_telemetry.txt"
    nvidia-smi --query-compute-apps=pid,used_memory --format=csv,noheader 2>&1 | sed "s/^/$(date -u +%FT%TZ) app /" >> "$OUT/gpu_telemetry.txt"
    sleep 15
  done ) &
TELEMETRY=$!
trap 'kill $TELEMETRY 2>/dev/null' EXIT

nvidia-smi > "$OUT/nvidia_smi_start.txt" 2>&1
git rev-parse HEAD > "$OUT/git_head.txt"
RESULTS=""
for C in $LEVELS; do
  NEED=$((C * MIB_PER_PROCESS + MARGIN_MIB)); FREE=$(free_mib)
  if [ "${FREE:-0}" -lt "$NEED" ]; then
    log "concurrency $C SKIPPED: free ${FREE} MiB < needed ${NEED} MiB"
    RESULTS="$RESULTS\"c$C\": \"skipped (free ${FREE} MiB < ${NEED} MiB)\", "
    continue
  fi
  log "concurrency $C start (free ${FREE} MiB)"
  $PY scripts/stage1_j0_benchmark.py --device cuda --sizes M --steps $STEPS --concurrency $C --out "$OUT/c$C" \
    >> "$OUT/bench_log.txt" 2>&1
  RC=$?
  log "concurrency $C rc=$RC"
  RESULTS="$RESULTS\"c$C\": $RC, "
done
nvidia-smi > "$OUT/nvidia_smi_end.txt" 2>&1
printf '{%s"steps": %d, "finished_utc": "%s"}\n' "$RESULTS" $STEPS "$(date -u +%FT%TZ)" > "$OUT/BENCH_DONE.json"
log "done"
