"""Runtime readiness checks shared by humans and editing agents."""

from __future__ import annotations

import json
import os
import re
import shutil
from pathlib import Path
from typing import Any

from .asr import verify_doubao_asr
from .io import load_json, run, sha256_file


ROOT = Path(__file__).resolve().parents[2]
ENVIRONMENT_LOCK_PATH = ROOT / "config" / "environment.lock.json"


def command_doctor(args: Any) -> int:
    environment_lock = load_json(ENVIRONMENT_LOCK_PATH)
    required = ["ffmpeg", "ffprobe", "node", "npm", "hyperframes"]
    runtime_missing: list[str] = []
    command_or_skill_missing: list[str] = []
    asset_missing: list[str] = []
    report: dict[str, Any] = {
        "ok": True,
        "commands": {},
        "skills": {},
        "assets": {},
        "optional": {},
        "readiness": {},
        "remediation": [],
    }
    for name in required:
        path = shutil.which(name)
        report["commands"][name] = path
        if not path:
            report["ok"] = False
            issue = f"command:{name}"
            runtime_missing.append(issue)
            command_or_skill_missing.append(issue)
    if report["commands"].get("node"):
        version = run(["node", "--version"]).stdout.strip()
        report["commands"]["nodeVersion"] = version
        try:
            minimum_major = int(environment_lock["tools"]["node"]["minimumMajor"])
            if int(version.lstrip("v").split(".", 1)[0]) < minimum_major:
                report["ok"] = False
                issue = f"node>={minimum_major}"
                runtime_missing.append(issue)
                command_or_skill_missing.append(issue)
        except ValueError:
            report["ok"] = False
            runtime_missing.append("node-version-unreadable")
            command_or_skill_missing.append("node-version-unreadable")
    if report["commands"].get("ffmpeg"):
        ffmpeg_version = run(["ffmpeg", "-version"]).stdout.splitlines()[0]
        report["commands"]["ffmpegVersion"] = ffmpeg_version
        match = re.search(r"ffmpeg version\s+(\d+)", ffmpeg_version)
        minimum_major = int(environment_lock["tools"]["ffmpeg"]["minimumMajor"])
        if not match or int(match.group(1)) < minimum_major:
            report["ok"] = False
            issue = f"ffmpeg>={minimum_major}"
            runtime_missing.append(issue)
            command_or_skill_missing.append(issue)
    if report["commands"].get("hyperframes"):
        version = run(["hyperframes", "--version"]).stdout.strip()
        expected = environment_lock["tools"]["hyperframes"]["projectVersion"]
        report["commands"].update({"hyperframesVersion": version, "hyperframesExpected": expected})
        if version != expected:
            report["ok"] = False
            issue = f"hyperframes=={expected}"
            runtime_missing.append(issue)
            command_or_skill_missing.append(issue)
    skill_root = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")) / "skills"
    for skill in environment_lock.get("activeSkills", []):
        expected = (ROOT / "skills" / skill).resolve()
        active = skill_root / skill
        matches = active.is_symlink() and active.resolve() == expected
        report["skills"][skill] = {"ok": matches, "active": str(active), "expected": str(expected)}
        if not matches:
            report["ok"] = False
            issue = f"skill:{skill}"
            runtime_missing.append(issue)
            command_or_skill_missing.append(issue)
    for asset in environment_lock.get("assets", []):
        path = ROOT / asset["path"]
        actual_hash = sha256_file(path) if path.is_file() else None
        matches = actual_hash == asset["sha256"]
        report["assets"][asset["path"]] = {"ok": matches, "sha256": actual_hash}
        if not matches:
            report["ok"] = False
            issue = f"asset:{asset['path']}"
            runtime_missing.append(issue)
            asset_missing.append(asset["path"])

    app_key = os.environ.get("DOUBAO_APP_KEY")
    access_key = os.environ.get("DOUBAO_ACCESS_KEY")
    asr_configured = bool(app_key and access_key)
    asr_verified = False
    asr_error: str | None = None
    if asr_configured and getattr(args, "verify_asr", False):
        try:
            verify_doubao_asr(str(app_key), str(access_key))
            asr_verified = True
        except (RuntimeError, OSError) as error:
            asr_error = str(error)
    report["optional"]["doubaoAsr"] = {
        "configured": asr_configured,
        "verified": asr_verified,
        "status": (
            "verified"
            if asr_verified
            else "verification-failed"
            if asr_error
            else "configured-unverified"
            if asr_configured
            else "not-configured"
        ),
        "error": asr_error,
    }
    remote_states = []
    for state_path in sorted((ROOT / "library" / "references").glob("*/remote.json")):
        state = load_json(state_path)
        if state.get("status") != "migrated" or not state.get("driveFileId"):
            remote_states.append(state.get("referenceId") or state_path.parent.name)
    report["optional"]["remoteReferences"] = {
        "pending": remote_states,
        "status": "ready" if not remote_states else "degraded",
    }
    report["readiness"]["runtime"] = {
        "status": "ready" if report["ok"] else "degraded",
        "missing": runtime_missing,
    }
    full_edit_missing = list(runtime_missing)
    if not asr_configured:
        full_edit_missing.append("doubao-asr")
        report["remediation"].append({
            "issue": "doubao-asr",
            "action": "Set DOUBAO_APP_KEY and DOUBAO_ACCESS_KEY in the local environment or keychain.",
            "secret": True,
        })
    elif asr_error:
        full_edit_missing.append("doubao-asr-verification-failed")
        report["remediation"].append({
            "issue": "doubao-asr-verification-failed",
            "action": "Check the local Doubao credentials and network, then rerun doctor --mode full-edit --verify-asr.",
            "secret": True,
        })
    elif not asr_verified:
        full_edit_missing.append("doubao-asr-unverified")
        report["remediation"].append({
            "issue": "doubao-asr-unverified",
            "action": "Run doctor --mode full-edit --verify-asr once to make a live provider request.",
            "secret": False,
        })
    if command_or_skill_missing:
        report["remediation"].append({
            "issue": "runtime",
            "action": "Run system/scripts/install-local-skills.sh and install versions from config/environment.lock.json.",
            "secret": False,
        })
    if asset_missing:
        report["remediation"].append({
            "issue": "runtime-assets",
            "action": "Restore the listed tracked assets from Git or a clean clone, then rerun doctor: " + ", ".join(asset_missing),
            "secret": False,
        })
    full_edit_warnings = []
    if remote_states:
        full_edit_warnings.append(f"remote-reference-assets:{len(remote_states)}")
        report["remediation"].append({
            "issue": "remote-reference-assets",
            "action": "Migrate the listed reference originals when needed; bundled contact sheets remain usable for selection.",
            "secret": False,
        })
    report["readiness"]["fullEdit"] = {
        "status": "ready" if report["ok"] and not full_edit_missing else "degraded",
        "missing": full_edit_missing,
        "warnings": full_edit_warnings,
    }
    if args.mode == "full-edit" and full_edit_missing:
        report["ok"] = False
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 1
