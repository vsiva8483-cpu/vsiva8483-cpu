"""
Generates siva-ascii.svg — an ASCII-art portrait rendered from a source
photo. Requires a photo committed at source-photo.jpg (any reasonably
front-facing, well-lit headshot works best).

Usage:
    python scripts/generate_ascii.py
"""
import os
import sys

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE_PATH = os.path.join(ROOT, "source-photo.jpg")
OUT_PATH = os.path.join(ROOT, "siva-ascii.svg")

# Darkest -> lightest
RAMP = "@%#*+=-:. "

COLS = 90
CHAR_W = 6.2
CHAR_H = 11
BG = "#0A0E14"
FG = "#22D3EE"


def image_to_ascii(path: str, cols: int) -> list[str]:
    img = Image.open(path).convert("L")
    aspect = img.height / img.width
    rows = int(cols * aspect * 0.5)  # 0.5 corrects for character cell aspect ratio
    img = img.resize((cols, rows))
    pixels = list(img.getdata())

    lines = []
    for r in range(rows):
        row_pixels = pixels[r * cols:(r + 1) * cols]
        line = "".join(
            RAMP[min(len(RAMP) - 1, px * len(RAMP) // 256)] for px in row_pixels
        )
        lines.append(line)
    return lines


def build_svg(lines: list[str]) -> str:
    width = int(len(lines[0]) * CHAR_W) + 20 if lines else 400
    height = int(len(lines) * CHAR_H) + 20

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">',
        f'<rect width="{width}" height="{height}" fill="{BG}"/>',
        f'<text x="10" y="24" font-family="Consolas, monospace" font-size="{CHAR_H}" '
        f'fill="{FG}" xml:space="preserve">',
    ]
    for i, line in enumerate(lines):
        escaped = (
            line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        )
        parts.append(f'<tspan x="10" dy="{0 if i == 0 else CHAR_H}">{escaped}</tspan>')
    parts.append("</text>")
    parts.append("</svg>")
    return "\n".join(parts)


def main():
    if not os.path.exists(SOURCE_PATH):
        print(
            f"No source photo found at {SOURCE_PATH}. "
            "Add a photo there (named source-photo.jpg) and re-run.",
            file=sys.stderr,
        )
        sys.exit(1)
    lines = image_to_ascii(SOURCE_PATH, COLS)
    svg = build_svg(lines)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"Wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
