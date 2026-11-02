"""Terminal-window cards (stats + portrait) for the profile README.

Both cards share one chrome so they read as two panes of the same terminal.
"""
from __future__ import annotations

from html import escape

BG = "#0d1117"
BAR = "#161b22"
BORDER = "#30363d"
FG = "#e6edf3"
MUTED = "#8b949e"
DIM = "#484f58"
ACCENT = "#39d353"
DOTS = ("#ff5f56", "#ffbd2e", "#27c93f")
FONT = "ui-monospace,SFMono-Regular,Consolas,'Liberation Mono',monospace"

W, H = 460, 520
BAR_H = 36


def chrome(w: int, h: int, cmd: str, right: str | None = None, user: str = "abubakar") -> list[str]:
    """Outer window: rounded frame, title bar with traffic lights, monospace command."""
    out = [
        f'<rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="12" fill="{BG}" stroke="{BORDER}"/>',
        f'<path d="M0 12a12 12 0 0 1 12-12h{w - 24}a12 12 0 0 1 12 12v{BAR_H}H0Z" fill="{BAR}"/>',
        f'<line x1="0" y1="{BAR_H}" x2="{w}" y2="{BAR_H}" stroke="{BORDER}"/>',
    ]
    for i, colour in enumerate(DOTS):
        out.append(f'<circle cx="{17 + i * 15}" cy="18" r="4.6" fill="{colour}"/>')
    out.append(
        f'<text x="62" y="22.5" font-family="{FONT}" font-size="11.5" fill="{MUTED}">'
        f"{escape(user)}@github: ~ $ {escape(cmd)}</text>"
    )
    if right:
        out.append(
            f'<text x="{w - 16}" y="22.5" text-anchor="end" font-family="{FONT}" '
            f'font-size="10.5" fill="{DIM}">{escape(right)}</text>'
        )
    return out


def _svg(w: int, h: int, label: str) -> list[str]:
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
        f'role="img" aria-label="{escape(label)}">'
    ]


# --------------------------------------------------------------------------- stats


def _boxes(stats: dict) -> list[tuple[str, str, str]]:
    def fmt(value):
        if not value:
            return ""
        if isinstance(value, str):
            from datetime import date as _d
            value = _d.fromisoformat(value)
        return value.strftime("%b %-d")

    def range_of(start, end) -> str:
        if not start or not end:
            return "no activity yet"
        a, b = fmt(start), fmt(end)
        return a if a == b else f"{a} – {b}"

    cur = stats["current_streak"]
    lon = stats["longest_streak"]
    pct = round(100 * stats["active_days"] / stats["total_days"]) if stats["total_days"] else 0
    best = stats.get("best_day") or {}
    return [
        ("current streak", f"{cur}d", range_of(stats.get("current_start"), stats.get("current_end")) if cur else "start one today"),
        ("longest streak", f"{lon}d", range_of(stats.get("longest_start"), stats.get("longest_end"))),
        ("contributions", f'{stats["contributions"]:,}', "in the last year"),
        ("active days", f'{stats["active_days"]} / {stats["total_days"]}', f"{pct}% of the year"),
        ("best day", f'{best.get("count", 0)}', best.get("label", "")),
        ("avg / active day", f'{stats["avg_active"]:.1f}', "contributions"),
    ]


def render_stats(stats: dict, out_path: str) -> str:
    login = stats["login"]
    out = _svg(W, H, f"{login} GitHub stats")
    out += chrome(W, H, "./stats.sh", right=f"--user {login}", user=login.split()[0].lower())

    pad, gap = 18, 10
    box_w = (W - 2 * pad - gap) // 2
    box_h = 68
    for i, (label, value, sub) in enumerate(_boxes(stats)):
        col, row = i % 2, i // 2
        x = pad + col * (box_w + gap)
        y = 50 + row * (box_h + 6)
        out.append(
            f'<rect x="{x}" y="{y}" width="{box_w}" height="{box_h}" rx="8" fill="#11161d" stroke="{BORDER}"/>'
        )
        out.append(
            f'<text x="{x + 12}" y="{y + 18}" font-family="{FONT}" font-size="10.5" fill="{MUTED}">'
            f"$ {escape(label)}</text>"
        )
        out.append(
            f'<text x="{x + 12}" y="{y + 42}" font-family="{FONT}" font-size="21" font-weight="600" '
            f'fill="{FG}">{escape(value)}</text>'
        )
        out.append(
            f'<text x="{x + 12}" y="{y + 58}" font-family="{FONT}" font-size="10" fill="{DIM}">'
            f"{escape(sub)}</text>"
        )

    # ---------------------------------------------------------------- monthly bars
    months = stats.get("monthly") or []
    chart_top = 52 + 3 * (box_h + 6) + 14
    out.append(
        f'<text x="{pad}" y="{chart_top + 12}" font-family="{FONT}" font-size="11.5" fill="{ACCENT}">'
        "$ contributions / month</text>"
    )
    if months:
        bottom = H - 62
        top = chart_top + 34
        span = bottom - top
        peak = max(m["count"] for m in months) or 1
        inner = W - 2 * pad
        slot = inner / len(months)
        bar_w = min(26.0, slot * 0.62)
        for i, m in enumerate(months):
            cx = pad + slot * (i + 0.5)
            hgt = span * (m["count"] / peak) if m["count"] else 3
            y = bottom - hgt
            fill = ACCENT if m["count"] else DIM
            out.append(
                f'<rect x="{cx - bar_w / 2:.1f}" y="{y:.1f}" width="{bar_w:.1f}" height="{hgt:.1f}" '
                f'rx="3" fill="{fill}"/>'
            )
            if m["count"] and m["count"] == peak:
                out.append(
                    f'<text x="{cx:.1f}" y="{y - 8:.1f}" text-anchor="middle" font-family="{FONT}" '
                    f'font-size="11" font-weight="600" fill="{ACCENT}">{m["count"]:,}</text>'
                )
            out.append(
                f'<text x="{cx:.1f}" y="{bottom + 18:.1f}" text-anchor="middle" font-family="{FONT}" '
                f'font-size="10" fill="{MUTED}">{escape(m["label"])}</text>'
            )
        out.append(
            f'<line x1="{pad}" y1="{bottom}" x2="{W - pad}" y2="{bottom}" stroke="{BORDER}"/>'
        )

    out.append("</svg>")
    svg = "\n".join(out)
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write(svg)
    return svg


# --------------------------------------------------------------------------- portrait


def render_portrait(lines: list[str], name: str, login: str, out_path: str) -> str:
    out = _svg(W, H, f"ASCII portrait of {name}")
    out += chrome(W, H, "./portrait.sh", right="640×640 ASCII", user=login)

    cols = max((len(line) for line in lines), default=1)
    rows = len(lines) or 1
    area_x, area_y, area_w, area_h = 18, 50, W - 36, 392
    line_h = area_h / rows
    font = round(min(line_h * 0.94, area_w / cols / 0.6), 2)

    out.append(
        f'<text xml:space="preserve" font-family="{FONT}" font-size="{font}" fill="{ACCENT}">'
    )
    for r, line in enumerate(lines):
        y = area_y + (r + 1) * line_h - (line_h - font) / 2
        out.append(f'<tspan x="{area_x}" y="{y:.1f}">{escape(line)}</tspan>')
    out.append("</text>")

    out.append(
        f'<text x="18" y="466" font-family="{FONT}" font-size="11.5" fill="{ACCENT}">$ whoami</text>'
    )
    out.append(
        f'<text x="18" y="496" font-family="{FONT}" font-size="19" font-weight="600" '
        f'fill="{FG}">{escape(name)}</text>'
    )
    out.append("</svg>")

    svg = "\n".join(out)
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write(svg)
    return svg
