from __future__ import annotations

from collections import Counter
import concurrent.futures
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import tempfile
from typing import Any, Iterable


VIDEO_EXTENSIONS = {".avi", ".mkv", ".mov", ".mp4", ".webm"}
AUDIO_EXTENSIONS = {".aac", ".flac", ".m4a", ".mp3", ".wav"}
IMAGE_EXTENSIONS = {".avif", ".gif", ".jpeg", ".jpg", ".png", ".webp"}
SUBTITLE_EXTENSIONS = {".srt", ".vtt"}
DATA_EXTENSIONS = {".csv", ".json", ".lottie", ".ndjson", ".tsv", ".yaml", ".yml"}
CODE_EXTENSIONS = {".css", ".html", ".js", ".mjs", ".py", ".sh", ".swift", ".ts"}
DOCUMENT_EXTENSIONS = {".md", ".pdf", ".txt"}

EXCLUDED_DIRECTORY_NAMES = {".git", ".worktrees"}
PRUNED_DIRECTORY_NAMES = {
    ".pytest_cache": "test-cache",
    ".thumbnails": "thumbnail-cache",
    ".transcode-cache": "transcode-cache",
    ".waveform-cache": "waveform-cache",
    "__hyperframes_video_frames": "generated-frames",
    "__pycache__": "python-bytecode-cache",
    "generated frames": "generated-frames",
    "generated-frames": "generated-frames",
    "generated_frames": "generated-frames",
    "node_modules": "dependency-directory",
}
PRUNED_DIRECTORY_PREFIXES = {
    ".venv": "python-environment",
    "work-": "render-work-directory",
}
QUICK_SAMPLE_BYTES = 1024 * 1024


@dataclass(frozen=True)
class InventorySummary:
    occurrence_count: int
    total_size_bytes: int
    pruned_directory_count: int
    error_count: int
    entity_type_counts: dict[str, int]
    kind_counts: dict[str, int]
    status_counts: dict[str, int]
    generated_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "schemaVersion": 1,
            "generatedAt": self.generated_at,
            "occurrenceCount": self.occurrence_count,
            "totalSizeBytes": self.total_size_bytes,
            "prunedDirectoryCount": self.pruned_directory_count,
            "errorCount": self.error_count,
            "entityTypeCounts": self.entity_type_counts,
            "kindCounts": self.kind_counts,
            "statusCounts": self.status_counts,
            "inventory": "inventory.ndjson",
            "errors": "errors.ndjson",
        }


@dataclass(frozen=True)
class _Candidate:
    path: Path
    entity_type: str
    reason_code: str | None = None


def infer_kind(path: Path) -> str:
    extension = path.suffix.lower()
    if extension in VIDEO_EXTENSIONS:
        return "video"
    if extension in AUDIO_EXTENSIONS:
        return "audio"
    if extension in IMAGE_EXTENSIONS:
        return "image"
    if extension in SUBTITLE_EXTENSIONS:
        return "subtitle"
    if extension in DATA_EXTENSIONS:
        return "data"
    if extension in CODE_EXTENSIONS:
        return "code"
    if extension in DOCUMENT_EXTENSIONS:
        return "document"
    return "other"


def _portable_relative(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def _occurrence_id(relative_path: str, entity_type: str) -> str:
    value = f"{entity_type}\0{relative_path}".encode("utf-8")
    return "occurrence." + hashlib.sha256(value).hexdigest()[:24]


def _quick_file_fingerprint(path: Path, size: int) -> str:
    digest = hashlib.sha256()
    digest.update(str(size).encode("ascii"))
    with path.open("rb") as source:
        digest.update(source.read(QUICK_SAMPLE_BYTES))
        if size > QUICK_SAMPLE_BYTES:
            source.seek(max(0, size - QUICK_SAMPLE_BYTES))
            digest.update(source.read(QUICK_SAMPLE_BYTES))
    return digest.hexdigest()


def _directory_facts(path: Path) -> tuple[int, int]:
    size = 0
    file_count = 0
    for current, directories, files in os.walk(path, topdown=True, followlinks=False):
        directories[:] = [
            name for name in directories if not (Path(current) / name).is_symlink()
        ]
        for name in files:
            child = Path(current) / name
            try:
                facts = child.lstat()
            except FileNotFoundError:
                continue
            size += facts.st_size
            file_count += 1
    return size, file_count


def _base_record(root: Path, path: Path, entity_type: str) -> dict[str, Any]:
    relative_path = _portable_relative(path, root)
    return {
        "schemaVersion": 1,
        "occurrenceId": _occurrence_id(relative_path, entity_type),
        "relativePath": relative_path,
        "entityType": entity_type,
        "kind": "directory" if entity_type == "pruned-directory" else infer_kind(path),
        "sha256": None,
    }


def _file_record(root: Path, path: Path) -> dict[str, Any]:
    facts = path.stat(follow_symlinks=False)
    record = _base_record(root, path, "file")
    record.update(
        {
            "status": "available",
            "sizeBytes": facts.st_size,
            "mtimeNs": facts.st_mtime_ns,
            "quickFingerprint": _quick_file_fingerprint(path, facts.st_size),
            "link": {
                "isSymlink": False,
                "targetExists": None,
                "targetScope": None,
                "targetPath": None,
            },
        }
    )
    return record


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _symlink_record(root: Path, path: Path) -> dict[str, Any]:
    facts = path.lstat()
    raw_target = os.readlink(path)
    target = Path(raw_target)
    if not target.is_absolute():
        target = path.parent / target
    resolved_target = target.resolve(strict=False)
    target_exists = path.exists()
    root_resolved = root.resolve()
    internal = _is_within(resolved_target, root_resolved)
    target_path = resolved_target.relative_to(root_resolved).as_posix() if internal else None
    relative_path = _portable_relative(path, root)
    quick_value = f"{relative_path}\0{raw_target}\0{facts.st_mtime_ns}".encode("utf-8")

    record = _base_record(root, path, "symlink")
    record.update(
        {
            "status": "available" if target_exists else "missing",
            "sizeBytes": 0,
            "mtimeNs": facts.st_mtime_ns,
            "quickFingerprint": hashlib.sha256(quick_value).hexdigest(),
            "link": {
                "isSymlink": True,
                "targetExists": target_exists,
                "targetScope": "internal" if internal else "external",
                "targetPath": target_path,
            },
        }
    )
    return record


def _pruned_directory_record(root: Path, path: Path, reason_code: str) -> dict[str, Any]:
    facts = path.stat(follow_symlinks=False)
    size, file_count = _directory_facts(path)
    relative_path = _portable_relative(path, root)
    quick_value = f"{relative_path}\0{size}\0{file_count}\0{facts.st_mtime_ns}".encode("utf-8")
    record = _base_record(root, path, "pruned-directory")
    record.update(
        {
            "status": "pruned",
            "sizeBytes": size,
            "fileCount": file_count,
            "mtimeNs": facts.st_mtime_ns,
            "quickFingerprint": hashlib.sha256(quick_value).hexdigest(),
            "reasonCode": reason_code,
            "link": {
                "isSymlink": False,
                "targetExists": None,
                "targetScope": None,
                "targetPath": None,
            },
        }
    )
    return record


def _prune_reason(directory_name: str) -> str | None:
    if directory_name in PRUNED_DIRECTORY_NAMES:
        return PRUNED_DIRECTORY_NAMES[directory_name]
    for prefix, reason in PRUNED_DIRECTORY_PREFIXES.items():
        if directory_name.startswith(prefix):
            return reason
    return None


def _collect_candidates(root: Path, output: Path) -> list[_Candidate]:
    candidates: list[_Candidate] = []
    output_resolved = output.resolve(strict=False)
    for current_value, directories, files in os.walk(root, topdown=True, followlinks=False):
        current = Path(current_value)
        kept_directories: list[str] = []
        for name in sorted(directories):
            path = current / name
            if path.is_symlink():
                candidates.append(_Candidate(path, "symlink"))
                continue
            resolved = path.resolve(strict=False)
            if (
                name in EXCLUDED_DIRECTORY_NAMES
                or resolved == output_resolved
                or _is_within(resolved, output_resolved)
            ):
                continue
            reason = _prune_reason(name)
            if reason:
                candidates.append(_Candidate(path, "pruned-directory", reason))
                continue
            kept_directories.append(name)
        directories[:] = kept_directories

        for name in sorted(files):
            path = current / name
            if path.is_symlink():
                candidates.append(_Candidate(path, "symlink"))
            else:
                candidates.append(_Candidate(path, "file"))
    return candidates


def _record_candidate(root: Path, candidate: _Candidate) -> dict[str, Any]:
    if candidate.entity_type == "file":
        return _file_record(root, candidate.path)
    if candidate.entity_type == "symlink":
        return _symlink_record(root, candidate.path)
    if candidate.entity_type == "pruned-directory" and candidate.reason_code:
        return _pruned_directory_record(root, candidate.path, candidate.reason_code)
    raise ValueError(f"unsupported candidate type: {candidate.entity_type}")


def _atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as destination:
            destination.write(content)
            destination.flush()
            os.fsync(destination.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _write_ndjson(path: Path, values: Iterable[dict[str, Any]]) -> None:
    content = "".join(json.dumps(value, ensure_ascii=False, sort_keys=True) + "\n" for value in values)
    _atomic_write_text(path, content)


def scan_workspace(root: Path, output: Path, *, workers: int = 8) -> InventorySummary:
    """Write a portable NDJSON inventory without mutating scanned files."""
    root = root.expanduser().resolve()
    output = output.expanduser().resolve()
    if not root.is_dir():
        raise FileNotFoundError(f"workspace root not found: {root}")
    if output == root:
        raise ValueError("catalog output must not equal workspace root")
    if workers < 1:
        raise ValueError("workers must be at least 1")

    candidates = _collect_candidates(root, output)
    records: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        future_to_candidate = {
            executor.submit(_record_candidate, root, candidate): candidate for candidate in candidates
        }
        for future in concurrent.futures.as_completed(future_to_candidate):
            candidate = future_to_candidate[future]
            try:
                records.append(future.result())
            except (FileNotFoundError, PermissionError, OSError) as error:
                errors.append(
                    {
                        "schemaVersion": 1,
                        "relativePath": _portable_relative(candidate.path, root),
                        "errorType": type(error).__name__,
                    }
                )

    records.sort(key=lambda value: (value["relativePath"], value["entityType"]))
    errors.sort(key=lambda value: value["relativePath"])
    entity_type_counts = Counter(record["entityType"] for record in records)
    kind_counts = Counter(record["kind"] for record in records)
    status_counts = Counter(record["status"] for record in records)
    generated_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    summary = InventorySummary(
        occurrence_count=len(records),
        total_size_bytes=sum(int(record["sizeBytes"]) for record in records),
        pruned_directory_count=entity_type_counts.get("pruned-directory", 0),
        error_count=len(errors),
        entity_type_counts=dict(sorted(entity_type_counts.items())),
        kind_counts=dict(sorted(kind_counts.items())),
        status_counts=dict(sorted(status_counts.items())),
        generated_at=generated_at,
    )

    output.mkdir(parents=True, exist_ok=True)
    _write_ndjson(output / "inventory.ndjson", records)
    _write_ndjson(output / "errors.ndjson", errors)
    _atomic_write_text(
        output / "summary.json",
        json.dumps(summary.to_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    )
    return summary


def load_summary(catalog: Path) -> dict[str, Any]:
    path = catalog.expanduser().resolve() / "summary.json"
    if not path.is_file():
        raise FileNotFoundError(f"catalog summary not found: {path}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if value.get("schemaVersion") != 1:
        raise ValueError("unsupported catalog schemaVersion")
    return value
