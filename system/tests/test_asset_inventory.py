from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
ASSETCTL = ROOT / "system/scripts/assetctl.py"


def read_ndjson(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def test_scan_writes_sorted_portable_inventory(tmp_path: Path) -> None:
    from system.assets.inventory import scan_workspace

    root = tmp_path / "workspace"
    output = root / "library/catalog/current"
    (root / "source").mkdir(parents=True)
    (root / "source/z.mov").write_bytes(b"z-video")
    (root / "source/a.wav").write_bytes(b"a-audio")
    (root / "README.md").write_text("notes\n", encoding="utf-8")

    summary = scan_workspace(root, output, workers=2)
    records = read_ndjson(output / "inventory.ndjson")
    serialized = (output / "inventory.ndjson").read_text(encoding="utf-8")

    assert [record["relativePath"] for record in records] == sorted(
        record["relativePath"] for record in records
    )
    assert str(root) not in serialized
    assert str(output) not in serialized
    assert summary.occurrence_count == 3
    assert summary.total_size_bytes == len(b"z-video") + len(b"a-audio") + len("notes\n")
    assert json.loads((output / "summary.json").read_text(encoding="utf-8"))["occurrenceCount"] == 3


def test_symlinks_are_described_without_following_external_targets(tmp_path: Path) -> None:
    from system.assets.inventory import scan_workspace

    root = tmp_path / "workspace"
    output = root / "catalog"
    root.mkdir()
    external = tmp_path / "outside.mov"
    external.write_bytes(b"do-not-read-as-workspace-content")
    (root / "external.mov").symlink_to(external)
    (root / "broken.mov").symlink_to(root / "missing.mov")

    scan_workspace(root, output)
    records = {record["relativePath"]: record for record in read_ndjson(output / "inventory.ndjson")}
    serialized = (output / "inventory.ndjson").read_text(encoding="utf-8")

    external_record = records["external.mov"]
    assert external_record["entityType"] == "symlink"
    assert external_record["link"] == {
        "isSymlink": True,
        "targetExists": True,
        "targetScope": "external",
        "targetPath": None,
    }
    assert external_record["sizeBytes"] == 0
    assert str(external) not in serialized

    broken_record = records["broken.mov"]
    assert broken_record["status"] == "missing"
    assert broken_record["link"]["targetExists"] is False
    assert broken_record["sha256"] is None


def test_rebuildable_directories_are_pruned_but_recorded(tmp_path: Path) -> None:
    from system.assets.inventory import scan_workspace

    root = tmp_path / "workspace"
    output = root / "library/catalog/current"
    fixtures = {
        "node_modules/pkg/index.js": b"dependency",
        ".venv-test/bin/python": b"environment",
        "renders/work-123/compiled/frame.png": b"render-work",
        ".transcode-cache/proxy.mp4": b"proxy",
        "shots/compiled/__hyperframes_video_frames/0001.png": b"frame",
    }
    for relative, data in fixtures.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    summary = scan_workspace(root, output)
    records = read_ndjson(output / "inventory.ndjson")
    pruned = {record["relativePath"]: record for record in records if record["entityType"] == "pruned-directory"}

    assert set(pruned) == {
        ".transcode-cache",
        ".venv-test",
        "node_modules",
        "renders/work-123",
        "shots/compiled/__hyperframes_video_frames",
    }
    assert all(record["status"] == "pruned" for record in pruned.values())
    assert all(record["sha256"] is None for record in pruned.values())
    assert summary.pruned_directory_count == 5
    assert not any(record["relativePath"].endswith("frame.png") for record in records)


def test_media_kind_and_quick_fingerprint_do_not_claim_sha256(tmp_path: Path) -> None:
    from system.assets.inventory import scan_workspace

    root = tmp_path / "workspace"
    output = root / "catalog"
    (root / "assets").mkdir(parents=True)
    (root / "assets/clip.MP4").write_bytes(b"video")
    (root / "assets/dialogue.m4a").write_bytes(b"audio")
    (root / "assets/frame.webp").write_bytes(b"image")
    (root / "assets/data.json").write_text("{}\n", encoding="utf-8")

    scan_workspace(root, output)
    records = {record["relativePath"]: record for record in read_ndjson(output / "inventory.ndjson")}

    assert records["assets/clip.MP4"]["kind"] == "video"
    assert records["assets/dialogue.m4a"]["kind"] == "audio"
    assert records["assets/frame.webp"]["kind"] == "image"
    assert records["assets/data.json"]["kind"] == "data"
    assert all(record["quickFingerprint"] for record in records.values())
    assert all(record["sha256"] is None for record in records.values())


def test_rescan_excludes_its_own_catalog_and_leaves_no_temp_files(tmp_path: Path) -> None:
    from system.assets.inventory import scan_workspace

    root = tmp_path / "workspace"
    output = root / "library/catalog/current"
    (root / "library").mkdir(parents=True)
    (root / "one.txt").write_text("one", encoding="utf-8")
    (root / "library/keep.json").write_text("{}\n", encoding="utf-8")

    first = scan_workspace(root, output)
    second = scan_workspace(root, output)
    records = read_ndjson(output / "inventory.ndjson")

    assert first.occurrence_count == second.occurrence_count == 2
    assert [record["relativePath"] for record in records] == ["library/keep.json", "one.txt"]
    assert not list(output.glob("*.tmp"))


def test_assetctl_audit_and_status_emit_json(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    catalog = tmp_path / "catalog"
    workspace.mkdir()
    (workspace / "file.txt").write_text("portable", encoding="utf-8")

    audited = subprocess.run(
        [
            sys.executable,
            str(ASSETCTL),
            "audit",
            "--root",
            str(workspace),
            "--output",
            str(catalog),
            "--workers",
            "2",
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    assert audited.returncode == 0, audited.stderr
    assert json.loads(audited.stdout)["occurrenceCount"] == 1

    status = subprocess.run(
        [sys.executable, str(ASSETCTL), "status", "--catalog", str(catalog)],
        text=True,
        capture_output=True,
        check=False,
    )
    assert status.returncode == 0, status.stderr
    assert json.loads(status.stdout)["occurrenceCount"] == 1
