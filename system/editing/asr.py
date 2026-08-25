"""Chinese speech-to-text transport and audio preparation."""

from __future__ import annotations

import base64
import json
import urllib.error
import urllib.request
import uuid
from pathlib import Path
import tempfile

from .io import run, write_json


ASR_ENDPOINT = "https://openspeech.bytedance.com/api/v3/auc/bigmodel/recognize/flash"


def extract_asr_audio(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    run([
        "ffmpeg", "-hide_banner", "-nostdin", "-y", "-i", str(source),
        "-vn", "-ac", "1", "-ar", "16000", "-c:a", "libmp3lame", "-b:a", "64k",
        str(destination),
    ])


def request_doubao_asr(
    source: Path,
    destination: Path,
    app_key: str,
    access_key: str,
    timeout_seconds: int = 300,
) -> None:
    payload = {
        "user": {"uid": app_key},
        "audio": {"data": base64.b64encode(source.read_bytes()).decode("ascii")},
        "request": {
            "model_name": "bigmodel",
            "enable_itn": True,
            "enable_punc": True,
            "enable_ddc": True,
            "show_utterances": True,
            "show_words": True,
        },
    }
    request = urllib.request.Request(
        ASR_ENDPOINT,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "X-Api-App-Key": app_key,
            "X-Api-Access-Key": access_key,
            "X-Api-Resource-Id": "volc.bigasr.auc_turbo",
            "X-Api-Request-Id": str(uuid.uuid4()),
            "X-Api-Sequence": "-1",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            status_code = response.headers.get("X-Api-Status-Code")
            message = response.headers.get("X-Api-Message")
            log_id = response.headers.get("X-Tt-Logid")
            body = response.read().decode("utf-8")
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Doubao ASR failed for {source.name}: {detail}") from error
    if status_code != "20000000":
        raise RuntimeError(
            f"Doubao ASR failed for {source.name}: "
            f"status={status_code or 'missing'} "
            f"message={message or 'missing'} "
            f"logId={log_id or 'missing'}"
        )
    try:
        raw = json.loads(body)
    except json.JSONDecodeError as error:
        raise RuntimeError(
            f"Doubao ASR returned invalid JSON for {source.name}: logId={log_id or 'missing'}"
        ) from error
    result = raw.get("result") or {}
    utterances = []
    for utterance in result.get("utterances") or []:
        utterances.append({
            "startMs": utterance.get("start_time", 0),
            "endMs": utterance.get("end_time", 0),
            "text": utterance.get("text", ""),
            "words": [
                {
                    "startMs": word.get("start_time", 0),
                    "endMs": word.get("end_time", 0),
                    "text": word.get("text", ""),
                }
                for word in utterance.get("words") or []
            ],
        })
    write_json(destination, {
        "provider": "volcengine-bigasr-flash",
        "sourceAudio": str(source),
        "request": {
            "statusCode": status_code,
            "logId": log_id,
        },
        "text": result.get("text", ""),
        "utterances": utterances,
    })


def verify_doubao_asr(app_key: str, access_key: str) -> None:
    """Perform a tiny live request so readiness never trusts non-empty junk credentials."""
    with tempfile.TemporaryDirectory(prefix="editing-asr-doctor-") as temporary:
        root = Path(temporary)
        audio = root / "probe.mp3"
        output = root / "probe.json"
        run([
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-f", "lavfi", "-i", "anullsrc=r=16000:cl=mono", "-t", "0.35",
            "-c:a", "libmp3lame", "-b:a", "64k", str(audio),
        ])
        request_doubao_asr(
            audio,
            output,
            app_key,
            access_key,
            timeout_seconds=30,
        )
