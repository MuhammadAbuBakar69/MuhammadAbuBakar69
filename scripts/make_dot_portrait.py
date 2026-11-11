"""A halftone dot portrait, drawn as plain vectors.

The hero used to place the ASCII block as <text> rows. Inside an <img>, GitHub drops
xml:space="preserve" and textLength, so the leading spaces that position every row collapse and the
portrait turns into a loose oval smudge. Characters cannot be made reliable there.

Dots can. Each sample becomes a <circle>, so the portrait is geometry: nothing to lose in sanitising,
no font to fall back, no spacing to collapse.
"""
from __future__ import annotations

import io
import os

MODEL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "model", "haarcascade_frontalface_default.xml")


def _face_box(img):
    """Largest face as (x, y, w, h) in pixels, or None when OpenCV or the cascade is missing."""
    try:
        import cv2
        import numpy as np
    except Exception:
        return None
    if not os.path.exists(MODEL):
        return None
    cascade = cv2.CascadeClassifier(MODEL)
    if cascade.empty():
        return None
    grey = np.array(img.convert("L"))
    faces = cascade.detectMultiScale(cv2.equalizeHist(grey), scaleFactor=1.1, minNeighbors=8, minSize=(60, 60))
    if len(faces) == 0:
        return None
    x, y, w, h = max(faces, key=lambda f: int(f[2]) * int(f[3]))
    return int(x), int(y), int(w), int(h)


def _crop(img, aspect: float):
    """Square-ish crop around the face, expanded so the head is not clipped."""
    box = _face_box(img)
    w, h = img.size
    if box:
        x, y, fw, fh = box
        cx, cy = x + fw / 2, y + fh / 2
        side = fh * 1.55
    else:
        cx, cy = w / 2, h * 0.42
        side = min(w, h) * 0.9

    ch = side
    cw = side * aspect
    left = max(0, int(cx - cw / 2))
    top = max(0, int(cy - ch / 2))
    right = min(w, int(left + cw))
    bottom = min(h, int(top + ch))
    return img.crop((left, top, right, bottom))


def dot_group(image_bytes: bytes, cols: int = 50, rows: int = 45, cell: float = 8.0,
              ink: str = "#111111", accent: str = "#2f55ff") -> tuple[str, float, float]:
    """Halftone the image into circles.

    Returns (markup, width, height) in local units. Cells whose tone is nearly paper get no dot at all,
    so the background stays empty instead of grey.
    """
    from PIL import Image, ImageOps

    img = Image.open(io.BytesIO(image_bytes))
    img = ImageOps.exif_transpose(img).convert("RGB")
    img = _crop(img, cols / rows).resize((cols, rows), Image.LANCZOS).convert("L")

    values = list(img.getdata())
    lo, hi = min(values), max(values)
    span = max(1, hi - lo)

    radius = cell * 0.52
    parts: list[str] = []
    dots = images = 0
    for row in range(rows):
        for col in range(cols):
            lum = values[row * cols + col]
            tone = (lum - lo) / span  # 0 = darkest
            coverage = (1.0 - tone) ** 0.85
            if coverage < 0.10:
                continue
            r = radius * coverage
            colour = accent if coverage > 0.93 else ink
            parts.append(
                f'<circle cx="{col * cell + cell / 2:.1f}" cy="{row * cell + cell / 2:.1f}" '
                f'r="{r:.1f}" fill="{colour}"/>'
            )
            dots += 1
    images += 1
    markup = f'<g fill-opacity="0.88">{"".join(parts)}</g>'
    return markup, cols * cell, rows * cell
