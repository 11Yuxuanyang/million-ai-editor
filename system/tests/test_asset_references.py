from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
ASSETCTL = ROOT / "system/scripts/assetctl.py"


def _valid_card(reference_id: str = "reference.opening.test.v1") -> dict[str, object]:
    return {
        "schemaVersion": 1,
        "id": reference_id,
        "title": "Opening tension reveal",
        "category": "opening",
        "status": "approved",
        "source": {
            "assetId": "asset.case.test.master",
            "relativePath": "videos/test/deliverables/master.mp4",
            "timeRange": {"start": "00:00:00.000", "end": "00:00:02.000"},
        },
        "semanticProblem": "Reveal a hidden cost before explaining the system.",
        "visibleMotion": ["speaker stays primary", "evidence cards enter behind subject"],
        "useWhen": ["the first claim needs proof and human stakes"],
        "avoidWhen": ["the source has no reliable subject matte"],
        "rights": {
            "status": "owned",
            "license": "Project-authored edit using user-owned footage.",
        },
        "productionEligibility": "recipe-only",
        "review": {"status": "approved", "basis": "user-approved source edit"},
    }


def _write_valid_reference(destination: Path) -> None:
    card = _valid_card(destination.name)
    destination.mkdir(parents=True)
    (destination / "reference.yaml").write_text(
        json.dumps(card, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (destination / "timestamps.json").write_text(
        json.dumps(
            {
                "schemaVersion": 1,
                "referenceId": card["id"],
                "timeRange": card["source"]["timeRange"],
                "moments": [],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (destination / "remote.json").write_text(
        json.dumps(
            {
                "schemaVersion": 1,
                "referenceId": card["id"],
                "provider": "google-drive",
                "status": "not-migrated",
                "driveFileId": None,
                "webViewLink": None,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def test_parse_time_range_is_exact_and_rejects_reverse_ranges() -> None:
    from system.assets.references import parse_time_range

    parsed = parse_time_range("00:00:01.250-00:00:03.500")

    assert parsed.start_seconds == 1.25
    assert parsed.end_seconds == 3.5
    assert parsed.duration_seconds == 2.25
    with pytest.raises(ValueError, match="end must be after start"):
        parse_time_range("00:00:03.500-00:00:01.250")


def test_reference_init_creates_portable_draft_placeholders(tmp_path: Path) -> None:
    from system.assets.references import init_reference

    destination = tmp_path / "reference.opening.test.v1"
    result = init_reference(
        asset_id="asset.case.test.master",
        time_range="00:00:00.000-00:00:02.000",
        destination=destination,
    )

    card = json.loads((destination / "reference.yaml").read_text(encoding="utf-8"))
    timestamps = json.loads((destination / "timestamps.json").read_text(encoding="utf-8"))
    remote = json.loads((destination / "remote.json").read_text(encoding="utf-8"))
    serialized = "\n".join(json.dumps(value) for value in (card, timestamps, remote))
    assert result["referenceId"] == "reference.opening.test.v1"
    assert card["source"]["assetId"] == "asset.case.test.master"
    assert timestamps["timeRange"]["end"] == "00:00:02.000"
    assert remote["driveFileId"] is None
    assert "/Users/" not in serialized
    assert "file://" not in serialized


def test_reference_validation_requires_semantics_rights_and_exact_timestamps(
    tmp_path: Path,
) -> None:
    from system.assets.references import validate_reference

    destination = tmp_path / "reference.opening.test.v1"
    destination.mkdir()
    card = _valid_card()
    (destination / "reference.yaml").write_text(
        json.dumps(card, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (destination / "timestamps.json").write_text(
        json.dumps(
            {
                "schemaVersion": 1,
                "referenceId": card["id"],
                "timeRange": card["source"]["timeRange"],
                "moments": [{"at": "00:00:01.000", "meaning": "proof enters"}],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (destination / "remote.json").write_text(
        json.dumps(
            {
                "schemaVersion": 1,
                "referenceId": card["id"],
                "provider": "google-drive",
                "status": "not-migrated",
                "driveFileId": None,
                "webViewLink": None,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    assert validate_reference(destination)["valid"] is True
    card["semanticProblem"] = ""
    (destination / "reference.yaml").write_text(
        json.dumps(card, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    invalid = validate_reference(destination)
    assert invalid["valid"] is False
    assert "semanticProblem must not be empty" in invalid["errors"]


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg is required")
def test_contact_sheet_extracts_a_small_visual_index(tmp_path: Path) -> None:
    from system.assets.references import create_contact_sheet

    source = tmp_path / "source.mp4"
    output = tmp_path / "contact-sheet.jpg"
    generated = subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-f",
            "lavfi",
            "-i",
            "testsrc2=size=320x180:rate=12:duration=1",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            str(source),
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    assert generated.returncode == 0, generated.stderr

    result = create_contact_sheet(
        source,
        time_range="00:00:00.000-00:00:01.000",
        output=output,
        columns=2,
        rows=2,
    )

    assert output.is_file()
    assert 0 < output.stat().st_size < 1_000_000
    assert result["frameCount"] == 4


def test_assetctl_reference_validate_emits_json(tmp_path: Path) -> None:
    destination = tmp_path / "reference.opening.test.v1"
    initialized = subprocess.run(
        [
            sys.executable,
            str(ASSETCTL),
            "reference",
            "init",
            "--asset",
            "asset.case.test.master",
            "--range",
            "00:00:00.000-00:00:02.000",
            "--destination",
            str(destination),
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    assert initialized.returncode == 0, initialized.stderr

    validated = subprocess.run(
        [
            sys.executable,
            str(ASSETCTL),
            "reference",
            "validate",
            "--path",
            str(destination),
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    assert validated.returncode == 1
    assert json.loads(validated.stdout)["valid"] is False


def test_reference_validate_all_resolves_cards_from_library_root(tmp_path: Path) -> None:
    from system.assets.references import validate_reference_library

    library = tmp_path / "library/references"
    _write_valid_reference(library / "reference.opening.one.v1")
    _write_valid_reference(library / "reference.transition.two.v1")

    result = validate_reference_library(library)

    assert result["valid"] is True
    assert result["referenceCount"] == 2
    assert result["validCount"] == 2

    cli = subprocess.run(
        [
            sys.executable,
            str(ASSETCTL),
            "reference",
            "validate",
            "--all",
            "--library",
            str(library),
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    assert cli.returncode == 0, cli.stderr
    assert json.loads(cli.stdout)["validCount"] == 2
