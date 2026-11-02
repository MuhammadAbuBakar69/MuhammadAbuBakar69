"""Render a stats card (streaks, totals, top languages) to a standalone SVG."""
from __future__ import annotations

from html import escape

BG = "#0d1117"
BORDER = "#21262d"
FG = "#e6edf3"
MUTED = "#7d8590"
ACCENT = "#39d353"

W, H = 420, 420


def render(stats: dict, out_path: str) -> str:
    login = escape(stats["login"])
    rows = [
        ("total contributions", f'{stats["contributions"]:,}'),
        ("current streak", f'{stats["current_streak"]}d'),
        ("longest streak", f'{stats["longest_streak"]}d'),
        ("public repos", f'{stats["repos"]}'),
        ("stars earned", f'{stats["stars"]}'),
        ("followers", f'{stats["followers"]}'),
    ]

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
        f'role="img" aria-label="{login} GitHub stats">',
        f'<rect width="{W}" height="{H}" rx="12" fill="{BG}" stroke="{BORDER}"/>',
        f'<text x="24" y="34" font-family="ui-monospace,SFMono-Regular,Consolas,monospace" '
        f'font-size="12" fill="{ACCENT}">$ ./stats.sh --user {login}</text>',
        f'<line x1="24" y1="48" x2="{W - 24}" y2="48" stroke="{BORDER}"/>',
    ]

    y = 76
    for label, value in rows:
        out.append(
            f'<text x="24" y="{y}" font-family="ui-monospace,SFMono-Regular,Consolas,monospace" '
            f'font-size="13" fill="{MUTED}">{label}</text>'
        )
        out.append(
            f'<text x="{W - 24}" y="{y}" text-anchor="end" '
            f'font-family="ui-monospace,SFMono-Regular,Consolas,monospace" font-size="14" '
            f'font-weight="600" fill="{FG}">{value}</text>'
        )
        y += 30

    # top languages bar
    langs = stats.get("languages") or {}
    total = sum(langs.values()) or 1
    top = sorted(langs.items(), key=lambda kv: kv[1], reverse=True)[:4]
    y += 6
    out.append(
        f'<text x="24" y="{y}" font-family="ui-monospace,SFMono-Regular,Consolas,monospace" '
        f'font-size="12" fill="{ACCENT}">$ top-langs --limit 4</text>'
    )
    y += 22
    shades = ["#39d353", "#26a641", "#006d32", "#0e4429"]
    bar_x, bar_w = 24, W - 48
    cursor = bar_x
    for i, (name, count) in enumerate(top):
        seg = max(6, round(bar_w * count / total))
        if cursor + seg > bar_x + bar_w:
            seg = bar_x + bar_w - cursor
        out.append(
            f'<rect x="{cursor}" y="{y}" width="{seg}" height="10" rx="3" '
            f'fill="{shades[i % len(shades)]}"/>'
        )
        cursor += seg + 2
    y += 30
    for i, (name, count) in enumerate(top):
        pct = round(100 * count / total)
        out.append(f'<circle cx="30" cy="{y - 4}" r="4" fill="{shades[i % len(shades)]}"/>')
        out.append(
            f'<text x="42" y="{y}" font-family="ui-monospace,SFMono-Regular,Consolas,monospace" '
            f'font-size="12" fill="{FG}">{escape(str(name))}</text>'
        )
        out.append(
            f'<text x="{W - 24}" y="{y}" text-anchor="end" '
            f'font-family="ui-monospace,SFMono-Regular,Consolas,monospace" font-size="12" '
            f'fill="{MUTED}">{pct}%</text>'
        )
        y += 22

    out.append("</svg>")
    svg = "\n".join(out)
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write(svg)
    return svg
