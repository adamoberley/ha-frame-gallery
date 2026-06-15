#!/usr/bin/env bash
# Entry point. The app reads its settings from /data/options.json (written by
# the Supervisor from the app config) itself - no bashio needed.
set -euo pipefail
echo "[frame-gallery] starting"
exec python3 /app/main.py
