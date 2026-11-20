#!/usr/bin/env bash
# Optional, local-only acquisition of the 25 original videos and intra-frame re-encoding.
set -euo pipefail
cd "$(dirname "$0")/.."
command -v ffmpeg >/dev/null || { echo "ffmpeg is required for optional video preparation." >&2; exit 1; }
INDEX=feasibility_2026-11-16/rehab24/index_videos.json
FETCH=camera_feasibility/tools/fetch_member.py
mkdir -p camera_plan7/data/raw camera_plan7/data/intra
IDS="Ex1/PM_000 Ex1/PM_001 Ex1/PM_002 Ex1/PM_012 Ex1/PM_016 Ex1/PM_023 Ex1/PM_024 Ex1/PM_032 Ex1/PM_039 Ex1/PM_101 Ex1/PM_109 Ex1/PM_114 Ex1/PM_122 Ex2/PM_003 Ex2/PM_004 Ex2/PM_013 Ex2/PM_014 Ex2/PM_025 Ex2/PM_026 Ex2/PM_033 Ex2/PM_040 Ex2/PM_102 Ex2/PM_110 Ex2/PM_115 Ex2/PM_123"
for entry in $IDS; do
  id="${entry#*/}"
  if [[ -s "camera_plan7/data/intra/$id.mp4" ]]; then echo "Existing prepared video: $id"; continue; fi
  python3 -P "$FETCH" "$INDEX" "$entry-Camera17-30fps.mp4" "camera_plan7/data/raw/$id-Camera17-30fps.mp4"
  ffmpeg -v error -y -i "camera_plan7/data/raw/$id-Camera17-30fps.mp4" -an -c:v libx264 -g 1 -crf 18 "camera_plan7/data/intra/${id}_preparing.mp4"
  mv "camera_plan7/data/intra/${id}_preparing.mp4" "camera_plan7/data/intra/$id.mp4"
done
