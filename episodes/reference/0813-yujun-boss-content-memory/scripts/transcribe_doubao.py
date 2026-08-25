#!/usr/bin/env python3
import base64
import json
import os
import sys
import urllib.error
import urllib.request
import uuid
from pathlib import Path


ENDPOINT = "https://openspeech.bytedance.com/api/v3/auc/bigmodel/recognize/flash"


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: transcribe_doubao.py <audio.mp3> <output.json>", file=sys.stderr)
        return 2

    app_key = os.environ.get("DOUBAO_APP_KEY")
    access_key = os.environ.get("DOUBAO_ACCESS_KEY")
    if not app_key or not access_key:
        print("DOUBAO_APP_KEY and DOUBAO_ACCESS_KEY are required", file=sys.stderr)
        return 2

    source = Path(sys.argv[1])
    destination = Path(sys.argv[2])
    encoded = base64.b64encode(source.read_bytes()).decode("ascii")
    payload = {
        "user": {"uid": app_key},
        "audio": {"data": encoded},
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
        ENDPOINT,
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
        with urllib.request.urlopen(request, timeout=180) as response:
            raw = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        print(error.read().decode("utf-8", errors="replace"), file=sys.stderr)
        return 1

    result = raw.get("result") or {}
    utterances = []
    for utterance in result.get("utterances") or []:
        utterances.append(
            {
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
            }
        )

    normalized = {
        "provider": "volcengine-bigasr-flash",
        "sourceAudio": str(source),
        "text": result.get("text", ""),
        "utterances": utterances,
    }
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(normalized, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"{source.name}: {normalized['text']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
