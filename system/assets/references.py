from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
from typing import Any

from system.assets.inventory import _atomic_write_text


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
TEMPLATE_ROOT = REPOSITORY_ROOT / "system/templates/reference-card"
TIMECODE = re.compile(r"^(\d{2}):(\d{2}):(\d{2})\.(\d{3})$")
RANGE = re.compile(
    r"^(\d{2}:\d{2}:\d{2}\.\d{3})-(\d{2}:\d{2}:\d{2}\.\d{3})$"
)
RIGHTS_STATUSES = {"unknown", "owned", "licensed", "reference-only", "restricted"}
PRODUCTION_ELIGIBILITY = {"blocked", "recipe-only", "owned-assets", "licensed-assets"}


@dataclass(frozen=True)
class TimeRange:
    start: str
    end: str
    start_seconds: float
    end_seconds: float

    @property
    def duration_seconds(self) -> float:
        return self.end_seconds - self.start_seconds


def _seconds(value: str) -> float:
    match = TIMECODE.fullmatch(value)
    if not match:
        raise ValueError(f"invalid timecode: {value}; expected HH:MM:SS.mmm")
    hours, minutes, seconds, milliseconds = (int(part) for part in match.groups())
    if minutes > 59 or seconds > 59:
        raise ValueError(f"invalid timecode: {value}")
    return hours * 3600 + minutes * 60 + seconds + milliseconds / 1000


def parse_time_range(value: str) -> TimeRange:
    match = RANGE.fullmatch(value)
    if not match:
        raise ValueError("range must use HH:MM:SS.mmm-HH:MM:SS.mmm")
    start, end = match.groups()
    start_seconds = _seconds(start)
    end_seconds = _seconds(end)
    if end_seconds <= start_seconds:
        raise ValueError("range end must be after start")
    return TimeRange(start, end, start_seconds, end_seconds)


def _load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(f"reference file not found: {path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError(f"{path.name} must be JSON-compatible YAML/JSON: {error}") from error
    if not isinstance(value, dict):
        raise ValueError(f"{path.name} must contain an object")
    return value


def _write_json(path: Path, value: dict[str, Any]) -> None:
    _atomic_write_text(
        path, json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    )


def init_reference(*, asset_id: str, time_range: str, destination: Path) -> dict[str, Any]:
    parsed = parse_time_range(time_range)
    destination = destination.expanduser().resolve()
    reference_id = destination.name
    if not reference_id.startswith("reference."):
        raise ValueError("reference destination directory name must start with reference.")
    if destination.exists() and any(destination.iterdir()):
        raise ValueError(f"reference destination is not empty: {destination}")
    destination.mkdir(parents=True, exist_ok=True)

    card = _load_json(TEMPLATE_ROOT / "reference.yaml")
    card["id"] = reference_id
    card["source"]["assetId"] = asset_id
    card["source"]["timeRange"] = {"start": parsed.start, "end": parsed.end}
    timestamps = _load_json(TEMPLATE_ROOT / "timestamps.json")
    timestamps["referenceId"] = reference_id
    timestamps["timeRange"] = {"start": parsed.start, "end": parsed.end}
    remote = _load_json(TEMPLATE_ROOT / "remote.json")
    remote["referenceId"] = reference_id

    _write_json(destination / "reference.yaml", card)
    _write_json(destination / "timestamps.json", timestamps)
    _write_json(destination / "remote.json", remote)
    return {
        "schemaVersion": 1,
        "referenceId": reference_id,
        "status": "draft-created",
        "files": ["reference.yaml", "timestamps.json", "remote.json"],
    }


def _portable_string_errors(value: Any, prefix: str = "") -> list[str]:
    errors: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            errors.extend(_portable_string_errors(child, f"{prefix}.{key}" if prefix else str(key)))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            errors.extend(_portable_string_errors(child, f"{prefix}[{index}]"))
    elif isinstance(value, str):
        if value.startswith(("/Users/", "/home/", "file://")) or re.match(r"^[A-Za-z]:[\\/]", value):
            errors.append(f"{prefix} contains a machine-local path")
    return errors


def _placeholder_errors(value: Any, prefix: str = "") -> list[str]:
    errors: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            errors.extend(_placeholder_errors(child, f"{prefix}.{key}" if prefix else str(key)))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            errors.extend(_placeholder_errors(child, f"{prefix}[{index}]"))
    elif isinstance(value, str) and value.strip().upper() == "TODO":
        errors.append(f"{prefix} still contains TODO")
    return errors


def _require_text(card: dict[str, Any], key: str, errors: list[str]) -> None:
    if not isinstance(card.get(key), str) or not str(card[key]).strip():
        errors.append(f"{key} must not be empty")


def _require_text_list(card: dict[str, Any], key: str, errors: list[str]) -> None:
    value = card.get(key)
    if not isinstance(value, list) or not value or not all(isinstance(item, str) and item.strip() for item in value):
        errors.append(f"{key} must contain at least one non-empty item")


def validate_reference(path: Path) -> dict[str, Any]:
    path = path.expanduser().resolve()
    errors: list[str] = []
    try:
        card = _load_json(path / "reference.yaml")
        timestamps = _load_json(path / "timestamps.json")
        remote = _load_json(path / "remote.json")
    except (FileNotFoundError, ValueError) as error:
        return {"schemaVersion": 1, "valid": False, "errors": [str(error)]}

    for key in ("id", "title", "category", "status", "semanticProblem"):
        _require_text(card, key, errors)
    for key in ("visibleMotion", "useWhen", "avoidWhen"):
        _require_text_list(card, key, errors)

    source = card.get("source")
    if not isinstance(source, dict):
        errors.append("source must be an object")
        source = {}
    if not source.get("assetId"):
        errors.append("source.assetId must not be empty")
    source_range = source.get("timeRange")
    parsed_source: TimeRange | None = None
    if isinstance(source_range, dict) and source_range.get("start") and source_range.get("end"):
        try:
            parsed_source = parse_time_range(f"{source_range['start']}-{source_range['end']}")
        except ValueError as error:
            errors.append(f"source.timeRange {error}")
    else:
        errors.append("source.timeRange must contain exact start and end")

    rights = card.get("rights")
    if not isinstance(rights, dict):
        errors.append("rights must be an object")
    else:
        if rights.get("status") not in RIGHTS_STATUSES:
            errors.append("rights.status is invalid")
        if not rights.get("license"):
            errors.append("rights.license must not be empty")
    if card.get("productionEligibility") not in PRODUCTION_ELIGIBILITY:
        errors.append("productionEligibility is invalid")

    reference_id = card.get("id")
    if timestamps.get("referenceId") != reference_id:
        errors.append("timestamps.referenceId must match card id")
    if timestamps.get("timeRange") != source_range:
        errors.append("timestamps.timeRange must exactly match source.timeRange")
    if remote.get("referenceId") != reference_id:
        errors.append("remote.referenceId must match card id")
    if remote.get("provider") != "google-drive":
        errors.append("remote.provider must be google-drive")

    if parsed_source:
        for index, moment in enumerate(timestamps.get("moments", [])):
            try:
                at = _seconds(str(moment["at"]))
            except (KeyError, TypeError, ValueError) as error:
                errors.append(f"timestamps.moments[{index}] has invalid at: {error}")
                continue
            if not parsed_source.start_seconds <= at <= parsed_source.end_seconds:
                errors.append(f"timestamps.moments[{index}] is outside source.timeRange")
            if not isinstance(moment.get("meaning"), str) or not moment["meaning"].strip():
                errors.append(f"timestamps.moments[{index}].meaning must not be empty")

    errors.extend(_portable_string_errors(card))
    errors.extend(_portable_string_errors(timestamps))
    errors.extend(_portable_string_errors(remote))
    errors.extend(_placeholder_errors(card))
    return {
        "schemaVersion": 1,
        "referenceId": reference_id,
        "valid": not errors,
        "errors": errors,
    }


def validate_reference_library(library: Path) -> dict[str, Any]:
    library = library.expanduser().resolve()
    if not library.is_dir():
        raise FileNotFoundError(f"reference library not found: {library}")
    results = [
        validate_reference(path)
        for path in sorted(library.iterdir(), key=lambda value: value.name)
        if path.is_dir() and path.name.startswith("reference.")
    ]
    valid_count = sum(bool(result["valid"]) for result in results)
    return {
        "schemaVersion": 1,
        "valid": valid_count == len(results) and bool(results),
        "referenceCount": len(results),
        "validCount": valid_count,
        "invalidCount": len(results) - valid_count,
        "references": results,
    }


def create_contact_sheet(
    source: Path,
    *,
    time_range: str,
    output: Path,
    columns: int = 4,
    rows: int = 2,
) -> dict[str, Any]:
    parsed = parse_time_range(time_range)
    source = source.expanduser().resolve()
    output = output.expanduser().resolve()
    if not source.is_file():
        raise FileNotFoundError(f"contact-sheet source not found: {source}")
    if columns < 1 or rows < 1:
        raise ValueError("contact-sheet columns and rows must be at least 1")
    frame_count = columns * rows
    output.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{output.stem}.", suffix=output.suffix or ".jpg", dir=output.parent
    )
    os.close(descriptor)
    temporary = Path(temporary_name)
    temporary.unlink()
    interval = frame_count / parsed.duration_seconds
    filters = (
        f"fps={interval:.9f},"
        "scale=480:270:force_original_aspect_ratio=decrease,"
        "pad=480:270:(ow-iw)/2:(oh-ih)/2:color=black,"
        f"tile={columns}x{rows}:nb_frames={frame_count}"
    )
    command = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-ss",
        f"{parsed.start_seconds:.3f}",
        "-t",
        f"{parsed.duration_seconds:.3f}",
        "-i",
        str(source),
        "-vf",
        filters,
        "-frames:v",
        "1",
        "-q:v",
        "3",
        "-y",
        str(temporary),
    ]
    completed = subprocess.run(command, text=True, capture_output=True, check=False)
    if completed.returncode != 0:
        temporary.unlink(missing_ok=True)
        raise ValueError(f"ffmpeg contact-sheet failed: {completed.stderr.strip()}")
    os.replace(temporary, output)
    return {
        "schemaVersion": 1,
        "output": output.name,
        "frameCount": frame_count,
        "columns": columns,
        "rows": rows,
        "timeRange": {"start": parsed.start, "end": parsed.end},
        "sizeBytes": output.stat().st_size,
    }
