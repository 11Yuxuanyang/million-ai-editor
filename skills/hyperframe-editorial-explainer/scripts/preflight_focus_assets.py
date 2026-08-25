#!/usr/bin/env python3
"""Preflight editorial focus-montage screenshots before animation work."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

from derive_focus_layouts import derive_layout, find_phrase, run_ocr, union_box


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_contact_sheet(
    rows: list[dict],
    destination: Path,
    columns: int = 3,
) -> None:
    tile_width = 600
    tile_height = 430
    label_height = 74
    count = max(1, len(rows))
    sheet_rows = (count + columns - 1) // columns
    sheet = Image.new(
        "RGB",
        (tile_width * columns, tile_height * sheet_rows),
        (18, 18, 18),
    )
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()

    for index, row in enumerate(rows):
        tile_x = (index % columns) * tile_width
        tile_y = (index // columns) * tile_height
        image_area = (
            tile_x + 8,
            tile_y + 8,
            tile_x + tile_width - 8,
            tile_y + tile_height - label_height,
        )
        image_width = image_area[2] - image_area[0]
        image_height = image_area[3] - image_area[1]

        image_path = Path(row["image"])
        if image_path.exists():
            try:
                source = Image.open(image_path).convert("RGB")
                thumb = ImageOps.contain(
                    source,
                    (image_width, image_height),
                    Image.Resampling.LANCZOS,
                )
                paste_x = image_area[0] + (image_width - thumb.width) // 2
                paste_y = image_area[1] + (image_height - thumb.height) // 2
                sheet.paste(thumb, (paste_x, paste_y))
            except Exception:
                draw.rectangle(image_area, fill=(80, 20, 20))
        else:
            draw.rectangle(image_area, fill=(80, 20, 20))

        status_color = {
            "error": (255, 92, 92),
            "review": (255, 198, 72),
            "ready_for_manual_review": (110, 230, 145),
        }.get(row["technicalStatus"], (220, 220, 220))
        dimensions = row.get("dimensionsPx", ["?", "?"])
        scale = row.get("predictedSourceUpscale")
        scale_text = "n/a" if scale is None else f"{scale:.2f}x"
        label_one = (
            f"{row['id']}  {dimensions[0]}x{dimensions[1]}  "
            f"predicted upscale={scale_text}"
        )
        label_two = (
            f"{row['technicalStatus']}  OCR={row.get('matchedText', 'n/a')}  "
            f"warnings={len(row['warnings'])} errors={len(row['errors'])}"
        )
        draw.text(
            (tile_x + 12, tile_y + tile_height - label_height + 10),
            label_one,
            fill=(235, 235, 235),
            font=font,
        )
        draw.text(
            (tile_x + 12, tile_y + tile_height - label_height + 34),
            label_two,
            fill=status_color,
            font=font,
        )

    destination.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(destination, quality=94)


def inspect_shot(
    shot: dict,
    defaults: dict,
    root: Path,
    canvas_size: tuple[int, int],
    seen_hashes: dict[str, str],
    max_source_upscale: float,
) -> dict:
    image_path = (root / shot["image"]).resolve()
    row = {
        "id": shot["id"],
        "image": str(image_path),
        "query": shot["query"],
        "sha256": None,
        "dimensionsPx": [0, 0],
        "matchedText": None,
        "matchScore": None,
        "ocrBoxPx": None,
        "predictedSourceUpscale": None,
        "zoomOverCover": None,
        "projectedTargetPx": None,
        "warnings": [],
        "errors": [],
        "technicalStatus": "error",
        "manualReview": "required",
        "manualConclusion": "pending",
    }

    if not image_path.exists():
        row["errors"].append("missing_file")
        return row

    try:
        fingerprint = sha256(image_path)
        row["sha256"] = fingerprint
        if fingerprint in seen_hashes:
            row["warnings"].append(
                f"duplicate_of:{seen_hashes[fingerprint]}"
            )
        else:
            seen_hashes[fingerprint] = shot["id"]

        with Image.open(image_path) as image:
            image.verify()
        with Image.open(image_path) as image:
            image_size = image.size
        row["dimensionsPx"] = list(image_size)
    except Exception as exc:
        row["errors"].append(f"unreadable_image:{type(exc).__name__}")
        return row

    if image_size[0] < canvas_size[0] or image_size[1] < canvas_size[1]:
        row["warnings"].append("source_smaller_than_output_canvas")

    try:
        words = run_ocr(
            image_path,
            shot.get("language", defaults.get("language", "eng")),
            int(shot.get("psm", defaults.get("psm", 11))),
        )
        query_value = shot["query"]
        queries = [query_value] if isinstance(query_value, str) else query_value
        matched_words, _, match_score = find_phrase(words, queries)
        box = union_box(matched_words)
        row["matchedText"] = " ".join(word.text for word in matched_words)
        row["matchScore"] = round(min(1.0, match_score), 4)
        row["ocrBoxPx"] = list(box)
        if row["matchScore"] < 0.7:
            row["warnings"].append("weak_ocr_match")

        focus_radius = tuple(
            shot.get(
                "focusRadiusPct",
                defaults.get("focusRadiusPct", [42, 25]),
            )
        )
        layout = derive_layout(
            image_size,
            box,
            canvas_size,
            tuple(
                shot.get(
                    "anchorPct",
                    defaults.get("anchorPct", [0.5, 0.5]),
                )
            ),
            tuple(
                shot.get(
                    "targetFill",
                    defaults.get("targetFill", [0.58, 0.22]),
                )
            ),
            float(shot.get("maxZoom", defaults.get("maxZoom", 10))),
            focus_radius,
            bool(
                shot.get(
                    "centerPriority",
                    defaults.get("centerPriority", True),
                )
            ),
        )
        cover_scale = max(
            canvas_size[0] / image_size[0],
            canvas_size[1] / image_size[1],
        )
        row["predictedSourceUpscale"] = round(layout["scale"], 4)
        row["zoomOverCover"] = round(layout["scale"] / cover_scale, 3)
        row["projectedTargetPx"] = [
            round((box[2] - box[0]) * layout["scale"], 1),
            round((box[3] - box[1]) * layout["scale"], 1),
        ]
        row["predictedFocusPct"] = layout["focusPct"]
        row["predictedCenterErrorPx"] = layout["centerErrorPx"]

        if layout["scale"] > max_source_upscale:
            row["warnings"].append(
                f"source_upscale_exceeds:{max_source_upscale:.2f}x"
            )
        if layout["scale"] / cover_scale > 5:
            row["warnings"].append("extreme_center_zoom_may_lose_page_context")
    except Exception as exc:
        row["errors"].append(f"ocr_or_layout_failed:{type(exc).__name__}:{exc}")

    if row["errors"]:
        row["technicalStatus"] = "error"
    elif row["warnings"]:
        row["technicalStatus"] = "review"
    else:
        row["technicalStatus"] = "ready_for_manual_review"
    return row


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--contact-sheet", required=True, type=Path)
    parser.add_argument("--max-source-upscale", type=float)
    args = parser.parse_args()

    spec = json.loads(args.spec.read_text())
    root = args.spec.resolve().parent
    defaults = spec.get("defaults", {})
    canvas_size = tuple(spec.get("canvas", [1920, 1080]))
    max_source_upscale = (
        args.max_source_upscale
        if args.max_source_upscale is not None
        else float(defaults.get("maxSourceUpscale", 2))
    )

    seen_hashes: dict[str, str] = {}
    rows = [
        inspect_shot(
            shot,
            defaults,
            root,
            canvas_size,
            seen_hashes,
            max_source_upscale,
        )
        for shot in spec["shots"]
    ]
    error_count = sum(bool(row["errors"]) for row in rows)
    warning_count = sum(len(row["warnings"]) for row in rows)
    report = {
        "schemaVersion": 1,
        "generator": "scripts/preflight_focus_assets.py",
        "spec": str(args.spec.resolve()),
        "canvas": list(canvas_size),
        "maxSourceUpscale": max_source_upscale,
        "overallStatus": (
            "blocked_by_technical_errors"
            if error_count
            else "manual_review_required"
        ),
        "manualGate": (
            "Open every original and the raw contact sheet. Record 通过, 重抓, "
            "or 淘汰 before layout or animation."
        ),
        "errorShotCount": error_count,
        "warningCount": warning_count,
        "shots": rows,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    write_contact_sheet(rows, args.contact_sheet)

    print(f"Wrote {args.report}")
    print(f"Wrote {args.contact_sheet}")
    print(
        f"overallStatus={report['overallStatus']} "
        f"errorShots={error_count} warnings={warning_count}"
    )
    raise SystemExit(1 if error_count else 0)


if __name__ == "__main__":
    main()
