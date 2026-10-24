#!/usr/bin/env bash
# Stage 1A pilot wrapper. NOT part of the frozen set: orchestration only; every computation is done by the frozen runner
# (scripts/stage1_run.py) and the frozen freeze tool. Runs the pre-registered pilot steps strictly in order:
#   verify the v2 freeze -> train (GPU) -> controls + validation-NLL evaluation at every checkpoint (CPU) -> pilot-decide
#   -> if needed, full evaluation at B (CPU) -> pilot-decide again.
# Usage (box, repository root, inside tmux):  bash pilot_tooling/run_stage1_pilot.sh <expected v2 manifest sha256>
# Progress: cat results_stage1/pilot/CURRENT_STEP ; tail -3 results_stage1/pilot/run_log.txt
# Completion marker: results_stage1/pilot/PILOT_DONE.json  {"stage": ..., "rc": ...}
# Never reads, prints or summarises anything under results_stage1/pilot/eval/ (per-context statistics; the full evaluation at
# B contains effect information that only the frozen pilot rule may use, and only to compute between-seed sds).
set -u
EXPECTED="${1:?usage: run_stage1_pilot.sh <expected v2 manifest sha256>}"
OUT=results_stage1/pilot
PY=.venv-stage1/bin/python
mkdir -p "$OUT"

step() { echo "$1 $(date -u +%FT%TZ)" > "$OUT/CURRENT_STEP"; echo "$(date -u +%FT%TZ) step $1" >> "$OUT/wrapper_log.txt"; }
finish() {
  printf '{"stage": "%s", "rc": %d, "finished_utc": "%s"}\n' "$1" "$2" "$(date -u +%FT%TZ)" > "$OUT/PILOT_DONE.json"
  nvidia-smi > "$OUT/nvidia_smi_end.txt" 2>&1
  exit 0
}

# GPU temperature / utilisation / memory every 5 minutes for the whole pilot
( while true; do
    echo "$(date -u +%FT%TZ) $(nvidia-smi --query-gpu=temperature.gpu,utilization.gpu,memory.used --format=csv,noheader 2>&1)" \
      >> "$OUT/gpu_telemetry.txt"
    sleep 300
  done ) &
TELEMETRY=$!
trap 'kill $TELEMETRY 2>/dev/null' EXIT

step verify
$PY scripts/stage1_freeze.py verify --manifest docs/FREEZE_MANIFEST_STAGE1_v2.json --expected-sha256 "$EXPECTED" \
  >> "$OUT/wrapper_log.txt" 2>&1 || finish verify $?
git rev-parse HEAD > "$OUT/git_head.txt"
git status --porcelain --untracked-files=no > "$OUT/git_status_tracked.txt"
nvidia-smi > "$OUT/nvidia_smi_start.txt" 2>&1

step train
$PY scripts/stage1_run.py train --config config/stage1_pilot.yaml --out "$OUT" --workers 8 --device cuda \
  >> "$OUT/train_stdout.txt" 2>&1 || finish train $?

step evaluate_controls
$PY scripts/stage1_run.py evaluate --config config/stage1_pilot.yaml --out "$OUT" --controls-only --device cpu \
  >> "$OUT/eval_stdout.txt" 2>&1 || finish evaluate_controls $?

DECIDE=(scripts/stage1_run.py pilot-decide --config config/stage1_pilot.yaml --out "$OUT"
        --confirmatory-config config/stage1.yaml --j0 results_stage1/j0/j0.json
        --smoke results_stage1/eng_smoke/eng_smoke.json)
step decide_1
$PY "${DECIDE[@]}" >> "$OUT/decide_stdout.txt" 2>&1 || finish decide_1 $?
cp "$OUT/pilot_decision.json" "$OUT/pilot_decision_pass1.json"
STATUS=$($PY -c "import json; print(json.load(open('$OUT/pilot_decision_pass1.json'))['status'])")

if [ "$STATUS" = "NEEDS FULL EVALUATION AT B" ]; then
  step evaluate_full
  $PY scripts/stage1_run.py evaluate --config config/stage1_pilot.yaml --out "$OUT" \
    --decision "$OUT/pilot_decision_pass1.json" --device cpu >> "$OUT/eval_stdout.txt" 2>&1 || finish evaluate_full $?
  step decide_2
  $PY "${DECIDE[@]}" >> "$OUT/decide_stdout.txt" 2>&1 || finish decide_2 $?
fi

step done
finish done 0
