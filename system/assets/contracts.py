from __future__ import annotations

import re
from typing import Any


ASSET_STATUSES = (
    "active",
    "canonical",
    "reference",
    "rebuildable",
    "superseded",
    "unknown",
    "missing",
)
RIGHTS_STATUSES = ("owned", "licensed", "reference-only", "unknown")
LOGICAL_LOCATORS = ("workspacePath", "storeKey", "remote")
LOGICAL_SCHEMES = ("episode://", "asset://", "workspace://", "repo://")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
WINDOWS_ABSOLUTE_RE = re.compile(r"^[A-Za-z]:[\\/]")


class ContractError(ValueError):
    """Raised when a portable asset contract is invalid."""


def _iter_strings(value: Any):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for nested in value.values():
            yield from _iter_strings(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from _iter_strings(nested)


def _is_machine_specific(value: str) -> bool:
    return (
        value.startswith("/Users/")
        or value.startswith("/home/")
        or value.startswith("file://")
        or bool(WINDOWS_ABSOLUTE_RE.match(value))
    )


def validate_asset_record(record: dict[str, Any]) -> None:
    required = ("schemaVersion", "assetId", "sha256", "sizeBytes", "kind", "role", "status", "rights")
    missing = [name for name in required if name not in record]
    if missing:
        raise ContractError(f"missing required fields: {', '.join(missing)}")

    if record["schemaVersion"] != 1:
        raise ContractError("schemaVersion must be 1")
    if not isinstance(record["assetId"], str) or not record["assetId"].startswith("asset."):
        raise ContractError("assetId must start with 'asset.'")
    if not isinstance(record["sha256"], str) or not SHA256_RE.fullmatch(record["sha256"]):
        raise ContractError("sha256 must be 64 lowercase hexadecimal characters")
    if isinstance(record["sizeBytes"], bool) or not isinstance(record["sizeBytes"], int) or record["sizeBytes"] < 0:
        raise ContractError("sizeBytes must be a non-negative integer")
    if record["status"] not in ASSET_STATUSES:
        raise ContractError(f"unsupported status: {record['status']}")

    rights = record["rights"]
    if not isinstance(rights, dict) or rights.get("status") not in RIGHTS_STATUSES:
        raise ContractError("rights.status is required and must be supported")

    present_locators = [name for name in LOGICAL_LOCATORS if record.get(name)]
    if not present_locators:
        raise ContractError("at least one logical locator is required")

    workspace_path = record.get("workspacePath")
    if workspace_path and not workspace_path.startswith(LOGICAL_SCHEMES):
        raise ContractError("workspacePath must use a portable logical scheme")
    store_key = record.get("storeKey")
    if store_key and (store_key.startswith("/") or WINDOWS_ABSOLUTE_RE.match(store_key)):
        raise ContractError("storeKey must be portable and relative")

    for value in _iter_strings(record):
        if _is_machine_specific(value):
            raise ContractError("asset records must contain only portable locations")
