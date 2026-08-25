#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
QUEUE_PATH = Path(
    os.environ.get(
        "DOUYIN_QUEUE_PATH",
        str(PROJECT_ROOT / "publishing" / "douyin-queue.json"),
    )
).expanduser()
PORTABLE_PATH_KEYS = ("video", "cover", "cover_3x4", "transcript", "notes")


def today_china() -> str:
    # macOS ships zoneinfo in current Python; fallback to local date is acceptable for this daily launcher.
    try:
        from zoneinfo import ZoneInfo

        return dt.datetime.now(ZoneInfo("Asia/Shanghai")).date().isoformat()
    except Exception:
        return dt.date.today().isoformat()


def load_queue() -> dict:
    if not QUEUE_PATH.is_file():
        example = PROJECT_ROOT / "publishing" / "douyin-queue.example.json"
        raise FileNotFoundError(
            f"Douyin queue not found: {QUEUE_PATH}. "
            f"Copy {example} to publishing/douyin-queue.json and edit it locally."
        )
    with QUEUE_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def pick_item(items: list[dict], date: str) -> dict | None:
    candidates = [
        item
        for item in items
        if item.get("status") in {"pending", "ready"}
        and item.get("scheduled_date") == date
    ]
    if not candidates:
        return None
    return sorted(candidates, key=lambda item: item.get("scheduled_date", ""))[0]


def resolve_project_path(value: str) -> Path:
    path = Path(value).expanduser()
    return path.resolve() if path.is_absolute() else (PROJECT_ROOT / path).resolve()


def resolve_item_paths(item: dict) -> dict:
    resolved = dict(item)
    for key in PORTABLE_PATH_KEYS:
        if resolved.get(key):
            resolved[key] = str(resolve_project_path(resolved[key]))
    return resolved


def upload_wizard() -> Path | None:
    value = os.environ.get("DOUYIN_UPLOAD_WIZARD")
    return Path(value).expanduser().resolve() if value else None


def validate_item(item: dict) -> list[str]:
    errors: list[str] = []
    for key in ["video", "cover"]:
        path = item.get(key, "")
        if not path:
            errors.append(f"missing {key}")
        elif not Path(path).is_file():
            errors.append(f"{key} not found: {path}")

    tags = item.get("tags", [])
    if not isinstance(tags, list) or not tags:
        errors.append("tags must be a non-empty list")
    elif len(tags) > 5:
        errors.append(f"too many tags: {len(tags)} > 5")

    if not item.get("title"):
        errors.append("missing title")
    return errors


def ffprobe(video: str) -> str:
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-select_streams",
                "v:0",
                "-show_entries",
                "stream=width,height,r_frame_rate,codec_name",
                "-show_entries",
                "format=duration,size",
                "-of",
                "default=noprint_wrappers=1",
                video,
            ],
            check=True,
            text=True,
            capture_output=True,
        )
        return result.stdout.strip()
    except Exception as exc:
        return f"ffprobe unavailable: {exc}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare today's Douyin upload package from publishing/douyin-queue.json.")
    parser.add_argument("--date", default=today_china(), help="Publish date, YYYY-MM-DD. Defaults to Asia/Shanghai today.")
    parser.add_argument("--dry-run", action="store_true", help="Validate and print the selected package only.")
    parser.add_argument("--open-only", action="store_true", help="Open Douyin and copy metadata, but do not start file chooser prompts.")
    args = parser.parse_args()

    queue = load_queue()
    item = pick_item(queue.get("items", []), args.date)
    if not item:
        print(f"No pending Douyin item scheduled exactly for {args.date}.")
        return 0
    item = resolve_item_paths(item)

    errors = validate_item(item)
    print(f"Selected: {item['id']} ({item['scheduled_date']})")
    print(f"Title: {item['title']}")
    print(f"Tags: {' '.join('#' + tag.lstrip('#') for tag in item['tags'])}")
    print(f"Video: {item['video']}")
    print(f"Cover: {item['cover']}")
    print()
    print(ffprobe(item["video"]))
    print()

    if errors:
        print("Package errors:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 2

    if args.dry_run:
        print("Dry run only. No browser action.")
        return 0

    wizard = upload_wizard()
    if wizard is None:
        print("DOUYIN_UPLOAD_WIZARD is not configured.", file=sys.stderr)
        return 2
    if not wizard.is_file():
        print(f"Douyin upload wizard not found: {wizard}", file=sys.stderr)
        return 2

    command = [
        str(wizard),
        "--video",
        item["video"],
        "--title",
        item["title"],
        "--tags",
        ",".join(item["tags"]),
        "--cover",
        item["cover"],
    ]
    if args.open_only:
        command.append("--open-only")

    print("Launching Douyin assisted upload. Final publish remains manual.")
    os.execv(command[0], command)


if __name__ == "__main__":
    raise SystemExit(main())
