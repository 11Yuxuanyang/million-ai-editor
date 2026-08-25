#!/usr/bin/env zsh
set -euo pipefail

SCRIPT_DIR="${0:A:h}"
PROJECT_ROOT="${SCRIPT_DIR:h:h}"
LAUNCHER="$PROJECT_ROOT/publishing/scripts/douyin_daily_cron_launcher.sh"
LOG="$PROJECT_ROOT/publishing/logs/douyin-cron.log"
MARKER="DOUYIN_DAILY_UPLOAD"
CRON_LINE="0 8 * * * /bin/zsh \"$LAUNCHER\" >> \"$LOG\" 2>&1 # $MARKER"
BACKUP="$PROJECT_ROOT/publishing/logs/crontab-backup-$(date '+%Y%m%d-%H%M%S').txt"

mkdir -p "$PROJECT_ROOT/publishing/logs"

if crontab -l > "$BACKUP" 2>/dev/null; then
  :
else
  : > "$BACKUP"
fi

TMP="$(mktemp)"
grep -v "$MARKER" "$BACKUP" > "$TMP" || true
printf '%s\n' "$CRON_LINE" >> "$TMP"
crontab "$TMP"
rm -f "$TMP"

echo "Installed cron:"
echo "$CRON_LINE"
echo "Previous crontab backup:"
echo "$BACKUP"
