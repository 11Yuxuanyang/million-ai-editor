#!/usr/bin/env python3
"""Validate resolvable structure and stable production facts without freezing creativity."""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = Path(__file__).resolve().parents[3]
CONFIG = PROJECT_ROOT / "config/editorial-defaults.json"


def tracked_files() -> set[str]:
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=PROJECT_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return {line for line in result.stdout.splitlines() if line}


def asset_paths(asset: dict) -> list[str]:
    values: list[str] = []
    for key in (
        "file",
        "audio",
        "recipe",
        "preview",
        "implementation",
        "configuration",
        "reference",
        "review",
    ):
        value = asset.get(key)
        if isinstance(value, str):
            values.append(value)
    values.extend(value for value in asset.get("files", []) if isinstance(value, str))
    return values


def markdown_files() -> list[Path]:
    return [SKILL_ROOT / "SKILL.md", *sorted((SKILL_ROOT / "references").glob("*.md"))]


def check_local_links(files: list[Path], errors: list[str]) -> None:
    link_pattern = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
    for path in files:
        text = path.read_text(encoding="utf-8")
        for target in link_pattern.findall(text):
            if target.startswith(("http://", "https://", "#")):
                continue
            local_target = target.split("#", 1)[0]
            if not local_target:
                continue
            if not (path.parent / local_target).resolve().exists():
                errors.append(f"broken local link in {path.name}: {target}")


def main() -> int:
    errors: list[str] = []
    skill_path = SKILL_ROOT / "SKILL.md"
    skill_text = skill_path.read_text(encoding="utf-8")
    files = markdown_files()

    frontmatter = re.match(r"^---\n(.*?)\n---\n", skill_text, re.DOTALL)
    if not frontmatter:
        errors.append("SKILL.md has no valid frontmatter block")
    else:
        meta = frontmatter.group(1)
        if "name: hyperframe-video-editor" not in meta:
            errors.append("frontmatter name is missing or changed")
        if not re.search(r"^description:\s+\S", meta, re.MULTILINE):
            errors.append("frontmatter description is missing")

    required_resources = (
        "references/production-invariants.md",
        "references/production-presets.md",
        "references/aesthetic-preferences.md",
        "references/color-direction.md",
        "references/capability-index.md",
        "references/creative-options-catalog.md",
        "references/motion-storyboard-template.md",
        "references/parallel-sequence-workflow.md",
        "references/delivery-and-qa.md",
        "references/growth-and-writeback.md",
        "skills/use-film-burn-shutter-transition/SKILL.md",
    )
    for relative in required_resources:
        if not (SKILL_ROOT / relative).is_file():
            errors.append(f"missing resource: {relative}")

    check_local_links(files, errors)

    catalog_text = (SKILL_ROOT / "references/creative-options-catalog.md").read_text(
        encoding="utf-8"
    )
    local_names = re.findall(r"\| \*\*([^*]+)\*\*", catalog_text)
    if len(local_names) != len(set(local_names)):
        errors.append("creative catalog contains duplicate local option names")

    shot_names: list[str] = []
    for path in sorted((SKILL_ROOT / "references").glob("shot-design-*.md")):
        if path.name == "shot-design-source-and-license.md":
            continue
        shot_names.extend(re.findall(r"^\| \[`([^`]+)`\]", path.read_text(encoding="utf-8"), re.MULTILINE))
    if len(shot_names) != len(set(shot_names)):
        errors.append("external shot references contain duplicate names")

    if re.search(r"实现入口：[^\n]*videos/[^\n]*/assets/", catalog_text):
        errors.append("shared catalog still depends on an episode-local implementation path")
    if not (PROJECT_ROOT / "library/techniques/transition-native/contour-flow.js").is_file():
        errors.append("promoted contour implementation is missing")
    if not (PROJECT_ROOT / "library/techniques/transition-native/dot-grid-blackout.js").is_file():
        errors.append("promoted point-field implementation is missing")
    if not (PROJECT_ROOT / "library/techniques/transition-native/contour-flow.config.json").is_file():
        errors.append("promoted contour configuration is missing")
    if not (PROJECT_ROOT / "library/techniques/transition-native/dot-grid-blackout.config.json").is_file():
        errors.append("promoted point-field configuration is missing")

    registry = json.loads(
        (PROJECT_ROOT / "library/techniques/registry.json").read_text(encoding="utf-8")
    )
    techniques = registry.get("techniques", [])
    registered_ids = {item.get("id") for item in techniques}
    if len(registered_ids) != len(techniques):
        errors.append("technique registry contains duplicate or missing ids")

    asset_registry = json.loads(
        (PROJECT_ROOT / "references/asset-library/registry.json").read_text(
            encoding="utf-8"
        )
    )
    if Path(asset_registry.get("root", "")).is_absolute():
        errors.append("asset registry root must be repository-relative")
    assets = asset_registry.get("assets", [])
    asset_ids = {item.get("id") for item in assets}
    if len(asset_ids) != len(assets):
        errors.append("asset registry contains duplicate or missing ids")

    tracked = tracked_files()
    for asset in assets:
        for raw_path in asset_paths(asset):
            if raw_path.startswith(("http://", "https://")):
                continue
            relative = raw_path.split("#", 1)[0]
            if relative.startswith("videos/"):
                errors.append(
                    f"asset {asset.get('id')} depends on episode-local videos path: {relative}"
                )
                continue
            if not (PROJECT_ROOT / relative).is_file():
                errors.append(f"asset {asset.get('id')} path is missing: {relative}")
            elif relative not in tracked:
                errors.append(f"asset {asset.get('id')} path is not git-tracked: {relative}")

    for technique in techniques:
        for asset_id in technique.get("assetRefs", []):
            if asset_id not in asset_ids:
                errors.append(
                    f"technique {technique.get('id')} references unknown asset: {asset_id}"
                )
    required_capabilities = {
        "technique.evidence.cue-locked-handoff",
        "technique.evidence.fullframe-to-pip-handoff",
        "technique.generated.vox-cutout-motion",
        "technique.camera.long-tail-scale-hold",
        "technique.display.layered-subject-occlusion",
        "technique.opening.counterclaim-subject-reveal",
        "technique.transition.contour-flow-bridge",
        "technique.transition.dynamic-line-dot-blackout",
        "technique.transition.pixel-resolve",
        "technique.system.scatter-index-retrieve",
    }
    for capability_id in sorted(required_capabilities - registered_ids):
        errors.append(f"reusable capability is not registered: {capability_id}")

    taste = json.loads(
        (PROJECT_ROOT / "library/taste/current.json").read_text(encoding="utf-8")
    )
    if taste.get("sources", {}).get("capabilityIndex") != (
        "skills/hyperframe-video-editor/references/capability-index.md"
    ):
        errors.append("active taste does not route through the capability index")
    if taste.get("sources", {}).get("assets") != "references/asset-library/registry.json":
        errors.append("active taste does not route through the asset registry")
    if taste.get("sources", {}).get("references") != "library/references":
        errors.append("active taste does not route through approved reference cards")

    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    required_config_paths = (
        ("editingSystem", "version"),
        ("delivery", "width"),
        ("delivery", "height"),
        ("delivery", "fps"),
        ("sourceRetime", "rate"),
        ("roughCut", "parallelizePerSource"),
        ("transcription", "preferredEngine"),
        ("captions", "chinese"),
        ("captions", "english"),
        ("rhythm", "maxUnchangedSecondsExclusive"),
        ("preview", "targetIntegratedLoudnessLufs"),
        ("master", "targetIntegratedLoudnessLufs"),
        ("covers", "ratios"),
    )
    for first, second in required_config_paths:
        if first not in config or second not in config[first]:
            errors.append(f"config missing {first}.{second}")

    if config.get("sourceRetime", {}).get("rate") != 1.1:
        errors.append("configured source retime is no longer 1.1x")
    if config.get("editingSystem", {}).get("version") != 3:
        errors.append("editing system version is not V3")
    if config.get("preview", {}).get("targetIntegratedLoudnessLufs") != config.get(
        "master", {}
    ).get("targetIntegratedLoudnessLufs"):
        errors.append("preview and master loudness targets differ")

    cover_sizes = {
        (item.get("name"), item.get("width"), item.get("height"))
        for item in config.get("covers", {}).get("ratios", [])
    }
    if not {("4x3", 1440, 1080), ("3x4", 1080, 1440)}.issubset(cover_sizes):
        errors.append("default 4:3 and 3:4 cover specifications are incomplete")

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    print(
        "OK: frontmatter, progressive references, technique-to-asset links, portable assets, "
        f"{len(local_names)} local options, {len(shot_names)} optional external references, "
        "production config, and cover handoff resolve"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
