#!/bin/bash
# 360 Camera Live Player (Auto Refresh Stream URL + PLAY_KEY)
#
# Required env:
#   DEVICE_SN     - camera SN
#   Q_COOKIE      - value of cookie Q
#   T_COOKIE      - value of cookie T
#
# Optional env:
#   COOKIE_HEADER - full cookie header (used directly if provided)
#
# Example:
#   DEVICE_SN=360170500071134 \
#   Q_COOKIE='...' \
#   T_COOKIE='...' \
#   bash tools/play_live_auto.sh

set -euo pipefail

cd "$(dirname "$0")/.."

if [[ -z "${DEVICE_SN:-}" ]]; then
  echo "Missing DEVICE_SN"
  echo "Usage: DEVICE_SN=... Q_COOKIE=... T_COOKIE=... bash tools/play_live_auto.sh"
  exit 1
fi

if [[ -z "${COOKIE_HEADER:-}" && ( -z "${Q_COOKIE:-}" || -z "${T_COOKIE:-}" ) ]]; then
  echo "Missing Q_COOKIE or T_COOKIE"
  echo "Usage: DEVICE_SN=... Q_COOKIE=... T_COOKIE=... bash tools/play_live_auto.sh"
  echo "   or: DEVICE_SN=... COOKIE_HEADER='k=v; k2=v2' bash tools/play_live_auto.sh"
  exit 1
fi

echo "Fetching fresh relayStream/playKey from 360 API..."

if [[ -n "${COOKIE_HEADER:-}" ]]; then
  cookie_header="${COOKIE_HEADER}"
else
  cookie_header="Q=${Q_COOKIE}; __NS_Q=${Q_COOKIE}; T=${T_COOKIE}; __NS_T=${T_COOKIE}"
fi
api_url="https://my.jia.360.cn/app/play?sn=${DEVICE_SN}&mode=0"

api_resp="$(
  curl -sS "${api_url}" \
    -H "accept: application/json, text/javascript, */*; q=0.01" \
    -H "x-requested-with: XMLHttpRequest" \
    -H "referer: https://my.jia.360.cn/web/index" \
    -H "cookie: ${cookie_header}"
)"

parsed="$(
  printf '%s' "${api_resp}" | node -e '
    const fs = require("fs");
    const input = fs.readFileSync(0, "utf8");
    let json;
    try {
      json = JSON.parse(input);
    } catch (e) {
      console.error("Failed to parse /app/play response as JSON.");
      console.error(input.slice(0, 300));
      process.exit(2);
    }

    if (json.errorCode !== 0) {
      console.error(`API errorCode=${json.errorCode}, errorMsg=${json.errorMsg || json.errmsg || "unknown"}`);
      process.exit(3);
    }

    if (!json.relayStream || !json.playKey) {
      console.error("Missing relayStream/playKey in API response.");
      process.exit(4);
    }

    process.stdout.write(`${json.relayStream}\n${json.playKey}\n`);
  '
)"

relay_stream="$(printf '%s\n' "${parsed}" | sed -n '1p')"
play_key="$(printf '%s\n' "${parsed}" | sed -n '2p')"
stream_url="https://flv-live.jia.360.cn/live_jia_personal/${relay_stream}.flv"

masked_key="${play_key:0:8}****${play_key: -8}"
echo "relayStream fetched: ${relay_stream:0:22}..."
echo "playKey fetched: ${masked_key}"
echo "Starting live playback..."

STREAM_URL="${stream_url}" PLAY_KEY="${play_key}" bash tools/play_live.sh
