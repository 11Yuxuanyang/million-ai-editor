#!/usr/bin/env python3
"""Generate editorial full-page focus layouts from OCR word boxes."""

from __future__ import annotations

import argparse
import csv
import difflib
import io
import json
import math
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont


@dataclass(frozen=True)
class Word:
    text: str
    normalized: str
    confidence: float
    left: int
    top: int
    width: int
    height: int
    block: int
    paragraph: int
    line: int

    @property
    def right(self) -> int:
        return self.left + self.width

    @property
    def bottom(self) -> int:
        return self.top + self.height


def normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def union_box(words: list[Word]) -> tuple[int, int, int, int]:
    return (
        min(word.left for word in words),
        min(word.top for word in words),
        max(word.right for word in words),
        max(word.bottom for word in words),
    )


def run_ocr(image_path: Path, language: str, psm: int) -> list[Word]:
    if not shutil.which("tesseract"):
        raise RuntimeError("Tesseract is required but was not found in PATH")
    result = subprocess.run(
        [
            "tesseract",
            str(image_path),
            "stdout",
            "--psm",
            str(psm),
            "-l",
            language,
            "tsv",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    words: list[Word] = []
    for row in csv.DictReader(io.StringIO(result.stdout), delimiter="\t"):
        text = (row.get("text") or "").strip()
        normalized = normalize(text)
        try:
            confidence = float(row.get("conf") or -1)
        except ValueError:
            confidence = -1
        if not normalized or confidence < 18:
            continue
        words.append(
            Word(
                text=text,
                normalized=normalized,
                confidence=confidence,
                left=int(row["left"]),
                top=int(row["top"]),
                width=int(row["width"]),
                height=int(row["height"]),
                block=int(row["block_num"]),
                paragraph=int(row["par_num"]),
                line=int(row["line_num"]),
            )
        )
    return words


def candidate_spans(words: list[Word], query_size: int) -> list[list[Word]]:
    spans: list[list[Word]] = []
    lines: dict[tuple[int, int, int], list[Word]] = {}
    for word in words:
        lines.setdefault((word.block, word.paragraph, word.line), []).append(word)

    sizes = range(max(1, query_size - 1), query_size + 3)
    for line_words in lines.values():
        for size in sizes:
            for start in range(0, len(line_words) - size + 1):
                spans.append(line_words[start : start + size])

    for start in range(len(words)):
        for size in sizes:
            span = words[start : start + size]
            if len(span) != size:
                continue
            box = union_box(span)
            median_height = sorted(word.height for word in span)[len(span) // 2]
            if box[3] - box[1] <= median_height * 3.4:
                spans.append(span)
    return spans


def find_phrase(words: list[Word], queries: list[str]) -> tuple[list[Word], str, float]:
    best: tuple[list[Word], str, float] | None = None
    for query in queries:
        normalized_query = normalize(query)
        query_tokens = normalized_query.split()
        for span in candidate_spans(words, len(query_tokens)):
            span_text = " ".join(word.normalized for word in span)
            ratio = difflib.SequenceMatcher(None, normalized_query, span_text).ratio()
            token_overlap = len(set(query_tokens) & set(span_text.split())) / max(
                1, len(set(query_tokens))
            )
            confidence = sum(word.confidence for word in span) / len(span) / 100
            box = union_box(span)
            area_bonus = min(
                0.08,
                math.log1p((box[2] - box[0]) * (box[3] - box[1])) / 180,
            )
            score = ratio * 0.62 + token_overlap * 0.28 + confidence * 0.10 + area_bonus
            if best is None or score > best[2]:
                best = (span, query, score)
    if best is None or best[2] < 0.54:
        sample = " ".join(word.text for word in words[:80])
        raise RuntimeError(
            f"No reliable OCR match. queries={queries!r}; best={best}; "
            f"OCR sample={sample!r}"
        )
    return best


def derive_layout(
    image_size: tuple[int, int],
    box: tuple[int, int, int, int],
    canvas_size: tuple[int, int],
    anchor_pct: tuple[float, float],
    target_fill: tuple[float, float],
    max_zoom: float,
    focus_radius_pct: tuple[float, float],
    center_priority: bool,
) -> dict:
    image_width, image_height = image_size
    canvas_width, canvas_height = canvas_size
    box_width = max(1, box[2] - box[0])
    box_height = max(1, box[3] - box[1])
    source_center_x = (box[0] + box[2]) / 2
    source_center_y = (box[1] + box[3]) / 2
    desired_x = canvas_width * anchor_pct[0]
    desired_y = canvas_height * anchor_pct[1]

    cover_scale = max(canvas_width / image_width, canvas_height / image_height)
    target_scale = min(
        canvas_width * target_fill[0] / box_width,
        canvas_height * target_fill[1] / box_height,
    )
    centering_scale = cover_scale
    if center_priority:
        centering_scale = max(
            cover_scale,
            desired_x / max(1, source_center_x),
            (canvas_width - desired_x) / max(1, image_width - source_center_x),
            desired_y / max(1, source_center_y),
            (canvas_height - desired_y) / max(1, image_height - source_center_y),
        )

    scale = clamp(
        max(target_scale, centering_scale),
        cover_scale,
        cover_scale * max_zoom,
    )
    scaled_width = image_width * scale
    scaled_height = image_height * scale
    offset_x = clamp(
        desired_x - source_center_x * scale,
        canvas_width - scaled_width,
        0,
    )
    offset_y = clamp(
        desired_y - source_center_y * scale,
        canvas_height - scaled_height,
        0,
    )
    actual_x_px = source_center_x * scale + offset_x
    actual_y_px = source_center_y * scale + offset_y
    actual_x = actual_x_px / canvas_width * 100
    actual_y = actual_y_px / canvas_height * 100

    return {
        "scale": scale,
        "scaledSizePx": [round(scaled_width, 2), round(scaled_height, 2)],
        "offsetPx": [round(offset_x, 2), round(offset_y, 2)],
        "focusPct": [round(actual_x, 3), round(actual_y, 3)],
        "anchorPct": [round(anchor_pct[0] * 100, 3), round(anchor_pct[1] * 100, 3)],
        "centerErrorPx": [
            round(actual_x_px - desired_x, 2),
            round(actual_y_px - desired_y, 2),
        ],
        "focusRadiusPct": list(focus_radius_pct),
        "css": {
            "--page-size": f"{scaled_width:.2f}px {scaled_height:.2f}px",
            "--page-position": f"{offset_x:.2f}px {offset_y:.2f}px",
            "--focus-x": f"{actual_x:.3f}%",
            "--focus-y": f"{actual_y:.3f}%",
            "--focus-w": f"{focus_radius_pct[0]:.3f}%",
            "--focus-h": f"{focus_radius_pct[1]:.3f}%",
        },
    }


def render_preview(
    image_path: Path,
    destination: Path,
    layout: dict,
    box: tuple[int, int, int, int],
    background_blur_px: float,
) -> None:
    canvas_width, canvas_height = layout["canvasSize"]
    source = Image.open(image_path).convert("RGB")
    scaled_width, scaled_height = (round(value) for value in layout["scaledSizePx"])
    offset_x, offset_y = (round(value) for value in layout["offsetPx"])
    resized = source.resize((scaled_width, scaled_height), Image.Resampling.LANCZOS)

    sharp = Image.new("RGB", (canvas_width, canvas_height), (8, 8, 8))
    sharp.paste(resized, (offset_x, offset_y))
    base = sharp.filter(ImageFilter.GaussianBlur(radius=background_blur_px))

    focus_x = layout["focusPct"][0] / 100 * canvas_width
    focus_y = layout["focusPct"][1] / 100 * canvas_height
    radius_x = layout["focusRadiusPct"][0] / 100 * canvas_width
    radius_y = layout["focusRadiusPct"][1] / 100 * canvas_height

    mask = Image.new("L", (canvas_width, canvas_height), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.ellipse(
        (
            focus_x - radius_x,
            focus_y - radius_y,
            focus_x + radius_x,
            focus_y + radius_y,
        ),
        fill=255,
    )
    mask = mask.filter(ImageFilter.GaussianBlur(radius=70))
    composite = Image.composite(sharp, base, mask)

    draw = ImageDraw.Draw(composite)
    source_box = (
        box[0] * layout["scale"] + offset_x,
        box[1] * layout["scale"] + offset_y,
        box[2] * layout["scale"] + offset_x,
        box[3] * layout["scale"] + offset_y,
    )
    draw.rectangle(source_box, outline=(61, 220, 255), width=5)
    draw.ellipse(
        (
            focus_x - radius_x,
            focus_y - radius_y,
            focus_x + radius_x,
            focus_y + radius_y,
        ),
        outline=(183, 255, 68),
        width=5,
    )
    font = ImageFont.load_default()
    draw.text(
        (32, 28),
        f"{layout['id']} OCR={layout['matchedText']} "
        f"score={layout['matchScore']:.3f}",
        fill=(255, 255, 255),
        stroke_width=3,
        stroke_fill=(0, 0, 0),
        font=font,
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    composite.save(destination, quality=94)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--preview-dir", required=True, type=Path)
    parser.add_argument("--css-output", type=Path)
    args = parser.parse_args()

    spec = json.loads(args.spec.read_text())
    root = args.spec.resolve().parent
    defaults = spec.get("defaults", {})
    canvas_size = tuple(spec.get("canvas", [1920, 1080]))
    results = []

    for shot in spec["shots"]:
        image_path = (root / shot["image"]).resolve()
        words = run_ocr(
            image_path,
            shot.get("language", defaults.get("language", "eng")),
            int(shot.get("psm", defaults.get("psm", 11))),
        )
        query_value = shot["query"]
        queries = [query_value] if isinstance(query_value, str) else query_value
        matched_words, matched_query, match_score = find_phrase(words, queries)
        box = union_box(matched_words)
        focus_radius = tuple(
            shot.get("focusRadiusPct", defaults.get("focusRadiusPct", [42, 25]))
        )
        layout = derive_layout(
            Image.open(image_path).size,
            box,
            canvas_size,
            tuple(shot.get("anchorPct", defaults.get("anchorPct", [0.5, 0.5]))),
            tuple(shot.get("targetFill", defaults.get("targetFill", [0.58, 0.22]))),
            float(shot.get("maxZoom", defaults.get("maxZoom", 10))),
            focus_radius,
            bool(shot.get("centerPriority", defaults.get("centerPriority", True))),
        )
        layout.update(
            {
                "id": shot["id"],
                "image": str(image_path),
                "query": matched_query,
                "matchedText": " ".join(word.text for word in matched_words),
                "matchScore": round(min(1.0, match_score), 4),
                "ocrBoxPx": list(box),
                "canvasSize": list(canvas_size),
                "backgroundBlurPx": float(
                    shot.get(
                        "backgroundBlurPx",
                        defaults.get("backgroundBlurPx", 14),
                    )
                ),
            }
        )
        results.append(layout)
        render_preview(
            image_path,
            args.preview_dir / f"{shot['id']}.jpg",
            layout,
            box,
            layout["backgroundBlurPx"],
        )

    output = {
        "schemaVersion": 1,
        "generator": "scripts/derive_focus_layouts.py",
        "method": "Tesseract OCR word boxes + deterministic full-page fit",
        "canvas": list(canvas_size),
        "shots": results,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n")

    if args.css_output:
        lines = ["/* Generated. Do not hand-edit. */"]
        for layout in results:
            lines.append(f"#{layout['id']} {{")
            for name, value in layout["css"].items():
                lines.append(f"  {name}: {value};")
            lines.append(
                f"  --background-blur: {layout['backgroundBlurPx']:.3f}px;"
            )
            lines.append("}")
        args.css_output.parent.mkdir(parents=True, exist_ok=True)
        args.css_output.write_text("\n".join(lines) + "\n")

    print(f"Wrote {args.output}")
    if args.css_output:
        print(f"Wrote {args.css_output}")
    print(f"Wrote {len(results)} annotated previews to {args.preview_dir}")


if __name__ == "__main__":
    main()
