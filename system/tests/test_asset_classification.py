from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
ASSETCTL = ROOT / "system/scripts/assetctl.py"


def _record(
    relative_path: str,
    *,
    entity_type: str = "file",
    status: str = "available",
    reason_code: str | None = None,
    sha256: str | None = None,
) -> dict[str, object]:
    record: dict[str, object] = {
        "schemaVersion": 1,
        "occurrenceId": "occurrence." + relative_path.replace("/", "."),
        "relativePath": relative_path,
        "entityType": entity_type,
        "kind": "directory" if entity_type == "pruned-directory" else "video",
        "status": status,
        "sizeBytes": 10,
        "mtimeNs": 1,
        "quickFingerprint": "quick-only",
        "sha256": sha256,
        "link": {
            "isSymlink": False,
            "targetExists": None,
            "targetScope": None,
            "targetPath": None,
        },
    }
    if reason_code:
        record["reasonCode"] = reason_code
    return record


def _write_catalog(path: Path, records: list[dict[str, object]]) -> None:
    path.mkdir(parents=True)
    content = "".join(json.dumps(record, ensure_ascii=False) + "\n" for record in records)
    (path / "inventory.ndjson").write_text(content, encoding="utf-8")


def test_unknown_source_is_never_cleanup_eligible() -> None:
    from system.assets.classification import CatalogContext, classify_record

    disposition = classify_record(_record("videos/demo/source/original.mov"), CatalogContext())

    assert disposition["proposedStatus"] == "unknown"
    assert disposition["decisionStatus"] == "proposed"
    assert disposition["cleanupEligible"] is False
    assert disposition["canonicalOwner"] is None
    assert "source-review-required" in disposition["reasonCodes"]
    assert "manual-review-required" in disposition["riskFlags"]


def test_pruned_cache_needs_existing_parent_and_recipe_before_cleanup() -> None:
    from system.assets.classification import CatalogContext, classify_record

    record = _record(
        "videos/demo/.transcode-cache",
        entity_type="pruned-directory",
        status="pruned",
        reason_code="transcode-cache",
    )
    without_evidence = classify_record(record, CatalogContext())
    with_evidence = classify_record(
        record,
        CatalogContext(
            rebuild_evidence={
                str(record["occurrenceId"]): {
                    "parentExists": True,
                    "recipe": "editctl proxy videos/demo/source/original.mov",
                }
            }
        ),
    )

    assert without_evidence["proposedStatus"] == "rebuildable"
    assert without_evidence["cleanupEligible"] is False
    assert "rebuild-evidence-missing" in without_evidence["riskFlags"]
    assert with_evidence["proposedStatus"] == "rebuildable"
    assert with_evidence["cleanupEligible"] is True
    assert with_evidence["rebuildEvidence"]["parentExists"] is True


def test_superseded_render_requires_an_explicit_canonical_owner() -> None:
    from system.assets.classification import CatalogContext, classify_record

    record = _record("videos/demo/renders/cut-v1.mp4")
    without_owner = classify_record(record, CatalogContext())
    with_owner = classify_record(
        record,
        CatalogContext(
            canonical_owners={
                str(record["occurrenceId"]): {
                    "occurrenceId": "occurrence.videos.demo.deliverables.master.mp4",
                    "relativePath": "videos/demo/deliverables/master.mp4",
                }
            }
        ),
    )

    assert without_owner["proposedStatus"] == "unknown"
    assert without_owner["cleanupEligible"] is False
    assert with_owner["proposedStatus"] == "superseded"
    assert with_owner["cleanupEligible"] is False
    assert with_owner["canonicalOwner"]["relativePath"].endswith("master.mp4")


def test_duplicate_requires_full_sha256_and_named_canonical_occurrence() -> None:
    from system.assets.classification import CatalogContext, classify_record

    sha256 = "a" * 64
    no_sha = _record("videos/demo/source/copy.mov")
    with_sha = _record("videos/demo/source/copy.mov", sha256=sha256)
    context = CatalogContext(
        duplicate_canonical_by_sha256={
            sha256: {
                "occurrenceId": "occurrence.canonical",
                "relativePath": "videos/demo/source/original.mov",
            }
        }
    )

    assert classify_record(no_sha, context)["proposedStatus"] == "unknown"
    duplicate = classify_record(with_sha, context)
    assert duplicate["proposedStatus"] == "duplicate"
    assert duplicate["cleanupEligible"] is False
    assert duplicate["canonicalOwner"]["occurrenceId"] == "occurrence.canonical"


def test_approved_reference_is_preserved_as_reference() -> None:
    from system.assets.classification import CatalogContext, classify_record

    record = _record("references/cases/approved-opening.mp4")
    disposition = classify_record(
        record,
        CatalogContext(approved_reference_paths=frozenset({str(record["relativePath"])})),
    )

    assert disposition["proposedStatus"] == "reference"
    assert disposition["cleanupEligible"] is False
    assert disposition["reasonCodes"] == ["approved-reference"]


def test_assetctl_classify_and_review_batch_are_read_only(tmp_path: Path) -> None:
    catalog = tmp_path / "catalog"
    _write_catalog(
        catalog,
        [
            _record("videos/demo/source/original.mov"),
            _record(
                "videos/demo/.transcode-cache",
                entity_type="pruned-directory",
                status="pruned",
                reason_code="transcode-cache",
            ),
        ],
    )

    classified = subprocess.run(
        [sys.executable, str(ASSETCTL), "classify", "--catalog", str(catalog)],
        text=True,
        capture_output=True,
        check=False,
    )
    assert classified.returncode == 0, classified.stderr
    summary = json.loads(classified.stdout)
    assert summary["occurrenceCount"] == 2
    assert summary["cleanupEligibleCount"] == 0
    assert (catalog / "dispositions.ndjson").exists()

    reviewed = subprocess.run(
        [
            sys.executable,
            str(ASSETCTL),
            "review-batch",
            "--catalog",
            str(catalog),
            "--status",
            "unknown",
            "--group-by",
            "project",
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    assert reviewed.returncode == 0, reviewed.stderr
    review = json.loads(reviewed.stdout)
    assert review["matchedCount"] == 1
    assert review["groups"][0]["group"] == "videos/demo"
