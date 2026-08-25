"""Small, dependency-free process and JSON helpers."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import uuid
from pathlib import Path
from typing import Any


def run(
    command: list[str], cwd: Path | None = None, check: bool = True
) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=False)
    if check and completed.returncode:
        detail = (completed.stderr or completed.stdout).strip()
        raise RuntimeError(f"command failed ({completed.returncode}): {' '.join(command)}\n{detail}")
    return completed


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_name(f".{path.name}.partial")
    partial.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    partial.replace(path)


def move_to_trash(path: Path) -> Path:
    """Move a generated or user-owned path to Trash without permanent deletion."""
    source = path.expanduser().resolve()
    trash_root = Path(
        os.environ.get("EDITING_TRASH_ROOT", str(Path.home() / ".Trash"))
    ).expanduser()
    trash_root.mkdir(parents=True, exist_ok=True)
    destination = trash_root / source.name
    if destination.exists():
        destination = trash_root / f"{source.name}-{uuid.uuid4().hex[:8]}"
    shutil.move(str(source), str(destination))
    return destination


def json_fingerprint(payload: Any) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def json_schema_issues(value: Any, schema: dict[str, Any], location: str = "$") -> list[str]:
    """Validate the small JSON Schema subset used by the V3 contracts."""
    issues: list[str] = []
    expected_type = schema.get("type")
    type_checks = {
        "object": lambda item: isinstance(item, dict),
        "array": lambda item: isinstance(item, list),
        "string": lambda item: isinstance(item, str),
        "number": lambda item: isinstance(item, (int, float)) and not isinstance(item, bool),
        "integer": lambda item: isinstance(item, int) and not isinstance(item, bool),
        "boolean": lambda item: isinstance(item, bool),
    }
    if expected_type in type_checks and not type_checks[expected_type](value):
        return [f"{location} must be {expected_type}"]
    if "const" in schema and value != schema["const"]:
        issues.append(f"{location} must equal {schema['const']!r}")
    if "enum" in schema and value not in schema["enum"]:
        issues.append(f"{location} must be one of {schema['enum']!r}")
    if isinstance(value, str):
        if len(value) < int(schema.get("minLength", 0)):
            issues.append(f"{location} is shorter than minLength")
        pattern = schema.get("pattern")
        if pattern and not re.search(pattern, value):
            issues.append(f"{location} does not match {pattern!r}")
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            issues.append(f"{location} must be >= {schema['minimum']}")
        if "exclusiveMinimum" in schema and value <= schema["exclusiveMinimum"]:
            issues.append(f"{location} must be > {schema['exclusiveMinimum']}")
    if isinstance(value, dict):
        properties = schema.get("properties") or {}
        for required in schema.get("required") or []:
            if required not in value:
                issues.append(f"{location}.{required} is required")
        if schema.get("additionalProperties") is False:
            for key in value.keys() - properties.keys():
                issues.append(f"{location}.{key} is not allowed")
        for key, child in value.items():
            child_schema = properties.get(key)
            if child_schema:
                issues.extend(json_schema_issues(child, child_schema, f"{location}.{key}"))
    if isinstance(value, list) and isinstance(schema.get("items"), dict):
        for index, child in enumerate(value):
            issues.extend(json_schema_issues(child, schema["items"], f"{location}[{index}]"))
    return issues


def validate_schema_file(value: Any, schema_path: Path, label: str) -> list[str]:
    return [f"{label}: {issue}" for issue in json_schema_issues(value, load_json(schema_path))]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
