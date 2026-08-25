#!/usr/bin/env python3
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TIMELINE = ROOT / "work" / "timeline.json"
OUTPUT = ROOT / "assets" / "media" / "a-roll-1080p60.mp4"


def main():
    timeline = json.loads(TIMELINE.read_text(encoding="utf-8"))
    clips = timeline["clips"]
    command = ["ffmpeg", "-y", "-hide_banner"]
    for clip in clips:
        command.extend(["-i", clip["source"]])

    filters = []
    video_labels = []
    audio_labels = []
    rate = timeline["rate"]
    for index, clip in enumerate(clips):
        video_label = f"v{index}"
        audio_label = f"a{index}"
        start = clip["sourceStart"]
        end = clip["sourceEnd"]
        filters.append(
            f"[{index}:v]trim=start={start}:end={end},setpts=(PTS-STARTPTS)/{rate},"
            f"fps=60,scale=1920:1080:force_original_aspect_ratio=decrease,"
            f"pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=black,setsar=1[{video_label}]"
        )
        filters.append(
            f"[{index}:a]atrim=start={start}:end={end},asetpts=PTS-STARTPTS,"
            f"atempo={rate},aresample=48000[{audio_label}]"
        )
        video_labels.append(f"[{video_label}]")
        audio_labels.append(f"[{audio_label}]")

    concat_inputs = "".join(
        video + audio for video, audio in zip(video_labels, audio_labels)
    )
    filters.append(
        f"{concat_inputs}concat=n={len(clips)}:v=1:a=1[vcat][acat]"
    )
    filters.append(
        "[vcat]tpad=stop_mode=clone:stop_duration=0.8,format=yuv420p[vout]"
    )
    filters.append(
        "[acat]acompressor=threshold=-18dB:ratio=2.5:attack=5:release=80:makeup=2dB,"
        "loudnorm=I=-8.72:TP=-1.0:LRA=7,apad=pad_dur=0.8[aout]"
    )

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    command.extend(
        [
            "-filter_complex",
            ";".join(filters),
            "-map",
            "[vout]",
            "-map",
            "[aout]",
            "-c:v",
            "libx264",
            "-preset",
            "fast",
            "-crf",
            "16",
            "-profile:v",
            "high",
            "-level",
            "4.2",
            "-g",
            "60",
            "-keyint_min",
            "60",
            "-c:a",
            "aac",
            "-b:a",
            "256k",
            "-ar",
            "48000",
            "-movflags",
            "+faststart",
            "-t",
            f"{timeline['duration'] + 0.8:.4f}",
            str(OUTPUT),
        ]
    )
    print("Building", OUTPUT)
    subprocess.run(command, check=True)


if __name__ == "__main__":
    main()
