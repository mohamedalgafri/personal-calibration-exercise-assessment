#!/usr/bin/env bash
# Reproduce the core studies in a separate workspace; skip completed outputs to resume.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
R="$ROOT/rerun_workspace"
if [[ ! -d "$R" ]]; then echo "Run bash rerun_guide/setup_rerun.sh first." >&2; exit 1; fi
P="$R/RERUN_PROGRESS.txt"
say() { echo "[$(date '+%H:%M:%S')] $*" | tee -a "$P"; }
step() {
  local label="$1" directory="$2" expected="$3"
  shift 3
  if [[ -s "$R/$expected" ]]; then say "SKIP $label (existing output; use a fresh workspace for a fresh run)"; return; fi
  say "START $label"
  if ! (cd "$R/$directory" && "$@") >> "$R/${label// /_}.log" 2>&1; then
    say "FAILED $label; inspect $R/${label// /_}.log"; exit 1
  fi
  if [[ ! -s "$R/$expected" ]]; then say "FAILED $label: expected output missing"; exit 1; fi
  say "DONE $label"
}
say "=== reproduction started ==="
step "Study 1 PHYTMO" phytmo_pilot/code phytmo_pilot/results/plan5/results_plan5.json python3 -P run_plan5.py ../data/raw ../results/plan5
step "Study 1 distribution" phytmo_pilot/code phytmo_pilot/results/plan5/posthoc_distribution_B16.json python3 -P posthoc_plan5_distribution.py
step "Pilot 4" phytmo_pilot/code phytmo_pilot/results/pilot4/results_pilot4.json python3 -P run_pilot4.py ../data/raw ../results/pilot4
step "Study 2 GAITEX" gaitex_plan6/code gaitex_plan6/results/results_plan6.json python3 -P run_plan6.py ../data/raw ../results
step "Study 2 diagnostic" gaitex_plan6/code gaitex_plan6/results/posthoc_uninvolved_sensors_RD.md python3 -P posthoc_uninvolved_sensors.py ../data/raw ../results/posthoc_uninvolved_sensors_RD.md
step "Study 3 MLP" stronger_plan8/code stronger_plan8/results/results_plan8.json python3 -P run_plan8.py
if [[ -d "$R/camera_plan7" ]]; then
  step "Camera primary" camera_plan7 camera_plan7/results/results_plan7.json python3 -P code/run_plan7.py
  step "Camera front" camera_plan7 camera_plan7/results/results_plan7_front.json python3 -P code/run_plan7.py --front
else
  say "Camera not included: see DATA.md. The comparison report will mark those outputs missing."
fi
say "=== numerical comparison ==="
python3 -P "$ROOT/rerun_guide/compare_rerun.py" | tee -a "$P"
