#!/usr/bin/env python3
"""Deterministic production commands for 百万AI剪辑师.

Creative decisions stay with the editing agent. This CLI handles repeatable work:
project setup, media inspection, batch ASR, A-roll assembly, rendering, and delivery
verification.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import math
import os
import posixpath
import re
import shutil
import subprocess
import sys
import tempfile
from html.parser import HTMLParser
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from system.editing.asr import extract_asr_audio, request_doubao_asr
from system.editing.io import (
    json_fingerprint,
    load_json,
    move_to_trash,
    run,
    sha256_file,
    validate_schema_file,
    write_json,
)
from system.editing.media import (
    IMAGE_EXTENSIONS,
    MEDIA_EXTENSIONS,
    measure_loudness,
    probe_media,
    stable_media_id,
)
from system.editing.runtime import command_doctor


DEFAULTS_PATH = ROOT / "config" / "editorial-defaults.json"
ENVIRONMENT_LOCK_PATH = ROOT / "config" / "environment.lock.json"
EPISODE_TEMPLATE_PATH = ROOT / "config" / "episode.template.json"
HYPERFRAME_TEMPLATE_DIR = ROOT / "system" / "templates" / "hyperframe-episode"
SEQUENCE_PLAN_SCHEMA_PATH = ROOT / "system" / "schemas" / "sequence-plan.schema.json"
SEQUENCE_TASK_SCHEMA_PATH = ROOT / "system" / "schemas" / "sequence-task.schema.json"
SEQUENCE_OUTPUT_SCHEMA_PATH = ROOT / "system" / "schemas" / "sequence-output.schema.json"
CREATIVE_BRIEF_SCHEMA_PATH = ROOT / "system" / "schemas" / "creative-brief.schema.json"
EPISODE_AGENTS_TEMPLATE_PATH = ROOT / "system" / "templates" / "episode-AGENTS.md"


def resolve_episode(path: str) -> Path:
    episode = Path(path).expanduser().resolve()
    if not (episode / "episode.json").is_file():
        raise FileNotFoundError(f"episode.json not found: {episode}")
    return episode


def resolve_episode_path(episode: Path, value: str) -> Path:
    path = Path(value).expanduser()
    return path.resolve() if path.is_absolute() else (episode / path).resolve()


def resolve_internal_episode_path(episode: Path, value: str, label: str) -> Path:
    resolved_episode = episode.resolve()
    resolved = resolve_episode_path(episode, value)
    if resolved_episode not in (resolved, *resolved.parents):
        raise ValueError(f"{label} must stay inside the episode directory: {value}")
    return resolved


def load_episode(path: str) -> tuple[Path, dict[str, Any], dict[str, Any]]:
    episode = resolve_episode(path)
    manifest = load_json(episode / "episode.json")
    defaults = load_json(DEFAULTS_PATH)
    return episode, manifest, defaults


def starter_text(title: str, purpose: str) -> str:
    return f"# {title}\n\n{purpose}\n"


def write_episode_agents(episode: Path, backup: bool = False) -> None:
    destination = episode / "AGENTS.md"
    if backup and destination.is_file() and destination.read_bytes() != EPISODE_AGENTS_TEMPLATE_PATH.read_bytes():
        backup_for_v3(episode, destination)
    shutil.copy2(EPISODE_AGENTS_TEMPLATE_PATH, destination)


def scaffold_episode(
    args: argparse.Namespace,
    staging: Path,
    profile: Path,
    hyperframes: str,
) -> None:
    environment = dict(os.environ)
    environment["HYPERFRAMES_SKIP_SKILLS"] = "1"
    completed = subprocess.run(
        [
            hyperframes,
            "init",
            str(staging),
            "--example",
            "blank",
            "--non-interactive",
            "--resolution",
            "landscape",
            "--skill",
            "hyperframe-video-editor",
        ],
        text=True,
        capture_output=True,
        env=environment,
        check=False,
    )
    if completed.returncode:
        raise RuntimeError(completed.stderr.strip() or completed.stdout.strip())

    for relative in (
        "source",
        "assets/source",
        "assets/media",
        "transcripts",
        "work",
        "sequences",
        "deliverables",
    ):
        (staging / relative).mkdir(parents=True, exist_ok=True)

    manifest = load_json(EPISODE_TEMPLATE_PATH)
    manifest.update({"id": args.id, "title": args.title, "profile": args.profile})
    write_json(staging / "episode.json", manifest)
    write_json(staging / "profile.snapshot.json", load_json(profile))
    write_json(staging / "editorial-defaults.snapshot.json", load_json(DEFAULTS_PATH))
    write_episode_agents(staging)
    starter_files = {
        "BRIEF.md": (args.title, "Write the audience, promise, facts, and delivery goal here."),
        "SCRIPT.md": ("Script", "Paste the manuscript here."),
        "SOURCES.md": ("Sources", "Record real-media provenance, permissions, and generated assets here."),
        "DESIGN.md": ("Episode Direction", "Record this episode's visual thesis, palette roles, and exceptions here."),
    }
    for name, (title, purpose) in starter_files.items():
        (staging / name).write_text(starter_text(title, purpose), encoding="utf-8")

    storyboard_template = (
        ROOT
        / "skills"
        / "hyperframe-video-editor"
        / "references"
        / "motion-storyboard-template.md"
    )
    shutil.copy2(storyboard_template, staging / "MOTION-STORYBOARD.md")
    creative_brief = load_json(ROOT / "config" / "creative-brief.template.json")
    creative_brief["episodeId"] = args.id
    write_json(staging / "work" / "creative-brief.json", creative_brief)
    sequence_plan = load_json(ROOT / "config" / "sequence-plan.template.json")
    sequence_plan["episodeId"] = args.id
    write_json(staging / "work" / "sequence-plan.json", sequence_plan)

    (staging / "scripts").mkdir(exist_ok=True)
    template_files = {
        "index.template.html": staging / "index.template.txt",
        "styles.css": staging / "styles.css",
        "build_index.mjs": staging / "scripts" / "build_index.mjs",
    }
    for source_name, destination in template_files.items():
        shutil.copy2(HYPERFRAME_TEMPLATE_DIR / source_name, destination)

    package_path = staging / "package.json"
    package = load_json(package_path)
    environment_lock = load_json(ENVIRONMENT_LOCK_PATH)
    hyperframes_version = environment_lock["tools"]["hyperframes"]["projectVersion"]
    package.setdefault("devDependencies", {})["hyperframes"] = hyperframes_version
    package["scripts"] = {
        "build": "node scripts/build_index.mjs",
        "dev": package.get("scripts", {}).get("dev", "hyperframes preview"),
        "check": "npm run build && hyperframes check",
        "render": "npm run build && hyperframes render",
    }
    write_json(package_path, package)
    run(
        ["npm", "install", "--save-dev", "--save-exact", f"hyperframes@{hyperframes_version}"],
        cwd=staging,
    )
    run(["npm", "run", "build"], cwd=staging)


def command_new(args: argparse.Namespace) -> int:
    destination_root = Path(args.root).expanduser().resolve() if args.root else ROOT / "episodes"
    episode_id = Path(args.id)
    if episode_id.is_absolute() or len(episode_id.parts) != 1 or args.id in {".", ".."}:
        raise ValueError("episode id must be one directory name")
    destination = destination_root / args.id
    if destination.exists():
        raise FileExistsError(f"episode already exists: {destination}")
    profile = ROOT / "config" / "profiles" / f"{args.profile}.json"
    if not profile.is_file():
        raise FileNotFoundError(f"unknown profile: {args.profile}")
    hyperframes = shutil.which("hyperframes")
    if not hyperframes:
        raise RuntimeError("hyperframes CLI is required; run editctl.py doctor")

    destination_root.mkdir(parents=True, exist_ok=True)
    transaction_root = Path(
        tempfile.mkdtemp(prefix=f".{args.id}.creating-", dir=destination_root)
    )
    staging = transaction_root / args.id
    try:
        scaffold_episode(args, staging, profile, hyperframes)
        if destination.exists():
            raise FileExistsError(f"episode appeared while creating it: {destination}")
        staging.replace(destination)
        transaction_root.rmdir()
    except Exception as error:
        trashed = move_to_trash(transaction_root)
        raise RuntimeError(
            f"episode creation failed ({error}); incomplete staging moved to Trash: {trashed}"
        ) from error
    print(destination)
    return 0


V3_TEMPLATE_PLACEHOLDERS = (
    "{{SEQUENCE_STYLES}}",
    "{{SEQUENCE_SCENES}}",
    "{{SEQUENCE_TIMELINE}}",
)


def v3_runtime_issues(episode: Path) -> list[str]:
    issues: list[str] = []
    template_path = episode / "index.template.txt"
    builder_path = episode / "scripts" / "build_index.mjs"
    if not template_path.is_file():
        issues.append("missing index.template.txt")
    else:
        template = template_path.read_text(encoding="utf-8")
        for placeholder in V3_TEMPLATE_PLACEHOLDERS:
            if placeholder not in template:
                issues.append(f"index.template.txt is missing {placeholder}")
    if not builder_path.is_file():
        issues.append("missing scripts/build_index.mjs")
    else:
        builder = builder_path.read_text(encoding="utf-8")
        for marker in ("assemblyPlan", '"{{SEQUENCE_SCENES}}"', '"{{SEQUENCE_TIMELINE}}"'):
            if marker not in builder:
                issues.append(f"scripts/build_index.mjs is not V3-aware: missing {marker}")
    return issues


def backup_for_v3(episode: Path, path: Path) -> Path | None:
    if not path.is_file():
        return None
    backup = episode / "work" / "migrations" / "v3" / path.relative_to(episode)
    if not backup.exists():
        backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, backup)
        return backup
    if backup.read_bytes() == path.read_bytes():
        return backup
    fingerprint = sha256_file(path)[:12]
    versioned = backup.with_name(f"{backup.stem}-{fingerprint}{backup.suffix}")
    if not versioned.exists():
        versioned.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, versioned)
    return versioned


def add_v3_template_placeholders(template: str) -> str:
    updated = template
    if "{{SEQUENCE_STYLES}}" not in updated:
        if "</head>" not in updated:
            raise ValueError("cannot add V3 styles placeholder: </head> not found")
        updated = updated.replace("</head>", "    <style>{{SEQUENCE_STYLES}}</style>\n  </head>", 1)
    if "{{SEQUENCE_SCENES}}" not in updated:
        if "<!-- AI-DIRECTED-SCENES -->" in updated:
            updated = updated.replace(
                "<!-- AI-DIRECTED-SCENES -->",
                "<!-- AI-DIRECTED-SCENES -->\n      {{SEQUENCE_SCENES}}",
                1,
            )
        elif "{{CAPTIONS}}" in updated:
            updated = updated.replace("{{CAPTIONS}}", "{{SEQUENCE_SCENES}}\n      {{CAPTIONS}}", 1)
        else:
            raise ValueError("cannot add V3 scenes placeholder: scene insertion marker not found")
    if "{{SEQUENCE_TIMELINE}}" not in updated:
        if "// AI-DIRECTED-TIMELINE" in updated:
            updated = updated.replace(
                "// AI-DIRECTED-TIMELINE",
                "// AI-DIRECTED-TIMELINE\n      {{SEQUENCE_TIMELINE}}",
                1,
            )
        elif "window.__timelines" in updated:
            updated = updated.replace(
                "window.__timelines",
                "{{SEQUENCE_TIMELINE}}\n      window.__timelines",
                1,
            )
        else:
            raise ValueError("cannot add V3 timeline placeholder: timeline insertion marker not found")
    return updated


def command_upgrade_v3(args: argparse.Namespace) -> int:
    episode, manifest, _ = load_episode(args.episode)
    path_defaults = {
        "creativeBrief": "work/creative-brief.json",
        "sequencePlan": "work/sequence-plan.json",
        "sequenceRoot": "sequences",
        "assemblyPlan": "work/assembly-plan.json",
    }
    manifest.setdefault("paths", {}).update(
        {key: manifest.get("paths", {}).get(key, value) for key, value in path_defaults.items()}
    )
    write_json(episode / "episode.json", manifest)
    write_episode_agents(episode, backup=True)
    paths = sequence_paths(episode, manifest)
    paths["sequenceRoot"].mkdir(parents=True, exist_ok=True)
    if not paths["creativeBrief"].is_file():
        brief = load_json(ROOT / "config" / "creative-brief.template.json")
        brief["episodeId"] = manifest["id"]
        write_json(paths["creativeBrief"], brief)
    if not paths["sequencePlan"].is_file():
        plan = load_json(ROOT / "config" / "sequence-plan.template.json")
        plan["episodeId"] = manifest["id"]
        write_json(paths["sequencePlan"], plan)

    template_path = episode / "index.template.txt"
    if template_path.is_file():
        original = template_path.read_text(encoding="utf-8")
        updated = add_v3_template_placeholders(original)
        if updated != original:
            backup_for_v3(episode, template_path)
            template_path.write_text(updated, encoding="utf-8")
    else:
        shutil.copy2(HYPERFRAME_TEMPLATE_DIR / "index.template.html", template_path)

    builder_path = episode / "scripts" / "build_index.mjs"
    canonical_builder = HYPERFRAME_TEMPLATE_DIR / "build_index.mjs"
    if not builder_path.is_file() or builder_path.read_bytes() != canonical_builder.read_bytes():
        backup_for_v3(episode, builder_path)
        builder_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(canonical_builder, builder_path)

    issues = v3_runtime_issues(episode)
    report = {
        "ok": not issues,
        "systemVersion": 3,
        "episode": str(episode),
        "backupRoot": str(episode / "work/migrations/v3"),
        "issues": issues,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if not issues else 1


def inspect_episode(episode: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    source_dir = resolve_episode_path(episode, manifest["inputs"]["sourceDir"])
    if not source_dir.is_dir():
        raise FileNotFoundError(f"source directory not found: {source_dir}")
    files = sorted(
        path for path in source_dir.rglob("*") if path.is_file() and path.suffix.lower() in MEDIA_EXTENSIONS
    )
    items = []
    for index, path in enumerate(files):
        relative = path.relative_to(episode).as_posix()
        details = probe_media(path)
        items.append(
            {
                "id": stable_media_id(relative),
                "discoveryIndex": index,
                "path": relative,
                "mediaKind": "image" if path.suffix.lower() in IMAGE_EXTENSIONS else "media",
                "sha256": sha256_file(path),
                **details,
            }
        )
    return {
        "schemaVersion": 1,
        "episodeId": manifest["id"],
        "sourceOrderMode": manifest["inputs"].get("sourceOrderMode"),
        "items": items,
    }


def command_inspect(args: argparse.Namespace) -> int:
    episode, manifest, _ = load_episode(args.episode)
    inventory = inspect_episode(episode, manifest)
    destination = resolve_episode_path(episode, manifest["paths"]["inventory"])
    write_json(destination, inventory)
    print(json.dumps({"inventory": str(destination), "items": len(inventory["items"])}, ensure_ascii=False))
    return 0


def command_transcribe(args: argparse.Namespace) -> int:
    episode, manifest, _ = load_episode(args.episode)
    app_key = os.environ.get("DOUBAO_APP_KEY")
    access_key = os.environ.get("DOUBAO_ACCESS_KEY")
    if not app_key or not access_key:
        raise RuntimeError("DOUBAO_APP_KEY and DOUBAO_ACCESS_KEY are required")
    inventory_path = resolve_episode_path(episode, manifest["paths"]["inventory"])
    if not inventory_path.is_file():
        write_json(inventory_path, inspect_episode(episode, manifest))
    inventory = load_json(inventory_path)
    transcript_dir = resolve_episode_path(episode, manifest["paths"]["transcripts"])
    audio_dir = episode / "work" / "asr-audio"
    jobs = [item for item in inventory["items"] if item.get("audio")]

    def transcribe_one(item: dict[str, Any]) -> dict[str, str]:
        source = resolve_episode_path(episode, item["path"])
        audio = audio_dir / f"{item['id']}.mp3"
        output = transcript_dir / f"{item['id']}.json"
        if output.is_file() and not args.force:
            return {"id": item["id"], "status": "cached", "output": str(output)}
        extract_asr_audio(source, audio)
        request_doubao_asr(audio, output, app_key, access_key)
        return {"id": item["id"], "status": "created", "output": str(output)}

    workers = max(1, min(args.workers, len(jobs) or 1))
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(transcribe_one, item) for item in jobs]
        for future in concurrent.futures.as_completed(futures):
            results.append(future.result())
    print(json.dumps({"jobs": len(jobs), "workers": workers, "results": results}, ensure_ascii=False, indent=2))
    return 0


def source_from_clip(episode: Path, clip: dict[str, Any], inventory: dict[str, Any]) -> Path:
    source_value = clip.get("source")
    if source_value:
        return resolve_episode_path(episode, source_value)
    item_id = clip.get("sourceId")
    item = next((candidate for candidate in inventory["items"] if candidate["id"] == item_id), None)
    if not item:
        raise ValueError(f"cut-plan sourceId not found: {item_id}")
    return resolve_episode_path(episode, item["path"])


def command_build_aroll(args: argparse.Namespace) -> int:
    episode, manifest, defaults = load_episode(args.episode)
    cut_plan_path = resolve_episode_path(episode, manifest["paths"]["cutPlan"])
    inventory_path = resolve_episode_path(episode, manifest["paths"]["inventory"])
    if not cut_plan_path.is_file():
        raise FileNotFoundError(f"AI must write the reviewed cut plan first: {cut_plan_path}")
    if not inventory_path.is_file():
        raise FileNotFoundError(f"run inspect first: {inventory_path}")
    cut_plan = load_json(cut_plan_path)
    inventory = load_json(inventory_path)
    clips = cut_plan.get("clips") or []
    if not clips:
        raise ValueError("cut plan contains no clips")
    rate = float(cut_plan.get("rate") or defaults["sourceRetime"]["rate"])
    width = int(manifest.get("deliveryOverrides", {}).get("width") or defaults["delivery"]["width"])
    height = int(manifest.get("deliveryOverrides", {}).get("height") or defaults["delivery"]["height"])
    fps = int(manifest.get("deliveryOverrides", {}).get("fps") or defaults["delivery"]["fps"])
    output = resolve_episode_path(episode, manifest["paths"]["aRoll"])
    command = ["ffmpeg", "-hide_banner", "-nostdin", "-y"]
    sources = []
    for clip in clips:
        source = source_from_clip(episode, clip, inventory)
        if not source.is_file():
            raise FileNotFoundError(source)
        if not probe_media(source).get("audio"):
            raise ValueError(f"A-roll clip has no audio: {source}")
        sources.append(source)
        command.extend(["-i", str(source)])

    filters = []
    concat_inputs = []
    total_duration = 0.0
    for index, clip in enumerate(clips):
        start = float(clip["sourceStart"])
        end = float(clip["sourceEnd"])
        if end <= start:
            raise ValueError(f"invalid clip range at index {index}: {start}..{end}")
        total_duration += (end - start) / rate
        filters.append(
            f"[{index}:v]trim=start={start}:end={end},setpts=(PTS-STARTPTS)/{rate},"
            f"fps={fps},scale={width}:{height}:force_original_aspect_ratio=decrease,"
            f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:color=black,setsar=1[v{index}]"
        )
        filters.append(
            f"[{index}:a]atrim=start={start}:end={end},asetpts=PTS-STARTPTS,"
            f"atempo={rate},aresample={defaults['master']['audioSampleRate']}[a{index}]"
        )
        concat_inputs.extend([f"[v{index}]", f"[a{index}]"])
    filters.append(f"{''.join(concat_inputs)}concat=n={len(clips)}:v=1:a=1[vcat][acat]")
    hold = float(cut_plan.get("tailHoldSeconds", 0.0))
    filters.append(
        f"[vcat]tpad=stop_mode=clone:stop_duration={hold},"
        f"format={defaults['master']['pixelFormat']},"
        f"setparams=color_primaries={defaults['master']['colorSpace']}:"
        f"color_trc={defaults['master']['colorSpace']}:"
        f"colorspace={defaults['master']['colorSpace']}[vout]"
    )
    filters.append(
        f"[acat]acompressor=threshold=-18dB:ratio=2.5:attack=5:release=80:makeup=2dB,"
        f"loudnorm=I={defaults['master']['targetIntegratedLoudnessLufs']}:"
        f"TP={defaults['master']['truePeakCeilingDbtp']}:LRA=7,apad=pad_dur={hold}[aout]"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    command.extend(
        [
            "-filter_complex",
            ";".join(filters),
            "-map",
            "[vout]",
            "-map",
            "[aout]",
            "-c:v",
            defaults["master"]["videoCodec"],
            "-preset",
            "fast",
            "-crf",
            "16",
            "-pix_fmt",
            defaults["master"]["pixelFormat"],
            "-colorspace",
            defaults["master"]["colorSpace"],
            "-color_primaries",
            defaults["master"]["colorSpace"],
            "-color_trc",
            defaults["master"]["colorSpace"],
            "-c:a",
            defaults["master"]["audioCodec"],
            "-b:a",
            defaults["master"]["audioBitrate"],
            "-ar",
            str(defaults["master"]["audioSampleRate"]),
            "-movflags",
            "+faststart",
            "-t",
            f"{total_duration + hold:.4f}",
            str(output),
        ]
    )
    completed = subprocess.run(command, text=True, check=False)
    if completed.returncode:
        return completed.returncode
    metadata = {
        "output": output.relative_to(episode).as_posix(),
        "clips": len(clips),
        "duration": round(total_duration + hold, 4),
        "rate": rate,
        "width": width,
        "height": height,
        "fps": fps,
    }
    write_json(episode / "work" / "a-roll.json", metadata)
    print(json.dumps(metadata))
    return 0


def sequence_paths(episode: Path, manifest: dict[str, Any]) -> dict[str, Path]:
    configured = manifest.get("paths") or {}
    return {
        "creativeBrief": resolve_internal_episode_path(
            episode,
            configured.get("creativeBrief", "work/creative-brief.json"),
            "creativeBrief",
        ),
        "sequencePlan": resolve_internal_episode_path(
            episode,
            configured.get("sequencePlan", "work/sequence-plan.json"),
            "sequencePlan",
        ),
        "sequenceRoot": resolve_internal_episode_path(
            episode,
            configured.get("sequenceRoot", "sequences"),
            "sequenceRoot",
        ),
        "assemblyPlan": resolve_internal_episode_path(
            episode,
            configured.get("assemblyPlan", "work/assembly-plan.json"),
            "assemblyPlan",
        ),
    }


def validate_sequence_inputs(
    manifest: dict[str, Any], creative_brief: dict[str, Any], sequence_plan: dict[str, Any]
) -> list[str]:
    issues: list[str] = []
    if not isinstance(creative_brief, dict):
        return ["creative brief must be an object"]
    if not isinstance(sequence_plan, dict):
        return ["sequence plan must be an object"]
    issues.extend(validate_schema_file(creative_brief, CREATIVE_BRIEF_SCHEMA_PATH, "creative brief"))
    issues.extend(validate_schema_file(sequence_plan, SEQUENCE_PLAN_SCHEMA_PATH, "sequence plan"))
    episode_id = manifest.get("id")
    if creative_brief.get("schemaVersion") != 1:
        issues.append("creative brief schemaVersion must be 1")
    if sequence_plan.get("schemaVersion") != 1:
        issues.append("sequence plan schemaVersion must be 1")
    if creative_brief.get("episodeId") != episode_id:
        issues.append("creative brief episodeId does not match episode.json")
    if sequence_plan.get("episodeId") != episode_id:
        issues.append("sequence plan episodeId does not match episode.json")
    if sequence_plan.get("sourceClock") != "retimed-aroll":
        issues.append("sequence plan must use the retimed-aroll clock")

    sequences = sequence_plan.get("sequences")
    if not isinstance(sequences, list) or not sequences:
        issues.append("sequence plan contains no semantic sequences")
        return issues

    ids: set[str] = set()
    previous_end = 0.0
    for index, sequence in enumerate(sequences):
        if not isinstance(sequence, dict):
            issues.append(f"sequence {index} must be an object")
            continue
        sequence_id = sequence.get("id")
        if not isinstance(sequence_id, str) or not re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]*", sequence_id):
            issues.append(f"sequence {index} has an invalid id")
        elif sequence_id in ids:
            issues.append(f"duplicate sequence id: {sequence_id}")
        else:
            ids.add(sequence_id)
        try:
            start = float(sequence.get("start"))
            end = float(sequence.get("end"))
        except (TypeError, ValueError):
            issues.append(f"sequence {sequence_id or index} has invalid start/end")
            continue
        if start < 0 or end <= start:
            issues.append(f"sequence {sequence_id or index} has invalid range {start}..{end}")
        if index and start < previous_end - 0.0001:
            issues.append(f"sequence {sequence_id or index} overlaps the previous sequence")
        previous_end = max(previous_end, end)
        for field in ("transcript", "audienceTask", "primaryVisualRole"):
            if not isinstance(sequence.get(field), str) or not sequence[field].strip():
                issues.append(f"sequence {sequence_id or index} is missing {field}")
        design = sequence.get("design")
        if not isinstance(design, dict):
            issues.append(f"sequence {sequence_id or index} is missing design")
            continue
        for field in ("entryState", "visibleAction", "landedComposition", "exitState"):
            if not isinstance(design.get(field), str) or not design[field].strip():
                issues.append(f"sequence {sequence_id or index} design is missing {field}")
    return issues


def shared_context_entry(episode: Path, scope: str, raw_path: str) -> dict[str, Any]:
    base = episode if scope == "episode" else ROOT
    target = (base / raw_path).expanduser().resolve()
    entry: dict[str, Any] = {
        "scope": scope,
        "path": raw_path,
        "exists": target.exists(),
        "kind": "file" if target.is_file() else "directory" if target.is_dir() else "missing",
    }
    if target.is_file():
        entry["sha256"] = sha256_file(target)
        entry["sizeBytes"] = target.stat().st_size
    return entry


def task_shared_context(episode: Path, manifest: dict[str, Any]) -> list[dict[str, Any]]:
    episode_paths = [
        "BRIEF.md",
        "SCRIPT.md",
        "SOURCES.md",
        "DESIGN.md",
        "MOTION-STORYBOARD.md",
        manifest.get("paths", {}).get("inventory", "work/media-inventory.json"),
        manifest.get("paths", {}).get("captions", "work/captions.json"),
        manifest.get("paths", {}).get("aRoll", "assets/media/a-roll-1080p60.mp4"),
    ]
    repository_paths = ["config/editorial-defaults.json", "library/taste/current.json"]
    taste_path = ROOT / "library" / "taste" / "current.json"
    if taste_path.is_file():
        taste_sources = load_json(taste_path).get("sources") or {}
        if isinstance(taste_sources, dict):
            repository_paths.extend(
                value for value in taste_sources.values() if isinstance(value, str)
            )
    entries = [shared_context_entry(episode, "episode", path) for path in episode_paths]
    entries.extend(shared_context_entry(episode, "repository", path) for path in repository_paths)
    unique: dict[tuple[str, str], dict[str, Any]] = {}
    for entry in entries:
        unique[(entry["scope"], entry["path"])] = entry
    return list(unique.values())


def source_contract(episode: Path, sequence: dict[str, Any]) -> list[dict[str, Any]]:
    contract: list[dict[str, Any]] = []
    for source in sequence.get("sourceMedia") or []:
        if not isinstance(source, dict):
            continue
        raw_path = source.get("path")
        if not isinstance(raw_path, str) or not raw_path.strip():
            continue
        target = resolve_episode_path(episode, raw_path)
        entry = dict(source)
        entry["exists"] = target.is_file()
        if target.is_file():
            entry["sha256"] = sha256_file(target)
            entry["sizeBytes"] = target.stat().st_size
        contract.append(entry)
    return contract


REGISTRY_PATH_FIELDS = (
    "file",
    "files",
    "audio",
    "implementation",
    "configuration",
    "recipe",
    "preview",
    "review",
    "reference",
)


def registry_file_contract(record: dict[str, Any]) -> list[dict[str, Any]]:
    files: list[dict[str, Any]] = []
    for field in REGISTRY_PATH_FIELDS:
        raw_values = record.get(field)
        values = raw_values if isinstance(raw_values, list) else [raw_values]
        for raw_value in values:
            if not isinstance(raw_value, str) or not raw_value.strip():
                continue
            if re.match(r"^[a-z][a-z0-9+.-]*://", raw_value, flags=re.I):
                files.append({"field": field, "path": raw_value, "external": True})
                continue
            raw_path, separator, fragment = raw_value.partition("#")
            target = (ROOT / raw_path).resolve()
            inside_root = ROOT.resolve() in (target, *target.parents)
            entry: dict[str, Any] = {
                "field": field,
                "path": raw_path,
                "exists": inside_root and target.is_file(),
            }
            if separator:
                entry["fragment"] = fragment
            if entry["exists"]:
                entry["sha256"] = sha256_file(target)
                entry["sizeBytes"] = target.stat().st_size
            files.append(entry)
    return files


def capability_contract(sequence: dict[str, Any]) -> list[dict[str, Any]]:
    technique_registry_path = ROOT / "library" / "techniques" / "registry.json"
    asset_registry_path = ROOT / "references" / "asset-library" / "registry.json"
    techniques = load_json(technique_registry_path).get("techniques") or []
    assets = load_json(asset_registry_path).get("assets") or []
    technique_by_id = {item.get("id"): item for item in techniques if isinstance(item, dict)}
    asset_by_id = {item.get("id"): item for item in assets if isinstance(item, dict)}
    resolved: list[dict[str, Any]] = []
    for requested in sequence.get("capabilities") or []:
        if not isinstance(requested, dict):
            continue
        technique_id = requested.get("techniqueId")
        technique = technique_by_id.get(technique_id)
        entry: dict[str, Any] = {
            **requested,
            "resolved": technique is not None,
        }
        if technique is not None:
            entry["technique"] = technique
            entry["techniqueFingerprint"] = json_fingerprint(technique)
            entry["techniqueFiles"] = registry_file_contract(technique)
            requested_assets = list(technique.get("assetRefs") or [])
            if requested.get("assetId"):
                requested_assets.append(requested["assetId"])
            linked_assets = []
            for asset_id in dict.fromkeys(requested_assets):
                asset = asset_by_id.get(asset_id)
                asset_entry: dict[str, Any] = {"id": asset_id, "resolved": asset is not None}
                if asset is not None:
                    asset_entry["asset"] = asset
                    asset_entry["assetFingerprint"] = json_fingerprint(asset)
                    asset_entry["files"] = registry_file_contract(asset)
                linked_assets.append(asset_entry)
            entry["assets"] = linked_assets
        reference = requested.get("reference")
        if isinstance(reference, str):
            direct_reference = (ROOT / reference).resolve()
            reference_card = ROOT / "library" / "references" / reference / "reference.yaml"
            reference_path = direct_reference if direct_reference.is_file() else reference_card.resolve()
            entry["referenceExists"] = reference_path.is_file()
            if reference_path.is_file():
                entry["referencePath"] = reference_path.relative_to(ROOT).as_posix()
                entry["referenceSha256"] = sha256_file(reference_path)
        resolved.append(entry)
    return resolved


def capability_contract_issues(sequence_id: str, capabilities: list[dict[str, Any]]) -> list[str]:
    issues: list[str] = []
    for capability in capabilities:
        technique_id = capability.get("techniqueId") or "unknown"
        if not capability.get("resolved"):
            issues.append(
                f"sequence {sequence_id} capability is not in the technique registry: {technique_id}"
            )
            continue
        if capability.get("reference") and not capability.get("referenceExists"):
            issues.append(
                f"sequence {sequence_id} capability reference does not exist: "
                f"{capability.get('reference')}"
            )
        for file_contract in capability.get("techniqueFiles") or []:
            if not file_contract.get("external") and not file_contract.get("exists"):
                issues.append(
                    f"sequence {sequence_id} capability file does not exist: "
                    f"{file_contract.get('path')}"
                )
        for linked_asset in capability.get("assets") or []:
            asset_id = linked_asset.get("id") or "unknown"
            if not linked_asset.get("resolved"):
                issues.append(
                    f"sequence {sequence_id} capability asset is not in the asset registry: {asset_id}"
                )
                continue
            for file_contract in linked_asset.get("files") or []:
                if not file_contract.get("external") and not file_contract.get("exists"):
                    issues.append(
                        f"sequence {sequence_id} capability asset file does not exist: "
                        f"{file_contract.get('path')}"
                    )
    return issues


def neighbor_summary(sequence: dict[str, Any] | None, edge: str) -> dict[str, Any] | None:
    if not sequence:
        return None
    design = sequence.get("design") or {}
    return {
        "id": sequence.get("id"),
        "start": sequence.get("start"),
        "end": sequence.get("end"),
        "boundaryState": design.get(edge, ""),
    }


def build_sequence_packet(
    episode: Path,
    manifest: dict[str, Any],
    creative_brief: dict[str, Any],
    sequences: list[dict[str, Any]],
    index: int,
    sequence_root: Path,
) -> dict[str, Any]:
    sequence = sequences[index]
    sequence_id = sequence["id"]
    root_relative = sequence_root.relative_to(episode).as_posix()
    sources = source_contract(episode, sequence)
    capabilities = capability_contract(sequence)
    packet = {
        "schemaVersion": 1,
        "systemVersion": 3,
        "episodeId": manifest["id"],
        "sequenceId": sequence_id,
        "creativeBrief": creative_brief,
        "sequence": sequence,
        "neighbors": {
            "previous": neighbor_summary(sequences[index - 1] if index else None, "exitState"),
            "next": neighbor_summary(
                sequences[index + 1] if index + 1 < len(sequences) else None,
                "entryState",
            ),
        },
        "sharedContext": task_shared_context(episode, manifest),
        "sourceContract": sources,
        "capabilityContract": capabilities,
        "outputContract": {
            "exclusiveWriteRoot": f"{root_relative}/{sequence_id}",
            "assetUrlPrefix": f"{root_relative}/{sequence_id}/",
            "manifest": "sequence.json",
            "fragment": "scene.html",
            "styles": "styles.css",
            "timeline": "timeline.js",
            "clock": "absolute-retimed-aroll-seconds",
            "domIdPrefix": f"{sequence_id}-",
            "singleWriterOutsideThisRoot": "director",
            "executionIsolation": "forked-worktree-or-equivalent",
        },
    }
    packet["taskFingerprint"] = json_fingerprint(packet)
    return packet


def command_pack_sequences(args: argparse.Namespace) -> int:
    episode, manifest, _ = load_episode(args.episode)
    runtime_issues = v3_runtime_issues(episode)
    if runtime_issues:
        raise RuntimeError(
            "episode runtime is not V3-ready; run upgrade-v3 first:\n- "
            + "\n- ".join(runtime_issues)
        )
    paths = sequence_paths(episode, manifest)
    if not paths["creativeBrief"].is_file():
        raise FileNotFoundError(paths["creativeBrief"])
    if not paths["sequencePlan"].is_file():
        raise FileNotFoundError(paths["sequencePlan"])
    creative_brief = load_json(paths["creativeBrief"])
    sequence_plan = load_json(paths["sequencePlan"])
    issues = validate_sequence_inputs(manifest, creative_brief, sequence_plan)
    planned_sequences = (
        sequence_plan.get("sequences") or [] if isinstance(sequence_plan, dict) else []
    )
    for sequence in planned_sequences if isinstance(planned_sequences, list) else []:
        if not isinstance(sequence, dict):
            continue
        sequence_id = sequence.get("id", "unknown")
        for source in source_contract(episode, sequence):
            if not source.get("exists"):
                issues.append(f"sequence {sequence_id} source does not exist: {source.get('path')}")
        issues.extend(capability_contract_issues(sequence_id, capability_contract(sequence)))
    if issues:
        raise ValueError("V3 sequence plan is not ready:\n- " + "\n- ".join(issues))

    sequence_root = paths["sequenceRoot"]
    sequence_root.mkdir(parents=True, exist_ok=True)
    sequences = sequence_plan["sequences"]
    packed = []
    for index, sequence in enumerate(sequences):
        sequence_id = sequence["id"]
        output_dir = sequence_root / sequence_id
        output_dir.mkdir(parents=True, exist_ok=True)
        packet = build_sequence_packet(
            episode,
            manifest,
            creative_brief,
            sequences,
            index,
            sequence_root,
        )
        task_path = output_dir / "TASK.json"
        if task_path.is_file() and not args.force:
            existing = load_json(task_path)
            if not isinstance(existing, dict):
                raise RuntimeError(
                    f"existing task packet is invalid for {sequence_id}; "
                    "rerun with --force to replace it"
                )
            if existing.get("taskFingerprint") != packet["taskFingerprint"]:
                raise RuntimeError(
                    f"task packet changed for {sequence_id}; rerun with --force after the director "
                    "accepts invalidating that worker output"
                )
        write_json(task_path, packet)
        packed.append(
            {
                "sequenceId": sequence_id,
                "task": task_path.relative_to(episode).as_posix(),
                "taskFingerprint": packet["taskFingerprint"],
            }
        )

    report = {
        "systemVersion": 3,
        "episodeId": manifest["id"],
        "sequencePlanFingerprint": json_fingerprint(sequence_plan),
        "creativeBriefFingerprint": json_fingerprint(creative_brief),
        "tasks": packed,
    }
    write_json(episode / "work" / "sequence-pack.json", report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


def safe_sequence_file(sequence_dir: Path, raw_path: str) -> Path:
    relative = Path(raw_path)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError(f"sequence output path must stay inside its directory: {raw_path}")
    resolved = (sequence_dir / relative).resolve()
    if sequence_dir.resolve() not in (resolved, *resolved.parents):
        raise ValueError(f"sequence output escapes its directory: {raw_path}")
    return resolved


def selector_starts_in_sequence(selector: str, sequence_id: str) -> bool:
    scoped = selector.strip()
    id_anchor = re.match(rf"#{re.escape(sequence_id)}-[A-Za-z0-9_-]+", scoped)
    attr_anchor = f'[data-sequence="{sequence_id}"]'
    if id_anchor:
        position = id_anchor.end()
    elif scoped.startswith(attr_anchor):
        position = len(attr_anchor)
    else:
        return False

    parentheses = 0
    brackets = 0
    quote: str | None = None
    while position < len(scoped):
        character = scoped[position]
        if quote:
            if character == quote and scoped[position - 1] != "\\":
                quote = None
        elif character in {"'", '"'}:
            quote = character
        elif character == "(":
            parentheses += 1
        elif character == ")":
            parentheses = max(0, parentheses - 1)
        elif character == "[":
            brackets += 1
        elif character == "]":
            brackets = max(0, brackets - 1)
        elif parentheses == 0 and brackets == 0:
            if character in {"+", "~", ","}:
                return False
            if character == ">":
                return True
            if character.isspace():
                while position < len(scoped) and scoped[position].isspace():
                    position += 1
                return position >= len(scoped) or scoped[position] not in {"+", "~", ","}
        position += 1
    return True


def sequence_css_issues(sequence_id: str, css: str) -> list[str]:
    issues: list[str] = []
    if re.search(r"</?style\b", css, flags=re.I):
        issues.append("styles contain style tags")
    without_comments = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    forbidden_at_rules = re.findall(
        r"@(import|charset|namespace|font-face|page|property|counter-style)\b",
        without_comments,
        flags=re.I,
    )
    for at_rule in forbidden_at_rules:
        issues.append(f"global CSS at-rule @{at_rule} is not allowed")
    for raw_selector in re.findall(r"([^{}]+)\{", without_comments):
        selector = raw_selector.strip()
        if not selector or selector.startswith("@"):
            continue
        if selector in {"from", "to"} or re.fullmatch(r"(?:\d+(?:\.\d+)?%\s*,?\s*)+", selector):
            continue
        for part in selector.split(","):
            scoped = part.strip()
            if not selector_starts_in_sequence(scoped, sequence_id):
                issues.append(f"unscoped CSS selector {scoped!r}")
    return issues


def mask_javascript_literals_and_comments(code: str) -> str:
    """Preserve offsets while hiding strings and comments from identifier checks."""
    masked = list(code)
    index = 0
    length = len(code)
    while index < length:
        if code.startswith("//", index):
            end = code.find("\n", index + 2)
            end = length if end == -1 else end
            for position in range(index, end):
                masked[position] = " "
            index = end
            continue
        if code.startswith("/*", index):
            end = code.find("*/", index + 2)
            end = length if end == -1 else end + 2
            for position in range(index, end):
                if masked[position] != "\n":
                    masked[position] = " "
            index = end
            continue
        if code[index] in {"'", '"', "`"}:
            quote = code[index]
            position = index
            while position < length:
                if masked[position] != "\n":
                    masked[position] = " "
                if position > index and code[position] == quote and code[position - 1] != "\\":
                    position += 1
                    break
                if code[position] == "\\" and position + 1 < length:
                    position += 1
                    if masked[position] != "\n":
                        masked[position] = " "
                position += 1
            index = position
            continue
        index += 1
    return "".join(masked)


class JavaScriptLiteralParser:
    """Parse the declarative JavaScript subset accepted in worker timelines."""

    def __init__(self, code: str) -> None:
        self.code = code
        self.position = 0

    def skip_trivia(self) -> None:
        while self.position < len(self.code):
            if self.code[self.position].isspace():
                self.position += 1
                continue
            if self.code.startswith("//", self.position):
                newline = self.code.find("\n", self.position + 2)
                self.position = len(self.code) if newline == -1 else newline + 1
                continue
            if self.code.startswith("/*", self.position):
                end = self.code.find("*/", self.position + 2)
                if end == -1:
                    raise ValueError("unterminated timeline comment")
                self.position = end + 2
                continue
            break

    def parse_string(self) -> str:
        quote = self.code[self.position]
        self.position += 1
        value: list[str] = []
        while self.position < len(self.code):
            character = self.code[self.position]
            if character == quote:
                self.position += 1
                return "".join(value)
            if character in "\r\n":
                raise ValueError("timeline strings may not contain an unescaped newline")
            if character == "\\":
                if self.position + 1 >= len(self.code):
                    raise ValueError("unterminated timeline string escape")
                escaped = self.code[self.position + 1]
                if escaped not in {quote, "\\"}:
                    raise ValueError(
                        "timeline strings may only escape their quote or backslash"
                    )
                value.append(escaped)
                self.position += 2
                continue
            value.append(character)
            self.position += 1
        raise ValueError("unterminated timeline string")

    def parse_number(self) -> float:
        number = re.match(
            r"[+-]?(?:(?:\d+(?:\.\d*)?)|(?:\.\d+))(?:[eE][+-]?\d+)?",
            self.code[self.position :],
        )
        if not number:
            raise ValueError("invalid timeline number")
        self.position += len(number.group(0))
        return float(number.group(0))

    def parse_array(self) -> list[Any]:
        self.position += 1
        values: list[Any] = []
        self.skip_trivia()
        if self.position < len(self.code) and self.code[self.position] == "]":
            self.position += 1
            return values
        while True:
            values.append(self.parse_value())
            self.skip_trivia()
            if self.position >= len(self.code):
                raise ValueError("unterminated timeline array")
            if self.code[self.position] == "]":
                self.position += 1
                return values
            if self.code[self.position] != ",":
                raise ValueError("timeline arrays may contain only literal values")
            self.position += 1
            self.skip_trivia()

    def parse_object_key(self) -> str:
        self.skip_trivia()
        if self.position >= len(self.code):
            raise ValueError("unterminated timeline object")
        if self.code[self.position] in {"'", '"'}:
            return self.parse_string()
        identifier = re.match(r"[A-Za-z_$][\w$-]*", self.code[self.position :])
        if not identifier:
            raise ValueError("timeline object keys must be direct identifiers or quoted strings")
        self.position += len(identifier.group(0))
        return identifier.group(0)

    def parse_object(self) -> dict[str, Any]:
        self.position += 1
        values: dict[str, Any] = {}
        self.skip_trivia()
        if self.position < len(self.code) and self.code[self.position] == "}":
            self.position += 1
            return values
        while True:
            key = self.parse_object_key()
            self.skip_trivia()
            if self.position >= len(self.code) or self.code[self.position] != ":":
                raise ValueError("timeline object entries must use key: literal-value syntax")
            self.position += 1
            values[key] = self.parse_value()
            self.skip_trivia()
            if self.position >= len(self.code):
                raise ValueError("unterminated timeline object")
            if self.code[self.position] == "}":
                self.position += 1
                return values
            if self.code[self.position] != ",":
                raise ValueError("timeline objects may contain only literal properties")
            self.position += 1
            self.skip_trivia()

    def parse_value(self) -> Any:
        self.skip_trivia()
        if self.position >= len(self.code):
            raise ValueError("missing timeline literal value")
        character = self.code[self.position]
        if character in {"'", '"'}:
            return self.parse_string()
        if character == "{":
            return self.parse_object()
        if character == "[":
            return self.parse_array()
        if character in "+-." or character.isdigit():
            return self.parse_number()
        identifier = re.match(r"[A-Za-z_$][\w$]*", self.code[self.position :])
        if identifier and identifier.group(0) in {"true", "false", "null"}:
            self.position += len(identifier.group(0))
            return {"true": True, "false": False, "null": None}[identifier.group(0)]
        raise ValueError("timeline arguments may contain only strings, numbers, booleans, arrays, and objects")


def timeline_statement_issues(
    code: str,
    sequence_id: str,
    sequence_start: float,
    sequence_end: float,
    root_dom_ids: set[str],
) -> list[str]:
    issues: list[str] = []
    parsed_calls: list[tuple[str, list[Any]]] = []
    direct = re.compile(r"timeline\s*\.\s*(set|to|from|fromTo)\s*\(")
    parser = JavaScriptLiteralParser(code)
    while True:
        try:
            parser.skip_trivia()
        except ValueError as error:
            issues.append(str(error))
            break
        while parser.position < len(code) and code[parser.position] == ";":
            parser.position += 1
            parser.skip_trivia()
        if parser.position >= len(code):
            break
        call = direct.match(code, parser.position)
        if not call:
            issues.append("timeline file may contain only direct timeline animation statements")
            break
        method = call.group(1)
        parser.position = call.end()
        arguments: list[Any] = []
        try:
            parser.skip_trivia()
            if parser.position < len(code) and code[parser.position] != ")":
                while True:
                    arguments.append(parser.parse_value())
                    parser.skip_trivia()
                    if parser.position >= len(code):
                        raise ValueError("timeline call has unbalanced parentheses")
                    if code[parser.position] == ")":
                        break
                    if code[parser.position] != ",":
                        raise ValueError("timeline arguments must be declarative literal values")
                    parser.position += 1
            if parser.position >= len(code) or code[parser.position] != ")":
                raise ValueError("timeline call has unbalanced parentheses")
            parser.position += 1
        except ValueError as error:
            issues.append(str(error))
            break
        expected = 4 if method == "fromTo" else 3
        if len(arguments) != expected:
            issues.append(
                f"timeline.{method} requires {expected} literal arguments, "
                "including an explicit absolute position"
            )
        if arguments and not isinstance(arguments[0], str):
            issues.append(f"timeline.{method} first argument must be a scoped selector string")
        parsed_calls.append((method, arguments))

    root_selector = f"#{sequence_id}-root"

    def selector_is_inside_root(selector: Any) -> bool:
        if not isinstance(selector, str):
            return False
        parts = [part.strip() for part in selector.split(",") if part.strip()]
        if not parts:
            return False
        for part in parts:
            anchor = re.match(r"#([A-Za-z][A-Za-z0-9_-]*)", part)
            if not anchor or anchor.group(1) not in root_dom_ids:
                return False
        return True

    has_hidden_root_initialization = any(
        method == "set"
        and len(arguments) == 3
        and arguments[0] == root_selector
        and isinstance(arguments[1], dict)
        and arguments[2] == 0
        and (
            arguments[1].get("autoAlpha") == 0
            or arguments[1].get("opacity") == 0
            or arguments[1].get("visibility") == "hidden"
        )
        for method, arguments in parsed_calls
    )
    for method, arguments in parsed_calls:
        expected = 4 if method == "fromTo" else 3
        if len(arguments) != expected:
            continue
        position = arguments[-1]
        if (
            not isinstance(position, (int, float))
            or isinstance(position, bool)
            or not math.isfinite(float(position))
        ):
            issues.append(f"timeline.{method} position must be a finite absolute second")
            continue
        absolute_position = float(position)
        destination_vars = arguments[2] if method == "fromTo" else arguments[1]
        hides_root = (
            arguments[0] == root_selector
            and isinstance(destination_vars, dict)
            and (
                destination_vars.get("autoAlpha") == 0
                or destination_vars.get("opacity") == 0
                or destination_vars.get("visibility") == "hidden"
            )
        )
        safe_zero_initialization = (
            method == "set"
            and absolute_position == 0
            and has_hidden_root_initialization
            and selector_is_inside_root(arguments[0])
            and (arguments[0] != root_selector or hides_root)
        )
        if (
            (absolute_position < sequence_start or absolute_position > sequence_end)
            and not safe_zero_initialization
        ):
            issues.append(
                f"timeline.{method} position {absolute_position} is outside sequence "
                f"{sequence_start}-{sequence_end}"
            )
        duration = destination_vars.get("duration", 0) if isinstance(destination_vars, dict) else 0
        if isinstance(duration, (int, float)) and not isinstance(duration, bool):
            duration_value = float(duration)
            if (
                math.isfinite(duration_value)
                and duration_value >= 0
                and not safe_zero_initialization
                and absolute_position + duration_value > sequence_end + 1e-6
            ):
                issues.append(
                    f"timeline.{method} ends at {absolute_position + duration_value} "
                    f"outside sequence {sequence_start}-{sequence_end}"
                )
    return issues


def sequence_timeline_issues(
    sequence_id: str,
    code: str,
    sequence_start: float,
    sequence_end: float,
    root_dom_ids: set[str],
) -> list[str]:
    issues: list[str] = []
    masked_code = mask_javascript_literals_and_comments(code)
    if re.search(r"</?script\b", code, flags=re.I):
        issues.append("timeline contains script tags")
    if re.search(r"\b(?:const|let|var)\s+timeline\b|gsap\s*(?:\.timeline|\[)", code):
        issues.append("timeline must append to the shared timeline, not create another one")
    if re.search(r"\b(?:window|document|globalThis|eval|Function)\b", code):
        issues.append("timeline may not access global browser state")
    if re.search(r"\bgsap\s*[.[]", code):
        issues.append("timeline may not call gsap directly; use the shared timeline")
    if "`" in code:
        issues.append("timeline template literals are not allowed")
    if re.search(r"=>|\bfunction\b|\bfetch\b|\bXMLHttpRequest\b|\bsetAttribute\b", masked_code):
        issues.append("timeline callbacks and dynamic resource APIs are not allowed")
    if "..." in masked_code:
        issues.append("timeline object spread is not allowed")
    issues.extend(
        timeline_statement_issues(
            code,
            sequence_id,
            sequence_start,
            sequence_end,
            root_dom_ids,
        )
    )
    direct_call_pattern = re.compile(
        r"\btimeline\b\s*\.\s*(set|to|from|fromTo)\s*\("
    )
    for member_call in re.finditer(
        r"\btimeline\b\s*\.\s*([A-Za-z_$][\w$]*)\s*\(", masked_code
    ):
        if member_call.group(1) not in {"set", "to", "from", "fromTo"}:
            issues.append(
                f"timeline method {member_call.group(1)!r} is not allowed in a sequence"
            )
    allowed_timeline_offsets = {match.start() for match in direct_call_pattern.finditer(masked_code)}
    for occurrence in re.finditer(r"\btimeline\b", masked_code):
        if occurrence.start() not in allowed_timeline_offsets:
            issues.append(
                "timeline may only appear as a direct set/to/from/fromTo call; aliases and computed access are forbidden"
            )

    def selector_issues(selector: str) -> list[str]:
        return [
            f"timeline selector is outside its sequence: {part.strip()!r}"
            for part in selector.split(",")
            if not selector_starts_in_sequence(part, sequence_id)
        ]

    for call in direct_call_pattern.finditer(masked_code):
        method = call.group(1)
        first_argument = re.match(r"\s*([\"'])(.*?)(?<!\\)\1", code[call.end() :], flags=re.S)
        if not first_argument:
            issues.append(f"timeline.{method} first argument must be a scoped selector string")
            continue
        selector = first_argument.group(2).strip()
        issues.extend(selector_issues(selector))
    for _, candidate in re.findall(r"([\"'])(.*?)(?<!\\)\1", code, flags=re.S):
        candidate = candidate.strip()
        if re.fullmatch(r"#[0-9a-fA-F]{3,8}", candidate):
            continue
        if candidate.startswith(("#", ".", "[")):
            issues.extend(selector_issues(candidate))

    with tempfile.NamedTemporaryFile("w", suffix=".js", encoding="utf-8", delete=False) as temporary:
        temporary.write(code)
        temporary.write("\n")
        syntax_path = Path(temporary.name)
    try:
        completed = run(["node", "--check", str(syntax_path)], check=False)
        if completed.returncode:
            detail = (completed.stderr or completed.stdout).strip().splitlines()
            issues.append(f"timeline JavaScript is invalid: {detail[-1] if detail else 'syntax error'}")
    finally:
        syntax_path.unlink(missing_ok=True)
    return issues


def normalize_local_reference(raw_reference: str) -> str | None:
    reference = raw_reference.strip().strip('"\'')
    if not reference or reference.startswith(("#", "data:", "blob:")):
        return None
    if re.match(r"^[a-z][a-z0-9+.-]*://", reference, flags=re.I):
        return None
    clean = reference.split("?", 1)[0].split("#", 1)[0]
    if not clean:
        return None
    normalized = posixpath.normpath(clean.replace("\\", "/"))
    return normalized[2:] if normalized.startswith("./") else normalized


def external_resource_reference(raw_reference: str) -> str | None:
    reference = raw_reference.strip().strip('"\'')
    if not reference or reference.startswith("#"):
        return None
    if reference.startswith(("data:", "blob:")) or re.match(
        r"^[a-z][a-z0-9+.-]*://", reference, flags=re.I
    ):
        return reference
    return None


RESOURCE_REFERENCE_PATTERN = re.compile(
    r"(?:^|/)[^/]+\.(?:avif|gif|jpe?g|json|lottie|m4a|mov|mp3|mp4|ogg|png|svg|tiff?|wav|webm|webp|woff2?)(?:[?#].*)?$",
    flags=re.I,
)


def quoted_resource_references(text: str) -> tuple[set[str], set[str]]:
    local: set[str] = set()
    external: set[str] = set()
    for match in re.finditer(r"([\"'])(.*?)(?<!\\)\1", text, flags=re.S):
        candidate = match.group(2).strip()
        remote = external_resource_reference(candidate)
        if remote:
            external.add(remote)
            continue
        if RESOURCE_REFERENCE_PATTERN.search(candidate) or candidate.startswith(
            ("source/", "sequences/", "assets/", "references/", "./", "../", "/")
        ):
            normalized = normalize_local_reference(candidate)
            if normalized:
                local.add(normalized)
    return local, external


def css_resource_references(css: str) -> tuple[set[str], set[str]]:
    local, external = quoted_resource_references(css)
    for match in re.finditer(r"url\(\s*([^)]*?)\s*\)", css, flags=re.I):
        raw_reference = match.group(1)
        remote = external_resource_reference(raw_reference)
        if remote:
            external.add(remote)
            continue
        normalized = normalize_local_reference(raw_reference)
        if normalized:
            local.add(normalized)
    return local, external


class FragmentReferenceParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.local_references: set[str] = set()
        self.external_references: set[str] = set()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        del tag
        for name, value in attrs:
            if not value:
                continue
            lowered = name.lower()
            values: list[str] = []
            if lowered in {"src", "href", "poster", "xlink:href"}:
                values = [value]
            elif lowered == "srcset":
                values = [candidate.strip().split()[0] for candidate in value.split(",") if candidate.strip()]
            elif lowered == "style":
                local, external = css_resource_references(value)
                self.local_references.update(local)
                self.external_references.update(external)
            for candidate in values:
                remote = external_resource_reference(candidate)
                if remote:
                    self.external_references.add(remote)
                    continue
                normalized = normalize_local_reference(candidate)
                if normalized:
                    self.local_references.add(normalized)


class FragmentDomScopeParser(HTMLParser):
    VOID_TAGS = {
        "area", "base", "br", "col", "embed", "hr", "img", "input",
        "link", "meta", "param", "source", "track", "wbr",
    }

    def __init__(self, root_id: str) -> None:
        super().__init__(convert_charrefs=True)
        self.root_id = root_id
        self.root_tag: str | None = None
        self.stack: list[str] = []
        self.root_depth: int | None = None
        self.ids_within_root: set[str] = set()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        dom_id = next((value for name, value in attrs if name.lower() == "id"), None)
        if dom_id == self.root_id and self.root_depth is None:
            self.root_tag = tag.lower()
            self.root_depth = len(self.stack)
        if self.root_depth is not None and dom_id:
            self.ids_within_root.add(dom_id)
        if tag.lower() not in self.VOID_TAGS:
            self.stack.append(tag.lower())

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)
        if tag.lower() not in self.VOID_TAGS:
            self.handle_endtag(tag)

    def handle_endtag(self, tag: str) -> None:
        lowered = tag.lower()
        if lowered not in self.stack:
            return
        while self.stack:
            popped = self.stack.pop()
            if popped == lowered:
                break
        if self.root_depth is not None and len(self.stack) <= self.root_depth:
            self.root_depth = None


def fragment_resource_references(fragment: str) -> tuple[set[str], set[str]]:
    parser = FragmentReferenceParser()
    parser.feed(fragment)
    parser.close()
    return parser.local_references, parser.external_references


def fragment_dom_scope(fragment: str, root_id: str) -> tuple[set[str], str | None]:
    parser = FragmentDomScopeParser(root_id)
    parser.feed(fragment)
    parser.close()
    return parser.ids_within_root, parser.root_tag


def timeline_resource_references(code: str) -> tuple[set[str], set[str]]:
    local, external = css_resource_references(code)
    resource_keys = "src|href|poster|backgroundImage|maskImage"
    if re.search(rf"\[\s*[\"'](?:{resource_keys})[\"']\s*\]", code):
        external.add("computed-resource-property")
    property_pattern = re.compile(
        rf"(?:\b(?:{resource_keys})\b|[\"'](?:{resource_keys})[\"'])\s*:\s*",
        flags=re.S,
    )
    for match in property_pattern.finditer(code):
        literal = re.match(r"([\"'])(.*?)(?<!\\)\1", code[match.end() :], flags=re.S)
        if not literal:
            external.add("dynamic-resource-expression")
            continue
        candidate = literal.group(2)
        remote = external_resource_reference(candidate)
        if remote:
            external.add(remote)
            continue
        normalized = normalize_local_reference(candidate)
        if normalized:
            local.add(normalized)
    for attr in re.finditer(r"\battr\s*:\s*", code):
        if not re.match(r"\{", code[attr.end() :].lstrip()):
            external.add("dynamic-attr-expression")
    return local, external


def validate_sequence_outputs(
    episode: Path, manifest: dict[str, Any]
) -> tuple[list[dict[str, Any]], list[str]]:
    paths = sequence_paths(episode, manifest)
    if not paths["creativeBrief"].is_file():
        return [], [f"missing creative brief: {paths['creativeBrief']}"]
    if not paths["sequencePlan"].is_file():
        return [], [f"missing sequence plan: {paths['sequencePlan']}"]
    creative_brief = load_json(paths["creativeBrief"])
    sequence_plan = load_json(paths["sequencePlan"])
    input_issues = validate_sequence_inputs(manifest, creative_brief, sequence_plan)
    if input_issues:
        return [], input_issues
    planned_sequences = sequence_plan["sequences"]
    checked: list[dict[str, Any]] = []
    issues: list[str] = []
    all_dom_ids: dict[str, str] = {}
    for index, sequence in enumerate(planned_sequences):
        sequence_id = sequence.get("id", "unknown")
        sequence_dir = paths["sequenceRoot"] / sequence_id
        task_path = sequence_dir / "TASK.json"
        manifest_path = sequence_dir / "sequence.json"
        if not task_path.is_file():
            issues.append(f"{sequence_id}: missing TASK.json; run pack-sequences")
            continue
        if not manifest_path.is_file():
            issues.append(f"{sequence_id}: missing sequence.json from worker")
            continue
        task = load_json(task_path)
        output = load_json(manifest_path)
        task_schema_issues = validate_schema_file(task, SEQUENCE_TASK_SCHEMA_PATH, "TASK.json")
        output_schema_issues = validate_schema_file(
            output, SEQUENCE_OUTPUT_SCHEMA_PATH, "sequence.json"
        )
        issues.extend(f"{sequence_id}: {issue}" for issue in task_schema_issues)
        issues.extend(f"{sequence_id}: {issue}" for issue in output_schema_issues)
        if not isinstance(task, dict) or not isinstance(output, dict):
            continue
        expected_task = build_sequence_packet(
            episode,
            manifest,
            creative_brief,
            planned_sequences,
            index,
            paths["sequenceRoot"],
        )
        if task != expected_task:
            issues.append(f"{sequence_id}: TASK.json is stale or was modified; rerun pack-sequences")
        if output.get("sequenceId") != sequence_id:
            issues.append(f"{sequence_id}: output sequenceId mismatch")
        if output.get("taskFingerprint") != task.get("taskFingerprint"):
            issues.append(f"{sequence_id}: worker output is stale for the current task packet")
        if output.get("status") != "ready":
            issues.append(f"{sequence_id}: output status must be ready")
        if not str(output.get("landedResult") or "").strip():
            issues.append(f"{sequence_id}: landedResult is required")
        boundary_result = output.get("boundaryResult") or {}
        if not isinstance(boundary_result, dict):
            issues.append(f"{sequence_id}: boundaryResult must be an object")
            boundary_result = {}
        expected_entry = str((sequence.get("design") or {}).get("entryState") or "")
        expected_exit = str((sequence.get("design") or {}).get("exitState") or "")
        if boundary_result.get("entryState") != expected_entry:
            issues.append(
                f"{sequence_id}: boundaryResult.entryState does not match the director plan"
            )
        if boundary_result.get("exitState") != expected_exit:
            issues.append(
                f"{sequence_id}: boundaryResult.exitState does not match the director plan"
            )
        used_sources = output.get("usedSources") or []
        if not isinstance(used_sources, list):
            issues.append(f"{sequence_id}: usedSources must be an array")
            used_sources = []
        declared_sources = {
            item.get("path") for item in task.get("sourceContract") or [] if isinstance(item, dict)
        }
        for used_source in used_sources:
            if used_source not in declared_sources:
                issues.append(f"{sequence_id}: undeclared source used by worker: {used_source}")
        used_capabilities = output.get("usedCapabilities") or []
        if not isinstance(used_capabilities, list):
            issues.append(f"{sequence_id}: usedCapabilities must be an array")
            used_capabilities = []
        declared_capabilities = {
            item.get("techniqueId")
            for item in task.get("capabilityContract") or []
            if isinstance(item, dict)
        }
        for used_capability in used_capabilities:
            if used_capability not in declared_capabilities:
                issues.append(
                    f"{sequence_id}: undeclared capability used by worker: {used_capability}"
                )
        notes = output.get("notes") or []
        if not isinstance(notes, list):
            issues.append(f"{sequence_id}: notes must be an array")
            notes = []

        files = output.get("files") or {}
        if not isinstance(files, dict):
            issues.append(f"{sequence_id}: files must be an object")
            files = {}
        unknown_file_keys = set(files) - {"fragment", "styles", "timeline", "assets"}
        for key in sorted(unknown_file_keys):
            issues.append(f"{sequence_id}: unknown files key: {key}")
        intentional_hold = str(output.get("intentionalHold") or "").strip()
        authored_files = {key: value for key, value in files.items() if key != "assets" and value}
        if not authored_files and not intentional_hold:
            issues.append(f"{sequence_id}: provide authored files or explain intentionalHold")
        resolved_files: dict[str, str] = {}
        actual_local_references: set[str] = set()
        actual_external_references: set[str] = set()
        fragment_root_ids: set[str] = set()
        timeline_code: str | None = None
        for key, raw_path in authored_files.items():
            if not isinstance(raw_path, str):
                issues.append(f"{sequence_id}: files.{key} must be a relative path")
                continue
            try:
                target = safe_sequence_file(sequence_dir, raw_path)
            except ValueError as error:
                issues.append(f"{sequence_id}: {error}")
                continue
            if not target.is_file():
                issues.append(f"{sequence_id}: missing files.{key}: {raw_path}")
                continue
            resolved_files[key] = target.relative_to(episode).as_posix()
            if key == "fragment":
                fragment = target.read_text(encoding="utf-8")
                fragment_root_ids, root_tag = fragment_dom_scope(
                    fragment, f"{sequence_id}-root"
                )
                if root_tag not in {"div", "section"}:
                    issues.append(
                        f"{sequence_id}: scene root must use a stable div or section container"
                    )
                local_refs, external_refs = fragment_resource_references(fragment)
                actual_local_references.update(local_refs)
                actual_external_references.update(external_refs)
                if re.search(r"</?(?:html|head|body|script)\b", fragment, flags=re.I):
                    issues.append(f"{sequence_id}: scene fragment contains document or script tags")
                for dom_id in re.findall(r"\bid=[\"']([^\"']+)[\"']", fragment):
                    if not dom_id.startswith(f"{sequence_id}-"):
                        issues.append(
                            f"{sequence_id}: DOM id {dom_id!r} must start with {sequence_id}-"
                        )
                    owner = all_dom_ids.get(dom_id)
                    if owner and owner != sequence_id:
                        issues.append(
                            f"{sequence_id}: duplicate DOM id {dom_id!r}: {owner} and {sequence_id}"
                        )
                    all_dom_ids[dom_id] = sequence_id
                if re.search(
                    r"<(?:style|link|iframe|object|embed)\b|</main\b",
                    fragment,
                    flags=re.I,
                ):
                    issues.append(f"{sequence_id}: scene fragment contains forbidden active tags")
                if re.search(r"\son[a-z]+\s*=", fragment, flags=re.I):
                    issues.append(f"{sequence_id}: scene fragment contains inline event handlers")
            if key == "styles":
                css = target.read_text(encoding="utf-8")
                local_refs, external_refs = css_resource_references(css)
                actual_local_references.update(local_refs)
                actual_external_references.update(external_refs)
                issues.extend(
                    f"{sequence_id}: {issue}" for issue in sequence_css_issues(sequence_id, css)
                )
            if key == "timeline":
                timeline_code = target.read_text(encoding="utf-8")
                local_refs, external_refs = timeline_resource_references(timeline_code)
                actual_local_references.update(local_refs)
                actual_external_references.update(external_refs)
        if timeline_code is not None:
            issues.extend(
                f"{sequence_id}: {issue}"
                for issue in sequence_timeline_issues(
                    sequence_id,
                    timeline_code,
                    float(sequence.get("start") or 0),
                    float(sequence.get("end") or 0),
                    fragment_root_ids,
                )
            )
        resolved_assets: list[str] = []
        raw_assets = files.get("assets") or []
        if not isinstance(raw_assets, list):
            issues.append(f"{sequence_id}: files.assets must be an array")
            raw_assets = []
        for raw_path in raw_assets:
            if not isinstance(raw_path, str):
                issues.append(f"{sequence_id}: asset paths must be strings")
                continue
            try:
                target = safe_sequence_file(sequence_dir, raw_path)
            except ValueError as error:
                issues.append(f"{sequence_id}: {error}")
                continue
            if not target.is_file():
                issues.append(f"{sequence_id}: missing asset: {raw_path}")
                continue
            resolved_assets.append(target.relative_to(episode).as_posix())

        allowed_local_references = {
            str(path) for path in declared_sources if isinstance(path, str)
        } | set(resolved_assets)
        for reference in sorted(actual_external_references):
            issues.append(
                f"{sequence_id}: external or embedded resource is not allowed in worker output: "
                f"{reference[:160]}"
            )
        for reference in sorted(actual_local_references):
            if reference not in allowed_local_references:
                issues.append(
                    f"{sequence_id}: undeclared local asset referenced by worker: {reference}"
                )
            elif reference in declared_sources and reference not in used_sources:
                issues.append(
                    f"{sequence_id}: source is referenced but missing from usedSources: {reference}"
                )

        checked.append(
            {
                "id": sequence_id,
                "start": sequence.get("start"),
                "end": sequence.get("end"),
                "directory": sequence_dir.relative_to(episode).as_posix(),
                "taskFingerprint": task.get("taskFingerprint"),
                "files": resolved_files,
                "assets": resolved_assets,
                "landedResult": output.get("landedResult"),
                "boundaryResult": boundary_result,
                "usedSources": used_sources,
                "usedCapabilities": used_capabilities,
                "notes": notes,
                "artifactSha256": {
                    relative: sha256_file(episode / relative)
                    for relative in sorted([*resolved_files.values(), *resolved_assets])
                },
                "outputFingerprint": json_fingerprint(
                    {
                        "manifest": output,
                        "files": {
                            key: sha256_file(episode / relative)
                            for key, relative in sorted(resolved_files.items())
                        },
                        "assets": {
                            relative: sha256_file(episode / relative)
                            for relative in sorted(resolved_assets)
                        },
                    }
                ),
                "intentionalHold": intentional_hold or None,
            }
        )
    checked_by_id = {item["id"]: item for item in checked}
    for previous_plan, following_plan in zip(planned_sequences, planned_sequences[1:]):
        previous = checked_by_id.get(previous_plan.get("id"))
        following = checked_by_id.get(following_plan.get("id"))
        if not previous or not following:
            continue
        previous_exit = (previous.get("boundaryResult") or {}).get("exitState")
        following_entry = (following.get("boundaryResult") or {}).get("entryState")
        if previous_exit != following_entry:
            issues.append(
                f"{previous['id']} -> {following['id']}: worker boundary results do not connect"
            )
    return checked, issues


def assembly_plan_issues(episode: Path, manifest: dict[str, Any]) -> list[str]:
    paths = sequence_paths(episode, manifest)
    if not paths["assemblyPlan"].is_file():
        if paths["sequencePlan"].is_file():
            sequence_plan = load_json(paths["sequencePlan"])
            if isinstance(sequence_plan, dict) and sequence_plan.get("sequences"):
                return [
                    "assembly plan missing for non-empty V3 sequence plan; "
                    "run assemble-sequences"
                ]
        return []
    assembly = load_json(paths["assemblyPlan"])
    issues: list[str] = []
    if not isinstance(assembly, dict):
        return ["assembly plan must be an object"]
    if assembly.get("systemVersion") != 3:
        issues.append("assembly plan is not Editing System V3")
    if assembly.get("episodeId") != manifest.get("id"):
        issues.append("assembly plan episodeId mismatch")
    if not paths["creativeBrief"].is_file() or not paths["sequencePlan"].is_file():
        issues.append("assembly inputs are missing")
        return issues
    creative_brief = load_json(paths["creativeBrief"])
    sequence_plan = load_json(paths["sequencePlan"])
    if assembly.get("creativeBriefFingerprint") != json_fingerprint(creative_brief):
        issues.append("assembly plan is stale after creative brief changes")
    if assembly.get("sequencePlanFingerprint") != json_fingerprint(sequence_plan):
        issues.append("assembly plan is stale after sequence plan changes")
    if assembly.get("creativeBriefSha256") != sha256_file(paths["creativeBrief"]):
        issues.append("assembly plan is stale or predates creative brief file locking")
    if assembly.get("sequencePlanSha256") != sha256_file(paths["sequencePlan"]):
        issues.append("assembly plan is stale or predates sequence plan file locking")
    current_sequences, output_issues = validate_sequence_outputs(episode, manifest)
    issues.extend(output_issues)
    if assembly.get("sequences") != current_sequences:
        issues.append("assembly plan is stale after sequence output changes")
    return issues


def command_check_sequences(args: argparse.Namespace) -> int:
    episode, manifest, _ = load_episode(args.episode)
    paths = sequence_paths(episode, manifest)
    sequence_plan = load_json(paths["sequencePlan"])
    planned_sequences = (
        sequence_plan.get("sequences") or [] if isinstance(sequence_plan, dict) else []
    )
    total = len(planned_sequences) if isinstance(planned_sequences, list) else 0
    sequences, issues = validate_sequence_outputs(episode, manifest)
    planned_ids = {
        str(sequence.get("id"))
        for sequence in planned_sequences
        if isinstance(sequence, dict)
    }
    invalid_ids: set[str] = set()
    global_issues: list[str] = []
    for issue in issues:
        prefix = issue.split(":", 1)[0] if ":" in issue else ""
        if prefix in planned_ids:
            invalid_ids.add(prefix)
        else:
            global_issues.append(issue)
    report = {
        "ok": not issues,
        "systemVersion": 3,
        "episodeId": manifest["id"],
        "ready": 0
        if global_issues
        else sum(1 for sequence in sequences if sequence.get("id") not in invalid_ids),
        "total": total,
        "issues": issues,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if not issues else 1


def command_assemble_sequences(args: argparse.Namespace) -> int:
    episode, manifest, _ = load_episode(args.episode)
    runtime_issues = v3_runtime_issues(episode)
    if runtime_issues:
        raise RuntimeError(
            "episode runtime is not V3-ready; run upgrade-v3 first:\n- "
            + "\n- ".join(runtime_issues)
        )
    paths = sequence_paths(episode, manifest)
    sequences, issues = validate_sequence_outputs(episode, manifest)
    if issues:
        raise ValueError("sequence outputs are not ready:\n- " + "\n- ".join(issues))
    creative_brief = load_json(paths["creativeBrief"])
    sequence_plan = load_json(paths["sequencePlan"])
    assembly = {
        "schemaVersion": 1,
        "systemVersion": 3,
        "episodeId": manifest["id"],
        "creativeBriefFingerprint": json_fingerprint(creative_brief),
        "sequencePlanFingerprint": json_fingerprint(sequence_plan),
        "creativeBriefSha256": sha256_file(paths["creativeBrief"]),
        "sequencePlanSha256": sha256_file(paths["sequencePlan"]),
        "sequences": sequences,
    }
    write_json(paths["assemblyPlan"], assembly)
    print(json.dumps({"assemblyPlan": str(paths["assemblyPlan"]), **assembly}, ensure_ascii=False, indent=2))
    return 0


def package_has_script(episode: Path, name: str) -> bool:
    package_path = episode / "package.json"
    if not package_path.is_file():
        return False
    return name in load_json(package_path).get("scripts", {})


def _css_value_is_clear(value: str) -> bool:
    normalized = value.lower().replace("!important", "").strip()
    if normalized in {"none", "transparent", "0", "0px"}:
        return True
    compact = re.sub(r"\s+", "", normalized)
    return bool(
        re.fullmatch(r"rgba\([^,]+,[^,]+,[^,]+,0(?:\.0+)?\)", compact)
        or re.fullmatch(r"rgb\([^/]+/0(?:\.0+)?\)", compact)
    )


def caption_style_issues(episode: Path) -> list[str]:
    issues: list[str] = []
    snapshot_path = episode / "editorial-defaults.snapshot.json"
    defaults = load_json(snapshot_path) if snapshot_path.is_file() else load_json(DEFAULTS_PATH)
    captions = defaults.get("captions") or {}
    if captions.get("background") != "none":
        issues.append("caption contract requires background=none")
    if captions.get("strokeEnabled") is not False:
        issues.append("caption contract requires strokeEnabled=false")
    if captions.get("fontSource") != "system":
        issues.append("caption contract requires system fonts")
    if (captions.get("chinese") or {}).get("position") != "top":
        issues.append("Chinese body caption must be on top")
    if (captions.get("english") or {}).get("position") != "bottom":
        issues.append("English body caption must be below Chinese")

    css_path = episode / "styles.css"
    if not css_path.is_file():
        issues.append(f"missing caption stylesheet: {css_path}")
        return issues
    css = css_path.read_text(encoding="utf-8")
    watched_selectors = (".body-caption", ".caption-cn", ".caption-en", "#captions")
    for selector, declarations in re.findall(r"([^{}]+)\{([^{}]*)\}", css, flags=re.S):
        if not any(watched in selector for watched in watched_selectors):
            continue
        for property_name, raw_value in re.findall(r"([\w-]+)\s*:\s*([^;]+)", declarations):
            property_name = property_name.lower()
            if property_name in {"background", "background-color", "box-shadow", "border", "border-color"}:
                if not _css_value_is_clear(raw_value):
                    issues.append(
                        f"caption selector {selector.strip()!r} sets {property_name}={raw_value.strip()!r}"
                    )

    html_path = episode / "index.html"
    if html_path.is_file():
        html = html_path.read_text(encoding="utf-8")
        for tag in re.findall(r"<[^>]+class=[\"'][^\"']*(?:body-caption|caption-cn|caption-en)[^\"']*[\"'][^>]*>", html):
            inline_style = re.search(r"style=[\"']([^\"']+)[\"']", tag)
            if not inline_style:
                continue
            for property_name, raw_value in re.findall(r"([\w-]+)\s*:\s*([^;]+)", inline_style.group(1)):
                if property_name.lower() in {"background", "background-color", "box-shadow", "border"}:
                    if not _css_value_is_clear(raw_value):
                        issues.append(f"caption inline style sets {property_name}={raw_value.strip()!r}")
    return issues


def visual_style_issues(episode: Path) -> list[str]:
    """Reject the deprecated decorative side-rail motif."""
    issues: list[str] = []
    vertical_border_properties = {
        "border-left",
        "border-left-color",
        "border-left-style",
        "border-left-width",
        "border-right",
        "border-right-color",
        "border-right-style",
        "border-right-width",
    }
    ignored_parts = {"node_modules", "deliverables", "source", "assets", ".git", "work"}
    css_paths = [
        path
        for path in sorted(episode.rglob("*.css"))
        if path.is_file() and not ignored_parts.intersection(path.relative_to(episode).parts)
    ]

    def is_decorative(selector: str, property_name: str, raw_value: str, declarations: str) -> bool:
        if _css_value_is_clear(raw_value):
            return False
        semantic_selector = bool(
            re.search(r"(?:side[-_]?rail|vertical[-_]?rail|callout|accent[-_]?line)", selector, re.I)
        )
        width_match = re.search(r"(-?\d+(?:\.\d+)?)px", raw_value)
        if not width_match:
            side = "left" if "left" in property_name else "right"
            width_declaration = re.search(
                rf"border-{side}-width\s*:\s*(-?\d+(?:\.\d+)?)px",
                declarations,
                flags=re.I,
            )
            width_match = width_declaration
        if width_match:
            return float(width_match.group(1)) >= 3
        return semantic_selector

    for css_path in css_paths:
        css = css_path.read_text(encoding="utf-8")
        for selector, declarations in re.findall(r"([^{}]+)\{([^{}]*)\}", css, flags=re.S):
            for property_name, raw_value in re.findall(r"([\w-]+)\s*:\s*([^;]+)", declarations):
                if property_name.lower() in vertical_border_properties and is_decorative(
                    selector, property_name.lower(), raw_value, declarations
                ):
                    issues.append(
                        f"decorative vertical side rail is forbidden: "
                        f"{css_path.relative_to(episode)} {selector.strip()!r} sets "
                        f"{property_name}={raw_value.strip()!r}"
                    )

    html_paths = [
        path
        for path in sorted(episode.rglob("*.html"))
        if path.is_file() and not ignored_parts.intersection(path.relative_to(episode).parts)
    ]
    for html_path in html_paths:
        html = html_path.read_text(encoding="utf-8")
        for tag in re.findall(r"<[^>]+style=[\"'][^\"']+[\"'][^>]*>", html):
            inline_style = re.search(r"style=[\"']([^\"']+)[\"']", tag)
            if not inline_style:
                continue
            for property_name, raw_value in re.findall(r"([\w-]+)\s*:\s*([^;]+)", inline_style.group(1)):
                if property_name.lower() in vertical_border_properties and is_decorative(
                    tag, property_name.lower(), raw_value, inline_style.group(1)
                ):
                    issues.append(
                        f"decorative vertical side rail is forbidden in inline style: "
                        f"{html_path.relative_to(episode)} {property_name}={raw_value.strip()!r}"
                    )
    return issues


def command_style_check(args: argparse.Namespace) -> int:
    episode, manifest, _ = load_episode(args.episode)
    issues = (
        caption_style_issues(episode)
        + visual_style_issues(episode)
        + assembly_plan_issues(episode, manifest)
    )
    report = {"ok": not issues, "episode": str(episode), "issues": issues}
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if not issues else 1


def delivery_dimensions(manifest: dict[str, Any], defaults: dict[str, Any]) -> tuple[int, int, int]:
    overrides = manifest.get("deliveryOverrides", {})
    return (
        int(overrides.get("width") or defaults["delivery"]["width"]),
        int(overrides.get("height") or defaults["delivery"]["height"]),
        int(overrides.get("fps") or defaults["delivery"]["fps"]),
    )


def preview_dimensions(manifest: dict[str, Any], defaults: dict[str, Any]) -> tuple[int, int, int]:
    width, height, _ = delivery_dimensions(manifest, defaults)
    preview = defaults["preview"]
    scale = min(float(preview["width"]) / width, float(preview["height"]) / height, 1.0)
    preview_width = max(2, int(width * scale) // 2 * 2)
    preview_height = max(2, int(height * scale) // 2 * 2)
    return preview_width, preview_height, int(preview["fps"])


def command_render(args: argparse.Namespace) -> int:
    episode, manifest, defaults = load_episode(args.episode)
    if args.quality == "master" and not args.approved:
        raise RuntimeError("master render requires --approved after the continuous preview is approved")
    prebuild_issues = assembly_plan_issues(episode, manifest)
    if prebuild_issues:
        raise RuntimeError("assembly contract failed:\n- " + "\n- ".join(prebuild_issues))
    if package_has_script(episode, "build"):
        run(["npm", "run", "build"], cwd=episode)
    style_issues = (
        caption_style_issues(episode)
        + visual_style_issues(episode)
        + assembly_plan_issues(episode, manifest)
    )
    if style_issues:
        raise RuntimeError("style contract failed:\n- " + "\n- ".join(style_issues))
    run(["npx", "hyperframes", "check"], cwd=episode)
    preset = defaults["preview"] if args.quality == "preview" else defaults["master"]
    _, _, render_fps = delivery_dimensions(manifest, defaults)
    output_key = "preview" if args.quality == "preview" else "master"
    output = resolve_episode_path(episode, manifest["paths"][output_key])
    output.parent.mkdir(parents=True, exist_ok=True)
    quality = "draft" if args.quality == "preview" else "high"
    with tempfile.TemporaryDirectory(prefix="hyperframe-render-") as temporary:
        render_output = Path(temporary) / "source.mp4"
        command = [
            "npx",
            "hyperframes",
            "render",
            "--quality",
            quality,
            "--fps",
            str(render_fps),
            "--crf",
            str(preset["crf"]),
            "--no-best-effort",
            "--output",
            str(render_output),
        ]
        run(command, cwd=episode)
        if args.quality == "preview":
            width, height, preview_fps = preview_dimensions(manifest, defaults)
            output_fps = preview_fps
        else:
            width, height, output_fps = delivery_dimensions(manifest, defaults)
        run(
            [
                "ffmpeg",
                "-hide_banner",
                "-nostdin",
                "-y",
                "-i",
                str(render_output),
                "-vf",
                f"fps={output_fps},scale={width}:{height}:force_original_aspect_ratio=decrease,"
                f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:color=black,setsar=1,"
                f"format={defaults['master']['pixelFormat']},"
                f"setparams=color_primaries={defaults['master']['colorSpace']}:"
                f"color_trc={defaults['master']['colorSpace']}:"
                f"colorspace={defaults['master']['colorSpace']}",
                "-af",
                f"loudnorm=I={preset['targetIntegratedLoudnessLufs']}:"
                f"TP={preset['truePeakCeilingDbtp']}:LRA=7",
                "-c:v",
                preset["videoCodec"],
                "-preset",
                preset["preset"],
                "-crf",
                str(preset["crf"]),
                "-pix_fmt",
                defaults["master"]["pixelFormat"],
                "-colorspace",
                defaults["master"]["colorSpace"],
                "-color_primaries",
                defaults["master"]["colorSpace"],
                "-color_trc",
                defaults["master"]["colorSpace"],
                "-c:a",
                preset["audioCodec"],
                "-b:a",
                preset["audioBitrate"],
                "-ar",
                str(defaults["master"]["audioSampleRate"]),
                "-movflags",
                "+faststart",
                str(output),
            ]
        )
    print(output)
    return 0


def expected_episode_duration(episode: Path, manifest: dict[str, Any]) -> float | None:
    metadata_path = episode / "work" / "a-roll.json"
    if metadata_path.is_file():
        metadata = load_json(metadata_path)
        if isinstance(metadata, dict):
            duration = float(metadata.get("duration") or 0)
            if math.isfinite(duration) and duration > 0:
                return duration

    manifest_duration = float(manifest.get("duration") or 0)
    if math.isfinite(manifest_duration) and manifest_duration > 0:
        return manifest_duration

    a_roll_value = (manifest.get("paths") or {}).get("aRoll")
    if a_roll_value:
        a_roll_path = resolve_internal_episode_path(episode, a_roll_value, "aRoll")
        if a_roll_path.is_file():
            duration = float(probe_media(a_roll_path).get("duration") or 0)
            if math.isfinite(duration) and duration > 0:
                return duration

    sequence_plan_path = sequence_paths(episode, manifest)["sequencePlan"]
    if sequence_plan_path.is_file():
        sequence_plan = load_json(sequence_plan_path)
        if isinstance(sequence_plan, dict):
            ends = [
                float(sequence.get("end") or 0)
                for sequence in sequence_plan.get("sequences") or []
                if isinstance(sequence, dict)
            ]
            if ends and max(ends) > 0:
                return max(ends)
    return None


def command_verify(args: argparse.Namespace) -> int:
    episode, manifest, defaults = load_episode(args.episode)
    default_output = "preview" if args.quality == "preview" else "master"
    path = Path(args.file).expanduser().resolve() if args.file else resolve_episode_path(
        episode, manifest["paths"][default_output]
    )
    if not path.is_file() or path.stat().st_size == 0:
        raise FileNotFoundError(f"delivery missing or empty: {path}")
    details = probe_media(path)
    video = details.get("video") or {}
    if args.quality == "preview":
        expected_width, expected_height, expected_fps_value = preview_dimensions(manifest, defaults)
    else:
        expected_width, expected_height, expected_fps_value = delivery_dimensions(manifest, defaults)
    expected_fps = float(expected_fps_value)
    issues = []
    preset = defaults["preview"] if args.quality == "preview" else defaults["master"]
    if video.get("width") != expected_width or video.get("height") != expected_height:
        issues.append(f"resolution {video.get('width')}x{video.get('height')} != {expected_width}x{expected_height}")
    if not math.isclose(float(video.get("fps") or 0), expected_fps, rel_tol=0, abs_tol=0.02):
        issues.append(f"fps {video.get('fps')} != {expected_fps}")
    if not details.get("audio"):
        issues.append("audio stream missing")
    expected_video_codec = "h264" if preset.get("videoCodec") == "libx264" else preset.get("videoCodec")
    if video.get("codec") != expected_video_codec:
        issues.append(f"video codec {video.get('codec')} != {expected_video_codec}")
    if video.get("pixelFormat") != defaults["master"]["pixelFormat"]:
        issues.append(
            f"pixel format {video.get('pixelFormat')} != {defaults['master']['pixelFormat']}"
        )
    expected_color = defaults["master"]["colorSpace"]
    for field in ("colorSpace", "colorTransfer", "colorPrimaries"):
        if video.get(field) != expected_color:
            issues.append(f"{field} {video.get(field)} != {expected_color}")
    audio = details.get("audio") or {}
    if audio and audio.get("codec") != preset.get("audioCodec"):
        issues.append(f"audio codec {audio.get('codec')} != {preset.get('audioCodec')}")
    if audio and audio.get("sampleRate") != defaults["master"]["audioSampleRate"]:
        issues.append(
            f"audio sample rate {audio.get('sampleRate')} != "
            f"{defaults['master']['audioSampleRate']}"
        )
    if details.get("duration", 0) <= 0:
        issues.append("duration is not positive")
    expected_duration = expected_episode_duration(episode, manifest)
    duration_tolerance = max(0.25, 2 / expected_fps)
    if expected_duration is not None and not math.isclose(
        float(details.get("duration") or 0),
        expected_duration,
        rel_tol=0,
        abs_tol=duration_tolerance,
    ):
        issues.append(
            f"duration {details.get('duration')} != {expected_duration} "
            f"(+/- {duration_tolerance:.3f}s)"
        )
    for label, stream in (("video", video), ("audio", audio)):
        if not stream:
            continue
        measured_stream_duration = float(stream.get("duration") or 0)
        if measured_stream_duration <= 0:
            issues.append(f"{label} stream duration could not be measured")
            continue
        stream_target = expected_duration or float(details.get("duration") or 0)
        if stream_target > 0 and not math.isclose(
            measured_stream_duration,
            stream_target,
            rel_tol=0,
            abs_tol=duration_tolerance,
        ):
            issues.append(
                f"{label} stream duration {measured_stream_duration} != {stream_target} "
                f"(+/- {duration_tolerance:.3f}s)"
            )
    loudness = measure_loudness(
        path,
        float(preset["targetIntegratedLoudnessLufs"]),
        float(preset["truePeakCeilingDbtp"]),
    ) if audio else {"integratedLufs": None, "truePeakDbtp": None}
    integrated = loudness.get("integratedLufs")
    true_peak = loudness.get("truePeakDbtp")
    if integrated is None:
        issues.append("integrated loudness could not be measured")
    elif not math.isclose(
        float(integrated),
        float(preset["targetIntegratedLoudnessLufs"]),
        rel_tol=0,
        abs_tol=1.0,
    ):
        issues.append(
            f"integrated loudness {integrated} LUFS is outside target "
            f"{preset['targetIntegratedLoudnessLufs']} +/- 1.0"
        )
    if true_peak is None:
        issues.append("true peak could not be measured")
    elif float(true_peak) > float(preset["truePeakCeilingDbtp"]) + 0.2:
        issues.append(
            f"true peak {true_peak} dBTP exceeds {preset['truePeakCeilingDbtp']} dBTP ceiling"
        )
    report = {
        "ok": not issues,
        "file": str(path),
        "quality": args.quality,
        "media": details,
        "expectedDuration": expected_duration,
        "durationTolerance": duration_tolerance,
        "loudness": loudness,
        "issues": issues,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if not issues else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generic production kernel for 百万AI剪辑师")
    commands = parser.add_subparsers(dest="command", required=True)

    doctor = commands.add_parser("doctor", help="Check deterministic runtime dependencies")
    doctor.add_argument("--mode", choices=("runtime", "full-edit"), default="runtime")
    doctor.add_argument(
        "--verify-asr",
        action="store_true",
        help="Make a tiny live Doubao request; required to prove full-edit readiness",
    )
    doctor.set_defaults(handler=command_doctor)

    new = commands.add_parser("new", help="Create a generic episode project")
    new.add_argument("id")
    new.add_argument("--title", required=True)
    new.add_argument("--profile", default="general")
    new.add_argument("--root", help="Destination parent; defaults to repository episodes/")
    new.set_defaults(handler=command_new)

    inspect = commands.add_parser("inspect", help="Probe source media and write an inventory")
    inspect.add_argument("episode")
    inspect.set_defaults(handler=command_inspect)

    transcribe = commands.add_parser("transcribe", help="Batch-transcribe source media with Doubao ASR")
    transcribe.add_argument("episode")
    transcribe.add_argument("--workers", type=int, default=6)
    transcribe.add_argument("--force", action="store_true")
    transcribe.set_defaults(handler=command_transcribe)

    ar = commands.add_parser("build-aroll", help="Build A-roll from the AI-reviewed cut plan")
    ar.add_argument("episode")
    ar.set_defaults(handler=command_build_aroll)

    upgrade_v3 = commands.add_parser(
        "upgrade-v3",
        help="Back up and migrate an existing episode runtime to Editing System V3",
    )
    upgrade_v3.add_argument("episode")
    upgrade_v3.set_defaults(handler=command_upgrade_v3)

    pack_sequences = commands.add_parser(
        "pack-sequences",
        help="Materialize V3 semantic-sequence task packets from the director plan",
    )
    pack_sequences.add_argument("episode")
    pack_sequences.add_argument(
        "--force",
        action="store_true",
        help="Replace changed task packets after the director accepts invalidating worker output",
    )
    pack_sequences.set_defaults(handler=command_pack_sequences)

    check_sequences = commands.add_parser(
        "check-sequences",
        help="Validate isolated V3 worker outputs without touching the master timeline",
    )
    check_sequences.add_argument("episode")
    check_sequences.set_defaults(handler=command_check_sequences)

    assemble_sequences = commands.add_parser(
        "assemble-sequences",
        help="Create the V3 assembly plan after every sequence output resolves",
    )
    assemble_sequences.add_argument("episode")
    assemble_sequences.set_defaults(handler=command_assemble_sequences)

    style_check = commands.add_parser("style-check", help="Reject locked visual-style drift before rendering")
    style_check.add_argument("episode")
    style_check.set_defaults(handler=command_style_check)

    render = commands.add_parser("render", help="Check and render a continuous preview or master")
    render.add_argument("episode")
    render.add_argument("--quality", choices=("preview", "master"), required=True)
    render.add_argument("--approved", action="store_true")
    render.set_defaults(handler=command_render)

    verify = commands.add_parser("verify", help="Verify delivery resolution, fps, audio, and duration")
    verify.add_argument("episode")
    verify.add_argument("--file")
    verify.add_argument("--quality", choices=("preview", "master"), default="master")
    verify.set_defaults(handler=command_verify)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return int(args.handler(args))
    except Exception as error:  # noqa: BLE001 - CLI should surface concise production failures.
        print(f"ERROR {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
