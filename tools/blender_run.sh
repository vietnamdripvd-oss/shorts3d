#!/usr/bin/env bash
# Wrapper: pakai GPU/EGL kalau ada, kalau nggak ada display -> xvfb + software GL (mesa llvmpipe).
# Pakai: tools/blender_run.sh -b file.blend -P script.py -- args
BL="${BLENDER:-blender}"
if [ -n "${DISPLAY:-}" ] || [ "${BLENDER_HEADLESS_OK:-0}" = "1" ]; then
  exec "$BL" "$@"
else
  exec xvfb-run -a -s "-screen 0 1920x1080x24" "$BL" "$@"
fi
