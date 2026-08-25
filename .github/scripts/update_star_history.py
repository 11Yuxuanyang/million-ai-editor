#!/usr/bin/env python3
"""Render a repository-owned SVG chart from GitHub stargazer timestamps."""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import os
import urllib.request
from collections import Counter
from pathlib import Path


API = "https://api.github.com"


def request_json(path: str, token: str) -> object:
    request = urllib.request.Request(
        f"{API}{path}",
        headers={
            "Accept": "application/vnd.github.star+json",
            "Authorization": f"Bearer {token}",
            "User-Agent": "million-ai-editor-star-history",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def fetch_history(repo: str, token: str) -> tuple[dt.date, list[dt.date]]:
    metadata = request_json(f"/repos/{repo}", token)
    if not isinstance(metadata, dict):
        raise RuntimeError("Unexpected repository metadata response")

    created = dt.datetime.fromisoformat(metadata["created_at"].replace("Z", "+00:00")).date()
    stars: list[dt.date] = []
    page = 1
    while True:
        entries = request_json(f"/repos/{repo}/stargazers?per_page=100&page={page}", token)
        if not isinstance(entries, list):
            raise RuntimeError("Unexpected stargazer response")
        for entry in entries:
            timestamp = entry.get("starred_at") if isinstance(entry, dict) else None
            if timestamp:
                stars.append(dt.datetime.fromisoformat(timestamp.replace("Z", "+00:00")).date())
        if len(entries) < 100:
            break
        page += 1
    return created, sorted(stars)


def render_svg(repo: str, created: dt.date, stars: list[dt.date]) -> str:
    today = dt.datetime.now(dt.timezone.utc).date()
    data_end = max(today, created)
    axis_end = max(data_end, created + dt.timedelta(days=1))
    counts = Counter(stars)
    dated_counts: list[tuple[dt.date, int]] = [(created, 0)]
    running = 0
    for day in sorted(counts):
        running += counts[day]
        dated_counts.append((day, running))
    if dated_counts[-1][0] != axis_end:
        dated_counts.append((axis_end, running))

    width, height = 960, 360
    left, right, top, bottom = 74, 34, 78, 58
    plot_width = width - left - right
    plot_height = height - top - bottom
    total_days = max(1, (axis_end - created).days)
    max_stars = max(1, running)

    def x_for(day: dt.date) -> float:
        return left + ((day - created).days / total_days) * plot_width

    def y_for(value: int) -> float:
        return top + plot_height - (value / max_stars) * plot_height

    points = " ".join(f"{x_for(day):.1f},{y_for(value):.1f}" for day, value in dated_counts)
    safe_repo = html.escape(repo)
    if max_stars <= 4:
        tick_values = list(range(max_stars + 1))
    else:
        tick_values = sorted({round(max_stars * index / 4) for index in range(5)})

    grid = []
    labels = []
    for value in tick_values:
        y = y_for(value)
        grid.append(f'<line x1="{left}" y1="{y:.1f}" x2="{width-right}" y2="{y:.1f}" class="grid"/>')
        labels.append(f'<text x="{left-16}" y="{y+5:.1f}" text-anchor="end" class="axis">{value}</text>')

    end_x, end_y = x_for(axis_end), y_for(running)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">
  <title id="title">{safe_repo} GitHub Star Trend</title>
  <desc id="desc">Cumulative GitHub stars from {created.isoformat()} to {data_end.isoformat()}: {running}</desc>
  <style>
    .title {{ fill: #f5f5f2; font: 700 24px -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }}
    .meta {{ fill: #9b9b96; font: 14px -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }}
    .axis {{ fill: #85857f; font: 12px -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }}
    .grid {{ stroke: #30302d; stroke-width: 1; }}
  </style>
  <rect width="100%" height="100%" rx="8" fill="#11110f"/>
  <text x="{left}" y="38" class="title">Star 趋势</text>
  <text x="{left}" y="61" class="meta">{safe_repo}</text>
  <text x="{width-right}" y="38" text-anchor="end" class="title">{running} ★</text>
  {''.join(grid)}
  {''.join(labels)}
  <polyline points="{points}" fill="none" stroke="#d8ff00" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>
  <circle cx="{end_x:.1f}" cy="{end_y:.1f}" r="6" fill="#d8ff00"/>
  <text x="{left}" y="{height-24}" class="axis">{created.isoformat()}</text>
  <text x="{width-right}" y="{height-24}" text-anchor="end" class="axis">{data_end.isoformat()}</text>
  <text x="{width/2:.1f}" y="{height-24}" text-anchor="middle" class="axis">Updated daily by GitHub Actions</text>
</svg>
'''


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise SystemExit("GITHUB_TOKEN is required")
    created, stars = fetch_history(args.repo, token)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render_svg(args.repo, created, stars), encoding="utf-8")


if __name__ == "__main__":
    main()
