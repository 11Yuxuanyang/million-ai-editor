from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
from pathlib import Path
import re
from typing import Any

from system.assets.inventory import _atomic_write_text, _write_ndjson


FULL_SHA256 = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True)
class CatalogContext:
    """Explicit evidence that may upgrade a conservative classification."""

    canonical_owners: dict[str, dict[str, str]] = field(default_factory=dict)
    duplicate_canonical_by_sha256: dict[str, dict[str, str]] = field(default_factory=dict)
    rebuild_evidence: dict[str, dict[str, Any]] = field(default_factory=dict)
    approved_reference_paths: frozenset[str] = frozenset()


def _path_segments(relative_path: str) -> set[str]:
    return {segment.lower() for segment in Path(relative_path).parts[:-1]}


def _is_output_path(relative_path: str) -> bool:
    return bool(_path_segments(relative_path) & {"preview", "previews", "render", "renders"})


def _is_valid_owner(owner: dict[str, Any] | None) -> bool:
    return bool(owner and owner.get("occurrenceId") and owner.get("relativePath"))


def _valid_rebuild_evidence(evidence: dict[str, Any] | None) -> bool:
    return bool(evidence and evidence.get("parentExists") is True and evidence.get("recipe"))


def classify_record(
    record: dict[str, Any], context: CatalogContext | None = None
) -> dict[str, Any]:
    """Return a proposal. Absence of evidence always resolves to preservation/review."""
    context = context or CatalogContext()
    occurrence_id = str(record["occurrenceId"])
    relative_path = str(record["relativePath"])
    sha256 = record.get("sha256")
    canonical_owner = context.canonical_owners.get(occurrence_id)
    rebuild_evidence = context.rebuild_evidence.get(occurrence_id)
    proposed_status = "unknown"
    reason_codes = ["unclassified-manual-review"]
    risk_flags = ["manual-review-required"]
    cleanup_eligible = False

    if relative_path in context.approved_reference_paths:
        proposed_status = "reference"
        reason_codes = ["approved-reference"]
        risk_flags = ["preserve-reference"]
    elif (
        isinstance(sha256, str)
        and FULL_SHA256.fullmatch(sha256)
        and _is_valid_owner(context.duplicate_canonical_by_sha256.get(sha256))
    ):
        proposed_status = "duplicate"
        canonical_owner = context.duplicate_canonical_by_sha256[sha256]
        reason_codes = ["full-sha256-duplicate"]
        risk_flags = ["approval-required"]
    elif _is_output_path(relative_path) and _is_valid_owner(canonical_owner):
        proposed_status = "superseded"
        reason_codes = ["explicit-canonical-owner"]
        risk_flags = ["approval-required"]
    elif record.get("entityType") == "pruned-directory" and record.get("reasonCode"):
        proposed_status = "rebuildable"
        reason_codes = [str(record["reasonCode"])]
        if _valid_rebuild_evidence(rebuild_evidence):
            risk_flags = ["approval-required"]
            cleanup_eligible = True
        else:
            risk_flags = ["rebuild-evidence-missing"]
    else:
        segments = _path_segments(relative_path)
        filename = Path(relative_path).name.lower()
        if "source" in segments:
            reason_codes = ["source-review-required"]
        elif segments & {"reference", "references", "research"}:
            reason_codes = ["reference-review-required"]
        elif segments & {"preview", "previews", "render", "renders"}:
            reason_codes = ["review-output"]
        elif any(token in filename for token in ("master", "formal", "final", "正式母版", "母版")):
            reason_codes = ["canonical-candidate-review-required"]

    return {
        "schemaVersion": 1,
        "occurrenceId": occurrence_id,
        "relativePath": relative_path,
        "proposedStatus": proposed_status,
        "decisionStatus": "proposed",
        "cleanupEligible": cleanup_eligible,
        "reasonCodes": reason_codes,
        "riskFlags": risk_flags,
        "canonicalOwner": canonical_owner if _is_valid_owner(canonical_owner) else None,
        "rebuildEvidence": rebuild_evidence,
    }


def _load_ndjson(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        raise FileNotFoundError(f"catalog inventory not found: {path}")
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def classify_catalog(catalog: Path, context: CatalogContext | None = None) -> dict[str, Any]:
    catalog = catalog.expanduser().resolve()
    records = _load_ndjson(catalog / "inventory.ndjson")
    dispositions = [classify_record(record, context) for record in records]
    dispositions.sort(key=lambda value: (value["relativePath"], value["occurrenceId"]))
    status_counts = Counter(value["proposedStatus"] for value in dispositions)
    summary = {
        "schemaVersion": 1,
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "occurrenceCount": len(dispositions),
        "cleanupEligibleCount": sum(bool(value["cleanupEligible"]) for value in dispositions),
        "decisionStatus": "proposed",
        "proposedStatusCounts": dict(sorted(status_counts.items())),
        "dispositions": "dispositions.ndjson",
    }
    _write_ndjson(catalog / "dispositions.ndjson", dispositions)
    _atomic_write_text(
        catalog / "classification-summary.json",
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    )
    return summary


def _project_group(relative_path: str) -> str:
    parts = Path(relative_path).parts
    if len(parts) >= 2 and parts[0] in {"videos", "episodes"}:
        return f"{parts[0]}/{parts[1]}"
    return parts[0] if parts else "."


def build_review_batch(catalog: Path, *, status: str, group_by: str) -> dict[str, Any]:
    if group_by not in {"project", "reason"}:
        raise ValueError("group-by must be project or reason")
    catalog = catalog.expanduser().resolve()
    dispositions = _load_ndjson(catalog / "dispositions.ndjson")
    matched = [value for value in dispositions if value.get("proposedStatus") == status]
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for value in matched:
        if group_by == "project":
            group = _project_group(str(value["relativePath"]))
        else:
            reasons = value.get("reasonCodes") or ["no-reason"]
            group = str(reasons[0])
        groups[group].append(value)
    return {
        "schemaVersion": 1,
        "status": status,
        "groupBy": group_by,
        "matchedCount": len(matched),
        "groups": [
            {"group": group, "count": len(values), "items": values}
            for group, values in sorted(groups.items())
        ],
    }
