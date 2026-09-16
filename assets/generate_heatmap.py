"""
Generates contrib-heatmap.svg — a hand-rendered contribution heatmap
(not a third-party embed) built from the GitHub GraphQL API.

Requires an environment variable GH_TOKEN with a token that has
'read:user' scope (a classic PAT, or the default GITHUB_TOKEN works
for public contribution data on GitHub-hosted runners in most cases).

Usage:
    GH_TOKEN=xxxx python scripts/generate_heatmap.py
"""
import json
import os
import sys
from datetime import datetime, timedelta, timezone

import requests

USERNAME = "vsiva8483-cpu"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_PATH = os.path.join(ROOT, "contrib-heatmap.svg")

BG = "#0A0E14"
BORDER = "#1E293B"
TEXT = "#94A3B8"
LEVELS = ["#11151C", "#0E4B4F", "#0F766E", "#14B8A6", "#22D3EE"]

QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays {
            date
            contributionCount
          }
        }
      }
    }
  }
}
"""


def fetch_calendar(token: str) -> dict:
    resp = requests.post(
        "https://api.github.com/graphql",
        json={"query": QUERY, "variables": {"login": USERNAME}},
        headers={"Authorization": f"bearer {token}"},
        timeout=30,
    )
    resp.raise_for_status()
    payload = resp.json()
    if "errors" in payload:
        raise RuntimeError(payload["errors"])
    return payload["data"]["user"]["contributionsCollection"]["contributionCalendar"]


def level_for(count: int, max_count: int) -> int:
    if count == 0 or max_count == 0:
        return 0
    ratio = count / max_count
    if ratio > 0.75:
        return 4
    if ratio > 0.5:
        return 3
    if ratio > 0.25:
        return 2
    return 1


def build_svg(calendar: dict) -> str:
    weeks = calendar["weeks"]
    total = calendar["totalContributions"]
    max_count = max(
        (day["contributionCount"] for week in weeks for day in week["contributionDays"]),
        default=0,
    )

    cell = 11
    gap = 3
    left_pad = 20
    top_pad = 34
    width = left_pad + len(weeks) * (cell + gap) + 20
    height = top_pad + 7 * (cell + gap) + 20

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" font-family="JetBrains Mono, Consolas, monospace">',
        f'<rect width="{width}" height="{height}" rx="10" fill="{BG}"/>',
        f'<rect x="1" y="1" width="{width-2}" height="{height-2}" rx="9" fill="none" stroke="{BORDER}"/>',
        f'<text x="{left_pad}" y="20" font-size="12" fill="{TEXT}">'
        f'{total} contributions in the last year</text>',
    ]

    for wi, week in enumerate(weeks):
        for di, day in enumerate(week["contributionDays"]):
            lvl = level_for(day["contributionCount"], max_count)
            x = left_pad + wi * (cell + gap)
            y = top_pad + di * (cell + gap)
            parts.append(
                f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="2" '
                f'fill="{LEVELS[lvl]}"><title>{day["date"]}: {day["contributionCount"]}</title></rect>'
            )

    parts.append("</svg>")
    return "\n".join(parts)


def main():
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not token:
        print("No GH_TOKEN / GITHUB_TOKEN set — skipping heatmap generation.", file=sys.stderr)
        sys.exit(0)
    try:
        calendar = fetch_calendar(token)
    except Exception as exc:  # noqa: BLE001
        print(f"Failed to fetch contribution data: {exc}", file=sys.stderr)
        sys.exit(1)
    svg = build_svg(calendar)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"Wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
