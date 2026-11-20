#!/usr/bin/env bash
# Downloads only the files the analyses need, from the datasets' official Zenodo records, by HTTP range requests.
# Resumable: run it again if the connection drops. Needs: python3, curl. Sizes are approximate.
set -euo pipefail
cd "$(dirname "$0")"
part="${1:-all}"   # all | phytmo | gaitex | camera

if [[ $part == all || $part == phytmo ]]; then
  echo "== PHYTMO (Zenodo 5052756, CC BY 4.0): inertial + optical rigid bodies, ~3.4 GB on disk"
  WANT_ALL=SQT,HAA,SQZ,EAH,EFE WANT_LEG=KFE OPT_EX=SQT,HAA,SQZ,EAH \
    python3 -P phytmo_pilot/code/fetch_members.py phytmo_pilot/data/zip_index.json phytmo_pilot/data/raw
fi
if [[ $part == all || $part == gaitex ]]; then
  echo "== GAITEX (Zenodo 15729056, CC BY 4.0): RD and RGS exercises, ~0.8 GB"
  python3 -P gaitex_plan6/code/fetch_gaitex.py feasibility_2026-11-16/gaitex_zip_index.json gaitex_plan6/data/raw
fi
if [[ $part == all || $part == camera ]]; then
  echo "== REHAB24-6 (Zenodo 13305826, CC BY-NC 4.0): 2D motion capture of camera 17 for 25 videos, ~33 MB"
  python3 -P tools/fetch_rehab_annotations.py
  IDS="Ex1/PM_000 Ex1/PM_001 Ex1/PM_002 Ex1/PM_012 Ex1/PM_016 Ex1/PM_023 Ex1/PM_024 Ex1/PM_032 Ex1/PM_039 Ex1/PM_101 Ex1/PM_109 Ex1/PM_114 Ex1/PM_122 Ex2/PM_003 Ex2/PM_004 Ex2/PM_013 Ex2/PM_014 Ex2/PM_025 Ex2/PM_026 Ex2/PM_033 Ex2/PM_040 Ex2/PM_102 Ex2/PM_110 Ex2/PM_115 Ex2/PM_123"
  mkdir -p camera_plan7/data/raw
  for e in $IDS; do
    id=${e#*/}
    python3 -P camera_feasibility/tools/fetch_member.py feasibility_2026-11-16/rehab24/index_2d_joints.json "$e-c17-30fps.npy" "camera_plan7/data/raw/$id-c17-30fps.npy" | tail -1
  done
  echo "Keypoints are not redistributed: obtain the source videos and extract them locally, as described in DATA.md."
  echo "Optional (only to repeat the in-browser extraction): see DATA.md for the videos."
fi
