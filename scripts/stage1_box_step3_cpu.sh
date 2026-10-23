#!/usr/bin/env bash
# Stage 1 step 3, box CPU jobs (no GPU training; the GPU is only queried for temperature/utilisation).
# Run inside tmux from the repository root:  bash scripts/stage1_box_step3_cpu.sh
# Writes results_stage1/step3/STEP3_DONE.json at the end (exit codes of every job).
set -u
OUT=results_stage1/step3
mkdir -p "$OUT"
PY=.venv-stage1/bin/python
gpu() { nvidia-smi --query-gpu=temperature.gpu,utilization.gpu,memory.used --format=csv,noheader 2>/dev/null || echo "no nvidia-smi"; }
echo "start $(date -u +%FT%TZ) gpu: $(gpu)" > "$OUT/gpu_log.txt"

$PY scripts/stage1_env_manifest.py --out "$OUT/STAGE1_ENVIRONMENT_MANIFEST.json" > "$OUT/env.log" 2>&1
ENV_RC=$?
$PY -m pytest tests_stage1 -q -p no:cacheprovider < /dev/null > "$OUT/tests.log" 2>&1
TEST_RC=$?

# F1 separability map (frozen-stack venv is enough: numpy/scipy only) and OC v2, concurrently
.venv/bin/python scripts/stage1_f1_map.py --out results_stage1/map_F1 --workers 20 > "$OUT/f1_map.log" 2>&1 &
F1_PID=$!
.venv/bin/python scripts/stage1_operating_characteristics.py --part all --out results_stage1/oc_1A_v2 > "$OUT/oc_v2.log" 2>&1
OC_RC=$?
wait $F1_PID
F1_RC=$?

echo "end $(date -u +%FT%TZ) gpu: $(gpu)" >> "$OUT/gpu_log.txt"
printf '{"env": %d, "tests": %d, "f1_map": %d, "oc_v2": %d, "finished_utc": "%s"}\n' \
  $ENV_RC $TEST_RC $F1_RC $OC_RC "$(date -u +%FT%TZ)" > "$OUT/STEP3_DONE.json"
