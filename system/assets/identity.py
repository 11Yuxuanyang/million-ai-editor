from __future__ import annotations

from collections import defaultdict
import concurrent.futures
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
from typing import Any, Iterable

from system.assets.inventory import (
    _atomic_write_text,
    _quick_file_fingerprint,
    _write_ndjson,
)


FULL_SHA256 = re.compile(r"^[0-9a-f]{64}$")
HASH_CHUNK_BYTES = 4 * 1024 * 1024


def _load_ndjson(path: Path, *, required: bool = True) -> list[dict[str, Any]]:
    if not path.is_file():
        if required:
            raise FileNotFoundError(f"catalog data not found: {path}")
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def _full_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(HASH_CHUNK_BYTES):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_source_path(root: Path, relative_path: str) -> Path:
    relative = Path(relative_path)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError(f"inventory path is not portable: {relative_path}")
    candidate = root / relative
    try:
        candidate.resolve(strict=False).relative_to(root)
    except ValueError as error:
        raise ValueError(f"inventory path leaves workspace root: {relative_path}") from error
    return candidate


def _candidate_records(records: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    by_size: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        if record.get("entityType") != "file" or record.get("status") != "available":
            continue
        size = record.get("sizeBytes")
        if isinstance(size, int):
            by_size[size].append(record)
    candidates = [record for values in by_size.values() if len(values) > 1 for record in values]
    return sorted(candidates, key=lambda value: (value["relativePath"], value["occurrenceId"]))


def _existing_hashes(catalog: Path) -> dict[str, dict[str, Any]]:
    return {
        str(value["occurrenceId"]): value
        for value in _load_ndjson(catalog / "hashes.ndjson", required=False)
        if value.get("occurrenceId")
    }


def _hash_candidate(
    root: Path, record: dict[str, Any], existing: dict[str, Any] | None
) -> dict[str, Any]:
    relative_path = str(record["relativePath"])
    path = _safe_source_path(root, relative_path)
    facts = path.stat(follow_symlinks=False)
    expected_size = int(record["sizeBytes"])
    expected_mtime = int(record["mtimeNs"])
    if facts.st_size != expected_size or facts.st_mtime_ns != expected_mtime:
        raise ValueError(f"inventory is stale for {relative_path}: size or mtime changed")
    quick_fingerprint = _quick_file_fingerprint(path, facts.st_size)
    if quick_fingerprint != record.get("quickFingerprint"):
        raise ValueError(f"inventory is stale for {relative_path}: quick fingerprint changed")

    reusable = bool(
        existing
        and existing.get("sizeBytes") == facts.st_size
        and existing.get("mtimeNs") == facts.st_mtime_ns
        and existing.get("quickFingerprint") == quick_fingerprint
        and isinstance(existing.get("sha256"), str)
        and FULL_SHA256.fullmatch(str(existing["sha256"]))
    )
    return {
        "schemaVersion": 1,
        "occurrenceId": record["occurrenceId"],
        "relativePath": relative_path,
        "sizeBytes": facts.st_size,
        "mtimeNs": facts.st_mtime_ns,
        "quickFingerprint": quick_fingerprint,
        "sha256": existing["sha256"] if reusable and existing else _full_sha256(path),
        "reused": reusable,
    }


def group_full_hash_records(records: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    by_sha256: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        sha256 = record.get("sha256")
        if isinstance(sha256, str) and FULL_SHA256.fullmatch(sha256):
            by_sha256[sha256].append(record)

    groups: list[dict[str, Any]] = []
    for sha256, members in sorted(by_sha256.items()):
        if len(members) < 2:
            continue
        ordered = sorted(members, key=lambda value: (value["relativePath"], value["occurrenceId"]))
        groups.append(
            {
                "schemaVersion": 1,
                "duplicateGroupId": "duplicate." + hashlib.sha256(sha256.encode("ascii")).hexdigest()[:24],
                "sha256": sha256,
                "sizeBytes": ordered[0]["sizeBytes"],
                "memberCount": len(ordered),
                "occurrenceIds": [value["occurrenceId"] for value in ordered],
                "relativePaths": [value["relativePath"] for value in ordered],
                "canonicalOwner": None,
                "decisionStatus": "unresolved",
                "cleanupEligible": False,
            }
        )
    return groups


def build_identity_report(root: Path, catalog: Path, *, workers: int = 8) -> dict[str, Any]:
    root = root.expanduser().resolve()
    catalog = catalog.expanduser().resolve()
    if not root.is_dir():
        raise FileNotFoundError(f"workspace root not found: {root}")
    if workers < 1:
        raise ValueError("workers must be at least 1")

    inventory = _load_ndjson(catalog / "inventory.ndjson")
    candidates = _candidate_records(inventory)
    previous = _existing_hashes(catalog)
    hashes: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(
                _hash_candidate,
                root,
                record,
                previous.get(str(record["occurrenceId"])),
            ): record
            for record in candidates
        }
        for future in concurrent.futures.as_completed(futures):
            record = futures[future]
            try:
                hashes.append(future.result())
            except (OSError, ValueError) as error:
                errors.append(
                    {
                        "schemaVersion": 1,
                        "occurrenceId": record["occurrenceId"],
                        "relativePath": record["relativePath"],
                        "errorType": type(error).__name__,
                        "message": str(error),
                    }
                )

    hashes.sort(key=lambda value: (value["relativePath"], value["occurrenceId"]))
    errors.sort(key=lambda value: (value["relativePath"], value["occurrenceId"]))
    groups = group_full_hash_records(hashes)
    summary = {
        "schemaVersion": 1,
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "scope": "duplicate-candidates",
        "candidateOccurrenceCount": len(candidates),
        "hashedOccurrenceCount": len(hashes),
        "reusedHashCount": sum(bool(value["reused"]) for value in hashes),
        "hashErrorCount": len(errors),
        "duplicateGroupCount": len(groups),
        "duplicateOccurrenceCount": sum(value["memberCount"] for value in groups),
        "duplicateBytesIncludingAllCopies": sum(
            int(value["sizeBytes"]) * int(value["memberCount"]) for value in groups
        ),
        "canonicalOwnerStatus": "unresolved",
        "cleanupEligibleCount": 0,
        "hashes": "hashes.ndjson",
        "duplicateGroups": "duplicate-groups.ndjson",
        "errors": "identity-errors.ndjson",
    }
    _write_ndjson(catalog / "hashes.ndjson", hashes)
    _write_ndjson(catalog / "duplicate-groups.ndjson", groups)
    _write_ndjson(catalog / "identity-errors.ndjson", errors)
    _atomic_write_text(
        catalog / "identity-summary.json",
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    )
    return summary


def write_link_reports(catalog: Path) -> dict[str, Any]:
    catalog = catalog.expanduser().resolve()
    inventory = _load_ndjson(catalog / "inventory.ndjson")
    broken: list[dict[str, Any]] = []
    external: list[dict[str, Any]] = []
    for record in inventory:
        if record.get("entityType") != "symlink":
            continue
        link = record.get("link") or {}
        base = {
            "schemaVersion": 1,
            "occurrenceId": record["occurrenceId"],
            "relativePath": record["relativePath"],
        }
        if record.get("status") == "missing" or link.get("targetExists") is False:
            broken.append({**base, "requiresRelink": True})
        if link.get("targetScope") == "external":
            external.append({**base, "targetExists": link.get("targetExists"), "migrationEvidence": False})

    broken.sort(key=lambda value: (value["relativePath"], value["occurrenceId"]))
    external.sort(key=lambda value: (value["relativePath"], value["occurrenceId"]))
    _write_ndjson(catalog / "broken-links.ndjson", broken)
    _write_ndjson(catalog / "external-links.ndjson", external)
    summary = {
        "schemaVersion": 1,
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "brokenLinkCount": len(broken),
        "externalLinkCount": len(external),
        "externalLinksAreMigrationEvidence": False,
        "brokenLinks": "broken-links.ndjson",
        "externalLinks": "external-links.ndjson",
    }
    _atomic_write_text(
        catalog / "link-summary.json",
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    )
    return summary
