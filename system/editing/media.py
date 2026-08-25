"""Media probing and delivery measurements."""

from __future__ import annotations

import hashlib
import json
import math
import re
from pathlib import Path
from typing import Any

from .io import run


VIDEO_AUDIO_EXTENSIONS = {
    ".mp4", ".mov", ".mkv", ".webm", ".avi", ".m4v",
    ".mp3", ".wav", ".m4a", ".aac", ".flac",
}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".tif", ".tiff", ".avif"}
MEDIA_EXTENSIONS = VIDEO_AUDIO_EXTENSIONS | IMAGE_EXTENSIONS


def parse_rate(value: str | None) -> float:
    if not value or value in {"0/0", "N/A"}:
        return 0.0
    if "/" in value:
        numerator, denominator = value.split("/", 1)
        denominator_value = float(denominator)
        return float(numerator) / denominator_value if denominator_value else 0.0
    return float(value)


def stream_duration(stream: dict[str, Any] | None) -> float:
    if not stream:
        return 0.0
    try:
        duration = float(stream.get("duration"))
        if math.isfinite(duration) and duration > 0:
            return duration
    except (TypeError, ValueError):
        pass
    try:
        duration = float(stream.get("duration_ts")) * parse_rate(stream.get("time_base"))
        if math.isfinite(duration) and duration > 0:
            return duration
    except (TypeError, ValueError):
        pass
    match = re.fullmatch(
        r"(\d+):(\d+):(\d+(?:\.\d+)?)",
        str((stream.get("tags") or {}).get("DURATION") or ""),
    )
    if match:
        hours, minutes, seconds = match.groups()
        duration = int(hours) * 3600 + int(minutes) * 60 + float(seconds)
        if math.isfinite(duration) and duration > 0:
            return duration
    return 0.0


def probe_media(path: Path) -> dict[str, Any]:
    completed = run([
        "ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)
    ])
    raw = json.loads(completed.stdout)
    video = next((item for item in raw.get("streams", []) if item.get("codec_type") == "video"), None)
    audio = next((item for item in raw.get("streams", []) if item.get("codec_type") == "audio"), None)
    duration = raw.get("format", {}).get("duration")
    if duration is None:
        duration = max((float(item.get("duration", 0)) for item in raw.get("streams", [])), default=0.0)
    return {
        "duration": round(float(duration or 0), 4),
        "format": raw.get("format", {}).get("format_name"),
        "sizeBytes": int(raw.get("format", {}).get("size") or path.stat().st_size),
        "video": None if video is None else {
            "codec": video.get("codec_name"),
            "width": video.get("width"),
            "height": video.get("height"),
            "pixelFormat": video.get("pix_fmt"),
            "fps": round(parse_rate(video.get("avg_frame_rate") or video.get("r_frame_rate")), 4),
            "bitRate": int(video.get("bit_rate") or 0),
            "colorSpace": video.get("color_space"),
            "colorTransfer": video.get("color_transfer"),
            "colorPrimaries": video.get("color_primaries"),
            "duration": round(stream_duration(video), 4),
        },
        "audio": None if audio is None else {
            "codec": audio.get("codec_name"),
            "sampleRate": int(audio.get("sample_rate") or 0),
            "channels": audio.get("channels"),
            "bitRate": int(audio.get("bit_rate") or 0),
            "duration": round(stream_duration(audio), 4),
        },
    }


def measure_loudness(path: Path, target_lufs: float, true_peak_dbtp: float) -> dict[str, float | None]:
    completed = run([
        "ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-map", "0:a:0",
        "-af", f"loudnorm=I={target_lufs}:TP={true_peak_dbtp}:LRA=7:print_format=json",
        "-f", "null", "-",
    ], check=False)
    matches = re.findall(r"\{\s*\"input_i\".*?\}", f"{completed.stdout}\n{completed.stderr}", flags=re.S)
    if not matches:
        return {"integratedLufs": None, "truePeakDbtp": None}
    raw = json.loads(matches[-1])

    def number(value: Any) -> float | None:
        try:
            parsed = float(value)
        except (TypeError, ValueError):
            return None
        return parsed if math.isfinite(parsed) else None

    return {"integratedLufs": number(raw.get("input_i")), "truePeakDbtp": number(raw.get("input_tp"))}


def stable_media_id(relative_path: str) -> str:
    stem = Path(relative_path).stem
    safe = re.sub(r"[^A-Za-z0-9._-]+", "-", stem).strip("-") or "media"
    digest = hashlib.sha1(relative_path.encode("utf-8"), usedforsecurity=False).hexdigest()[:8]
    return f"{safe}-{digest}"
