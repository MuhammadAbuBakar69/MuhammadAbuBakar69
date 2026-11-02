"""Turn a photo into an ASCII portrait rendered as an SVG.

    python scripts/make_ascii_svg.py photo.jpg assets/ascii-portrait.svg

Uses only Pillow. Tweak --width for detail (40-70 looks best at 420px wide).
"""
from __future__ import annotations

import argparse
from html import escape

from PIL import Image, ImageEnhance, ImageOps

RAMP = " .`:;-=+*#%@"
BG = "#0d1117"
INK = "#39d353"


def build(src: str, out_path: str, width: int = 56, contrast: float = 1.35) -> str:
    img = Image.open(src).convert("L")

    # square-ish crop on the face-friendly centre, then downscale
    side = min(img.size)
    left = (img.width - side) // 2
    top = int((img.height - side) * 0.35)
    img = img.crop((left, top, left + side, top + side))

    rows = max(1, int(width * 0.52))
    img = img.resize((width, rows), Image.LANCZOS)
    img = ImageOps.autocontrast(img)
    img = ImageEnhance.Contrast(img).enhance(contrast)

    px = img.tobytes()  # L mode: one byte per pixel
    chars = [RAMP[min(len(RAMP) - 1, p * len(RAMP) // 256)] for p in px]

    # size the canvas to match the stats card so the README table lines up
    canvas_w, canvas_h = 410, 420
    inner = canvas_w - 32
    font_size = round(inner / (width * 0.6), 2)
    line_h = font_size * 1.08
    art_h = rows * line_h

    # shrink if the portrait would overflow the canvas
    if art_h > canvas_h - 24:
        font_size = round(font_size * (canvas_h - 24) / art_h, 2)
        line_h = font_size * 1.08
        art_h = rows * line_h

    w, h = canvas_w, canvas_h
    top_pad = (canvas_h - art_h) / 2

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
        f'role="img" aria-label="ASCII portrait">',
        f'<rect width="{w}" height="{h}" rx="12" fill="{BG}"/>',
        f'<text xml:space="preserve" font-family="ui-monospace,SFMono-Regular,Consolas,monospace" '
        f'font-size="{font_size}" fill="{INK}">',
    ]
    for r in range(rows):
        line = "".join(chars[r * width : (r + 1) * width])
        y = top_pad + (r + 1) * line_h - (line_h - font_size) / 2
        out.append(f'<tspan x="16" y="{y:.1f}">{escape(line)}</tspan>')
    out.append("</text>")
    out.append("</svg>")

    svg = "\n".join(out)
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write(svg)
    return svg


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("out")
    ap.add_argument("--width", type=int, default=56)
    ap.add_argument("--contrast", type=float, default=1.35)
    a = ap.parse_args()
    build(a.src, a.out, a.width, a.contrast)
    print(f"wrote {a.out}")
