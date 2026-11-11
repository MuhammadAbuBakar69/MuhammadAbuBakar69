"""The cover image: one wide pane that says who this is, in the same language as the cards.

1280x300 is the widest GitHub will show in a README without scrolling on desktop; anything taller
pushes the statistics below the fold, which is the opposite of what a cover is for.

Everything on it is real: the numbers come from the same stats dict as the cards, and the sparkline
is the same monthly contribution series, so the banner cannot drift away from the panels under it.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import cards  # noqa: E402

W, H = 1280, 300
PAD = 28  # wider than the card gutter: at this width 18px reads as a margin error
COL = 210  # metric columns; 4 * 210 + PAD * 2 = 896, so the sparkline starts clear of them
SPARK_W = 232
SPARK_BOTTOM = 196
SPARK_H = 56


def _metrics(stats: dict) -> list[tuple[str, str, str]]:
    """(label, value, unit) for the four headline numbers, in descending importance."""
    out = [
        ("contributions", f"{stats['contributions']:,}", "last 12 months"),
        ("repositories", f"{stats['repos']:,}", "public"),
        (
            "longest streak",
            str(stats["longest_streak"]),
            "days" if stats["longest_streak"] != 1 else "day",
        ),
        ("best day", f"{stats['best_day']['count']:,}", stats["best_day"]["label"]),
    ]
    return out


def _sparkline(monthly: list[dict]) -> list[str]:
    """Eleven bars, one per month, sharing the metric baseline."""
    out: list[str] = []
    left = W - PAD - SPARK_W
    if not monthly:
        return out
    peak = max((m["count"] for m in monthly), default=0) or 1
    slot = SPARK_W / len(monthly)
    bar_w = min(14.0, slot * 0.56)
    out.append(
        cards.mono(left, SPARK_BOTTOM - SPARK_H - 12, 9.5, cards.DIM, "contributions / month")
    )
    for i, month in enumerate(monthly):
        cx = left + slot * (i + 0.5)
        height = max(3.0, SPARK_H * (month["count"] / peak)) if month["count"] else 3.0
        fill = cards.ACCENT if month["count"] else cards.DIM
        out.append(
            f'<rect x="{cx - bar_w / 2:.1f}" y="{SPARK_BOTTOM - height:.1f}" '
            f'width="{bar_w:.1f}" height="{height:.1f}" rx="2" fill="{fill}"/>'
        )
        out.append(
            cards.mono(cx, SPARK_BOTTOM + 15, 9, cards.MUTED, month["label"], anchor="middle")
        )
    return out


def render(stats: dict, out_path: str) -> str:
    user = stats["login"]
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
        f'role="img" aria-label="{cards.escape(stats["name"])} — profile cover">',
        *cards.chrome(W, H, user, "./profile.sh --short", right="--cover", pad=PAD),
        # name block
        cards.mono(PAD, 108, 40, cards.FG, stats["name"], weight=700, spacing="-0.6"),
        cards.mono(PAD + 2, 142, 15.5, cards.ACCENT, "Full-Stack Developer  ·  AI Automation Engineer", spacing="0.4"),
    ]

    for i, (label, value, unit) in enumerate(_metrics(stats)):
        x = PAD + i * COL
        out.append(cards.mono(x, 176, 10.5, cards.MUTED, f"$ {label}"))
        out.append(cards.mono(x, 202, 22, cards.FG, value, weight=700))
        value_w = len(value) * 22 * 0.6
        out.append(cards.mono(x + value_w + 6, 202, 10.5, cards.DIM, unit))

    out += _sparkline(stats.get("monthly") or [])

    out.append(f'<line x1="{PAD}" y1="{H - 56}" x2="{W - PAD}" y2="{H - 56}" stroke="{cards.BORDER}"/>')
    out.append(cards.mono(PAD, H - 26, 10.5, cards.MUTED, "auto-refreshed daily from the GitHub API"))
    out.append(
        cards.mono(
            W - PAD,
            H - 26,
            10.5,
            cards.MUTED,
            f"github.com/{user}",
            anchor="end",
        )
    )
    out.append("</svg>")

    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(out))
    return "".join(out)
