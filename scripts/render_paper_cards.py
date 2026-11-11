"""The README card set: paper, ink, one colour per world.

Visual system matched to the reference profile: light paper canvas, Instrument Serif display type,
Geist for body, Geist Mono for labels, a single accent colour per card, and CSS/SMIL animation that
degrades to a still image under prefers-reduced-motion.

Content is this account's own. Everything printed here comes from the stats dict built by build.py
from the GitHub API, so no number is typed by hand.
"""
from __future__ import annotations

import base64
import os
import re
from datetime import date
from html import escape

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(os.path.dirname(HERE), "fonts")

PAPER = "#f3f3f1"
PAPER_DEEP = "#e2e2de"
INK = "#111111"
INK_SOFT = "#3a3a3c"
MUTED = "#6e6e73"
RULE = "#dcdcd7"
BLUE = "#2f55ff"
RED = "#ef3b2d"
YELLOW = "#ffc81a"

W = 880
GAP = 12
BOTTOM = 12
COL = W / 3
TILE_W, TILE_H = W / 3 - 8, 210
REPO_W, REPO_H = W / 3 - 8, 176

SERIF = "'Instrument Serif', Georgia, serif"
SANS = "Geist, system-ui, -apple-system, sans-serif"
MONO = "'Geist Mono', ui-monospace, SFMono-Regular, Menlo, monospace"

FONT_FILES = {
    "serif": ("Instrument Serif", "normal", 400, "serif-400.woff"),
    "serif-i": ("Instrument Serif", "italic", 400, "serif-italic.woff"),
    "sans": ("Geist", "normal", 400, "geist-400.woff"),
    "sans-b": ("Geist", "normal", 600, "geist-600.woff"),
    "mono": ("Geist Mono", "normal", 400, "geistmono-400.woff"),
}

CSS = """
@keyframes rise{from{opacity:0;transform:translateY(16px)}to{opacity:1;transform:none}}
@keyframes fade{from{opacity:0}to{opacity:1}}
@keyframes grow{from{transform:scaleY(0)}to{transform:scaleY(1)}}
@keyframes pop{0%{opacity:0;transform:scale(.3)}70%{opacity:1;transform:scale(1.15)}100%{opacity:1;transform:none}}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.25}}
@keyframes nudgeup{0%,100%{transform:none}50%{transform:translate(3px,-3px)}}
@keyframes tilein{0%{opacity:0;transform:translateY(90px) scale(.6) rotate(-9deg)}55%{opacity:1;transform:translateY(-10px) scale(1.05) rotate(2deg)}75%{transform:translateY(3px) scale(.98) rotate(-.8deg)}100%{opacity:1;transform:none}}
@keyframes sheen{0%{transform:translateX(-260px) skewX(-20deg)}22%,100%{transform:translateX(420px) skewX(-20deg)}}
.r{opacity:0;animation:rise .8s cubic-bezier(.2,.7,.2,1) both;transform-box:fill-box}
.f{opacity:0;animation:fade .9s ease-out both}
.g{transform-box:fill-box;transform-origin:bottom;transform:scaleY(0);animation:grow .8s cubic-bezier(.2,.7,.2,1) both}
.p{opacity:0;transform-box:fill-box;transform-origin:center;animation:pop .4s ease-out both}
.live{animation:pulse 1.6s ease-in-out infinite}
.nu{transform-box:fill-box;animation:nudgeup 1.8s ease-in-out infinite}
.ti{opacity:0;transform-box:fill-box;transform-origin:50% 60%;animation:tilein 1.1s cubic-bezier(.2,.8,.2,1) both}
.sh{animation:sheen 5s ease-in-out infinite}
/* Hover rules below only fire when the SVG is inlined or opened directly. Inside an img element, which is
   how GitHub renders a README image, the document has no pointer, so these are a bonus, not the
   effect you see on the profile. The breathing glow and the dot tint carry the colour there. */
.portrait{transition:filter .35s ease}
.portrait:hover{filter:drop-shadow(0 0 22px rgba(47,85,255,.55))}
.breathe{animation:breathe 6s ease-in-out infinite}
@keyframes breathe{0%,100%{opacity:.55}50%{opacity:1}}
@media (prefers-reduced-motion: reduce){.r,.f,.g,.p,.live,.nu,.ti,.breathe{animation:none!important;opacity:1!important;transform:none!important}.sh{display:none}}
"""


def font_face(keys):
    out = []
    for key in keys:
        fam, style, weight, fn = FONT_FILES[key]
        b64 = base64.b64encode(open(os.path.join(FONTS, fn), "rb").read()).decode()
        out.append(
            f"@font-face{{font-family:'{fam}';font-style:{style};font-weight:{weight};"
            f"src:url(data:font/woff;base64,{b64}) format('woff')}}"
        )
    return "".join(out)


def wrap(text, n):
    lines, line = [], ""
    for word in text.split():
        if line and len(line) + 1 + len(word) > n:
            lines.append(line)
            line = word
        else:
            line = f"{line} {word}".strip()
    return lines + [line] if line else lines


def text_lines(x, y, lines, lh, attrs):
    return "".join(
        f'<text x="{x}" y="{y + i * lh}" {attrs}>{escape(line)}</text>'
        for i, line in enumerate(lines)
    )


def d(seconds):
    return f'style="animation-delay:{seconds:.2f}s"'


def svg(w, h, body, fonts, label, left=0, right=0, bottom=BOTTOM):
    if left:
        body = f'<g transform="translate({left:.3f} 0)">{body}</g>'
    w, h = w + left + right, h + bottom
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w:.3f}" height="{h}" '
        f'viewBox="0 0 {w:.3f} {h}" role="img" aria-label="{escape(label)}">'
        f"<title>{escape(label)}</title><style>{font_face(fonts)}{CSS}</style>{body}</svg>"
    )


def _write(out_dir, name, content):
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, name)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content)
    return path


def count_up(num, word, x, y, attrs, begin, dur=1.1, frames=18):
    """Count from 0 with SMIL frames, which is the only animation primitive that survives <img>."""
    match = re.match(r"([\d.]+)(.*)", str(num))
    value, suffix = float(match.group(1)), match.group(2)
    dec = len(match.group(1).split(".")[1]) if "." in match.group(1) else 0
    tail = f' <tspan font-style="italic">{escape(word)}</tspan>'
    out = []
    for i in range(frames + 1):
        eased = 1 - (1 - i / frames) ** 3
        text = f"{num}{suffix}" if i == frames else f"{value * eased:.{dec}f}{suffix}"
        on = begin + dur * i / frames
        off = (
            ""
            if i == frames
            else f'<set attributeName="opacity" to="0" begin="{begin + dur * (i + 1) / frames:.3f}s"/>'
        )
        out.append(
            f'<text x="{x}" y="{y}" {attrs} opacity="0">{escape(text)}{tail}'
            f'<set attributeName="opacity" to="1" begin="{on:.3f}s"/>{off}</text>'
        )
    return "".join(out)


def hero(stats, portrait_dots, out_dir):
    first, *rest = (stats.get("name") or stats["login"]).split(" ", 1)
    second = rest[0] if rest else ""
    tagline = "I build AI products that ship: agents, RAG pipelines, and the web apps around them."
    # The portrait is vector dots, scaled to fill the right block (520..848 wide, 46..330 tall).
    dots_markup, dots_w, dots_h = portrait_dots
    # Target box on the right of the hero: as tall as the card allows, without touching the name.
    box_x, box_y, box_w, box_h = 502.0, 48.0, 344.0, 324.0
    scale = min(box_w / dots_w, box_h / dots_h)
    off_x = box_x + (box_w - dots_w * scale) / 2
    off_y = box_y + (box_h - dots_h * scale) / 2
    box_cx = off_x + dots_w * scale / 2
    box_cy = off_y + dots_h * scale / 2
    rows = (
        f'<g class="f" style="animation-delay:.25s" '
        f'transform="translate({off_x:.1f} {off_y:.1f}) scale({scale:.4f})">{dots_markup}</g>'
    )
    body = f"""
<defs>
  <clipPath id="heroClip"><rect width="{W}" height="420" rx="14"/></clipPath>
  <linearGradient id="dotTint" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="{INK}"/>
    <stop offset=".55" stop-color="#1b3fc9"/>
    <stop offset="1" stop-color="{BLUE}"/>
  </linearGradient>
  <radialGradient id="dotGlow" cx=".5" cy=".42" r=".62">
    <stop offset="0" stop-color="{BLUE}" stop-opacity=".22"/>
    <stop offset=".62" stop-color="{BLUE}" stop-opacity=".07"/>
    <stop offset="1" stop-color="{BLUE}" stop-opacity="0"/>
  </radialGradient>
  <linearGradient id="shine" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="600" y2="0">
    <stop offset="0" stop-color="{INK}"/><stop offset=".42" stop-color="{INK}"/>
    <stop offset=".5" stop-color="{BLUE}"/><stop offset=".58" stop-color="{INK}"/>
    <stop offset="1" stop-color="{INK}"/>
    <animateTransform attributeName="gradientTransform" type="translate" values="-600 0;600 0;600 0"
      keyTimes="0;.45;1" dur="7s" begin="1.6s" repeatCount="indefinite"/>
  </linearGradient>
</defs>
<rect width="{W}" height="420" rx="14" fill="{PAPER}"/>
<g class="f" {d(0)}>
  <rect class="live" x="48" y="49" width="8" height="8" rx="2" fill="{BLUE}"/>
  <text x="66" y="57" font-family="{MONO}" font-size="12" letter-spacing="1" fill="{MUTED}">FULL-STACK DEVELOPER AT KARACHI</text>
</g>
<text class="r" {d(0.15)} x="44" y="190" font-family="{SERIF}" font-size="96" letter-spacing="-2" fill="{INK}">{escape(first)}</text>
<text class="r" {d(0.3)} x="44" y="282" font-family="{SERIF}" font-style="italic" font-size="96" letter-spacing="-2" fill="url(#shine)">{escape(second)}</text>
<g class="r" {d(0.55)}>
  {text_lines(48, 326, wrap(tagline, 46), 26, f'font-family="{SANS}" font-size="17" fill="{INK_SOFT}"')}
</g>
<g class="f" {d(0.8)}>
  <text x="48" y="398" font-family="{MONO}" font-size="13" fill="{INK}">withabubakar.netlify.app</text>
  <text class="nu" x="272" y="398" font-family="{MONO}" font-size="13" fill="{BLUE}">&#8599;</text>
</g>
<g class="portrait" clip-path="url(#heroClip)">
  <ellipse class="breathe" cx="{box_cx:.1f}" cy="{box_cy:.1f}" rx="{box_w / 2:.1f}" ry="{box_h / 2:.1f}" fill="url(#dotGlow)"/>
  <g fill="url(#dotTint)">{rows}</g>
</g>
"""
    label = f"{stats.get('name')}. {tagline}"
    return _write(out_dir, "hero.svg", svg(W, 420, body, ["serif", "serif-i", "sans", "mono"], label))


def tile(name, label, color, on, num, word, blurb, delay, pos, out_dir):
    lines = wrap(blurb, 34)
    blurbs = "".join(
        f'<text class="r" {d(delay + 0.75 + i * 0.1)} x="24" y="{150 + i * 20}" font-family="{SANS}" '
        f'font-size="14" fill="{on}" opacity=".92">{escape(line)}</text>'
        for i, line in enumerate(lines)
    )
    body = f"""
<defs>
  <clipPath id="card"><rect width="{TILE_W}" height="{TILE_H}" rx="14"/></clipPath>
  <clipPath id="slot"><rect x="0" y="62" width="{TILE_W}" height="62"/></clipPath>
  <linearGradient id="gl" x1="0" x2="1">
    <stop offset="0" stop-color="#fff" stop-opacity="0"/>
    <stop offset=".5" stop-color="#fff" stop-opacity=".35"/>
    <stop offset="1" stop-color="#fff" stop-opacity="0"/>
  </linearGradient>
</defs>
<g class="ti" {d(delay)}>
  <g clip-path="url(#card)">
    <rect width="{TILE_W}" height="{TILE_H}" fill="{color}"/>
    <rect class="sh" style="animation-delay:{delay + 1.4:.2f}s" x="0" y="-20" width="90"
      height="{TILE_H + 40}" fill="url(#gl)" transform="translate(-260 0)"/>
  </g>
  <text class="f" {d(delay + 0.35)} x="24" y="38" font-family="{MONO}" font-size="12"
    letter-spacing="1.2" fill="{on}">{label}</text>
  <text class="f" {d(delay + 0.5)} x="{TILE_W - 36}" y="38" font-family="{MONO}" font-size="14"
    fill="{on}">&#8594;</text>
  <g clip-path="url(#slot)">{count_up(num, word, 22, 112, f'font-family="{SERIF}" font-size="44" fill="{on}"', delay + 0.45)}</g>
  {blurbs}
</g>
"""
    return _write(
        out_dir,
        f"{name}.svg",
        svg(TILE_W, TILE_H, body, ["serif", "serif-i", "sans", "mono"], f"{label}: {num} {word}. {blurb}",
            left=4 * pos, right=8 - 4 * pos),
    )


def activity(stats, out_dir):
    h = 340
    monthly = stats["monthly"][-12:]
    best_total = max((m["count"] for m in monthly[:-1]), default=0)
    x0, x1, base, max_h, gap = 40, 600, 306, 118, 10
    bw = (x1 - x0 - gap * (len(monthly) - 1)) / len(monthly)
    bars = []
    for i, month in enumerate(monthly):
        partial = i == len(monthly) - 1
        best = month["count"] == best_total and best_total > 0
        height = max(4, round(month["count"] / best_total * max_h)) if best_total else 4
        x = x0 + i * (bw + gap)
        fill = BLUE if best else ("#c9c9c4" if partial else INK)
        bars.append(
            f'<rect class="g" style="animation-delay:{2.2 + i * 0.07:.2f}s" x="{x:.1f}" y="{base - height}" '
            f'width="{bw:.1f}" height="{height}" rx="4" fill="{fill}">'
            f"<title>{escape(month['label'])}: {month['count']:,}</title></rect>"
            f'<text class="f" style="animation-delay:{2.2 + i * 0.07:.2f}s" x="{x + bw / 2:.1f}" '
            f'y="{base + 22}" text-anchor="middle" font-family="{MONO}" font-size="11" fill="{MUTED}">'
            f"{escape(month['label'])}</text>"
        )
        if best:
            bars.append(
                f'<text class="p" style="animation-delay:3.2s" x="{x + bw / 2:.1f}" y="{base - height - 10}" '
                f'text-anchor="middle" font-family="{MONO}" font-size="11" fill="{BLUE}">{month["count"]:,}</text>'
            )

    side = [
        (f'{stats["current_streak"]} <tspan font-style="italic">days</tspan>', "current streak on GitHub"),
        (f'{stats["active_days"]}<tspan fill="#8e8e93"> / {stats["total_days"]}</tspan>', "days with a commit"),
        (f'{stats["best_day"]["count"]}', f'on the busiest day ({escape(stats["best_day"]["label"])})'),
    ]
    right = []
    for i, (big, small) in enumerate(side):
        y = 104 + i * 92
        right.append(
            f'<g class="r" {d(2.6 + i * 0.15)}>'
            f'<text x="650" y="{y}" font-family="{SERIF}" font-size="40" fill="{INK}">{big}</text>'
            f'<text x="650" y="{y + 24}" font-family="{SANS}" font-size="13" fill="{MUTED}">{small}</text></g>'
        )
        if i < 2:
            right.append(f'<rect class="f" {d(2.6)} x="650" y="{y + 44}" width="190" height="1" fill="{RULE}"/>')


    # Milestone progress: the next round number of contributions, measured not promised.
    total = stats["contributions"]
    target = 1000 if total < 1000 else (2500 if total < 2500 else 5000)
    left_to = max(0, target - total)
    frac = min(1.0, total / target)
    milestone = (
        f'<g class="r" {d(2.5)}>'
        f'<rect x="40" y="136" width="560" height="6" rx="3" fill="{RULE}"/>'
        f'<rect class="g" style="animation-delay:2.6s" x="40" y="136" width="{560 * frac:.1f}" '
        f'height="6" rx="3" fill="{BLUE}"/>'
        f'<text x="40" y="166" font-family="{MONO}" font-size="11" fill="{MUTED}">'
        f'{total:,} of {target:,} &#183; {left_to:,} to go</text>'
        f'</g>'
    )
    body = f"""
<rect width="{W}" height="{h}" rx="14" fill="{PAPER}"/>
<text class="f" {d(1.9)} x="40" y="58" font-family="{MONO}" font-size="12" letter-spacing="1" fill="{MUTED}">THE LAST 12 MONTHS ON GITHUB</text>
<text class="r" {d(2.0)} x="38" y="114" font-family="{SERIF}" font-size="52" fill="{INK}">{stats["contributions"]:,} <tspan font-style="italic">contributions</tspan></text>
{milestone}
{"".join(bars)}
{"".join(right)}
"""
    label = f'{stats["contributions"]:,} contributions in the last year'
    return _write(out_dir, "activity.svg", svg(W, h, body, ["serif", "serif-i", "sans", "mono"], label))


def repo_card(index, name, desc, meta, color, out_dir):
    delay = 4.6 + index * 0.12
    body = f"""
<rect width="{REPO_W}" height="{REPO_H}" rx="14" fill="{PAPER}"/>
<g class="r" {d(delay)}>
  <rect x="24" y="30" width="8" height="8" rx="2" fill="{color}"/>
  <text x="40" y="39" font-family="{SANS}" font-weight="600" font-size="18" fill="{INK}">{escape(name)}</text>
  {text_lines(24, 72, wrap(desc, 34), 21, f'font-family="{SANS}" font-size="14" fill="{INK_SOFT}"')}
  <text x="24" y="{REPO_H - 24}" font-family="{MONO}" font-size="12" fill="{MUTED}">{escape(meta)}</text>
</g>
"""
    return _write(
        out_dir,
        f"repo-{name}.svg",
        svg(REPO_W, REPO_H, body, ["sans", "sans-b", "mono"], f"{name}: {desc}",
            left=4 * index, right=8 - 4 * index),
    )


def section_title(text, italic, theme, out_dir):
    fg = "#e6edf3" if theme == "dark" else INK
    body = (
        f'<text class="r" {d(4.4)} x="2" y="46" font-family="{SERIF}" font-size="34" fill="{fg}">'
        f'{escape(text)} <tspan font-style="italic">{escape(italic)}</tspan></text>'
    )
    return _write(
        out_dir,
        f"title-building-{theme}.svg",
        svg(W, 64, body, ["serif", "serif-i"], f"{text} {italic}", bottom=0),
    )


BLUE_STEPS = [PAPER_DEEP, "#c8d3ff", "#94a8ff", "#6280ff", BLUE, "#1a3be0"]


def _level(count):
    if count == 0:
        return 0
    if count <= 5:
        return 1
    if count <= 15:
        return 2
    if count <= 30:
        return 3
    if count <= 50:
        return 4
    return 5


def heatmap(days, total, out_dir):
    items = sorted(days.items(), key=lambda kv: kv[0])

    def _as_date(value):
        return value if isinstance(value, date) else date.fromisoformat(str(value))

    first = _as_date(items[0][0])
    lead = (first.weekday() + 1) % 7
    cell, step, gx, gy = 12, 15, 44, 96
    cells, months, seen = [], [], set()
    for i, (day, count) in enumerate(items):
        col, row = divmod(i + lead, 7)
        current = _as_date(day)
        if current.day <= 7 and (current.year, current.month) not in seen and row == 0:
            seen.add((current.year, current.month))
            months.append((col, current.strftime("%b")))
        cells.append(
            f'<rect class="p" style="animation-delay:{1.0 + col * 0.03 + row * 0.02:.2f}s" '
            f'x="{gx + col * step}" y="{gy + row * step}" width="{cell}" height="{cell}" rx="3" '
            f'fill="{BLUE_STEPS[_level(count)]}"><title>{day}: {count} contribution'
            f'{"s" if count != 1 else ""}</title></rect>'
        )
    ncols = (len(items) + lead + 6) // 7
    right = gx + ncols * step - 3
    labels = "".join(
        f'<text x="{gx + col * step}" y="{gy + 7 * step + 16}" font-family="{MONO}" font-size="11" '
        f'fill="{MUTED}">{month}</text>'
        for col, month in months
        if col < ncols - 12
    )
    legend_x = right - len(BLUE_STEPS) * 14
    legend = "".join(
        f'<rect x="{legend_x + i * 14}" y="{gy + 7 * step + 6}" width="11" height="11" rx="2.5" fill="{c}"/>'
        for i, c in enumerate(BLUE_STEPS)
    )
    h = gy + 7 * step + 44
    body = f"""
<rect width="{W}" height="{h}" rx="14" fill="{PAPER}"/>
<text class="r" {d(0.8)} x="42" y="62" font-family="{SERIF}" font-size="34" fill="{INK}">Every day, <tspan font-style="italic" fill="{BLUE}">in blue</tspan></text>
<text class="f" {d(0.8)} x="{right}" y="60" text-anchor="end" font-family="{MONO}" font-size="12" letter-spacing="1" fill="{MUTED}">REFRESHED DAILY</text>
{"".join(cells)}
<g class="f" {d(2.4)}>{labels}
<text x="{legend_x - 8}" y="{gy + 7 * step + 16}" text-anchor="end" font-family="{MONO}" font-size="11" fill="{MUTED}">less</text>
{legend}
<text x="{legend_x + len(BLUE_STEPS) * 14 + 2}" y="{gy + 7 * step + 16}" font-family="{MONO}" font-size="11" fill="{MUTED}">more</text></g>
"""
    return _write(out_dir, "heatmap.svg", svg(W, h, body, ["serif", "serif-i", "mono"],
                                              f"{total:,} contributions in the last year"))


FEATURED_ORDER = ("threadmind-ai", "jobpilot", "otto")


def featured_repos(repos):
    """The three flagship repos, in the order they should be shown, with API facts attached."""
    by_name = {r["name"].lower(): r for r in repos}
    out = []
    for name in FEATURED_ORDER:
        repo = by_name.get(name)
        if not repo:
            continue
        out.append(
            {
                "name": repo["name"],
                "description": repo.get("description") or "Work in progress.",
                "language": repo.get("language"),
                "stars": repo.get("stargazers_count", 0),
                "topics": repo.get("topics") or [],
                "url": repo.get("html_url"),
            }
        )
    for repo in repos:
        if len(out) >= 3:
            break
        if repo["name"] not in {r["name"] for r in out} and repo.get("description"):
            out.append(
                {
                    "name": repo["name"],
                    "description": repo["description"],
                    "language": repo.get("language"),
                    "stars": repo.get("stargazers_count", 0),
                    "topics": repo.get("topics") or [],
                    "url": repo.get("html_url"),
                }
            )
    return out[:3]


def portrait_rows_from(svg_text):
    """Pull the ASCII rows out of the generated portrait so the hero and the pane agree."""
    rows = re.findall(r'<tspan[^>]*>([^<]*)</tspan>', svg_text)
    return [row for row in rows if row.strip()]


def render_all(stats, days, portrait_dots, out_dir):
    written = [hero(stats, portrait_dots, out_dir)]
    written.append(
        tile("focus-build", "BUILD", BLUE, "#ffffff", str(stats["repos"]), "repos",
             "Production web apps in React, Next.js and TypeScript, shipped and maintained.", 3.1, 0, out_dir)
    )
    written.append(
        tile("focus-automate", "AUTOMATE", RED, "#ffffff", "3", "flagships",
             "ThreadMind, jobpilot and otto: agents, RAG pipelines and CLI tooling.", 3.35, 1, out_dir)
    )
    written.append(
        tile("focus-write", "WRITE", YELLOW, INK, str(stats["active_days"]), "days",
             "Active on GitHub this year, mostly in public, mostly with AI in the loop.", 3.6, 2, out_dir)
    )
    written.append(activity(stats, out_dir))
    written.append(section_title("What I'm", "building", "dark", out_dir))
    written.append(section_title("What I'm", "building", "light", out_dir))
    written.append(heatmap(days, stats["contributions"], out_dir))
    for i, repo in enumerate(stats["featured"][:3]):
        meta = repo["language"] or "code"
        if repo.get("topics"):
            meta = f"{meta}  ·  {repo['topics'][0]}"
        written.append(repo_card(i, repo["name"], repo["description"], meta,
                                 (BLUE, RED, YELLOW)[i % 3], out_dir))
    return written
