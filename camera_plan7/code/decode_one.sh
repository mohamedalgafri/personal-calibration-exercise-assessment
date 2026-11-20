#!/usr/bin/env bash
# Decode a prepared video, restricting writes to its validated recording directory.
set -euo pipefail
cd "$(dirname "$0")/.."
id="${1:-}"
if [[ ! "$id" =~ ^PM_[0-9]{3}$ ]]; then echo "Expected a recording ID such as PM_013." >&2; exit 1; fi
source_video="data/raw/$id-Camera17-30fps.mp4"
prepared_video="data/intra/$id.mp4"
if [[ ! -f "$source_video" || ! -f "$prepared_video" ]]; then echo "Both original and prepared video are required for $id." >&2; exit 1; fi
n="$(ffprobe -v error -count_packets -select_streams v:0 -show_entries stream=nb_read_packets -of csv=p=0 "$source_video" | tr -d ',')"
if [[ ! "$n" =~ ^[0-9]+$ || "$n" == 0 ]]; then echo "Invalid source frame count for $id." >&2; exit 1; fi
directory="data/frames/$id"
if [[ -f "$directory/.done" && "$(cat "$directory/.done")" == "$n" ]]; then exit 0; fi
rm -rf -- "$directory"
mkdir -p "$directory"
ffmpeg -v error -threads 1 -i "$prepared_video" -q:v 2 -start_number 0 "$directory/%06d.jpg"
shopt -s nullglob
frames=("$directory"/*.jpg)
count="${#frames[@]}"
if [[ "$count" != "$n" ]]; then echo "COUNT MISMATCH: $id has $count images, expected $n." >&2; exit 1; fi
printf '%s\n' "$n" > "$directory/.done"
echo "$id: $count frames; count matches source."
