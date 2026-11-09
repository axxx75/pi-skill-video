#!/usr/bin/env bash
# render.sh — check + render + normalizzazione loudness del video.
# Uso: bash render.sh [file.mp4 di output]   (default: video/renders/<nome>.mp4 normalizzato)
set -euo pipefail
cd "$(dirname "$0")/../../.."   # dalla skill alla cartella di lavoro del video

HF="npx -y hyperframes@0.9.26"
OUT="${1:-}"

$HF check

echo "== render =="
$HF render 2>&1 | tail -8
SRC=$(ls -t video/renders/*.mp4 | head -1)
[ -n "$OUT" ] || OUT="video/renders/final.mp4"

echo "== loudness (target -16 LUFS, TP -1.5) =="
ffmpeg -hide_banner -nostats -i "$SRC" -af ebur128=peak=true -f null - 2>&1 \
  | awk '/Integrated loudness/{getline; print "prima: " $2 " LUFS"}'
ffmpeg -hide_banner -v error -y -i "$SRC" \
  -af "loudnorm=I=-16:TP=-1.5:LRA=11" -c:v copy -c:a aac -b:a 192k "$OUT"
ffmpeg -hide_banner -nostats -i "$OUT" -af ebur128=peak=true -f null - 2>&1 \
  | awk '/Integrated loudness/{getline; print "dopo:  " $2 " LUFS"}'
ffprobe -v error -show_entries format=duration,size -of default=nw=1 "$OUT"
echo "$OUT"
