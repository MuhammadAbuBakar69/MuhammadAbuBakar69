"""Achievement strip: six real numbers with the milestones they belong to.

No invented badges. GitHub retired its achievement API, and a hand-drawn "Pull Shark" tile would be
decoration pretending to be data. Every tile here is computed from the same stats dict as the cards,
and a tile that has no supporting number is simply left out rather than filled with a placeholder.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import cards  # noqa: E402

W, H = 1280, 208
PAD = 28
TILE_H = 96
TILE_TOP = 54
GAP = 12


def _tiles(stats: dict) -> list[dict]:
    total = stats["contributions"]
    next_milestone = 1000 if total < 1000 else (2500 if total < 2500 else 5000)
    work = stats.get("work") or {}

    tiles = [
        {
            "label": "contributions",
            "value": f"{total:,}",
            "unit": "last 12 months",
            "sub": f"next milestone {next_milestone:,}",
            "progress": min(1.0, total / next_milestone),
        },
        {
            "label": "active days",
            "value": str(stats["active_days"]),
            "unit": f"of {stats['total_days']}",
            "sub": f"{stats['avg_active']:.1f} contributions / active day",
        },
        {
            "label": "longest streak",
            "value": str(stats["longest_streak"]),
            "unit": "days",
            "sub": stats.get("longest_label") or "personal best",
        },
        {
            "label": "repositories",
            "value": f"{stats['repos']:,}",
            "unit": "public",
            "sub": f"{stats['languages']} languages",
        },
    ]
    if work.get("merged_prs") is not None:
        tiles.append(
            {
                "label": "pull requests",
                "value": f"{work['merged_prs']:,}",
                "unit": "merged",
                "sub": f"{work.get('issues', 0):,} issues opened",
            }
        )
    if work.get("commits_year") is not None:
        tiles.append(
            {
                "label": "commits",
                "value": f"{work['commits_year']:,}",
                "unit": "in the last year",
                "sub": f"{work.get('prs_year', 0)} PRs · {work.get('reviews_year', 0)} reviews",
            }
        )
    return tiles[:6]


def render(stats: dict, out_path: str) -> str:
    tiles = _tiles(stats)
    col_w = (W - 2 * PAD - GAP * (len(tiles) - 1)) / len(tiles)
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
        f'role="img" aria-label="{cards.escape(stats["name"])} — achievements">',
        *cards.chrome(W, H, stats["login"], "./achievements.sh", right="--all-time"),
    ]

    for i, tile in enumerate(tiles):
        x = PAD + i * (col_w + GAP)
        out.append(
            f'<rect x="{x:.1f}" y="{TILE_TOP}" width="{col_w:.1f}" height="{TILE_H}" rx="8" '
            f'fill="{cards.BAR}" stroke="{cards.BORDER}"/>'
        )
        out.append(cards.mono(x + 12, TILE_TOP + 22, 10, cards.MUTED, f"$ {tile['label']}"))
        out.append(cards.mono(x + 12, TILE_TOP + 56, 24, cards.FG, tile["value"], weight=700))
        value_w = len(tile["value"]) * 24 * 0.6
        out.append(cards.mono(x + 12 + value_w + 5, TILE_TOP + 56, 10, cards.DIM, tile["unit"]))
        out.append(cards.mono(x + 12, TILE_TOP + 74, 9, cards.DIM, tile["sub"]))

        track_y = TILE_TOP + TILE_H - 8
        track_w = col_w - 24
        out.append(
            f'<rect x="{x + 12:.1f}" y="{track_y}" width="{track_w:.1f}" height="3" rx="1.5" '
            f'fill="{cards.DIM}" opacity="0.55"/>'
        )
        if tile.get("progress"):
            out.append(
                f'<rect x="{x + 12:.1f}" y="{track_y}" width="{track_w * tile["progress"]:.1f}" '
                f'height="3" rx="1.5" fill="{cards.ACCENT}"/>'
            )

    out.append(f'<line x1="{PAD}" y1="{H - 44}" x2="{W - PAD}" y2="{H - 44}" stroke="{cards.BORDER}"/>')
    out.append(
        cards.mono(PAD, H - 18, 10, cards.MUTED, "computed from the GitHub API · no badges, just numbers")
    )
    out.append(
        cards.mono(W - PAD, H - 18, 10, cards.MUTED, f"built {stats['built']}", anchor="end")
    )
    out.append("</svg>")

    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(out))
    return "".join(out)
