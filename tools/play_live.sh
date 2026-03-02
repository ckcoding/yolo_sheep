#!/bin/bash
# 360 Camera Live Player
# Decodes encrypted stream and plays with ffplay

set -o pipefail

cd "$(dirname "$0")/.."

echo "Starting 360 Camera Live Player..."
echo "Press Ctrl+C to stop"
echo "Tip: decoder errors are now shown on stderr"
if [[ -n "${STREAM_URL:-}" ]]; then
  echo "Using STREAM_URL from env"
fi

# Run decoder and pipe to ffplay
node tools/decoder_service.js | \
  ffplay -autoexit -f rawvideo -pixel_format yuv420p -video_size 1920x1080 -framerate 25 -i -
