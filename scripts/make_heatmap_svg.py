"""Render a GitHub-style contribution heatmap to a standalone SVG."""
from __future__ import annotations

from datetime import date, timedelta
from html import escape

import cards

PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]
BG = "#0d1117"
FG = "#7d8590"
ACCENT = "#39d353"
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

CELL, GAP = 12, 3
PAD_LEFT, PAD_TOP, PAD_RIGHT, PAD_BOTTOM = 34, 62, 16, 38


def _level(count: int, top: int) -> int:
    if count <= 0:
        return 0
    if top <= 1:
        return 4
    ratio = count / top
    if ratio > 0.66:
        return 4
    if ratio > 0.33:
        return 3
    if ratio > 0.12:
        return 2
    return 1


def render(days: dict[date, int], user: str, out_path: str) -> str:
    days = dict(sorted(days.items()))
    if not days:
        raise SystemExit("no contribution days to render")

    # pad so the first column starts on a Sunday
    first = min(days)
    lead = (first.weekday() + 1) % 7  # Monday=0 -> Sunday-based offset
    start = first - timedelta(days=lead)
    last = max(days)
    trail = 6 - ((last.weekday() + 1) % 7)
    end = last + timedelta(days=trail)

    all_days: list[date] = []
    d = start
    while d <= end:
        all_days.append(d)
        d += timedelta(days=1)
    weeks = [all_days[i : i + 7] for i in range(0, len(all_days), 7)]

    peak = max(days.values()) if days else 1
    total = sum(days.values())

    width = PAD_LEFT + len(weeks) * (CELL + GAP) + PAD_RIGHT
    height = PAD_TOP + 7 * (CELL + GAP) + PAD_BOTTOM

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" '
        f'aria-label="{escape(user)} GitHub contribution graph">',
    ]
    out += cards.chrome(width, height, "./contributions.sh", right=f"{total:,} contributions", user=user)

    # month labels
    seen: set[int] = set()
    for i, week in enumerate(weeks):
        m = week[0].month
        if m not in seen:
            seen.add(m)
            x = PAD_LEFT + i * (CELL + GAP)
            out.append(
                f'<text x="{x}" y="{PAD_TOP - 8}" font-family="ui-monospace,SFMono-Regular,Consolas,monospace" '
                f'font-size="10" fill="{FG}">{MONTHS[m - 1]}</text>'
            )

    # weekday labels
    for row, label in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        y = PAD_TOP + row * (CELL + GAP) + CELL - 2
        out.append(
            f'<text x="4" y="{y}" font-family="ui-monospace,SFMono-Regular,Consolas,monospace" '
            f'font-size="9" fill="{FG}">{label}</text>'
        )

    # cells: reveal animation, one column at a time
    for i, week in enumerate(weeks):
        delay = 0.008 * i
        for row, day in enumerate(week):
            count = days.get(day, 0)
            fill = PALETTE[_level(count, peak)]
            x = PAD_LEFT + i * (CELL + GAP)
            y = PAD_TOP + row * (CELL + GAP)
            tip = f"{count} contribution{'s' if count != 1 else ''} on {day.isoformat()}"
            out.append(
                f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="3" fill="{fill}" '
                f'data-day="{day.isoformat()}" data-count="{count}">'
                f"<title>{escape(tip)}</title>"
                f'<animate attributeName="opacity" from="0" to="1" dur="0.35s" '
                f'begin="{delay:.3f}s" fill="freeze"/></rect>'
            )

    # legend
    lx = width - PAD_RIGHT - 5 * (CELL + GAP) - 46
    ly = height - 18
    out.append(
        f'<text x="{lx - 34}" y="{ly + 10}" font-family="ui-monospace,SFMono-Regular,Consolas,monospace" '
        f'font-size="10" fill="{FG}">Less</text>'
    )
    for i, colour in enumerate(PALETTE):
        out.append(
            f'<rect x="{lx + i * (CELL + GAP)}" y="{ly}" width="{CELL}" height="{CELL}" '
            f'rx="3" fill="{colour}"/>'
        )
    out.append(
        f'<text x="{lx + 5 * (CELL + GAP) + 6}" y="{ly + 10}" '
        f'font-family="ui-monospace,SFMono-Regular,Consolas,monospace" font-size="10" '
        f'fill="{FG}">More</text>'
    )
    out.append("</svg>")

    svg = "\n".join(out)
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write(svg)
    return svg
