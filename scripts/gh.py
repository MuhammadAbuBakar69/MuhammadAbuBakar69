"""Small GitHub API client used by the profile-asset generators.

Works with or without a token:
  * no token  -> unauthenticated REST (60 req/hour) + the public contributions page
  * GITHUB_TOKEN set -> 5000 req/hour and the GraphQL contribution calendar

Set GITHUB_TOKEN in the environment (the bundled workflow does it automatically).
"""
from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from datetime import date, datetime, timedelta

API = "https://api.github.com"
UA = "profile-readme-builder"
TOKEN = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN") or ""


def _get(url: str) -> tuple[str, dict]:
    req = urllib.request.Request(url)
    req.add_header("User-Agent", UA)
    req.add_header("Accept", "application/vnd.github+json")
    if TOKEN:
        req.add_header("Authorization", f"Bearer {TOKEN}")
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace"), dict(r.headers)


def get_user(login: str) -> dict:
    body, _ = _get(f"{API}/users/{login}")
    return json.loads(body)


def get_repos(login: str, limit: int = 100) -> list[dict]:
    repos: list[dict] = []
    page = 1
    while len(repos) < limit:
        body, _ = _get(
            f"{API}/users/{login}/repos?per_page=100&page={page}"
            "&sort=updated&type=owner"
        )
        chunk = json.loads(body)
        if not chunk:
            break
        repos.extend(chunk)
        page += 1
    return repos


# --- contributions -----------------------------------------------------------

_CELL = re.compile(
    r'<td[^>]*?data-date="(\d{4}-\d{2}-\d{2})"[^>]*?id="([^"]+)"[^>]*?'
    r'data-level="(\d)"',
    re.S,
)
_TIP = re.compile(r'<tool-tip[^>]*?for="([^"]+)"[^>]*?>(.*?)</tool-tip>', re.S)


def _count_from_tip(text: str) -> int:
    text = re.sub(r"\s+", " ", text).strip()
    if text.lower().startswith("no contributions"):
        return 0
    m = re.match(r"(\d+) contribution", text)
    return int(m.group(1)) if m else 0


def get_contributions(login: str, year: int | None = None) -> dict[date, int]:
    """Return {date: contribution_count} using the public calendar page."""
    url = f"https://github.com/users/{login}/contributions"
    if year:
        url += f"?tab=overview&from={year}-01-01&to={year}-12-31"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        html = r.read().decode("utf-8", "replace")

    tips = {tid: _count_from_tip(txt) for tid, txt in _TIP.findall(html)}
    days: dict[date, int] = {}
    for iso, cell_id, _level in _CELL.findall(html):
        try:
            days[date.fromisoformat(iso)] = tips.get(cell_id, 0)
        except ValueError:
            continue
    return days


def streaks(days: dict[date, int], today: date | None = None) -> tuple[int, int]:
    """(current_streak, longest_streak) in days, ignoring empty days."""
    today = today or date.today()
    active = sorted(d for d, c in days.items() if c > 0)
    if not active:
        return 0, 0

    longest = run = 1
    for prev, cur in zip(active, active[1:]):
        run = run + 1 if (cur - prev).days == 1 else 1
        longest = max(longest, run)

    # current streak: walk backwards from today (today may still be empty)
    cursor = today if days.get(today, 0) > 0 else today - timedelta(days=1)
    current = 0
    while days.get(cursor, 0) > 0:
        current += 1
        cursor -= timedelta(days=1)
    return current, longest


def totals(repos: list[dict]) -> dict:
    stars = sum(r.get("stargazers_count", 0) for r in repos)
    forks = sum(r.get("forks_count", 0) for r in repos)
    langs: dict[str, int] = {}
    for r in repos:
        if r.get("fork"):
            continue
        if r.get("language"):
            langs[r["language"]] = langs.get(r["language"], 0) + 1
    return {"stars": stars, "forks": forks, "languages": langs}


def top_repos(repos: list[dict], n: int = 6) -> list[dict]:
    own = [r for r in repos if not r.get("fork") and not r.get("archived")]
    own.sort(key=lambda r: (r.get("stargazers_count", 0), r.get("updated_at", "")), reverse=True)
    return own[:n]
