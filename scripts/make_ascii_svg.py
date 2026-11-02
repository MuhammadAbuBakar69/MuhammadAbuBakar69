"""Turn a photo into an ASCII portrait.

    python scripts/make_ascii_svg.py photo.jpg out.svg --width 60

The face is located with OpenCV when the cascade model is available, so the
portrait is centred on the eyes instead of on whatever happened to be in the
middle of the frame. Everything degrades gracefully to a centre crop if the
model or OpenCV is missing.
"""
from __future__ import annotations

import argparse
import io
import os
from html import escape

RAMP = " .:-=+*#%@"  # index by luminance: bright pixels get the densest glyph
MODEL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "model", "haarcascade_frontalface_default.xml")
BG = "#0d1117"
INK = "#dfe6f0"  # near-white ink; the chrome stays green


def _face_box(grey):
    """Largest detected face as (x, y, w, h), or None."""
    try:
        import cv2  # noqa: PLC0415
    except Exception:
        return None
    if not os.path.exists(MODEL):
        return None
    cascade = cv2.CascadeClassifier(MODEL)
    if cascade.empty():
        return None
    import numpy as np  # noqa: PLC0415

    arr = np.frombuffer(grey.tobytes(), dtype=np.uint8).reshape(grey.height, grey.width)
    eq = cv2.equalizeHist(arr)
    faces = cascade.detectMultiScale(eq, scaleFactor=1.1, minNeighbors=8, minSize=(60, 60))
    if len(faces) == 0:
        return None
    x, y, w, h = max(faces, key=lambda f: int(f[2]) * int(f[3]))
    return int(x), int(y), int(w), int(h)


def _vignette(cols: int, rows: int, rx: float = 0.46, ry: float = 0.60, feather: float = 0.26):
    """Soft elliptical mask: bright over the head, fading to black at the sides."""
    import numpy as np  # noqa: PLC0415
    from PIL import Image  # noqa: PLC0415

    yy, xx = np.mgrid[0:rows, 0:cols]
    cx, cy = (cols - 1) / 2.0, rows * 0.44
    radius = np.sqrt(((xx - cx) / (cols * rx)) ** 2 + ((yy - cy) / (rows * ry)) ** 2)
    mask = np.clip((1.0 - radius) / feather, 0.0, 1.0)
    return Image.fromarray((mask * 255).astype("uint8"))


def to_ascii_lines(data: bytes, cols: int = 66, rows: int = 40) -> list[str]:
    """Render image bytes as rows of monospace characters."""
    from PIL import Image, ImageEnhance, ImageFilter, ImageOps  # noqa: PLC0415

    grey = Image.open(io.BytesIO(data)).convert("L")
    side = min(grey.size)
    box = _face_box(grey)
    if box:
        x, y, w, h = box
        cx, cy = x + w // 2, y + h // 2 + int(h * 0.08)  # nudge down to keep the chin
        span = min(int(w * 1.18), side)  # tight head shot, like the reference
        left = max(0, min(cx - span // 2, grey.width - span))
        top = max(0, min(cy - span // 2, grey.height - span))
    else:
        span = side
        left, top = (grey.width - side) // 2, int((grey.height - side) * 0.25)

    tile = grey.crop((left, top, left + span, top + span)).resize((cols * 3, rows * 3), Image.LANCZOS)

    # Local contrast first (CLAHE) so eyes, nose and mouth survive a small crop,
    # then an edge-preserving smoothing pass so grain does not become noise.
    try:
        import cv2  # noqa: PLC0415
        import numpy as np  # noqa: PLC0415

        arr = np.array(tile)
        arr = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(arr)
        arr = cv2.bilateralFilter(arr, 9, 60, 60)
        tile = Image.fromarray(arr)
    except Exception:
        pass

    tile = tile.resize((cols, rows), Image.LANCZOS)

    # Vignette: fade everything outside an ellipse around the head to nothing, so
    # the photo's background never shows up as clutter down the sides.
    import numpy as np  # noqa: PLC0415

    masked = np.array(tile).astype(np.float32) * (np.array(_vignette(cols, rows)).astype(np.float32) / 255.0)
    tile = Image.fromarray(masked.astype("uint8"))
    tile = ImageOps.autocontrast(tile, cutoff=1)
    tile = tile.point(lambda v: int(255 * ((v / 255) ** 1.0)))
    tile = tile.filter(ImageFilter.UnsharpMask(radius=1.5, percent=150, threshold=2))
    tile = ImageEnhance.Contrast(tile).enhance(1.05)

    pixels = tile.tobytes()
    return ["".join(RAMP[min(9, p * 10 // 256)] for p in pixels[r * cols : (r + 1) * cols]) for r in range(rows)]


def render(lines: list[str], out_path: str) -> str:
    """Standalone SVG of the portrait (the README uses cards.render_portrait)."""
    cols = max((len(line) for line in lines), default=1)
    rows = len(lines) or 1
    font = round(min(11.0, 380 / cols / 0.6), 2)
    line_h = font * 1.08
    w, h = round(cols * font * 0.6) + 32, round(rows * line_h) + 32
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
        f'role="img" aria-label="ASCII portrait">',
        f'<rect width="{w}" height="{h}" rx="12" fill="{BG}"/>',
        f'<text xml:space="preserve" font-family="ui-monospace,SFMono-Regular,Consolas,monospace" '
        f'font-size="{font}" fill="{INK}">',
    ]
    for r, line in enumerate(lines):
        y = 16 + (r + 1) * line_h - (line_h - font) / 2
        out.append(f'<tspan x="16" y="{y:.1f}">{escape(line)}</tspan>')
    out.append("</text></svg>")
    svg = "\n".join(out)
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write(svg)
    return svg


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("image")
    ap.add_argument("out")
    ap.add_argument("--width", type=int, default=60)
    ap.add_argument("--height", type=int, default=0, help="defaults to width * 0.6 for square pixels")
    a = ap.parse_args()
    rows = a.height or max(1, round(a.width * 0.6))
    lines = to_ascii_lines(open(a.image, "rb").read(), a.width, rows)
    render(lines, a.out)
    print(f"wrote {a.out}")


if __name__ == "__main__":
    main()
