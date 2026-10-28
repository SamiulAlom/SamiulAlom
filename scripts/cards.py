"""SVG card renderer for the profile. Every card is drawn twice: dark and light.

Pure standard library. All text that comes from the GitHub API is escaped.
"""
import html
import math

THEMES = {
    "dark": dict(bg="#0D1117", panel="#151B23", line="#262F3B", ink="#E9EEF3", muted="#8B97A6",
                 amber="#F2A93B", mint="#4FD1A5", blue="#7AA2F7", rose="#F7768E",
                 heat=["#1A212B", "#12463A", "#16735A", "#2FA87D", "#5FE0AE"]),
    "light": dict(bg="#FFFFFF", panel="#F6F5F1", line="#E3DFD5", ink="#1D2329", muted="#5D6773",
                  amber="#B86E00", mint="#0E8A63", blue="#3456C9", rose="#C2314F",
                  heat=["#ECE9E1", "#B5E3CF", "#6CC6A1", "#259A6E", "#0B6B4B"]),
}
SANS = "Inter,'Segoe UI',Helvetica,Arial,sans-serif"
MONO = "'JetBrains Mono',SFMono-Regular,Menlo,Consolas,monospace"

LANG_COLORS = {
    "Python": "#3572A5", "Jupyter Notebook": "#DA5B0B", "JavaScript": "#F1E05A", "TypeScript": "#3178C6",
    "HTML": "#E34C26", "CSS": "#663399", "PHP": "#4F5D95", "C#": "#178600", "C++": "#F34B7D", "C": "#A8B9CC",
    "PLpgSQL": "#336790", "Shell": "#89E051", "Batchfile": "#C1F12E", "Java": "#B07219", "Dart": "#00B4AB",
    "Kotlin": "#A97BFF", "Go": "#00ADD8", "Rust": "#DEA584", "SCSS": "#C6538C", "Vue": "#41B883", "R": "#198CE7",
}
FALLBACK = ["#8B97A6", "#B4A7D6", "#9FC5E8", "#B6D7A8", "#F9CB9C"]


def lang_color(name, i=0):
    return LANG_COLORS.get(name, FALLBACK[i % len(FALLBACK)])


def esc(s):
    return html.escape(str(s), quote=True)


def t(x, y, s, size=14, fill="#000", weight=400, font=SANS, anchor="start", extra=""):
    return (f'<text x="{x}" y="{y}" font-family="{font}" font-size="{size}" font-weight="{weight}" '
            f'fill="{fill}" text-anchor="{anchor}" {extra}>{esc(s)}</text>')


def r(x, y, w, h, fill, rx=10, stroke=None, extra=""):
    s = f' stroke="{stroke}"' if stroke else ""
    return f'<rect x="{x}" y="{y}" width="{max(w, 0):.1f}" height="{h}" rx="{rx}" fill="{fill}"{s} {extra}/>'


def fmt(n):
    if n is None:
        return "—"
    n = int(n)
    if n >= 10000:
        return f"{n / 1000:.1f}k".replace(".0k", "k")
    return f"{n:,}"


def wrap(text, width_px, size):
    """Greedy word wrap using an average glyph width estimate."""
    per = max(int(width_px / (size * 0.53)), 8)
    lines, cur = [], ""
    for word in str(text).split():
        if len(cur) + len(word) + 1 > per and cur:
            lines.append(cur)
            cur = word
        else:
            cur = f"{cur} {word}".strip()
    if cur:
        lines.append(cur)
    return lines


def clip(text, width_px, size):
    per = max(int(width_px / (size * 0.53)), 8)
    text = str(text)
    return text if len(text) <= per else text[: per - 1].rstrip() + "…"


def frame(w, h, body, title, th, extra_style=""):
    style = ("@keyframes blink{0%,49%{opacity:1}50%,100%{opacity:0}}"
             "@keyframes rise{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:none}}"
             ".blink{animation:blink 1.1s steps(1) infinite}"
             ".rise{animation:rise .7s ease-out both}" + extra_style +
             "@media(prefers-reduced-motion:reduce){*{animation:none!important}}")
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
            f'role="img" aria-label="{esc(title)}"><title>{esc(title)}</title><style>{style}</style>'
            f'{r(0.5, 0.5, w - 1, h - 1, th["bg"], 14, th["line"])}{body}</svg>')


def header(x, y, label, th, right=None, w=900):
    out = t(x, y, label, 11, th["amber"], 700, MONO, extra='letter-spacing="1.5"')
    if right:
        out += t(w - x, y, right, 11, th["muted"], 400, MONO, "end")
    return out


# ---------------------------------------------------------------- hero

def hero(d, cfg, th):
    w, h = 900, 290
    roles = cfg.get("roles") or ["Developer"]
    n = len(roles)
    dur = 3.2 * n
    style = "".join(
        f"@keyframes role{i}{{0%{{opacity:0}}{100 * i / n + 2:.2f}%{{opacity:1}}"
        f"{100 * (i + 1) / n - 2:.2f}%{{opacity:1}}{100 * (i + 1) / n:.2f}%{{opacity:0}}100%{{opacity:0}}}}"
        f".role{i}{{opacity:0;animation:role{i} {dur}s linear infinite}}" for i in range(n))
    b = ""
    for gx in range(560, w - 20, 22):
        for gy in range(30, h - 30, 22):
            b += f'<circle cx="{gx}" cy="{gy}" r="1" fill="{th["line"]}"/>'
    b += t(40, 52, f"~/{d['login'].lower()} $ whoami", 13, th["mint"], 500, MONO)
    b += t(40, 104, cfg.get("display_name") or d["name"] or d["login"], 40, th["ink"], 750)
    for i, role in enumerate(roles):
        b += f'<g class="role{i}">' + t(40, 142, role, 20, th["amber"], 600, MONO) + '</g>'
    b += f'<rect class="blink" x="40" y="152" width="11" height="3" fill="{th["amber"]}"/>'
    y = 184
    for line in wrap(d.get("bio") or cfg.get("intro", ""), 470, 14)[:3]:
        b += t(40, y, line, 14, th["muted"])
        y += 21
    meta = " · ".join(x for x in [d.get("location"), f"on GitHub since {d['joined'][:4]}"] if x)
    b += t(40, 258, meta.upper(), 10.5, th["muted"], 600, MONO, extra='letter-spacing="1.2"')
    # live panel
    px, py, pw, ph = 600, 46, 260, 198
    b += r(px, py, pw, ph, th["panel"], 12, th["line"])
    b += f'<circle cx="{px + 20}" cy="{py + 22}" r="4" fill="{th["mint"]}"><animate attributeName="opacity" values="1;.25;1" dur="2s" repeatCount="indefinite"/></circle>'
    b += t(px + 32, py + 26, "LIVE FROM THE GITHUB API", 10, th["muted"], 600, MONO, extra='letter-spacing="1"')
    stats = [("repositories", d["public_repos"]), ("stars", d["stars"]),
             ("followers", d["followers"]), ("contrib · 12 mo", d["year_total"])]
    for i, (label, val) in enumerate(stats):
        cx = px + 20 + (i % 2) * 124
        cy = py + 74 + (i // 2) * 62
        b += t(cx, cy, fmt(val), 28, th["ink"], 700)
        b += t(cx, cy + 20, label, 11, th["muted"], 400, MONO)
    b += t(px + 20, py + ph - 14, f"updated {d['stamp_short']}", 10, th["muted"], 400, MONO)
    b += r(40, h - 16, 140, 3, th["amber"], 1.5) + r(184, h - 16, 60, 3, th["mint"], 1.5) + r(248, h - 16, 24, 3, th["blue"], 1.5)
    return frame(w, h, b, f"{d['name']} — {', '.join(roles)}", th, style)


# ---------------------------------------------------------------- stats

def stats(d, th):
    w, h = 900, 236
    b = header(28, 34, "GITHUB AT A GLANCE", th, f"member for {d['years']} yrs · since {d['joined'][:4]}")
    tiles = [
        ("Public repositories", d["public_repos"], th["amber"]), ("Stars earned", d["stars"], th["amber"]),
        ("Forks of my work", d["forks"], th["amber"]), ("Followers", d["followers"], th["amber"]),
        ("Contributions · 12 mo", d["year_total"], th["mint"]), ("Commits · 12 mo", d["year_commits"], th["mint"]),
        ("Pull requests · all time", d["prs"], th["blue"]), ("Issues · all time", d["issues"], th["blue"]),
    ]
    for i, (label, val, col) in enumerate(tiles):
        x = 28 + (i % 4) * 214
        y = 52 + (i // 4) * 80
        b += f'<g class="rise" style="animation-delay:{i * 60}ms">' + r(x, y, 202, 68, th["panel"], 10, th["line"])
        b += r(x, y + 14, 3, 40, col, 1.5)
        b += t(x + 18, y + 36, fmt(val), 24, th["ink"], 700) + t(x + 18, y + 56, label, 11, th["muted"], 400, MONO) + '</g>'
    b += t(28, 222, f"All-time contributions: {fmt(d['all_time'])} · Repositories contributed to: {fmt(d['contributed_to'])}", 11, th["muted"], 400, MONO)
    return frame(w, h, b, "GitHub statistics", th)


# ---------------------------------------------------------------- languages

def languages(d, th):
    langs = d["languages"]
    rows = (len(langs) + 1) // 2
    w, h = 900, 126 + rows * 44 + 20
    b = header(28, 34, "LANGUAGES ACROSS ALL REPOSITORIES", th, f"{d['lang_repos']} repos · {d['lang_total_kb']}")
    x = 28
    bw = w - 56
    b += f'<clipPath id="bar"><rect x="28" y="54" width="{bw}" height="14" rx="7"/></clipPath><g clip-path="url(#bar)">'
    for i, L in enumerate(langs):
        seg = bw * L["share"]
        b += r(x, 54, seg + 0.5, 14, lang_color(L["name"], i), 0)
        x += seg
    b += '</g>'
    b += t(28, 94, "Ranked by √(code size) × √(repositories) so one huge notebook can't drown out everything else.", 11, th["muted"], 400, MONO)
    for i, L in enumerate(langs):
        cx = 28 + (i % 2) * 432
        cy = 128 + (i // 2) * 44
        col = lang_color(L["name"], i)
        b += f'<circle cx="{cx + 6}" cy="{cy - 4}" r="6" fill="{col}"/>'
        b += t(cx + 20, cy, L["name"], 14, th["ink"], 600)
        b += t(cx + 404, cy, f"{L['share'] * 100:.1f}%", 14, th["ink"], 700, MONO, "end")
        b += t(cx + 20, cy + 18, f"{L['repos']} repo{'s' if L['repos'] != 1 else ''} · {L['size']}", 11, th["muted"], 400, MONO)
        b += r(cx + 240, cy + 11, 164, 4, th["line"], 2) + r(cx + 240, cy + 11, 164 * L["share"] / langs[0]["share"], 4, col, 2)
    return frame(w, h, b, "Language breakdown across all repositories", th)


# ---------------------------------------------------------------- heatmap

def heatmap(d, th):
    days = d["calendar"]
    w, h = 900, 236
    b = header(28, 34, "CONTRIBUTIONS · LAST 12 MONTHS", th, f"{fmt(d['year_total'])} total · busiest month {d['busiest_month']}")
    cell, gap, ox, oy = 12, 3, 58, 70
    first_wd = (days[0]["weekday"]) if days else 0
    col = 0
    last_month = None
    for i, day in enumerate(days):
        idx = i + first_wd
        col, row = idx // 7, idx % 7
        x = ox + col * (cell + gap)
        y = oy + row * (cell + gap)
        if row == 0 or i == 0:
            m = day["date"][5:7]
            if m != last_month and day["date"][8:10] <= "07":
                b += t(x, oy - 10, day["month_name"], 10, th["muted"], 400, MONO)
                last_month = m
        b += f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="2.5" fill="{th["heat"][day["level"]]}"><title>{day["date"]}: {day["count"]}</title></rect>'
    for row, name in [(1, "Mon"), (3, "Wed"), (5, "Fri")]:
        b += t(28, oy + row * (cell + gap) + 10, name, 10, th["muted"], 400, MONO)
    ly = oy + 7 * (cell + gap) + 22
    b += t(w - 28 - 5 * 16 - 40, ly + 10, "less", 10, th["muted"], 400, MONO, "end")
    for i in range(5):
        b += r(w - 28 - 5 * 16 - 34 + i * 16, ly, 12, 12, th["heat"][i], 2.5)
    b += t(w - 28, ly + 10, "more", 10, th["muted"], 400, MONO, "end")
    b += t(28, ly + 10, f"{d['active_days']} active days · best day {fmt(d['best_day']['count'])} on {d['best_day']['label']}", 11, th["muted"], 400, MONO)
    return frame(w, h, b, "Contribution calendar for the last year", th)


# ---------------------------------------------------------------- streaks + weekday

def streaks(d, th):
    w, h = 900, 210
    b = header(28, 34, "STREAKS & RHYTHM", th, "from the contribution calendar")
    big = [("Current streak", d["streak_now"], d["streak_now_range"], th["amber"]),
           ("Longest streak", d["streak_max"], d["streak_max_range"], th["mint"]),
           ("Active days", d["active_days"], f"of the last {len(d['calendar'])} days", th["blue"])]
    for i, (label, val, sub, col) in enumerate(big):
        x = 28 + i * 172
        b += r(x, 52, 160, 130, th["panel"], 10, th["line"])
        b += t(x + 80, 104, fmt(val), 38, col, 750, SANS, "middle")
        b += t(x + 80, 128, label + (" (days)" if i < 2 else ""), 12, th["ink"], 600, SANS, "middle")
        b += t(x + 80, 160, sub, 10, th["muted"], 400, MONO, "middle")
    # weekday bars
    wx, wy, ww, wh = 560, 52, 312, 130
    b += r(wx, wy, ww, wh, th["panel"], 10, th["line"])
    b += t(wx + 16, wy + 24, f"Busiest weekday: {d['top_weekday']}", 12, th["ink"], 600)
    mx = max(d["weekday_totals"]) or 1
    names = ["S", "M", "T", "W", "T", "F", "S"]
    for i, v in enumerate(d["weekday_totals"]):
        bh = 62 * v / mx
        x = wx + 22 + i * 41
        b += r(x, wy + 104 - bh, 24, max(bh, 2), th["amber"] if v == mx and v else th["line"], 3)
        b += t(x + 12, wy + 120, names[i], 10, th["muted"], 400, MONO, "middle")
    return frame(w, h, b, "Contribution streaks and weekday rhythm", th)


# ---------------------------------------------------------------- yearly + weekly trend

def trend(d, th):
    w, h = 900, 230
    b = header(28, 34, "GROWTH OVER TIME", th, f"{fmt(d['all_time'])} contributions since {d['joined'][:4]}")
    # yearly bars
    yrs = d["yearly"]
    bx, by, bw, bh = 28, 52, 330, 150
    b += r(bx, by, bw, bh, th["panel"], 10, th["line"]) + t(bx + 16, by + 24, "Per year", 12, th["ink"], 600)
    mx = max([v for _, v in yrs] or [1]) or 1
    slot = (bw - 32) / max(len(yrs), 1)
    for i, (yr, v) in enumerate(yrs):
        hh = 78 * v / mx
        x = bx + 16 + i * slot + slot * 0.18
        b += r(x, by + 118 - hh, slot * 0.64, max(hh, 2), th["mint"], 3)
        b += t(x + slot * 0.32, by + 112 - hh, fmt(v), 10, th["ink"], 600, MONO, "middle")
        b += t(x + slot * 0.32, by + 136, f"'{str(yr)[2:]}", 10, th["muted"], 400, MONO, "middle")
    # weekly area
    ax, ay, aw, ah = 372, 52, 500, 150
    b += r(ax, ay, aw, ah, th["panel"], 10, th["line"]) + t(ax + 16, ay + 24, "Weekly activity · last 52 weeks", 12, th["ink"], 600)
    wk = d["weekly"] or [0]
    mw = max(wk) or 1
    pts = []
    for i, v in enumerate(wk):
        x = ax + 16 + (aw - 32) * i / max(len(wk) - 1, 1)
        y = ay + 126 - 82 * v / mw
        pts.append((x, y))
    line = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    area = f"{pts[0][0]:.1f},{ay + 126} " + line + f" {pts[-1][0]:.1f},{ay + 126}"
    b += f'<polygon points="{area}" fill="{th["blue"]}" opacity=".16"/><polyline points="{line}" fill="none" stroke="{th["blue"]}" stroke-width="2" stroke-linejoin="round"/>'
    peak = max(range(len(wk)), key=lambda i: wk[i])
    b += f'<circle cx="{pts[peak][0]:.1f}" cy="{pts[peak][1]:.1f}" r="4" fill="{th["blue"]}"/>'
    b += t(min(pts[peak][0] + 8, ax + aw - 90), max(pts[peak][1] - 6, ay + 40), f"peak {wk[peak]}", 10, th["ink"], 600, MONO)
    b += t(ax + 16, ay + 142, f"avg {d['weekly_avg']:.1f}/week · {d['active_weeks']} active weeks", 10, th["muted"], 400, MONO)
    return frame(w, h, b, "Contributions per year and weekly trend", th)


# ---------------------------------------------------------------- project card

def project(p, th):
    w, h = 440, 222
    b = r(14, 18, 3, 26, th["amber"], 1.5)
    b += t(28, 30, p["tag"], 10, th["amber"], 700, MONO, extra='letter-spacing="1.3"')
    b += t(w - 20, 30, f"★ {p['stars']}", 11, th["muted"], 600, MONO, "end")
    b += t(28, 58, clip(p["title"], 390, 20), 20, th["ink"], 700)
    b += t(28, 78, clip(p["subtitle"], 390, 11), 11, th["muted"], 400, MONO)
    y = 108
    for f in p["features"][:3]:
        b += f'<path d="M30 {y - 8}l5 4-5 4" fill="none" stroke="{th["mint"]}" stroke-width="1.8" stroke-linecap="round"/>'
        b += t(44, y, clip(f, 370, 13), 13, th["ink"])
        y += 24
    # language bar
    x, bw = 28, w - 56
    b += f'<clipPath id="pb"><rect x="28" y="{h - 46}" width="{bw}" height="6" rx="3"/></clipPath><g clip-path="url(#pb)">'
    b += r(28, h - 46, bw, 6, th["line"], 0)
    for i, (name, share) in enumerate(p["langs"]):
        b += r(x, h - 46, bw * share + 0.5, 6, lang_color(name, i), 0)
        x += bw * share
    b += '</g>'
    lx = 28
    for i, (name, share) in enumerate(p["langs"][:3]):
        label = f"{name} {share * 100:.0f}%"
        b += f'<circle cx="{lx + 4}" cy="{h - 23}" r="4" fill="{lang_color(name, i)}"/>' + t(lx + 12, h - 19, label, 10.5, th["muted"], 400, MONO)
        lx += 22 + len(label) * 6.3
    b += t(w - 20, h - 19, p["updated"], 10.5, th["muted"], 400, MONO, "end")
    return frame(w, h, b, f"{p['title']}: " + "; ".join(p["features"]), th)
