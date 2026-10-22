#!/usr/bin/env bash
# DynaICL Stage 0: long validation pipeline for a remote machine. CPU only; no GPU is used.
#
# What it runs:
#   1. the full pytest suite (baseline), with junit XML
#   2. the full mutation-detection matrix: every validation check under every injected bug, and the
#      whole pytest suite under every bug (scripts/mutation_report.py --pytest)
#   3. optionally (RUN_EXPERIMENT=1) the main separability experiment, for a cross-machine comparison
#
# Expected wall time on a modern 8+ core box: about 25 min for the check matrix (single process, by design:
# mutations patch module state in-process) plus about 8 min for the six pytest-suite runs at JOBS=6.
#
# Usage (from the repository root):
#   bash scripts/remote_validation_pipeline.sh                # JOBS=6 by default
#   JOBS=12 RUN_EXPERIMENT=1 bash scripts/remote_validation_pipeline.sh
#
# Send back: the printed remote_results_<UTC>.tar.gz (or just its matrix.md and pytest_baseline.txt).
set -euo pipefail
cd "$(dirname "$0")/.."

JOBS="${JOBS:-6}"
RUN_EXPERIMENT="${RUN_EXPERIMENT:-0}"
PY="${PYTHON:-python3}"
OUT="remote_results_$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$OUT"

echo "== environment" | tee "$OUT/environment.txt"
{ "$PY" --version; "$PY" -c "import numpy, scipy, yaml, pytest; print('numpy', numpy.__version__, 'scipy', scipy.__version__, 'pyyaml', yaml.__version__, 'pytest', pytest.__version__)"; uname -a; nproc; } >> "$OUT/environment.txt" 2>&1 || true
cat "$OUT/environment.txt"

echo "== 1/3 full pytest suite (baseline)"
set +e
"$PY" -m pytest -q -p no:cacheprovider -rfE --durations=10 --junitxml="$OUT/junit_baseline.xml" 2>&1 | tee "$OUT/pytest_baseline.txt"
PYTEST_STATUS=${PIPESTATUS[0]}
set -e

echo "== 2/3 mutation-detection matrix (checks + pytest under each mutation, JOBS=$JOBS)"
set +e
"$PY" scripts/mutation_report.py --pytest --jobs "$JOBS" 2>&1 | tee "$OUT/mutation_report.txt"
MUTATION_STATUS=${PIPESTATUS[0]}
set -e
latest=$(ls -dt runs/mutation_report_* | head -1)
cp -r "$latest" "$OUT/"

if [ "$RUN_EXPERIMENT" = "1" ]; then
  echo "== 3/3 main separability experiment"
  "$PY" -m dynaicl.experiments.separability --config config/separability.yaml --workers "$JOBS" 2>&1 | tee "$OUT/experiment.txt"
  exp=$(head -1 "$OUT/experiment.txt")   # the CLI prints the run directory first
  [ -d "$exp" ] && cp -r "$exp" "$OUT/"
fi

echo "pytest_exit=$PYTEST_STATUS mutation_report_exit=$MUTATION_STATUS" | tee "$OUT/STATUS.txt"
tar czf "$OUT.tar.gz" "$OUT"
echo "== done: $OUT.tar.gz"
echo "   (mutation_report exits 1 if any mutation is undetected or any baseline check fails)"
