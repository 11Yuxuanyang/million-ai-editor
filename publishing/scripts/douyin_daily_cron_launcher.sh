#!/usr/bin/env zsh
set -euo pipefail

SCRIPT_DIR="${0:A:h}"
PROJECT_ROOT="${SCRIPT_DIR:h:h}"
RUNNER="$PROJECT_ROOT/publishing/scripts/douyin_prepare_today.py"
LOG_DIR="$PROJECT_ROOT/publishing/logs"
PYTHON="${EDITING_PYTHON:-/usr/bin/python3}"

mkdir -p "$LOG_DIR"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] launching Douyin daily upload handoff" >> "$LOG_DIR/douyin-cron.log"

osascript <<APPLESCRIPT
tell application "Terminal"
  activate
  do script "cd '$PROJECT_ROOT' && '$PYTHON' '$RUNNER'"
end tell
APPLESCRIPT
