"""Assert that the two profile panes are actually aligned.

Design drift in an SVG is invisible until someone screenshots it and notices the halves sit at
different heights. These checks make the geometry a build failure instead of a typo somebody spots
three weeks later:

  * identical canvas, title bar and footer baselines across both panes
  * one gutter: no text starts left of PAD or ends right of W - PAD
  * the six stat tiles sit on an exact two-column grid with equal widths
  * the portrait block is centred inside the card, not stuck to the left edge
  * the prompt is the lowercase login in both panes
  * no text below a legibility floor

    python scripts/verify_layout.py assets/stats.svg assets/portrait.svg --login someone
"""

from __future__ import annotations

import argparse
import re
from html import unescape
import sys

PAD = 18
W, H = 460, 548
LEGIBLE_MIN = 9.0

TEXT_RE = re.compile(r"<text\b([^>]*)>(.*?)</text>", re.S)
TSPAN_RE = re.compile(r'<tspan\b([^>]*)>(.*?)</tspan>', re.S)
ATTR_RE = re.compile(r'([a-zA-Z:-]+)="([^"]*)"')
RECT_RE = re.compile(r'<rect\b([^>]*)/>')


def _attrs(blob: str) -> dict[str, str]:
    return dict(ATTR_RE.findall(blob))


def _texts(svg: str) -> list[tuple[dict[str, str], str]]:
    """Every drawable run.

    A <text> that wraps <tspan> rows is an ASCII block, not one string: flattening it would treat 66
    columns as a single 14,000px word and every gutter check would fire. Each tspan inherits the
    parent's font-size and is measured on its own.
    """
    runs: list[tuple[dict[str, str], str]] = []
    for parent_attrs, body in TEXT_RE.findall(svg):
        parent = _attrs(parent_attrs)
        rows = TSPAN_RE.findall(body)
        if rows:
            for row_attrs, row_body in rows:
                attrs = {**parent, **_attrs(row_attrs)}
                runs.append((attrs, row_body))
        else:
            runs.append((parent, body))
    return runs


def _plain(body: str) -> str:
    """Text content with entities decoded: '&#8594;' is one glyph, not eight characters."""
    return unescape(re.sub(r"<[^>]+>", "", body)).strip()


def _untagged(body: str) -> str:
    """Content without stripping: leading spaces are part of an ASCII column count."""
    return unescape(re.sub(r"<[^>]+>", "", body))


def _advance(attrs: dict[str, str], size: float) -> float:
    """Average advance width per character for the family in play.

    Monospace is exactly 0.6em. Geist and Instrument Serif are proportional and run noticeably
    narrower, and measuring them at 0.6em produced false "overflow" failures on text that fits.
    """
    family = (attrs.get("font-family") or "").lower()
    if "serif" in family and "mono" not in family:
        return 0.45 * size
    if "geist" in family or "system-ui" in family or "sans" in family:
        return 0.53 * size
    return 0.6 * size


def _canvas(svg: str, path: str) -> tuple[float, float]:
    m = re.search(r'width="([\d.]+)" height="([\d.]+)"', svg)
    if not m:
        raise AssertionError(f"{path}: no width/height on the root <svg>")
    return float(m.group(1)), float(m.group(2))


CARDS = {
    # The paper cards bake their own padding into the canvas, so the gutter check here is 0 and the
    # meaningful assertions are size, legibility and horizontal containment.
    "hero.svg": (880.0, 432, 0),
    "activity.svg": (880.0, 352, 0),
    "heatmap.svg": (880.0, 257, 0),
    "title-building-light.svg": (880.0, 64, 0),
    "title-building-dark.svg": (880.0, 64, 0),
    "focus-build.svg": (293.333, 222, 0),
    "focus-automate.svg": (293.333, 222, 0),
    "focus-write.svg": (293.333, 222, 0),
    "repo-threadmind-ai.svg": (293.333, 188, 0),
    "repo-jobpilot.svg": (293.333, 188, 0),
    "repo-otto.svg": (293.333, 188, 0),
}

PANELS = {"banner.svg": (1280, 300), "achievements.svg": (1280, 312), "badges.svg": (1280, 324)}


def _panel(name: str, svg: str, login: str) -> list[str]:
    """Wide panels: same rules as the cards, at their own canvas size."""
    problems: list[str] = []
    want_w, want_h = PANELS[name]
    w, h = _canvas(svg, name)
    if (w, h) != (want_w, want_h):
        problems.append(f"{name}: canvas {w}x{h}, expected {want_w}x{want_h}")
    if not svg.rstrip().endswith("</svg>"):
        problems.append(f"{name}: truncated file (no closing </svg>)")

    runs = _texts(svg)
    prompt = re.compile(rf"^{re.escape(login.lower())}@github: ~ \$ \./[a-z]+\.sh( [a-z-]+)*$")
    if not any(prompt.match(_plain(body)) for attrs, body in runs):
        problems.append(f"{name}: title bar does not carry the standard prompt")

    # Both wide panels are read at 1:1 on a desktop README, so they get the same 28px gutter.
    left, right = 28, want_w - 28
    for attrs, body in runs:
        text = _plain(body)
        if not text or "x" not in attrs or not attrs.get("font-size"):
            continue
        size = float(attrs["font-size"])
        # The hero's ASCII portrait is 7.2px on purpose: it is art scaled to a fixed textLength,
        # not prose. Prose keeps the 9px floor.
        if size < 9 and "textLength" not in attrs:
            problems.append(f"{name}: '{text[:28]}' is {size}px, below the 9px floor")
        x = float(attrs["x"])
        span = len(text) * _advance(attrs, size)
        anchor = attrs.get("text-anchor", "start")
        start = x if anchor == "start" else (x - span if anchor == "end" else x - span / 2)
        if start < left - 0.6 or start + span > right + 0.6:
            problems.append(f"{name}: '{text[:28]}' breaks the {left}px gutter")
    return problems


def _card(name: str, svg: str) -> list[str]:
    """README cards: no terminal chrome, so no prompt rule - size, legibility and gutter only."""
    problems: list[str] = []
    want_w, want_h, pad = CARDS[name]
    w, h = _canvas(svg, name)
    if abs(w - want_w) > 0.01 or h != want_h:
        problems.append(f"cards/{name}: canvas {w}x{h}, expected {want_w}x{want_h}")
    if not svg.rstrip().endswith("</svg>"):
        problems.append(f"cards/{name}: truncated file (no closing </svg>)")
    # count_up() emits one <text> per animation frame and toggles their opacity, so those runs sit
    # at the same coordinates on purpose. They are excluded from the collision check.
    seen: set[tuple[str, str, str]] = set()
    runs = []
    for a, b in _texts(svg):
        text = _plain(b)
        if not text:
            continue
        key = (a.get("x", ""), a.get("y", ""), text)
        if key in seen:  # duplicate of an animation frame, already counted once
            continue
        seen.add(key)
        runs.append((a, text))
    # Two lines sharing a column must not sit on the same baseline. This is the check that would have
    # caught the repo cards printing five lines of copy on top of the meta line.
    for i in range(len(runs)):
        for j in range(i + 1, len(runs)):
            (a1, t1), (a2, t2) = runs[i], runs[j]
            if "y" not in a1 or "y" not in a2 or "x" not in a1 or "x" not in a2:
                continue
            if abs(float(a1["x"]) - float(a2["x"])) > 2:
                continue
            # Each run owns a band around its baseline: ascent above, descender below. Overlap is
            # when two bands intersect, which is stricter and fairer than comparing baselines - a
            # 40px number with its 13px caption underneath is 24px apart and fine.
            def band(attrs) -> tuple[float, float]:
                size = float(attrs.get("font-size", 0))
                y = float(attrs["y"])
                # Display sizes are set tight - 96px lines 92 apart is deliberate. Body sizes get a
                # fuller box, which is where collisions actually happen.
                up, down = (0.62, 0.10) if size >= 24 else (0.78, 0.22)
                return y - up * size, y + down * size

            top1, bot1 = band(a1)
            top2, bot2 = band(a2)
            if top2 < bot1 - 0.5 and top1 < bot2 - 0.5:
                problems.append(
                    f"cards/{name}: '{t1[:22]}' and '{t2[:22]}' collide on the same baseline column"
                )

    for attrs, body in _texts(svg):
        text = _plain(body)
        if not text or "x" not in attrs or not attrs.get("font-size"):
            continue
        size = float(attrs["font-size"])
        # The hero's ASCII portrait is 7.2px on purpose: it is art scaled to a fixed textLength,
        # not prose. Prose keeps the 9px floor.
        if size < 9 and "textLength" not in attrs:
            problems.append(f"cards/{name}: '{text[:28]}' is {size}px, below the 9px floor")
        x = float(attrs["x"])
        span = len(text) * _advance(attrs, size)
        anchor = attrs.get("text-anchor", "start")
        start = x if anchor == "start" else (x - span if anchor == "end" else x - span / 2)
        if start < pad - 1.0 or start + span > want_w - pad + 1.0:
            problems.append(f"cards/{name}: '{text[:28]}' breaks the {pad}px gutter")
    return problems


def verify(
    stats_svg: str,
    portrait_svg: str,
    login: str,
    panels: dict[str, str] | None = None,
    cards_set: dict[str, str] | None = None,
) -> list[str]:
    problems: list[str] = []
    prompt = re.compile(rf"^{re.escape(login.lower())}@github: ~ \$ \./[a-z]+\.sh( [a-z-]+)*$")

    for path, svg in (("stats.svg", stats_svg), ("portrait.svg", portrait_svg)):
        w, h = _canvas(svg, path)
        if (w, h) != (W, H):
            problems.append(f"{path}: canvas {w}x{h}, expected {W}x{H} — the panes will not line up")
        if not svg.rstrip().endswith("</svg>"):
            problems.append(f"{path}: truncated file (no closing </svg>)")

        texts = _texts(svg)
        # title bar prompt
        cmds = [_plain(b) for a, b in texts if "@github: ~ $" in _plain(b)]
        if len(cmds) != 1:
            problems.append(f"{path}: expected exactly one prompt in the title bar, found {len(cmds)}")
        for cmd in cmds:
            if not prompt.match(cmd):
                problems.append(f"{path}: prompt {cmd!r} is not `{login.lower()}@github: ~ $ ./x.sh`")

        # gutter discipline
        for a, body in texts:
            size = float(a.get("font-size", "0"))
            txt = _plain(body)
            if not txt:
                continue
            if size < LEGIBLE_MIN:
                problems.append(f"{path}: {txt[:28]!r} at {size}px is below the {LEGIBLE_MIN}px floor")
            x = float(a.get("x", "0"))
            anchor = a.get("text-anchor", "start")
            width = len(txt) * size * 0.6  # monospace advance
            left = x - width / 2 if anchor == "middle" else (x - width if anchor == "end" else x)
            right = left + width
            if left < PAD - 1.5:
                problems.append(f"{path}: {txt[:28]!r} starts at {left:.1f}, inside the {PAD}px gutter")
            if right > W - PAD + 1.5:
                problems.append(f"{path}: {txt[:28]!r} ends at {right:.1f}, past the right gutter")

        # shared footer band
        footer_y = [float(a["y"]) for a, b in texts if "auto-refreshed daily" in _plain(b)]
        if footer_y != [H - 14]:
            problems.append(f"{path}: footer baseline {footer_y}, expected [{H - 14}]")
        if "built " not in " ".join(_plain(b) for _, b in texts):
            problems.append(f"{path}: footer is missing the build date")

    # ---------------------------------------------------------------- pane-to-pane
    left_footer = [a["y"] for a, b in _texts(stats_svg) if "auto-refreshed daily" in _plain(b)]
    right_footer = [a["y"] for a, b in _texts(portrait_svg) if "auto-refreshed daily" in _plain(b)]
    if left_footer != right_footer:
        problems.append(f"footer baselines differ between panes: {left_footer} vs {right_footer}")

    # ---------------------------------------------------------------- stat grid
    tiles = [_attrs(m.group(1)) for m in RECT_RE.finditer(stats_svg)]
    tiles = [t for t in tiles if t.get("width") == str((W - 2 * PAD - 10) // 2) and t.get("height") == "66"]
    if len(tiles) != 6:
        problems.append(f"expected 6 stat tiles, found {len(tiles)}")
    else:
        xs = sorted({float(t["x"]) for t in tiles})
        if xs != [PAD, PAD + (W - 2 * PAD - 10) // 2 + 10]:
            problems.append(f"tile columns are not on the two-column grid: {xs}")
        ys = sorted({float(t["y"]) for t in tiles})
        if len(ys) != 3 or any(b - a != 74 for a, b in zip(ys, ys[1:])):
            problems.append(f"tile rows are not on a 74px rhythm: {ys}")

    # ---------------------------------------------------------------- portrait block
    # The art is the x value shared by the most rows; footer/whoami lines also carry an x and would
    # otherwise be mistaken for the portrait block.
    rows_by_x: dict[float, list[tuple[dict[str, str], str]]] = {}
    for attrs, body in _texts(portrait_svg):
        if attrs.get("x") and len(_plain(body)) >= 20:
            rows_by_x.setdefault(float(attrs["x"]), []).append((attrs, body))
    if rows_by_x:
        left, art_rows = max(rows_by_x.items(), key=lambda kv: len(kv[1]))
        font = float(art_rows[0][0]["font-size"])
        cols = max(len(_untagged(b)) for _, b in art_rows)
        art_w = cols * font * 0.6
        # every tspan shares one x; the block must be centred within the gutter box
        if abs((left - PAD) - ((W - 2 * PAD) - art_w) / 2) > 2.0:
            problems.append(
                f"portrait block is not centred: starts at {left:.1f}, "
                f"centre would be {PAD + ((W - 2 * PAD) - art_w) / 2:.1f}"
            )
        if left + art_w > W - PAD + 1.5:
            problems.append(f"portrait block overflows the right gutter by {left + art_w - (W - PAD):.1f}px")

    for name, svg in (panels or {}).items():
        problems.extend(_panel(name, svg, login))
    for name, svg in (cards_set or {}).items():
        problems.extend(_card(name, svg))

    return problems


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("stats")
    ap.add_argument("portrait")
    ap.add_argument("--login", required=True)
    ap.add_argument("--banner", default="")
    ap.add_argument("--achievements", default="")
    a = ap.parse_args()
    panels = {}
    for name, path in (("banner.svg", a.banner), ("achievements.svg", a.achievements)):
        if path:
            panels[name] = open(path, encoding="utf-8").read()
    problems = verify(
        open(a.stats, encoding="utf-8").read(),
        open(a.portrait, encoding="utf-8").read(),
        a.login,
        panels,
    )
    if problems:
        print(f"layout check failed ({len(problems)} problems):", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        return 1
    print("ok: layout verified — panes aligned, gutters clean, grid exact")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
