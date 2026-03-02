#!/bin/bash
# Prompt SN/account/password, then auto login and play.

set -euo pipefail

cd "$(dirname "$0")/.."

if ! node -e "require.resolve('playwright')" >/dev/null 2>&1; then
  echo "Missing dependency: playwright"
  echo "Run: npm i -D playwright && npx playwright install chromium"
  exit 1
fi

read -r -p "Device SN: " DEVICE_SN
read -r -p "360 Account: " LOGIN_ACCOUNT
read -r -s -p "360 Password: " LOGIN_PASSWORD
echo ""

if [[ -z "${DEVICE_SN}" || -z "${LOGIN_ACCOUNT}" || -z "${LOGIN_PASSWORD}" ]]; then
  echo "SN/account/password are required."
  exit 1
fi

LOGIN_ACCOUNT="${LOGIN_ACCOUNT}" \
LOGIN_PASSWORD="${LOGIN_PASSWORD}" \
node tools/fetch_play_info_browser.mjs --sn "${DEVICE_SN}" --play
