#!/usr/bin/env bash
# Render lokal tes TAHAP 0. Pakai: test_e2e/render.sh [pct=100]
set -euo pipefail
cd "$(dirname "$0")/.."
PCT=${1:-100}
blender -b -P test_e2e/scene.py -- --out test_e2e/scene.blend
blender -b test_e2e/scene.blend -P tools/render_frames.py -- --out test_e2e/render/frames_$PCT --pct $PCT
tools/encode.sh test_e2e/render/frames_$PCT test_e2e/render/test_e2e_$PCT.mp4
