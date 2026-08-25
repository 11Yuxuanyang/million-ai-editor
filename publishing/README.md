# Douyin Publishing Desk

This folder is the publishing control center for edited short videos.

## Rule

Publish at most one video per day. The daily handoff time is `08:00 Asia/Shanghai`.

The cron job opens the user's real Google Chrome session, prepares the Douyin upload page, and stops before the final publish click. Final publish stays manual unless explicitly changed for a specific item.

## Files

- `douyin-queue.example.json`: anonymized queue template.
- `douyin-queue.json`: local source of truth for publish date, title, tags, video and cover; ignored by Git.
- `packages/`: lightweight package folders with symlinks to each video's final assets.
- `scripts/douyin_prepare_today.py`: selects the pending item scheduled exactly for today and launches the Douyin upload wizard.
- `scripts/douyin_daily_cron_launcher.sh`: cron-safe launcher that opens Terminal for the interactive upload handoff.
- `scripts/install_douyin_cron.sh`: idempotently installs the `DOUYIN_DAILY_UPLOAD` crontab line.
- `logs/`: cron logs and crontab backups.

## Manual Commands

Dry-run today's package:

```bash
cp publishing/douyin-queue.example.json publishing/douyin-queue.json
python3 publishing/scripts/douyin_prepare_today.py --dry-run
```

Open only, copy metadata, no file chooser prompts:

```bash
DOUYIN_UPLOAD_WIZARD=/absolute/path/to/douyin_macos_upload_wizard.sh \
  python3 publishing/scripts/douyin_prepare_today.py --open-only
```

Install or refresh the cron:

```bash
/bin/zsh publishing/scripts/install_douyin_cron.sh
```

Queue media paths are repository-relative. The upload wizard is machine-specific and
must be provided through `DOUYIN_UPLOAD_WIZARD`; it is never stored in Git.

The example queue contains no real schedule, account data or production paths. Keep the working queue local.
