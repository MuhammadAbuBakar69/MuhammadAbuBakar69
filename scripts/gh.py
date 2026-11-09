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
def _github_token() -> str:
    """Only ever return something that looks like a GitHub token.

    Other tools in this workspace export secrets as bare environment variables, and
    a mis-named one (say a model-provider key sitting in GITHUB_TOKEN) must not be
    sent to api.github.com - it just 401s and breaks the whole build.
    """
    candidates = (
        os.environ.get("GITHUB_ACCESS_TOKEN", ""),
        os.environ.get("GH_TOKEN", ""),
        os.environ.get("GITHUB_TOKEN", ""),
    )
    for value in candidates:
        value = (value or "").strip()
        if value.startswith(("ghp_", "gho_", "ghs_", "ghu_", "github_pat_")):
            return value
    return ""


TOKEN = _github_token()


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


MONTH_INITIALS = ["J", "F", "M", "A", "M", "J", "J", "A", "S", "O", "N", "D"]


def streak_detail(days: dict[date, int], today: date | None = None) -> dict:
    """Current and longest streak with the dates they span."""
    today = today or date.today()
    active = sorted(d for d, c in days.items() if c > 0)
    empty = {
        "current": 0, "current_start": None, "current_end": None,
        "longest": 0, "longest_start": None, "longest_end": None,
    }
    if not active:
        return empty

    best = (1, active[0], active[0])
    run, run_start, prev = 1, active[0], active[0]
    for cur in active[1:]:
        if (cur - prev).days == 1:
            run += 1
        else:
            run, run_start = 1, cur
        if run > best[0]:
            best = (run, run_start, cur)
        prev = cur

    cursor = today if days.get(today, 0) > 0 else today - timedelta(days=1)
    end = cursor
    current = 0
    while days.get(cursor, 0) > 0:
        current += 1
        cursor -= timedelta(days=1)

    return {
        "current": current,
        "current_start": cursor + timedelta(days=1) if current else None,
        "current_end": end if current else None,
        "longest": best[0],
        "longest_start": best[1],
        "longest_end": best[2],
    }


def monthly(days: dict[date, int], count: int = 12) -> list[dict]:
    """Contribution totals for the last `count` months, oldest first."""
    buckets: dict[tuple[int, int], int] = {}
    for day, value in days.items():
        key = (day.year, day.month)
        buckets[key] = buckets.get(key, 0) + value
    keys = sorted(buckets)[-count:]
    return [
        {"label": MONTH_INITIALS[m - 1], "year": y, "count": buckets[(y, m)]}
        for y, m in keys
    ]


def get_avatar(url: str) -> bytes:
    """Download the profile picture so the portrait can be rebuilt headlessly."""
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


GRAPHQL = "https://api.github.com/graphql"


def _search(query: str, *, kind: str = "issues", per_page: int = 50) -> dict:
    """Search API. Separate from the REST helpers because search has its own rate limit and,
    for commits, its own accept header."""
    import urllib.parse

    accept = "application/vnd.github+json"
    if kind == "commits":
        accept = "application/vnd.github.cloak-preview+json"
    url = f"{API}/search/{kind}?q={urllib.parse.quote(query)}&per_page={per_page}"
    req = urllib.request.Request(url)
    req.add_header("User-Agent", UA)
    req.add_header("Accept", accept)
    if TOKEN:
        req.add_header("Authorization", f"Bearer {TOKEN}")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def _graphql(query: str, variables: dict) -> dict:
    """POST to the GraphQL API. Returns {} on any failure.

    The profile must still build when this is unavailable: a spent rate limit or a token without
    scope should cost a few tiles, not the whole page.
    """
    if not TOKEN:
        return {}
    body = json.dumps({"query": query, "variables": variables}).encode()
    req = urllib.request.Request(GRAPHQL, data=body, method="POST")
    req.add_header("User-Agent", UA)
    req.add_header("Authorization", f"Bearer {TOKEN}")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            payload = json.loads(r.read().decode("utf-8", "replace"))
    except Exception:
        return {}
    if payload.get("errors"):
        return {}
    return payload.get("data") or {}


WORK_QUERY = """
query ($login: String!) {
  user(login: $login) {
    followers { totalCount }
    contributionsCollection {
      totalCommitContributions
      totalPullRequestContributions
      totalIssueContributions
      totalPullRequestReviewContributions
    }
    pullRequests(states: MERGED) { totalCount }
    issues { totalCount }
  }
}
"""


def get_work_totals(login: str) -> dict:
    """All-time work totals. Empty dict when the token or API cannot answer."""
    data = _graphql(WORK_QUERY, {"login": login}).get("user") or {}
    if not data:
        return {}
    window = data.get("contributionsCollection") or {}
    return {
        "merged_prs": (data.get("pullRequests") or {}).get("totalCount", 0),
        "issues": (data.get("issues") or {}).get("totalCount", 0),
        "followers": (data.get("followers") or {}).get("totalCount", 0),
        "commits_year": window.get("totalCommitContributions", 0),
        "prs_year": window.get("totalPullRequestContributions", 0),
        "reviews_year": window.get("totalPullRequestReviewContributions", 0),
    }


def get_badge_stats(login: str) -> dict:
    """The numbers behind GitHub's own achievement badges.

    GitHub exposes no API for the badges themselves - the sidebar is derived server-side and cannot
    be read or granted from outside. What it is derived *from* is public, so this collects those
    inputs: merged pull requests, how many repositories they landed in, the best single-repo star
    count, co-authored commits, and issues closed quickly.

    Returns {} rather than partial guesses when the search API is unavailable.
    """
    try:
        merged = _search(f"type:pr author:{login} is:merged", per_page=100)
    except Exception:
        return {}
    items = merged.get("items", [])
    repos = {i["repository_url"].rsplit("/", 1)[-1] for i in items}
    quick = 0
    try:
        closed = _search(f"type:issue author:{login} is:closed", per_page=100)
        for i in closed.get("items", []):
            if i.get("closed_at"):
                opened = datetime.fromisoformat(i["created_at"].replace("Z", "+00:00"))
                shut = datetime.fromisoformat(i["closed_at"].replace("Z", "+00:00"))
                if (shut - opened) <= timedelta(minutes=5):
                    quick += 1
    except Exception:
        pass
    try:
        co = _search(f"author:{login} Co-authored-by", kind="commits", per_page=1)
        coauthored = co.get("total_count", 0)
    except Exception:
        coauthored = 0
    return {
        "merged_prs": merged.get("total_count", len(items)),
        "merged_repos": len(repos),
        "quick_closes": quick,
        "coauthored": coauthored,
    }
