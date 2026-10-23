#!/usr/bin/env bash
# Stage 1 step 3, GPU jobs: J0 throughput benchmark and the UNIF-only engineering smoke test.
# Run ONLY after the user says the GPU is free, inside tmux, from the repository root:
#   bash scripts/stage1_box_j0_smoke.sh
# Writes results_stage1/j0/j0.json, results_stage1/eng_smoke/eng_smoke.json and results_stage1/gpu_jobs/GPU_JOBS_DONE.json.
set -u
OUT=results_stage1/gpu_jobs
mkdir -p "$OUT" results_stage1/j0 results_stage1/eng_smoke
PY=.venv-stage1/bin/python
gpu() { nvidia-smi --query-gpu=temperature.gpu,utilization.gpu,memory.used --format=csv,noheader 2>/dev/null || echo "no nvidia-smi"; }
echo "start $(date -u +%FT%TZ) gpu: $(gpu)" > "$OUT/gpu_log.txt"
nvidia-smi > "$OUT/nvidia_smi_start.txt" 2>&1

$PY scripts/stage1_j0_benchmark.py --device cuda --out results_stage1/j0 > "$OUT/j0.log" 2>&1
J0_RC=$?
echo "after J0 $(date -u +%FT%TZ) gpu: $(gpu)" >> "$OUT/gpu_log.txt"
$PY scripts/stage1_engineering_smoke.py --device cuda --steps 5000 --out results_stage1/eng_smoke > "$OUT/eng_smoke.log" 2>&1
SMOKE_RC=$?

echo "end $(date -u +%FT%TZ) gpu: $(gpu)" >> "$OUT/gpu_log.txt"
nvidia-smi > "$OUT/nvidia_smi_end.txt" 2>&1
printf '{"j0": %d, "eng_smoke": %d, "finished_utc": "%s"}\n' $J0_RC $SMOKE_RC "$(date -u +%FT%TZ)" > "$OUT/GPU_JOBS_DONE.json"
