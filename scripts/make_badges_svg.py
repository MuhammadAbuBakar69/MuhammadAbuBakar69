"""The badge ladder: GitHub's own achievements, with the evidence underneath each one.

GitHub derives the badges in the profile sidebar server-side and exposes no API to read or grant
them, so this panel rebuilds the *conditions* from public data instead of pretending to own the
badges. A card is marked earned only when its own threshold is met by a number in `badges`; the rest
show how far away they are. Nothing here claims a badge GitHub has not awarded.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import cards  # noqa: E402

W, H = 1280, 324
PAD = 28
COLS = 4
GAP = 12
CARD_H = 104
ROW_TOPS = (54, 170)
CARD_W = (W - 2 * PAD - GAP * (COLS - 1)) // COLS  # 297


def _cards(stats: dict) -> list[dict]:
    b = stats.get("badges") or {}
    merged = b.get("merged_prs", 0)
    repos = b.get("merged_repos", 0)
    stars = stats.get("stars", 0)
    best_stars = stats.get("best_repo_stars", 0)

    def ladder(name, requirement, value, tiers, note):
        earned = value >= tiers[0]
        target = next((t for t in tiers if value < t), None)
        if earned and target is None:
            return {"name": name, "req": requirement, "state": "max", "note": note}
        return {
            "name": name,
            "req": requirement,
            "state": "earned" if earned else "locked",
            "progress": min(1.0, value / target) if target else None,
            "note": note,
            "detail": f"{value:,} / {target:,}" if target else "",
        }

    return [
        ladder("Pull Shark", "merged pull requests", merged, [2, 16, 128], "16 for silver"),
        ladder("Starstruck", "stars on one repository", best_stars, [16], f"{stars} stars total"),
        {
            "name": "YOLO",
            "req": "merged without review",
            "state": "earned" if merged and not (stats.get("work") or {}).get("reviews_year") else "locked",
            "note": "self-merged PRs",
        },
        {
            "name": "Open Sourcerer",
            "req": "merged PRs across repos",
            "state": "earned" if repos >= 2 else "locked",
            "note": f"{repos} repositories",
        },
        ladder("Quickdraw", "issue closed within 5 min", b.get("quick_closes", 0), [1], "fast resolutions"),
        ladder("Pair Extraordinaire", "co-authored commits", b.get("coauthored", 0), [1], "pairing credit"),
        {
            "name": "Galaxy Brain",
            "req": "2 accepted discussion answers",
            "state": "locked",
            "note": "discussions not used yet",
        },
        {
            "name": "Public Sponsor",
            "req": "sponsor open source",
            "state": "locked",
            "note": "no sponsorships",
        },
    ]


def render(stats: dict, out_path: str) -> str:
    cards_data = _cards(stats)
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
        f'role="img" aria-label="{cards.escape(stats["name"])} — GitHub achievements and progress">',
        *cards.chrome(W, H, stats["login"], "./badges.sh", right="--github"),
    ]
    for i, card in enumerate(cards_data):
        row, col = divmod(i, COLS)
        x = PAD + col * (CARD_W + GAP)
        y = ROW_TOPS[row]
        earned = card["state"] in ("earned", "max")
        stroke = cards.ACCENT if earned else cards.BORDER
        name_fill = cards.FG if earned else cards.MUTED
        out.append(
            f'<rect x="{x}" y="{y}" width="{CARD_W}" height="{CARD_H}" rx="8" '
            f'fill="{cards.BAR}" stroke="{stroke}"/>'
        )
        out.append(cards.mono(x + 14, y + 26, 12.5, name_fill, card["name"], weight=600))
        out.append(cards.mono(x + 14, y + 44, 9.5, cards.DIM, card["req"]))
        if card.get("progress") is not None:
            track_w = CARD_W - 28
            out.append(
                f'<rect x="{x + 14}" y="{y + 62}" width="{track_w}" height="4" rx="2" fill="{cards.DIM}"/>'
            )
            out.append(
                f'<rect x="{x + 14}" y="{y + 62}" width="{track_w * card["progress"]:.1f}" '
                f'height="4" rx="2" fill="{cards.ACCENT}"/>'
            )
        if earned:
            out.append(cards.mono(x + 14, y + 86, 10, cards.ACCENT, "earned", weight=600))
            out.append(cards.mono(x + CARD_W - 14, y + 86, 9.5, cards.MUTED, card["note"], anchor="end"))
        else:
            detail = card.get("detail") or "locked"
            out.append(cards.mono(x + 14, y + 86, 10, cards.MUTED, detail))
            out.append(cards.mono(x + CARD_W - 14, y + 86, 9.5, cards.DIM, card["note"], anchor="end"))
    out.append(f'<line x1="{PAD}" y1="{H - 44}" x2="{W - PAD}" y2="{H - 44}" stroke="{cards.BORDER}"/>')
    out.append(cards.mono(PAD, H - 22, 9.5, cards.DIM, "conditions rebuilt from the GitHub API · badges are awarded by GitHub"))
    out.append(cards.mono(W - PAD, H - 22, 9.5, cards.DIM, f"built {stats.get('built', '')}", anchor="end"))
    out.append("</svg>")
    svg = "\n".join(out)
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write(svg)
    return svg
