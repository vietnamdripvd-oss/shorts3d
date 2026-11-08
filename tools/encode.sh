#!/usr/bin/env bash
# encode.sh <frames_dir> <out.mp4> [audio.wav]
set -euo pipefail
FR="$1"; OUT="$2"; AUD="${3:-}"
if [ -n "$AUD" ]; then
  ffmpeg -y -loglevel error -framerate 30 -i "$FR/%05d.png" -i "$AUD" \
    -c:v libx264 -pix_fmt yuv420p -crf 18 -preset medium -c:a aac -b:a 192k -shortest "$OUT"
else
  ffmpeg -y -loglevel error -framerate 30 -i "$FR/%05d.png" \
    -c:v libx264 -pix_fmt yuv420p -crf 18 -preset medium "$OUT"
fi
echo "-> $OUT ($(ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT")s)"
