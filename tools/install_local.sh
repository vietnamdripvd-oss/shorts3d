#!/usr/bin/env bash
# Install Blender 4.2 LTS portable + ffmpeg + EGL (Ubuntu/Debian). Jalanin sekali.
set -euo pipefail
VER=${BLENDER_VER:-4.2.3}; MM=${VER%.*}
DEST=${BLENDER_DIR:-/opt/blender}
sudo apt-get update -qq
sudo apt-get install -y -qq ffmpeg xvfb libegl1 libegl-mesa0 libgl1 libxi6 libxkbcommon0 libxrender1 libsm6
sudo mkdir -p "$DEST"
curl -sSLf "https://download.blender.org/release/Blender$MM/blender-$VER-linux-x64.tar.xz" | sudo tar xJ -C "$DEST"
sudo ln -sf "$DEST/blender-$VER-linux-x64/blender" /usr/local/bin/blender
blender --version | head -1
blender -b --factory-startup -P "$(dirname "$0")/gpu_info.py" 2>&1 | grep "\[gpu\]"
