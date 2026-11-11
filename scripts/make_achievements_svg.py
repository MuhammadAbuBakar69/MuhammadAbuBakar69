"""Achievement strip: twelve real numbers on a 6x2 grid, each with its milestone.

No invented badges. GitHub retired its achievement API, and a hand-drawn "Pull Shark" tile would be
decoration pretending to be data. Every tile here is computed from the same stats dict as the cards,
and a tile that has no supporting number is simply left out rather than filled with a placeholder.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import cards  # noqa: E402

W, H = 1280, 312
PER_ROW = 6
PAD = 28
TILE_H = 96
TILE_TOP = 54
GAP = 12
GAP_Y = 12


def _tiles(stats: dict) -> list[dict]:
    total = stats["contributions"]
    next_milestone = 1000 if total < 1000 else (2500 if total < 2500 else 5000)
    work = stats.get("work") or {}

    languages = stats.get("languages") or {}
    top_lang = max(languages, key=languages.get) if languages else None
    top_star = max((r["stars"] for r in stats.get("top_repos") or []), default=0) if stats.get("top_repos") else 0
    top_repo = next((r["name"] for r in stats.get("top_repos") or [] if r["stars"] == top_star), None)
    pct_year = 100 * stats["active_days"] / max(1, stats["total_days"])

    def next_goal(value, ladder=(10, 25, 50, 75, 100, 250, 500, 1000, 2500, 5000)):
        for step in ladder:
            if value < step:
                return step
        return None

    tiles = [
        {
            "label": "contributions",
            "value": f"{total:,}",
            "unit": "last 12 months",
            "sub": f"next {next_goal(total):,}",
            "progress": total / next_goal(total),
        },
        {
            "label": "active days",
            "value": str(stats["active_days"]),
            "unit": f"of {stats['total_days']}",
            "sub": f"{pct_year:.0f}% of the year",
            "progress": stats["active_days"] / max(1, stats["total_days"]),
        },
        {
            "label": "longest streak",
            "value": str(stats["longest_streak"]),
            "unit": "days",
            "sub": stats.get("longest_label") or "personal best",
        },
        {
            "label": "best day",
            "value": f"{stats['best_day']['count']:,}",
            "unit": "in one day",
            "sub": f"on {stats['best_day']['label']}",
            "progress": stats["best_day"]["count"] / max(1, next_goal(stats["best_day"]["count"])),
        },
        {
            "label": "avg / active day",
            "value": f"{stats['avg_active']:.1f}",
            "unit": "per day",
            "sub": "across the year",
        },
    ]
    if work.get("commits_year") is not None:
        goal = next_goal(work["commits_year"])
        tiles.append({
            "label": "commits",
            "value": f"{work['commits_year']:,}",
            "unit": "last 12 months",
            "sub": f"next {goal:,}" if goal else "all in one year",
            "progress": (work["commits_year"] / goal) if goal else None,
        })
    if stats.get("repos"):
        goal = next_goal(stats["repos"])
        tiles.append({
            "label": "repositories",
            "value": f"{stats['repos']:,}",
            "unit": "public",
            "sub": f"next {goal:,}" if goal else f"{stats['repos']} public",
            "progress": (stats["repos"] / goal) if goal else None,
        })
    if work.get("merged_prs") is not None:
        goal = next_goal(work["merged_prs"])
        tiles.append({
            "label": "merged PRs",
            "value": f"{work['merged_prs']:,}",
            "unit": "all time",
            "sub": f"{work.get('prs_year', 0)} opened this year",
            "progress": (work["merged_prs"] / goal) if goal else None,
        })
    if work.get("issues") is not None:
        goal = next_goal(work["issues"])
        tiles.append({
            "label": "issues opened",
            "value": f"{work['issues']:,}",
            "unit": "all time",
            "sub": f"next {goal:,}" if goal else "all time",
            "progress": (work["issues"] / goal) if goal else None,
        })
    if stats.get("stars"):
        goal = next_goal(stats["stars"])
        tiles.append({
            "label": "stars earned",
            "value": f"{stats['stars']:,}",
            "unit": "across repos",
            "sub": f"top: {top_repo}" if top_repo else "across repos",
            "progress": (stats["stars"] / goal) if goal else None,
        })
    if languages:
        tiles.append({
            "label": "languages",
            "value": str(len(languages)),
            "unit": "in use",
            "sub": f"{top_lang} leads" if top_lang else "in use",
        })
    if work.get("prs_year") is not None:
        tiles.append({
            "label": "PRs opened",
            "value": f"{work['prs_year']:,}",
            "unit": "last 12 months",
            "sub": f"{work.get('merged_prs', 0)} merged",
        })
    return tiles[: PER_ROW * 2]


def render(stats: dict, out_path: str) -> str:
    tiles = _tiles(stats)
    col_w = (W - 2 * PAD - GAP * (PER_ROW - 1)) / PER_ROW
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
        f'role="img" aria-label="{cards.escape(stats["name"])} — achievements">',
        *cards.chrome(W, H, stats["login"], "./achievements.sh", right="--all-time", pad=PAD),
    ]

    for i, tile in enumerate(tiles):
        row, col = divmod(i, PER_ROW)
        x = PAD + col * (col_w + GAP)
        y = TILE_TOP + row * (TILE_H + GAP_Y)
        out.append(
            f'<rect x="{x:.1f}" y="{y}" width="{col_w:.1f}" height="{TILE_H}" rx="8" '
            f'fill="{cards.BAR}" stroke="{cards.BORDER}"/>'
        )
        out.append(cards.mono(x + 12, y + 22, 10, cards.MUTED, f"$ {tile['label']}"))
        out.append(cards.mono(x + 12, y + 56, 24, cards.FG, tile["value"], weight=700))
        value_w = len(tile["value"]) * 24 * 0.6
        out.append(cards.mono(x + 12 + value_w + 5, y + 56, 10, cards.DIM, tile["unit"]))
        out.append(cards.mono(x + 12, y + 74, 9, cards.DIM, tile["sub"]))

        track_y = y + TILE_H - 8
        track_w = col_w - 24
        out.append(
            f'<rect x="{x + 12:.1f}" y="{track_y}" width="{track_w:.1f}" height="3" rx="1.5" '
            f'fill="{cards.DIM}" opacity="0.55"/>'
        )
        if tile.get("progress"):
            out.append(
                f'<rect x="{x + 12:.1f}" y="{track_y}" width="{track_w * min(1.0, tile["progress"]):.1f}" '
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
