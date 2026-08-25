#!/usr/bin/env python3
"""Convert subtitle and transcript timestamps to the mandatory 1.1x clock."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PLAYBACK_RATE = 1.1
SECONDS_KEYS = {
    "start",
    "end",
    "time",
    "timestamp",
    "duration",
    "start_time",
    "end_time",
    "startTime",
    "endTime",
}
MILLISECONDS_KEYS = {
    "start_ms",
    "end_ms",
    "time_ms",
    "duration_ms",
    "startMs",
    "endMs",
    "timeMs",
    "durationMs",
}
TIMESTAMP_RE = re.compile(
    r"(?<!\d)(?:(?P<hours>\d{1,2}):)?(?P<minutes>\d{2}):"
    r"(?P<seconds>\d{2})(?P<separator>[,.])(?P<millis>\d{3})(?!\d)"
)


def retime_milliseconds(value: int) -> int:
    return round(value / PLAYBACK_RATE)


def format_timestamp(match: re.Match[str]) -> str:
    hours_text = match.group("hours")
    hours = int(hours_text or 0)
    minutes = int(match.group("minutes"))
    seconds = int(match.group("seconds"))
    millis = int(match.group("millis"))
    total = (((hours * 60) + minutes) * 60 + seconds) * 1000 + millis
    retimed = retime_milliseconds(total)
    new_hours, remainder = divmod(retimed, 3_600_000)
    new_minutes, remainder = divmod(remainder, 60_000)
    new_seconds, new_millis = divmod(remainder, 1000)
    separator = match.group("separator")
    if hours_text is None and new_hours == 0:
        return f"{new_minutes:02d}:{new_seconds:02d}{separator}{new_millis:03d}"
    return (
        f"{new_hours:02d}:{new_minutes:02d}:{new_seconds:02d}"
        f"{separator}{new_millis:03d}"
    )


def retime_text(text: str) -> tuple[str, int]:
    return TIMESTAMP_RE.subn(format_timestamp, text)


def retime_json(value: Any, parent_key: str | None = None) -> tuple[Any, int]:
    if isinstance(value, dict):
        output: dict[str, Any] = {}
        replacements = 0
        for key, item in value.items():
            converted, count = retime_json(item, key)
            output[key] = converted
            replacements += count
        return output, replacements
    if isinstance(value, list):
        output_list: list[Any] = []
        replacements = 0
        for item in value:
            converted, count = retime_json(item, parent_key)
            output_list.append(converted)
            replacements += count
        return output_list, replacements
    if parent_key in SECONDS_KEYS and isinstance(value, (int, float)):
        return round(float(value) / PLAYBACK_RATE, 6), 1
    if parent_key in MILLISECONDS_KEYS and isinstance(value, (int, float)):
        return round(float(value) / PLAYBACK_RATE), 1
    if isinstance(value, str):
        converted, count = retime_text(value)
        return converted, count
    return value, 0


def atomic_write_text(path: Path, text: str) -> None:
    partial = path.with_name(f".{path.name}.partial")
    if partial.exists():
        raise FileExistsError(f"partial output already exists: {partial}")
    partial.write_text(text, encoding="utf-8")
    partial.replace(path)


def update_manifest(
    manifest_path: Path,
    source: Path,
    output: Path,
    file_format: str,
    replacements: int,
) -> None:
    if not manifest_path.is_file():
        raise FileNotFoundError(f"retime manifest does not exist: {manifest_path}")
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    if float(payload.get("playback_rate", 0)) != PLAYBACK_RATE:
        raise ValueError("retime manifest playback_rate is not 1.1")
    entries = payload.setdefault("timing_files", [])
    entries.append(
        {
            "source": str(source),
            "output": str(output),
            "format": file_format,
            "playback_rate": PLAYBACK_RATE,
            "replacements": replacements,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
    )
    partial = manifest_path.with_name(f".{manifest_path.name}.partial")
    if partial.exists():
        raise FileExistsError(f"partial manifest already exists: {partial}")
    partial.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    partial.replace(manifest_path)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Retime SRT, VTT, or common transcript JSON timestamps by 1/1.1."
    )
    parser.add_argument("source", help="Original timing file")
    parser.add_argument("--output", help="New timing file; never overwrites the source")
    parser.add_argument(
        "--manifest",
        help="Append the converted timing file to retime-manifest.json",
    )
    args = parser.parse_args()

    source = Path(args.source).expanduser().resolve()
    if not source.is_file():
        print(f"ERROR source does not exist: {source}", file=sys.stderr)
        return 2
    if source.stem.endswith("__1p1x"):
        print(
            f"ERROR timing source already appears retimed; reuse it: {source}",
            file=sys.stderr,
        )
        return 2
    suffix = source.suffix.lower()
    if suffix not in {".srt", ".vtt", ".json"}:
        print("ERROR supported formats are .srt, .vtt, and .json", file=sys.stderr)
        return 2
    output = (
        Path(args.output).expanduser().resolve()
        if args.output
        else source.with_name(f"{source.stem}__1p1x{source.suffix}")
    )
    if output == source:
        print("ERROR output must not overwrite the source", file=sys.stderr)
        return 2
    if output.exists():
        print(f"ERROR output already exists: {output}", file=sys.stderr)
        return 2
    output.parent.mkdir(parents=True, exist_ok=True)

    if suffix == ".json":
        payload = json.loads(source.read_text(encoding="utf-8"))
        converted, replacements = retime_json(payload)
        rendered = json.dumps(converted, ensure_ascii=False, indent=2) + "\n"
        file_format = "json"
    else:
        rendered, replacements = retime_text(source.read_text(encoding="utf-8"))
        file_format = suffix.removeprefix(".")
    if replacements == 0:
        print("ERROR no supported timestamps were found", file=sys.stderr)
        return 1

    atomic_write_text(output, rendered)
    if args.manifest:
        try:
            update_manifest(
                Path(args.manifest).expanduser().resolve(),
                source,
                output,
                file_format,
                replacements,
            )
        except Exception as exc:  # noqa: BLE001 - surface deterministic update failures.
            print(
                f"ERROR timing file was created but manifest update failed: {exc}",
                file=sys.stderr,
            )
            return 1
    print(
        f"OK timing: {source.name} -> {output.name};"
        f" {replacements} timestamp value(s) divided by {PLAYBACK_RATE}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
