"""Build every generated asset for the profile README.

    python scripts/build.py --user your-login

Writes assets/contrib-heatmap.svg, assets/stats.svg and assets/data.json.
Run it locally, or let .github/workflows/update-profile-art.yml run it daily.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import gh  # noqa: E402
import cards  # noqa: E402
import make_ascii_svg  # noqa: E402
import make_achievements_svg  # noqa: E402
import make_badges_svg  # noqa: E402
import render_cards  # noqa: E402
import make_banner_svg  # noqa: E402
import make_heatmap_svg  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "assets")
README = os.path.join(ROOT, "README.md")


def render_featured(stats: dict) -> str:
    """Markdown table of the strongest public repos, spliced into the README."""
    repos = stats.get("top_repos") or []
    if not repos:
        return "_No public repositories yet._"
    lines = ["| Project | What it does | Stack | Stars |", "| :--- | :--- | :--- | ---: |"]
    for r in repos:
        desc = (r.get("description") or "Work in progress").replace("|", "\\|")
        if len(desc) > 90:
            desc = desc[:87].rstrip() + "..."
        stack = r.get("language") or "-"
        lines.append(f'| **[{r["name"]}]({r["url"]})** | {desc} | {stack} | {r["stars"]} |')
    return "\n".join(lines)


def splice_readme(block: str) -> bool:
    """Replace whatever sits between the featured markers."""
    if not os.path.exists(README):
        return False
    text = open(README, encoding="utf-8").read()
    start, end = "<!-- featured:start -->", "<!-- featured:end -->"
    if start not in text or end not in text:
        return False
    head, rest = text.split(start, 1)
    _, tail = rest.split(end, 1)
    open(README, "w", encoding="utf-8").write(f"{head}{start}\n\n{block}\n\n{end}{tail}")
    return True


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--user", required=True, help="GitHub login, e.g. octocat")
    a = ap.parse_args()
    os.makedirs(ASSETS, exist_ok=True)

    print(f"fetching github.com/{a.user} ...")
    user = gh.get_user(a.user)
    repos = gh.get_repos(a.user)
    days = gh.get_contributions(a.user)

    if not days:
        raise SystemExit(
            "Could not read the contribution calendar. Check the username, or set "
            "GITHUB_TOKEN for higher rate limits."
        )

    current, longest = gh.streaks(days, today=date.today())
    spans = gh.streak_detail(days, today=date.today())
    agg = gh.totals(repos)

    active_days = sum(1 for c in days.values() if c > 0)
    best_day, best_count = max(days.items(), key=lambda kv: (kv[1], kv[0]))

    # " ".join(split()) collapses the double space in the display name on GitHub, which otherwise
    # lands in the card, the SVG aria-label and the README as a visible typo.
    display_name = " ".join((user.get("name") or user["login"]).split())

    stats = {
        "login": user["login"],
        "name": display_name,
        "contributions": sum(days.values()),
        "current_streak": current,
        "longest_streak": longest,
        "repos": user.get("public_repos", len(repos)),
        "stars": agg["stars"],
        "followers": user.get("followers", 0),
        "languages": agg["languages"],
        "top_repos": [
            {
                "name": r["name"],
                "description": r.get("description"),
                "language": r.get("language"),
                "stars": r.get("stargazers_count", 0),
                "url": r["html_url"],
            }
            for r in gh.top_repos(repos)
        ],
        "active_days": active_days,
        "total_days": len(days),
        "avg_active": (sum(days.values()) / active_days) if active_days else 0.0,
        "best_day": {"count": best_count, "label": best_day.strftime("%b %-d")},
        "monthly": gh.monthly(days),
        "current_start": spans["current_start"].isoformat() if spans["current_start"] else None,
        "current_end": spans["current_end"].isoformat() if spans["current_end"] else None,
        "longest_start": spans["longest_start"].isoformat() if spans["longest_start"] else None,
        "longest_end": spans["longest_end"].isoformat() if spans["longest_end"] else None,
        "built": date.today().isoformat(),
        "work": gh.get_work_totals(user["login"]),
        "badges": gh.get_badge_stats(user["login"]),
        "best_repo_stars": max((r.get("stargazers_count", 0) for r in repos), default=0),
    }

    stats["focus"] = render_cards.focus_specs(stats)
    stats["featured"] = render_cards.featured_repos(repos)

    if spans["longest_start"] and spans["longest_end"]:
        stats["longest_label"] = (
            f"{spans['longest_start'].strftime('%b %-d')} - "
            f"{spans['longest_end'].strftime('%b %-d')}"
        )

    make_heatmap_svg.render(days, stats["login"], os.path.join(ASSETS, "contrib-heatmap.svg"))
    make_banner_svg.render(stats, os.path.join(ASSETS, "banner.svg"))
    make_achievements_svg.render(stats, os.path.join(ASSETS, "achievements.svg"))
    make_badges_svg.render(stats, os.path.join(ASSETS, "badges.svg"))
    cards_written = render_cards.render_all(stats, os.path.join(ASSETS, "cards"))
    cards.render_stats(stats, os.path.join(ASSETS, "stats.svg"))
    try:
        # A photo dropped in assets/photo.* beats the avatar: the avatar is only
        # 460px, so a real camera file is the only way to get finer ASCII detail.
        photo = next(
            (os.path.join(ASSETS, n) for n in ("photo.jpg", "photo.jpeg", "photo.png", "photo.webp")
             if os.path.exists(os.path.join(ASSETS, n))),
            None,
        )
        source = open(photo, "rb").read() if photo else gh.get_avatar(user["avatar_url"])
        portrait = make_ascii_svg.to_ascii_lines(source)
        cards.render_portrait(
            portrait, stats["name"], stats["login"], os.path.join(ASSETS, "portrait.svg"), stats
        )
        print(f"ok: portrait rebuilt from {os.path.basename(photo) if photo else 'the profile picture'}")
    except Exception as exc:  # keep the previous portrait rather than fail the build
        print(f"skip: portrait not rebuilt ({exc})")
    with open(os.path.join(ASSETS, "data.json"), "w", encoding="utf-8") as fh:
        json.dump(stats, fh, indent=2)

    import verify_layout  # noqa: E402  (same directory, imported after the assets exist)

    problems = verify_layout.verify(
        open(os.path.join(ASSETS, "stats.svg"), encoding="utf-8").read(),
        open(os.path.join(ASSETS, "portrait.svg"), encoding="utf-8").read(),
        stats["login"],
        {
            "banner.svg": open(os.path.join(ASSETS, "banner.svg"), encoding="utf-8").read(),
            "achievements.svg": open(
                os.path.join(ASSETS, "achievements.svg"), encoding="utf-8"
            ).read(),
            "badges.svg": open(os.path.join(ASSETS, "badges.svg"), encoding="utf-8").read(),
        },
        {
            os.path.basename(path): open(path, encoding="utf-8").read()
            for path in cards_written
        },
    )
    if problems:
        for p in problems:
            print(f"layout: {p}", file=sys.stderr)
        raise SystemExit("layout check failed — refusing to publish misaligned art")

    if splice_readme(render_featured(stats)):
        print("ok: README featured section refreshed")

    print(
        f"ok: {stats['contributions']} contributions, "
        f"{current}d current streak, {longest}d longest, {stats['repos']} repos"
    )


if __name__ == "__main__":
    main()
