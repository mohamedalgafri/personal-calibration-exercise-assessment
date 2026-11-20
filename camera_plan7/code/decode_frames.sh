#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
shopt -s nullglob
videos=(data/intra/PM_*.mp4)
ids=()
for video in "${videos[@]}"; do
  name="${video##*/}"
  id="${name%.mp4}"
  [[ "$id" =~ ^PM_[0-9]{3}$ ]] && ids+=("$id")
done
if [[ ${#ids[@]} == 0 ]]; then echo "No complete prepared videos; see DATA.md." >&2; exit 1; fi
printf '%s\0' "${ids[@]}" | xargs -0 -P 4 -n 1 bash ./code/decode_one.sh
