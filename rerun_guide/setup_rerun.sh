#!/usr/bin/env bash
# Copy code to an isolated workspace; link user-downloaded data read-only by convention.
set -euo pipefail
cd "$(dirname "$0")/.."
R=rerun_workspace
if [[ -e "$R" ]]; then
  echo "rerun_workspace already exists. Keep it to resume, or move it aside before a fresh setup." >&2
  exit 1
fi
for study in phytmo_pilot gaitex_plan6; do
  if [[ ! -d "$study/data/raw" ]]; then
    echo "Missing $study/data/raw. Obtain the study data with bash get_data.sh first." >&2
    exit 1
  fi
done
mkdir -p "$R"
for study in phytmo_pilot gaitex_plan6; do
  mkdir -p "$R/$study/results"
  cp -r "$study/code" "$R/$study/"
  ln -s "$PWD/$study/data" "$R/$study/data"
done
mkdir -p "$R/phytmo_pilot/results/plan5" "$R/phytmo_pilot/results/pilot4" "$R/stronger_plan8/results"
cp -r stronger_plan8/code "$R/stronger_plan8/"
ln -s "$PWD/feasibility_2026-11-16" "$R/feasibility_2026-11-16"
shopt -s nullglob
points=(camera_plan7/results/PM_*_jpg1.json)
if [[ ${#points[@]} -gt 0 && -f feasibility_2026-11-16/rehab24/Segmentation.csv && -d camera_plan7/data/raw ]]; then
  mkdir -p "$R/camera_plan7/results"
  cp -r camera_plan7/code "$R/camera_plan7/"
  ln -s "$PWD/camera_plan7/data" "$R/camera_plan7/data"
  cp "${points[@]}" camera_plan7/results/extraction_log.jsonl "$R/camera_plan7/results/"
  echo "Camera workspace included. All required keypoint files must be present for a complete camera reproduction."
else
  echo "Camera workspace omitted: obtain the reference data and extract keypoints locally first (DATA.md)."
fi
echo "Ready: $PWD/$R. Saved study results outside this workspace are unchanged."
