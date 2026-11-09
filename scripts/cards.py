"""Terminal-window cards (stats + portrait) for the profile README.

Both cards share one chrome, one height and one footer band, so the two panes read as a single
terminal split rather than two artefacts that happen to sit side by side. The geometry below is the
contract `scripts/verify_layout.py` enforces: change a constant, the build tells you what broke.
"""

from __future__ import annotations

from html import escape

# --------------------------------------------------------------------------- colour
BG = "#0d1117"
BAR = "#161b22"
BORDER = "#30363d"
FG = "#e6edf3"
MUTED = "#8b949e"
DIM = "#484f58"
ACCENT = "#39d353"
INK = "#dfe6f0"  # portrait ink: near-white, like the reference window
DOTS = ("#ff5f56", "#ffbd2e", "#27c93f")
FONT = "ui-monospace,SFMono-Regular,Consolas,'Liberation Mono',monospace"

# --------------------------------------------------------------------------- geometry
W, H = 460, 548
BAR_H = 36
PAD = 18  # one gutter for both panes; nothing is allowed to start outside it
GUTTER = 10
CONTENT_TOP = 50
FOOTER_RULE_Y = H - 32
FOOTER_TEXT_Y = H - 14

TILE_H, TILE_GAP = 66, 8
COL_W = (W - 2 * PAD - GUTTER) // 2  # 207: equal halves, no rounding drift
PORTRAIT_AREA = (CONTENT_TOP, 444)  # y from, y to
CHART_TOP, CHART_BOTTOM = 306, 470


def mono(
    x: float,
    y: float,
    size: float,
    fill: str,
    text: str,
    *,
    anchor: str | None = None,
    weight: int | None = None,
    spacing: str | None = None,
) -> str:
    """One text element, one set of attributes. Keeps every pane visually identical."""
    attrs = [
        f'x="{x:.1f}"',
        f'y="{y:.1f}"',
        f'font-family="{FONT}"',
        f'font-size="{size}"',
        f'fill="{fill}"',
    ]
    if anchor:
        attrs.append(f'text-anchor="{anchor}"')
    if weight:
        attrs.append(f'font-weight="{weight}"')
    if spacing:
        attrs.append(f'letter-spacing="{spacing}"')
    return f"<text {' '.join(attrs)}>{escape(text)}</text>"


def chrome(w: int, h: int, login: str, cmd: str, right: str | None = None) -> list[str]:
    """Outer window: rounded frame, title bar with traffic lights, monospace command.

    The prompt is always the lowercase login. GitHub logins are case-insensitive, and a title bar
    that mixes `MuhammadAbuBakar69` and `muhammadabubakar69` across two panes looks like two
    different people's terminals.
    """
    out = [
        f'<rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="12" fill="{BG}" stroke="{BORDER}"/>',
        f'<path d="M0 12a12 12 0 0 1 12-12h{w - 24}a12 12 0 0 1 12 12v{BAR_H}H0Z" fill="{BAR}"/>',
        f'<line x1="0" y1="{BAR_H}" x2="{w}" y2="{BAR_H}" stroke="{BORDER}"/>',
    ]
    for i, colour in enumerate(DOTS):
        out.append(f'<circle cx="{17 + i * 15}" cy="18" r="4.6" fill="{colour}"/>')
    out.append(mono(62, 22.5, 11.5, MUTED, f"{login.lower()}@github: ~ $ {cmd}"))
    if right:
        out.append(mono(w - PAD, 22.5, 10.5, DIM, right, anchor="end"))
    return out


def footer(stats: dict) -> list[str]:
    """Shared footer band: same rule, same baselines, same two ends of information."""
    left = f"auto-refreshed daily · {stats['contributions']:,} contributions / 12 months"
    right = f"built {stats['built']}"
    return [
        f'<line x1="{PAD}" y1="{FOOTER_RULE_Y}" x2="{W - PAD}" y2="{FOOTER_RULE_Y}" stroke="{BORDER}"/>',
        mono(PAD, FOOTER_TEXT_Y, 9.5, DIM, left),
        mono(W - PAD, FOOTER_TEXT_Y, 9.5, DIM, right, anchor="end"),
    ]


def _svg(h: int = H, label: str = "") -> list[str]:
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{h}" viewBox="0 0 {W} {h}" '
        f'role="img" aria-label="{escape(label)}">'
    ]


# --------------------------------------------------------------------------- stats


def _tiles(stats: dict) -> list[tuple[str, str, str, str]]:
    """(label, number, unit, sub) — number and unit are drawn separately so the digits line up."""

    def fmt(value) -> str:
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

    cur, lon = stats["current_streak"], stats["longest_streak"]
    pct = round(100 * stats["active_days"] / stats["total_days"]) if stats["total_days"] else 0
    best = stats.get("best_day") or {}
    return [
        (
            "current streak",
            f"{cur}",
            "d",
            range_of(stats.get("current_start"), stats.get("current_end")) if cur else "none today",
        ),
        ("longest streak", f"{lon}", "d", range_of(stats.get("longest_start"), stats.get("longest_end"))),
        ("contributions", f'{stats["contributions"]:,}', "", "in the last year"),
        ("active days", f'{stats["active_days"]}', f' / {stats["total_days"]}', f"{pct}% of the year"),
        ("best day", f'{best.get("count", 0)}', "", best.get("label", "")),
        ("avg / active day", f'{stats["avg_active"]:.1f}', "", "contributions"),
    ]


def render_stats(stats: dict, out_path: str) -> str:
    login = stats["login"]
    out = _svg(label=f"{login} GitHub stats")
    out += chrome(W, H, login, "./stats.sh", right=f"--12mo")

    for i, (label, number, unit, sub) in enumerate(_tiles(stats)):
        col, row = i % 2, i // 2
        x = PAD + col * (COL_W + GUTTER)
        y = CONTENT_TOP + row * (TILE_H + TILE_GAP)
        out.append(
            f'<rect x="{x}" y="{y}" width="{COL_W}" height="{TILE_H}" rx="8" '
            f'fill="#11161d" stroke="{BORDER}"/>'
        )
        # three baselines, identical in every tile: label, value, sub
        out.append(mono(x + 12, y + 19, 10.5, MUTED, f"$ {label}"))
        out.append(mono(x + 12, y + 42, 20, FG, number, weight=600))
        if unit:
            unit_x = x + 12 + len(number) * 12.0 + 2  # 0.6 advance at 20px
            out.append(mono(unit_x, y + 42, 13, MUTED, unit))
        out.append(mono(x + 12, y + 58, 9.5, DIM, sub))

    # ---------------------------------------------------------------- monthly bars
    months = stats.get("monthly") or []
    out.append(mono(PAD, 288, 11.5, ACCENT, "$ contributions / month"))
    if months:
        peak = max(m["count"] for m in months) or 1
        out.append(mono(W - PAD, 288, 9.5, DIM, f"peak {peak:,}", anchor="end"))

        span = CHART_BOTTOM - CHART_TOP
        usable = span * 0.88  # headroom so the peak label never collides with the header
        slot = (W - 2 * PAD) / len(months)
        bar_w = min(24.0, slot * 0.62)
        for i, m in enumerate(months):
            cx = PAD + slot * (i + 0.5)
            hgt = usable * (m["count"] / peak) if m["count"] else 3
            y = CHART_BOTTOM - hgt
            fill = ACCENT if m["count"] else DIM
            out.append(
                f'<rect x="{cx - bar_w / 2:.1f}" y="{y:.1f}" width="{bar_w:.1f}" height="{hgt:.1f}" '
                f'rx="3" fill="{fill}"/>'
            )
            if m["count"] == peak:
                out.append(
                    mono(cx, y - 8, 10.5, ACCENT, f'{m["count"]:,}', anchor="middle", weight=600)
                )
            out.append(mono(cx, CHART_BOTTOM + 18, 10, MUTED, m["label"], anchor="middle"))

    out.append(
        f'<line x1="{PAD}" y1="{CHART_BOTTOM}" x2="{W - PAD}" y2="{CHART_BOTTOM}" stroke="{BORDER}"/>'
    )
    out += footer(stats)
    out.append("</svg>")

    svg = "\n".join(out)
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write(svg)
    return svg


# --------------------------------------------------------------------------- portrait


def render_portrait(lines: list[str], name: str, login: str, out_path: str, stats: dict | None = None) -> str:
    out = _svg(label=f"ASCII portrait of {name}")
    out += chrome(W, H, login, "./portrait.sh", right="--ascii")

    cols = max((len(line) for line in lines), default=1)
    rows = len(lines) or 1
    top, bottom = PORTRAIT_AREA
    area_h = bottom - top
    area_w = W - 2 * PAD
    line_h = area_h / rows
    font = round(min(line_h * 0.94, area_w / cols / 0.6), 2)

    # Centre on the block's real width, not on the frame: a 66-column grid at 9px is narrower than
    # the card, and left-aligning it is what makes an ASCII portrait look crooked.
    art_w = cols * font * 0.6
    art_x = PAD + (area_w - art_w) / 2
    out.append(f'<text xml:space="preserve" font-family="{FONT}" font-size="{font}" fill="{INK}">')
    for r, line in enumerate(lines):
        y = top + (r + 1) * line_h - (line_h - font) / 2
        out.append(f'<tspan x="{art_x:.1f}" y="{y:.1f}">{escape(line)}</tspan>')
    out.append("</text>")

    out.append(mono(PAD, 468, 11.5, ACCENT, "$ whoami"))
    out.append(mono(PAD, 496, 19, FG, name, weight=600))
    if stats is not None:
        out += footer(stats)
    out.append("</svg>")

    svg = "\n".join(out)
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write(svg)
    return svg
