from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
ASSETCTL = ROOT / "system/scripts/assetctl.py"


def _read_ndjson(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def test_equal_size_different_content_is_not_a_duplicate(tmp_path: Path) -> None:
    from system.assets.identity import build_identity_report
    from system.assets.inventory import scan_workspace

    root = tmp_path / "workspace"
    catalog = tmp_path / "catalog"
    root.mkdir()
    (root / "a.mov").write_bytes(b"abc")
    (root / "b.mov").write_bytes(b"def")
    scan_workspace(root, catalog)

    summary = build_identity_report(root, catalog, workers=2)

    assert summary["candidateOccurrenceCount"] == 2
    assert summary["hashedOccurrenceCount"] == 2
    assert summary["duplicateGroupCount"] == 0
    assert _read_ndjson(catalog / "duplicate-groups.ndjson") == []


def test_exact_content_creates_unresolved_duplicate_group(tmp_path: Path) -> None:
    from system.assets.identity import build_identity_report
    from system.assets.inventory import scan_workspace

    root = tmp_path / "workspace"
    catalog = tmp_path / "catalog"
    root.mkdir()
    (root / "a.mov").write_bytes(b"same")
    (root / "b.mov").write_bytes(b"same")
    scan_workspace(root, catalog)

    summary = build_identity_report(root, catalog, workers=2)
    groups = _read_ndjson(catalog / "duplicate-groups.ndjson")

    assert summary["duplicateGroupCount"] == 1
    assert len(groups[0]["sha256"]) == 64
    assert groups[0]["relativePaths"] == ["a.mov", "b.mov"]
    assert groups[0]["canonicalOwner"] is None
    assert groups[0]["decisionStatus"] == "unresolved"
    assert groups[0]["cleanupEligible"] is False


def test_quick_fingerprint_alone_never_forms_a_duplicate_group() -> None:
    from system.assets.identity import group_full_hash_records

    records = [
        {
            "occurrenceId": "occurrence.a",
            "relativePath": "a.mov",
            "quickFingerprint": "same-quick-value",
            "sha256": None,
            "sizeBytes": 4,
        },
        {
            "occurrenceId": "occurrence.b",
            "relativePath": "b.mov",
            "quickFingerprint": "same-quick-value",
            "sha256": None,
            "sizeBytes": 4,
        },
    ]

    assert group_full_hash_records(records) == []


def test_broken_and_external_links_are_reported_separately(tmp_path: Path) -> None:
    from system.assets.identity import write_link_reports
    from system.assets.inventory import scan_workspace

    root = tmp_path / "workspace"
    catalog = tmp_path / "catalog"
    root.mkdir()
    external = tmp_path / "external.mov"
    external.write_bytes(b"outside")
    (root / "external.mov").symlink_to(external)
    (root / "broken.mov").symlink_to(root / "missing.mov")
    scan_workspace(root, catalog)

    summary = write_link_reports(catalog)
    broken = _read_ndjson(catalog / "broken-links.ndjson")
    external_links = _read_ndjson(catalog / "external-links.ndjson")

    assert summary["brokenLinkCount"] == 1
    assert summary["externalLinkCount"] == 1
    assert [item["relativePath"] for item in broken] == ["broken.mov"]
    assert [item["relativePath"] for item in external_links] == ["external.mov"]
    assert external_links[0]["migrationEvidence"] is False


def test_assetctl_hash_and_links_emit_json(tmp_path: Path) -> None:
    from system.assets.inventory import scan_workspace

    root = tmp_path / "workspace"
    catalog = tmp_path / "catalog"
    root.mkdir()
    (root / "a.mov").write_bytes(b"same")
    (root / "b.mov").write_bytes(b"same")
    scan_workspace(root, catalog)

    hashed = subprocess.run(
        [
            sys.executable,
            str(ASSETCTL),
            "hash",
            "--root",
            str(root),
            "--catalog",
            str(catalog),
            "--scope",
            "duplicate-candidates",
            "--workers",
            "2",
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    assert hashed.returncode == 0, hashed.stderr
    assert json.loads(hashed.stdout)["duplicateGroupCount"] == 1

    linked = subprocess.run(
        [sys.executable, str(ASSETCTL), "links", "--catalog", str(catalog)],
        text=True,
        capture_output=True,
        check=False,
    )
    assert linked.returncode == 0, linked.stderr
    assert json.loads(linked.stdout)["brokenLinkCount"] == 0
