#!/usr/bin/env bash
# render.sh — check + render + normalizzazione loudness del video.
# Va eseguito DALLA cartella di lavoro del video (quella con scenes.json e video/).
# Uso: bash <skill>/scripts/render.sh [file.mp4 di output]
set -euo pipefail
[ -f video/index.html ] || { echo "esegui render.sh dalla cartella del video (manca video/index.html)"; exit 2; }
CALLER="$(pwd)"
HF="npx -y hyperframes@0.9.26"

# HyperFrames legge il progetto dalla cwd: si entra in video/ per check e render.
cd video
$HF check

echo "== render =="
$HF render 2>&1 | tail -8
SRC="$(ls -t renders/*.mp4 | head -1)"
[ -n "${1:-}" ] && OUT="$1" || OUT="$CALLER/video/renders/final.mp4"

echo "== loudness (target -16 LUFS, TP -1.5) =="
ffmpeg -hide_banner -nostats -i "$SRC" -af ebur128=peak=true -f null - 2>&1 \
  | awk '/Integrated loudness/{getline; print "prima: " $2 " LUFS"}'
ffmpeg -hide_banner -v error -y -i "$SRC" \
  -af "loudnorm=I=-16:TP=-1.5:LRA=11" -c:v copy -c:a aac -b:a 192k "$OUT"
ffmpeg -hide_banner -nostats -i "$OUT" -af ebur128=peak=true -f null - 2>&1 \
  | awk '/Integrated loudness/{getline; print "dopo:  " $2 " LUFS"}'
ffprobe -v error -show_entries format=duration,size -of default=nw=1 "$OUT"
echo "$OUT"
