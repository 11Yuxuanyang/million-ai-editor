#!/usr/bin/env python3
"""Retime filmed source media to the project's mandatory 1.1x clock."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PLAYBACK_RATE = 1.1
MANIFEST_NAME = "retime-manifest.json"
FINGERPRINT_TAG_PREFIX = "hyperframe_source_fingerprint="


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, capture_output=True, text=True, check=False)


def probe(path: Path, ffprobe: str) -> dict[str, Any]:
    completed = run(
        [
            ffprobe,
            "-v",
            "error",
            "-show_streams",
            "-show_format",
            "-of",
            "json",
            str(path),
        ]
    )
    if completed.returncode:
        detail = completed.stderr.strip().splitlines()
        raise RuntimeError(detail[-1] if detail else f"ffprobe failed: {path}")
    return json.loads(completed.stdout)


def duration(probe_data: dict[str, Any]) -> float:
    value = probe_data.get("format", {}).get("duration")
    if value is not None:
        return float(value)
    values = [
        float(stream["duration"])
        for stream in probe_data.get("streams", [])
        if stream.get("duration") is not None
    ]
    return max(values, default=0.0)


def stream_summary(probe_data: dict[str, Any], kind: str) -> dict[str, Any] | None:
    stream = next(
        (
            item
            for item in probe_data.get("streams", [])
            if item.get("codec_type") == kind
        ),
        None,
    )
    if not stream:
        return None
    keys = (
        "codec_name",
        "codec_long_name",
        "width",
        "height",
        "pix_fmt",
        "avg_frame_rate",
        "sample_rate",
        "channels",
        "channel_layout",
    )
    return {key: stream[key] for key in keys if stream.get(key) is not None}


def source_fingerprint(path: Path) -> str:
    digest = hashlib.sha256()
    size = path.stat().st_size
    digest.update(str(size).encode("ascii"))
    with path.open("rb") as handle:
        digest.update(handle.read(1024 * 1024))
        if size > 1024 * 1024:
            handle.seek(max(0, size - 1024 * 1024))
            digest.update(handle.read(1024 * 1024))
    return digest.hexdigest()


def embedded_source_fingerprint(probe_data: dict[str, Any]) -> str:
    tags = probe_data.get("format", {}).get("tags", {})
    comment = str(tags.get("comment") or tags.get("COMMENT") or "")
    if not comment.startswith(FINGERPRINT_TAG_PREFIX):
        return ""
    return comment[len(FINGERPRINT_TAG_PREFIX) :]


def output_path(source: Path, output_dir: Path, codec: str) -> Path:
    suffix = ".mov" if codec == "prores" else ".mp4"
    return output_dir / f"{source.stem}__1p1x{suffix}"


def ffmpeg_command(
    ffmpeg: str,
    source: Path,
    partial: Path,
    has_audio: bool,
    codec: str,
    fps: float,
    fingerprint: str,
) -> list[str]:
    command = [
        ffmpeg,
        "-hide_banner",
        "-nostdin",
        "-y",
        "-i",
        str(source),
        "-map",
        "0:v:0",
    ]
    if has_audio:
        command.extend(["-map", "0:a:0"])
    command.extend(
        [
            "-map_metadata",
            "0",
            "-metadata",
            f"comment={FINGERPRINT_TAG_PREFIX}{fingerprint}",
            "-vf",
            f"setpts=PTS/{PLAYBACK_RATE}",
            "-r",
            f"{fps:g}",
        ]
    )
    if codec == "prores":
        command.extend(["-c:v", "prores_ks", "-profile:v", "3", "-pix_fmt", "yuv422p10le"])
        if has_audio:
            command.extend(["-af", f"atempo={PLAYBACK_RATE}", "-c:a", "pcm_s24le"])
    else:
        command.extend(
            [
                "-c:v",
                "libx264",
                "-preset",
                "slow",
                "-crf",
                "14",
                "-pix_fmt",
                "yuv420p",
                "-movflags",
                "+faststart",
            ]
        )
        if has_audio:
            command.extend(
                ["-af", f"atempo={PLAYBACK_RATE}", "-c:a", "aac", "-b:a", "320k"]
            )
    command.append(str(partial))
    return command


def atomic_json_write(path: Path, payload: dict[str, Any]) -> None:
    partial = path.with_name(f".{path.name}.partial")
    if partial.exists():
        raise FileExistsError(f"partial manifest already exists: {partial}")
    partial.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    partial.replace(path)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Create verified 1.1x edit sources without modifying originals. "
            "All outputs use the accelerated clock."
        )
    )
    parser.add_argument("sources", nargs="+", help="Filmed source files to retime")
    parser.add_argument("--output-dir", required=True, help="New directory for retimed media")
    parser.add_argument(
        "--manifest",
        help=f"Manifest path; defaults to <output-dir>/{MANIFEST_NAME}",
    )
    parser.add_argument(
        "--append",
        action="store_true",
        help="Append newly sourced footage to an existing 1.1x manifest",
    )
    parser.add_argument(
        "--codec",
        choices=("h264", "prores"),
        default="h264",
        help="h264 creates high-quality browser edit sources; prores creates larger masters",
    )
    parser.add_argument("--fps", type=float, default=60.0)
    args = parser.parse_args()

    ffmpeg = shutil.which("ffmpeg")
    ffprobe = shutil.which("ffprobe")
    if not ffmpeg or not ffprobe:
        print("ERROR ffmpeg and ffprobe are required", file=sys.stderr)
        return 2
    if args.fps <= 0:
        print("ERROR --fps must be positive", file=sys.stderr)
        return 2

    output_dir = Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = (
        Path(args.manifest).expanduser().resolve()
        if args.manifest
        else output_dir / MANIFEST_NAME
    )
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    existing_manifest: dict[str, Any] | None = None
    if manifest_path.exists():
        if not args.append:
            print(
                f"ERROR manifest already exists; use --append for new footage: {manifest_path}",
                file=sys.stderr,
            )
            return 2
        try:
            existing_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            if int(existing_manifest.get("schema_version", 0)) != 2:
                raise ValueError(
                    "existing manifest predates source fingerprints; regenerate it"
                )
            if float(existing_manifest.get("playback_rate", 0)) != PLAYBACK_RATE:
                raise ValueError("existing manifest playback_rate is not 1.1")
            if not isinstance(existing_manifest.get("entries"), list):
                raise ValueError("existing manifest entries is not a list")
            if not isinstance(existing_manifest.get("timing_files"), list):
                raise ValueError("existing manifest timing_files is not a list")
        except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
            print(f"ERROR invalid existing manifest: {exc}", file=sys.stderr)
            return 2
    elif args.append:
        print(f"ERROR --append requires an existing manifest: {manifest_path}", file=sys.stderr)
        return 2

    sources = [Path(value).expanduser().resolve() for value in args.sources]
    missing = [path for path in sources if not path.is_file()]
    if missing:
        for path in missing:
            print(f"ERROR source does not exist: {path}", file=sys.stderr)
        return 2
    apparently_retimed = [path for path in sources if path.stem.endswith("__1p1x")]
    if apparently_retimed:
        for path in apparently_retimed:
            print(
                f"ERROR source already appears retimed; reuse its manifest: {path}",
                file=sys.stderr,
            )
        return 2
    outputs = [output_path(source, output_dir, args.codec) for source in sources]
    if len(set(outputs)) != len(outputs):
        print("ERROR duplicate source stems would produce the same output name", file=sys.stderr)
        return 2
    if existing_manifest:
        existing_sources = {
            str(Path(entry["source"]).expanduser().resolve())
            for entry in existing_manifest["entries"]
            if isinstance(entry, dict) and isinstance(entry.get("source"), str)
        }
        duplicates = [path for path in sources if str(path) in existing_sources]
        if duplicates:
            for path in duplicates:
                print(f"ERROR source already exists in manifest: {path}", file=sys.stderr)
            return 2
        existing_outputs = {
            str(Path(entry["output"]).expanduser().resolve())
            for entry in existing_manifest["entries"]
            if isinstance(entry, dict) and isinstance(entry.get("output"), str)
        }
        chained_outputs = [path for path in sources if str(path) in existing_outputs]
        if chained_outputs:
            for path in chained_outputs:
                print(
                    f"ERROR refusing to retime an existing 1.1x output again: {path}",
                    file=sys.stderr,
                )
            return 2
    collisions = [path for path in outputs if path.exists()]
    if collisions:
        for path in collisions:
            print(f"ERROR output already exists: {path}", file=sys.stderr)
        return 2

    entries: list[dict[str, Any]] = []
    for index, (source, output) in enumerate(zip(sources, outputs, strict=True), start=1):
        source_probe = probe(source, ffprobe)
        video_summary = stream_summary(source_probe, "video")
        audio_summary = stream_summary(source_probe, "audio")
        if not video_summary:
            print(f"ERROR source has no video stream: {source}", file=sys.stderr)
            return 1
        source_duration = duration(source_probe)
        if source_duration <= 0:
            print(f"ERROR source duration is invalid: {source}", file=sys.stderr)
            return 1
        fingerprint = source_fingerprint(source)

        partial = output.with_name(f".{output.stem}.partial{output.suffix}")
        if partial.exists():
            print(f"ERROR partial output already exists: {partial}", file=sys.stderr)
            return 2
        print(f"[{index}/{len(sources)}] RETIME {source.name} -> {output.name}")
        command = ffmpeg_command(
            ffmpeg,
            source,
            partial,
            audio_summary is not None,
            args.codec,
            args.fps,
            fingerprint,
        )
        completed = run(command)
        if completed.returncode:
            detail = completed.stderr.strip().splitlines()
            print(
                f"ERROR ffmpeg failed; partial output retained at {partial}",
                file=sys.stderr,
            )
            if detail:
                print(detail[-1], file=sys.stderr)
            return 1

        output_probe = probe(partial, ffprobe)
        output_duration = duration(output_probe)
        expected_duration = source_duration / PLAYBACK_RATE
        tolerance = max(0.10, expected_duration * 0.002)
        duration_error = abs(output_duration - expected_duration)
        output_audio = stream_summary(output_probe, "audio")
        output_fingerprint = embedded_source_fingerprint(output_probe)
        if duration_error > tolerance:
            print(
                "ERROR retimed duration mismatch;"
                f" expected {expected_duration:.3f}s, got {output_duration:.3f}s;"
                f" partial output retained at {partial}",
                file=sys.stderr,
            )
            return 1
        if audio_summary and not output_audio:
            print(
                f"ERROR output lost synchronized audio; partial retained at {partial}",
                file=sys.stderr,
            )
            return 1
        if output_fingerprint != fingerprint:
            print(
                f"ERROR output source fingerprint mismatch: {partial}",
                file=sys.stderr,
            )
            return 1

        partial.replace(output)
        entries.append(
            {
                "source": str(source),
                "output": str(output),
                "playback_rate": PLAYBACK_RATE,
                "source_duration_seconds": round(source_duration, 6),
                "expected_output_duration_seconds": round(expected_duration, 6),
                "output_duration_seconds": round(output_duration, 6),
                "duration_error_seconds": round(duration_error, 6),
                "output_fps": args.fps,
                "video_codec_policy": args.codec,
                "audio_pitch_preserved": True,
                "source_fingerprint": fingerprint,
                "output_source_fingerprint": output_fingerprint,
                "source_video": video_summary,
                "source_audio": audio_summary,
                "output_video": stream_summary(output_probe, "video"),
                "output_audio": output_audio,
            }
        )
        print(
            f"OK {output.name}: source={source_duration:.3f}s,"
            f" expected={expected_duration:.3f}s,"
            f" output={output_duration:.3f}s"
        )

    if existing_manifest:
        manifest = existing_manifest
        manifest["entries"].extend(entries)
        manifest["updated_at"] = datetime.now(timezone.utc).isoformat()
    else:
        manifest = {
            "schema_version": 2,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "playback_rate": PLAYBACK_RATE,
            "timeline_transform": "output_time = source_time / 1.1",
            "timestamp_policy": "retime every source-relative timestamp to the accelerated clock",
            "entries": entries,
            "timing_files": [],
        }
    atomic_json_write(manifest_path, manifest)
    print(f"OK manifest: {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
