"""The README card set: hero, activity, three focus cards, three repo cards.

Layout follows the reference profile the owner asked to match - a full-width hero, the heatmap and
activity strip, three equal cards, a title rule, then three repo cards, each image on one line with
no whitespace between them so GitHub renders no gaps.

Content is his own: every number comes from the stats dict, every repo from the API. The palette is
the one he already uses - near-black panel, one green accent, monospace throughout.
"""
from __future__ import annotations

import os
import sys
import textwrap

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import cards  # noqa: E402

BG, BORDER, FG, MUTED, DIM, ACCENT, FONT = (
    cards.BG, cards.BORDER, cards.FG, cards.MUTED, cards.DIM, cards.ACCENT, cards.FONT,
)
HERO_W, HERO_H, PAD = 880.0, 432, 48
WIDE, WIDE_H = 880.0, 352
FEAT_W, FEAT_H = 293.333, 222
REPO_W, REPO_H = 293.333, 188
TITLE_H = 132


def _head(w: float, h: float, label: str) -> list[str]:
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w:.3f}" height="{h}" '
        f'viewBox="0 0 {w:.3f} {h}" role="img" aria-label="{cards.escape(label)}">',
        f'<rect x="0.5" y="0.5" width="{w - 1:.3f}" height="{h - 1}" rx="14" '
        f'fill="{BG}" stroke="{BORDER}"/>',
    ]


def _wrap(text: str, width: float, size: float) -> list[str]:
    return textwrap.wrap(text, width=int(width / (size * 0.6))) or [""]


def _write(path: str, lines: list[str]) -> None:
    lines.append("</svg>")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))


def render_hero(stats: dict, out: str) -> None:
    name = stats["name"]
    first, _, last = name.partition(" ")
    lines = _head(HERO_W, HERO_H, f"{name}. Full-stack developer in Karachi.")
    lines.append(f'<rect x="{PAD}" y="72" width="40" height="4" fill="{ACCENT}"/>')
    lines.append(cards.mono(PAD, 110, 11, MUTED, "FULL-STACK DEVELOPER · KARACHI, PK", spacing="2.2"))
    lines.append(cards.mono(PAD, 200, 62, FG, first, weight=700))
    lines.append(cards.mono(PAD, 268, 62, FG, last, weight=700))
    tag = (
        "I build AI products that ship: agents, RAG pipelines,"
        " and the web apps around them."
    )
    wrapped = _wrap(tag, HERO_W - 2 * PAD, 17)
    for i, row in enumerate(wrapped[:2]):
        lines.append(cards.mono(PAD, 320 + i * 27, 17, MUTED, row))
    lines.append(cards.mono(PAD, 398, 13, FG, "withabubakar.netlify.app"))
    lines.append(cards.mono(PAD + 13 * 0.6 * 21 + 8, 398, 13, ACCENT, "↗"))
    _write(out, lines)


def render_activity(stats: dict, out: str) -> None:
    monthly = stats["monthly"]
    total = stats["contributions"]
    best = stats["best_day"]
    lines = _head(
        WIDE, WIDE_H, f"{total:,} contributions in the last 12 months, best streak {stats['longest_streak']} days"
    )
    lines.append(cards.mono(PAD, 64, 11, MUTED, "THE LAST 12 MONTHS ON GITHUB", spacing="1.8"))
    summary = (
        f"{total:,} contributions · {best['count']:,} on the busiest day "
        f"({best['label']}) · {stats['longest_streak']}-day best streak"
    )
    lines.append(cards.mono(PAD, 104, 12, MUTED, summary))

    top, bottom = 148, 300
    span = bottom - top
    peak = max(m["count"] for m in monthly) or 1
    inner = WIDE - 2 * PAD
    slot = inner / len(monthly)
    bar_w = min(34.0, slot * 0.56)
    for i, m in enumerate(monthly):
        cx = PAD + slot * (i + 0.5)
        hgt = span * (m["count"] / peak) if m["count"] else 3
        y = bottom - hgt
        fill = ACCENT if m["count"] else DIM
        lines.append(
            f'<rect x="{cx - bar_w / 2:.1f}" y="{y:.1f}" width="{bar_w:.1f}" '
            f'height="{hgt:.1f}" rx="3" fill="{fill}"/>'
        )
        if m["count"] == peak:
            lines.append(cards.mono(cx, y - 10, 11, ACCENT, f"{m['count']:,}", anchor="middle", weight=600))
        lines.append(cards.mono(cx, bottom + 22, 10, DIM, m["label"], anchor="middle"))
    lines.append(f'<line x1="{PAD}" y1="{bottom}" x2="{WIDE - PAD}" y2="{bottom}" stroke="{BORDER}"/>')
    _write(out, lines)


def render_feature(spec: dict, out: str) -> None:
    lines = _head(FEAT_W, FEAT_H, f"{spec['label']}: {spec['value']}")
    lines.append(cards.mono(24, 64, 12, ACCENT, spec["label"], spacing="2.0"))
    lines.append(cards.mono(FEAT_W - 24, 64, 14, ACCENT, "→", anchor="end"))
    lines.append(cards.mono(24, 128, 30, FG, spec["value"], weight=700))
    copy = " ".join(spec["lines"])
    for i, row in enumerate(_wrap(copy, FEAT_W - 48, 12)[:3]):
        lines.append(cards.mono(24, 162 + i * 20, 12, MUTED, row))
    _write(out, lines)


def render_title(out: str) -> None:
    lines = _head(WIDE, TITLE_H, "What I'm building")
    label = "WHAT I'M BUILDING"
    width = len(label) * 15 * 0.6 + 16 * 3
    mid = WIDE / 2
    lines.append(cards.mono(mid, 74, 15, MUTED, label, anchor="middle", spacing="3"))
    for x1, x2 in ((PAD, mid - width / 2 - 24), (mid + width / 2 + 24, WIDE - PAD)):
        lines.append(f'<line x1="{x1:.1f}" y1="69" x2="{x2:.1f}" y2="69" stroke="{BORDER}"/>')
    _write(out, lines)


def render_repo(repo: dict, out: str) -> None:
    lines = _head(REPO_W, REPO_H, f"{repo['name']}: {repo['description']}")
    lines.append(cards.mono(24, 56, 15, FG, repo["name"], weight=600))
    for i, row in enumerate(_wrap(repo["description"], REPO_W - 48, 12)[:3]):
        lines.append(cards.mono(24, 88 + i * 19, 12, MUTED, row))
    meta = repo["meta"]
    lines.append(cards.mono(24, 162, 11, DIM, meta))
    lines.append(f'<line x1="24" y1="{REPO_H - 34}" x2="{REPO_W - 24}" y2="{REPO_H - 34}" stroke="{BORDER}"/>')
    _write(out, lines)


def focus_specs(stats: dict) -> list[dict]:
    """The three equal cards. Numbers are real; the wording stays within what he actually does."""
    repos = stats.get("repos") or 0
    return [
        {
            "key": "build",
            "label": "BUILD",
            "value": f"{repos} repos",
            "lines": ["Production web apps in React, Next.js and TypeScript - shipped, not sketched."],
        },
        {
            "key": "automate",
            "label": "AUTOMATE",
            "value": "AI agents",
            "lines": ["LangChain, n8n and RAG pipelines, with the evals to prove they work."],
        },
        {
            "key": "write",
            "label": "WRITE",
            "value": "Daily",
            "lines": ["Building in public with Cursor and AI copilots, one commit at a time."],
        },
    ]


def featured_repos(repos: list[dict]) -> list[dict]:
    """The three cards under the title rule, in a fixed order, only if the repo exists."""
    wanted = ("threadmind-ai", "jobpilot", "otto")
    by_name = {r["name"].lower(): r for r in repos}
    out = []
    for name in wanted:
        repo = by_name.get(name)
        if not repo:
            continue
        topics = repo.get("topics") or []
        meta = "  ·  ".join(
            [p for p in (repo.get("language"), topics[0].replace("-", " ") if topics else None) if p]
        )
        out.append(
            {
                "name": repo["name"],
                "description": repo.get("description") or "Work in progress",
                "meta": meta,
            }
        )
    return out


def render_all(stats: dict, out_dir: str) -> list[str]:
    os.makedirs(out_dir, exist_ok=True)
    written: list[str] = []
    hero = os.path.join(out_dir, "hero.svg")
    render_hero(stats, hero)
    written.append(hero)
    activity = os.path.join(out_dir, "activity.svg")
    render_activity(stats, activity)
    written.append(activity)

    for spec in stats["focus"]:
        path = os.path.join(out_dir, f"focus-{spec['key']}.svg")
        render_feature(spec, path)
        written.append(path)

    title = os.path.join(out_dir, "title-building.svg")
    render_title(title)
    written.append(title)

    for repo in stats["featured"]:
        path = os.path.join(out_dir, f"repo-{repo['name'].lower().replace('_', '-')}.svg")
        render_repo(repo, path)
        written.append(path)
    return written
