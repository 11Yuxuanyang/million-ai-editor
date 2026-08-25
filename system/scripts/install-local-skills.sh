#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd -P)"
TARGET="${CODEX_HOME:-$HOME/.codex}/skills"
MODE="${1:-install}"

if [[ "$MODE" != "install" && "$MODE" != "--check" ]]; then
  printf 'usage: %s [--check]\n' "$0" >&2
  exit 2
fi

mkdir -p "$TARGET"

skills=(
  hyperframe-video-editor
  hyperframe-sequence-worker
  auto-cover-imagegen
  hyperframe-cinematic-templates
  hyperframe-editorial-explainer
)

status=0
for skill in "${skills[@]}"; do
  source_path="$ROOT/skills/$skill"
  target_path="$TARGET/$skill"

  if [[ ! -d "$source_path" ]]; then
    printf 'missing: %s\n' "$source_path" >&2
    exit 1
  fi
  source_real="$(realpath "$source_path")"

  if [[ -L "$target_path" ]] && [[ "$(realpath "$target_path")" == "$source_real" ]]; then
    printf 'ready: %s\n' "$skill"
    continue
  fi

  if [[ "$MODE" == "--check" ]]; then
    printf 'mismatch: %s must resolve to %s\n' "$target_path" "$source_real" >&2
    status=1
    continue
  fi

  if [[ -e "$target_path" || -L "$target_path" ]]; then
    timestamp="$(date +%Y%m%d-%H%M%S)"
    backup_root="${CODEX_HOME:-$HOME/.codex}/skill-backups/$timestamp"
    mkdir -p "$backup_root"
    mv "$target_path" "$backup_root/$skill"
    printf 'backed up: %s -> %s\n' "$target_path" "$backup_root/$skill"
  fi

  ln -s "$source_real" "$target_path"
  printf 'linked: %s -> %s\n' "$skill" "$source_real"
done

exit "$status"
