from __future__ import annotations

import json
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))


def valid_asset_record() -> dict[str, object]:
    digest = "a" * 64
    return {
        "schemaVersion": 1,
        "assetId": "asset.source.example",
        "sha256": digest,
        "sizeBytes": 10,
        "kind": "video",
        "role": "source",
        "status": "canonical",
        "rights": {"status": "owned"},
        "workspacePath": "episode://source/a.mov",
        "storeKey": f"objects/sha256/aa/{digest}.mov",
    }


def test_valid_asset_record_passes() -> None:
    from system.assets.contracts import validate_asset_record

    validate_asset_record(valid_asset_record())


@pytest.mark.parametrize(
    "location",
    [
        "/Users/alice/Movies/a.mov",
        "/home/alice/videos/a.mov",
        r"C:\Users\alice\Videos\a.mov",
        "file:///Volumes/media/a.mov",
    ],
)
def test_machine_specific_locations_are_rejected(location: str) -> None:
    from system.assets.contracts import ContractError, validate_asset_record

    record = valid_asset_record()
    record["workspacePath"] = location
    with pytest.raises(ContractError, match="portable"):
        validate_asset_record(record)


def test_rights_status_is_required() -> None:
    from system.assets.contracts import ContractError, validate_asset_record

    record = valid_asset_record()
    record["rights"] = {}
    with pytest.raises(ContractError, match="rights.status"):
        validate_asset_record(record)


def test_at_least_one_logical_locator_is_required() -> None:
    from system.assets.contracts import ContractError, validate_asset_record

    record = valid_asset_record()
    record.pop("workspacePath")
    record.pop("storeKey")
    with pytest.raises(ContractError, match="logical locator"):
        validate_asset_record(record)


def test_schema_files_define_expected_enums() -> None:
    asset_schema = json.loads(
        (ROOT / "system/schemas/asset-record.schema.json").read_text(encoding="utf-8")
    )
    rights_status = asset_schema["properties"]["rights"]["properties"]["status"]["enum"]
    lifecycle_status = asset_schema["properties"]["status"]["enum"]

    assert lifecycle_status == [
        "active",
        "canonical",
        "reference",
        "rebuildable",
        "superseded",
        "unknown",
        "missing",
    ]
    assert rights_status == ["owned", "licensed", "reference-only", "unknown"]
    for name in ("reference-card.schema.json", "cleanup-manifest.schema.json"):
        schema = json.loads((ROOT / "system/schemas" / name).read_text(encoding="utf-8"))
        assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"


def test_asset_policy_only_proposes_dispositions() -> None:
    policy = json.loads((ROOT / "config/asset-policy.json").read_text(encoding="utf-8"))

    expected_rule_ids = {
        "dependency-directory",
        "python-environment",
        "render-work-directory",
        "transcode-cache",
        "waveform-cache",
        "thumbnail-cache",
        "preview-or-render",
        "source-directory",
        "reference-study",
        "canonical-delivery-name",
    }
    assert {rule["id"] for rule in policy["rules"]} == expected_rule_ids
    assert all("proposedStatus" in rule for rule in policy["rules"])
    assert all("delete" not in rule for rule in policy["rules"])


def test_machine_example_contains_env_names_not_paths() -> None:
    machine = json.loads((ROOT / "config/machine.example.json").read_text(encoding="utf-8"))

    assert machine == {
        "schemaVersion": 1,
        "assetStoreRootEnv": "EDITING_ASSET_STORE_ROOT",
        "workspaceRootEnv": "EDITING_WORKSPACE_ROOT",
        "secrets": {
            "doubaoAppKeyEnv": "DOUBAO_APP_KEY",
            "doubaoAccessKeyEnv": "DOUBAO_ACCESS_KEY",
        },
    }


def test_publishing_automation_is_machine_portable() -> None:
    tracked = [
        ROOT / "publishing/douyin-queue.example.json",
        ROOT / "publishing/scripts/douyin_prepare_today.py",
        ROOT / "publishing/scripts/douyin_daily_cron_launcher.sh",
        ROOT / "publishing/scripts/install_douyin_cron.sh",
        ROOT / "publishing/README.md",
    ]
    for path in tracked:
        assert "/Users/" not in path.read_text(encoding="utf-8"), path

    queue = json.loads((ROOT / "publishing/douyin-queue.example.json").read_text(encoding="utf-8"))
    for item in queue["items"]:
        for key in ("video", "cover", "cover_3x4", "transcript", "notes"):
            if item.get(key):
                assert not Path(item[key]).is_absolute(), (item["id"], key)
