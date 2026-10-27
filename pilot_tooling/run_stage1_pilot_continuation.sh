#!/usr/bin/env bash
# Stage 1A pilot continuation under Amendment 2 (freeze v3). NOT part of the frozen set: orchestration only; every
# computation is done by the frozen runner. Runs strictly in order, on the EXISTING pilot models (nothing is retrained):
#   verify v3 -> the original v2 decision must equal its frozen copy -> no full-evaluation file may exist yet
#   -> keep the original decision aside -> pilot-decide (expects NEEDS FULL EVALUATION AT B under the 128 h cap)
#   -> full evaluation at B on CPU -> pilot-decide again (final decision; M from the frozen lookup).
# Usage (box, repository root, inside tmux):  bash pilot_tooling/run_stage1_pilot_continuation.sh <expected v3 manifest sha256>
# Progress: cat results_stage1/pilot/CURRENT_STEP ; tail -3 results_stage1/pilot/run_log.txt
# Completion marker: results_stage1/pilot/CONTINUATION_DONE.json  {"stage": ..., "rc": ...}
# Never reads, prints or summarises anything under results_stage1/pilot/eval/ (the full evaluation at B holds pilot effect
# information that only the frozen rule may use, and only for between-seed sds); it only counts file names there.
set -u
EXPECTED="${1:?usage: run_stage1_pilot_continuation.sh <expected v3 manifest sha256>}"
OUT=${OUT:-results_stage1/pilot}                     # overrides exist only for the local dry run
FROZEN=${FROZEN:-results_stage1/pilot_outcome_v2}
PY=${PY:-.venv-stage1/bin/python}
MANIFEST=${MANIFEST:-docs/FREEZE_MANIFEST_STAGE1_v3.json}
PILOT_CFG=${PILOT_CFG:-config/stage1_pilot.yaml}
LOG="$OUT/continuation_log.txt"

step() { echo "$1 $(date -u +%FT%TZ)" > "$OUT/CURRENT_STEP"; echo "$(date -u +%FT%TZ) step $1" >> "$LOG"; }
finish() {
  printf '{"stage": "%s", "rc": %d, "note": "%s", "finished_utc": "%s"}\n' "$1" "$2" "${3:-}" "$(date -u +%FT%TZ)" \
    > "$OUT/CONTINUATION_DONE.json"
  exit 0
}
full_eval_files() { find "$OUT/eval" -type f -name 'step*.npz' ! -name '*_controls.npz' 2>/dev/null | wc -l; }
status_of() { $PY -c "import json, sys; print(json.load(open(sys.argv[1]))['status'])" "$1"; }

[ -d "$OUT/models" ] || { echo "no pilot models in $OUT" >&2; exit 2; }
step verify_v3
$PY scripts/stage1_freeze.py verify --manifest "$MANIFEST" --expected-sha256 "$EXPECTED" \
  >> "$LOG" 2>&1 || finish verify_v3 3 "v3 freeze does not verify"
git rev-parse HEAD > "$OUT/continuation_git_head.txt"
git status --porcelain --untracked-files=no > "$OUT/continuation_git_status_tracked.txt"

step check_original
ORIG=$(sha256sum "$OUT/pilot_decision.json" | cut -d' ' -f1)
FRZ=$(sha256sum "$FROZEN/pilot_decision.json" | cut -d' ' -f1)
[ "$ORIG" = "$FRZ" ] || finish check_original 3 "pilot_decision.json differs from the frozen original ($ORIG vs $FRZ)"
N=$(full_eval_files)
[ "$N" -eq 0 ] || finish check_original 3 "$N full-evaluation files already exist: no compute amendment is allowed (user condition 2)"
[ -e "$OUT/pilot_decision_v2_original.json" ] || cp "$OUT/pilot_decision.json" "$OUT/pilot_decision_v2_original.json"
cmp -s "$OUT/pilot_decision_v2_original.json" "$FROZEN/pilot_decision.json" || finish check_original 3 "kept original differs"

DECIDE=(scripts/stage1_run.py pilot-decide --config "$PILOT_CFG" --out "$OUT"
        --confirmatory-config config/stage1.yaml --j0 results_stage1/j0/j0.json
        --smoke results_stage1/eng_smoke/eng_smoke.json)
step decide_v3_pass1
$PY "${DECIDE[@]}" >> "$OUT/decide_stdout.txt" 2>&1 || finish decide_v3_pass1 $?
cp "$OUT/pilot_decision.json" "$OUT/pilot_decision_v3_pass1.json"
STATUS=$(status_of "$OUT/pilot_decision_v3_pass1.json")
[ "$STATUS" = "NEEDS FULL EVALUATION AT B" ] || finish decide_v3_pass1 4 "unexpected status: $STATUS"

step evaluate_full
T0=$(date +%s)
$PY scripts/stage1_run.py evaluate --config "$PILOT_CFG" --out "$OUT" \
  --decision "$OUT/pilot_decision_v3_pass1.json" --device cpu >> "$OUT/eval_stdout.txt" 2>&1 || finish evaluate_full $?
echo "$(date -u +%FT%TZ) full evaluation at B: $(( $(date +%s) - T0 )) s for $(full_eval_files) files" >> "$LOG"

step decide_v3_final
$PY "${DECIDE[@]}" >> "$OUT/decide_stdout.txt" 2>&1 || finish decide_v3_final $?
cp "$OUT/pilot_decision.json" "$OUT/pilot_decision_v3_final.json"
step done
finish done 0 "$(status_of "$OUT/pilot_decision_v3_final.json")"
