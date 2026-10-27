#!/usr/bin/env bash
# Stage 1A confirmatory run, one phase per authorization artifact. NOT part of the frozen set: orchestration only; the
# frozen runner's gate checks the v3 freeze, the artifact (HMAC under the user's key), the bound pilot decision and the run
# lock when each subcommand starts. Plan and key handling: pilot_tooling/STAGE1_CONFIRMATORY_PLAN.md.
# Usage (box, repository root, inside tmux; ONLY after the user approved this phase in the box session):
#   bash pilot_tooling/run_stage1_confirmatory.sh <train|evaluate-analyze> <expected v3 manifest sha256> <run id> \
#        <artifact path (outside the repo)> <key file (outside the repo; shredded at start)> [workers] [eval device]
# Progress: cat results_stage1/confirmatory/<run id>/CURRENT_STEP ; tail -3 results_stage1/confirmatory/<run id>/run_log.txt
# Completion marker: results_stage1/confirmatory/<run id>/DONE_<phase>.json  {"stage": ..., "rc": ...}
set -u
PHASE="${1:?phase}"; EXPECTED="${2:?v3 manifest sha256}"; RUN_ID="${3:?run id}"; ART="${4:?artifact}"; KEYFILE="${5:?key file}"
WORKERS="${6:-8}"; EVAL_DEVICE="${7:-cpu}"
PY=${PY:-.venv-stage1/bin/python}                 # overrides exist only for the local dry run
OUT="${OUTROOT:-results_stage1/confirmatory}/$RUN_ID"
DECISION=results_stage1/pilot/pilot_decision_v3_final.json
mkdir -p "$OUT"

# the key lives only in this process's environment: read it, then destroy the file before anything else runs
[ -f "$KEYFILE" ] || { echo "key file missing" >&2; exit 2; }
DYNAICL_STAGE1_AUTH_KEY="$(cat "$KEYFILE")"; export DYNAICL_STAGE1_AUTH_KEY
shred -u "$KEYFILE" 2>/dev/null || rm -f "$KEYFILE"

step() { echo "$1 $(date -u +%FT%TZ)" > "$OUT/CURRENT_STEP"; echo "$(date -u +%FT%TZ) step $1" >> "$OUT/wrapper_log.txt"; }
finish() {
  printf '{"stage": "%s", "rc": %d, "finished_utc": "%s"}\n' "$1" "$2" "$(date -u +%FT%TZ)" > "$OUT/DONE_$PHASE.json"
  nvidia-smi > "$OUT/nvidia_smi_end_$PHASE.txt" 2>&1
  exit 0
}
( while true; do
    echo "$(date -u +%FT%TZ) $(nvidia-smi --query-gpu=temperature.gpu,utilization.gpu,memory.used --format=csv,noheader 2>&1)" \
      >> "$OUT/gpu_telemetry.txt"
    sleep 300
  done ) &
TELEMETRY=$!
trap 'kill $TELEMETRY 2>/dev/null' EXIT

echo "$(date -u +%FT%TZ) phase $PHASE run $RUN_ID artifact sha256 $(sha256sum "$ART" | cut -d' ' -f1) decision sha256 $(sha256sum "$DECISION" | cut -d' ' -f1) workers $WORKERS eval_device $EVAL_DEVICE" \
  >> "$OUT/wrapper_log.txt"
git rev-parse HEAD > "$OUT/git_head_$PHASE.txt"
git status --porcelain --untracked-files=no > "$OUT/git_status_tracked_$PHASE.txt"
nvidia-smi > "$OUT/nvidia_smi_start_$PHASE.txt" 2>&1
GATE=(--manifest docs/FREEZE_MANIFEST_STAGE1_v3.json --expected-manifest-sha256 "$EXPECTED"
      --snapshot dist/stage1_frozen_snapshot_v3.zip --authorization "$ART" --run-id "$RUN_ID" --decision "$DECISION")

case "$PHASE" in
  train)
    step train
    $PY scripts/stage1_run.py train --config config/stage1.yaml --out "$OUT" --workers "$WORKERS" --device cuda \
      "${GATE[@]}" >> "$OUT/train_stdout.txt" 2>&1 || finish train $?
    ;;
  evaluate-analyze)
    step evaluate
    $PY scripts/stage1_run.py evaluate --config config/stage1.yaml --out "$OUT" --device "$EVAL_DEVICE" \
      "${GATE[@]}" >> "$OUT/eval_stdout.txt" 2>&1 || finish evaluate $?
    step analyze
    $PY scripts/stage1_run.py analyze --config config/stage1.yaml --out "$OUT" \
      "${GATE[@]}" >> "$OUT/analyze_stdout.txt" 2>&1 || finish analyze $?
    ;;
  *) echo "unknown phase $PHASE" >&2; finish unknown_phase 2 ;;
esac
unset DYNAICL_STAGE1_AUTH_KEY
step "done_$PHASE"
finish "done_$PHASE" 0
