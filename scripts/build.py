#!/usr/bin/env python3
"""Build the dynamic GitHub profile: README.md and every SVG card in assets/.

Runs in GitHub Actions on a schedule (see .github/workflows/profile.yml) with the
repository's built-in GITHUB_TOKEN. Standard library only — nothing to install.

  python3 scripts/build.py                  # fetch live data and rebuild everything
  python3 scripts/build.py --dump data.json # also save the fetched data
  python3 scripts/build.py --offline data.json  # rebuild from saved data (no network)

Content you can edit lives in profile.json. Everything else (repositories, stars,
languages, contribution history, activity) is fetched fresh on every run.
"""
import collections
import datetime as dt
import json
import math
import os
import pathlib
import shutil
import sys
import time
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import cards  # noqa: E402

CFG = json.loads((ROOT / "profile.json").read_text(encoding="utf-8"))
USER = CFG["user"]
API = "https://api.github.com"

# Files from the previous design that this build replaces.
OBSOLETE = ["scripts/update-profile.py", "scripts/design_v2.py", "assets/icons", "assets/hero.svg",
            "assets/stats.svg", "assets/streak.svg", "assets/academic.svg", "assets/focus.svg",
            "assets/stack.svg", "assets/typing.svg", "assets/connect.svg", "assets/project-skin.svg",
            "assets/project-thyroid.svg", "assets/project-news.svg", "assets/project-agro.svg"]


# ------------------------------------------------------------------ fetching

def request(path, body=None):
    headers = {"User-Agent": f"{USER}-profile-builder", "Accept": "application/vnd.github+json"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = json.dumps(body).encode() if body is not None else None
    url = path if path.startswith("http") else API + path
    for attempt in range(4):
        try:
            req = urllib.request.Request(url, data=data, headers=headers)
            with urllib.request.urlopen(req, timeout=40) as res:
                return json.load(res)
        except urllib.error.HTTPError as e:
            if e.code in (502, 503, 504) or (e.code == 403 and attempt < 3 and "rate" in e.reason.lower()):
                time.sleep(3 * (attempt + 1))
                continue
            raise
        except urllib.error.URLError:
            if attempt == 3:
                raise
            time.sleep(3 * (attempt + 1))


def paged(path):
    out = []
    for page in range(1, 50):
        sep = "&" if "?" in path else "?"
        batch = request(f"{path}{sep}per_page=100&page={page}")
        out.extend(batch)
        if len(batch) < 100:
            return out
    return out


def fetch():
    user = request(f"/users/{USER}")
    repos = [r for r in paged(f"/users/{USER}/repos?type=owner&sort=pushed") if not r.get("private")]
    langs = {}
    for r in repos:
        if not r["fork"]:
            langs[r["name"]] = request(r["languages_url"])
    events = request(f"/users/{USER}/events/public?per_page=60")

    now = dt.datetime.now(dt.timezone.utc)
    joined = dt.datetime.fromisoformat(user["created_at"].replace("Z", "+00:00"))
    years = "".join(
        f'y{y}: contributionsCollection(from:"{y}-01-01T00:00:00Z", to:"{min(dt.datetime(y, 12, 31, 23, 59, 59, tzinfo=dt.timezone.utc), now).strftime("%Y-%m-%dT%H:%M:%SZ")}")'
        " { contributionCalendar { totalContributions } }"
        for y in range(joined.year, now.year + 1))
    query = (f'{{ user(login:"{USER}") {{ pullRequests(first:1) {{ totalCount }} issues(first:1) {{ totalCount }} '
             "repositoriesContributedTo(first:1, contributionTypes:[COMMIT,PULL_REQUEST,ISSUE,REPOSITORY]) { totalCount } "
             "contributionsCollection { totalCommitContributions restrictedContributionsCount "
             "contributionCalendar { totalContributions weeks { contributionDays { date contributionCount weekday } } } } "
             f"{years} }} }}")
    gql = request("/graphql", {"query": query})
    if gql.get("errors"):
        raise RuntimeError(f"GraphQL query failed: {gql['errors']}")
    g = gql["data"]["user"]
    cal = [d for w in g["contributionsCollection"]["contributionCalendar"]["weeks"] for d in w["contributionDays"]]
    return {
        "fetched_at": now.isoformat(),
        "user": {k: user.get(k) for k in ("login", "name", "bio", "location", "followers", "following", "public_repos", "created_at", "html_url")},
        "repos": [{k: r.get(k) for k in ("name", "description", "language", "stargazers_count", "forks_count", "fork",
                                          "archived", "pushed_at", "created_at", "topics", "homepage", "html_url")} for r in repos],
        "languages": langs,
        "events": [{"type": e["type"], "repo": e["repo"]["name"], "created_at": e["created_at"],
                    "payload": {k: e["payload"].get(k) for k in ("size", "ref_type", "action", "ref") if k in e["payload"]}}
                   for e in events],
        "calendar": [{"date": d["date"], "count": d["contributionCount"]} for d in cal],
        "commits_year": g["contributionsCollection"]["totalCommitContributions"],
        "private_year": g["contributionsCollection"]["restrictedContributionsCount"],
        "prs": g["pullRequests"]["totalCount"],
        "issues": g["issues"]["totalCount"],
        "contributed_to": g["repositoriesContributedTo"]["totalCount"],
        "yearly": {k[1:]: v["contributionCalendar"]["totalContributions"] for k, v in g.items() if k.startswith("y") and k[1:].isdigit()},
    }


# ------------------------------------------------------------------ helpers

def parse(ts):
    return dt.datetime.fromisoformat(ts.replace("Z", "+00:00"))


def ago(ts, now):
    s = (now - parse(ts)).total_seconds()
    for unit, size in (("y", 31536000), ("mo", 2592000), ("w", 604800), ("d", 86400), ("h", 3600), ("m", 60)):
        if s >= size:
            return f"{int(s // size)}{unit} ago"
    return "just now"


def kb(n):
    if n >= 1 << 20:
        return f"{n / (1 << 20):.1f} MB"
    return f"{max(n / 1024, 0.1):.0f} KB" if n >= 1024 else f"{n} B"


def nice_date(iso):
    d = dt.date.fromisoformat(iso)
    return f"{d.strftime('%b')} {d.day}"


# ------------------------------------------------------------------ metrics

def compute(raw):
    now = parse(raw["fetched_at"])
    u = raw["user"]
    hide = set(CFG.get("hide", []))
    owned = [r for r in raw["repos"] if not r["fork"]]
    shown = [r for r in owned if r["name"] not in hide]

    # Languages: GitHub-readme-stats style weighting so notebook outputs don't swamp everything.
    rk = CFG.get("language_ranking", {})
    sw, cw, top = rk.get("size_weight", 0.5), rk.get("count_weight", 0.5), rk.get("top", 8)
    size, count = collections.Counter(), collections.Counter()
    for name, langs in raw["languages"].items():
        for lang, b in langs.items():
            if b > 0:
                size[lang] += b
                count[lang] += 1
    score = {k: (size[k] ** sw) * (count[k] ** cw) for k in size}
    ranked = sorted(score, key=score.get, reverse=True)
    head = ranked[:top]
    total_score = sum(score.values()) or 1
    langs = [{"name": k, "share": score[k] / total_score, "repos": count[k], "size": kb(size[k])} for k in head]
    rest = ranked[top:]
    if rest:
        langs.append({"name": f"Other ({len(rest)})", "share": sum(score[k] for k in rest) / total_score,
                      "repos": len({n for n, ls in raw["languages"].items() if any(k in ls for k in rest)}),
                      "size": kb(sum(size[k] for k in rest))})

    # Calendar
    cal = sorted(raw["calendar"], key=lambda d: d["date"])
    counts = sorted(c["count"] for c in cal if c["count"])
    q = lambda p: counts[min(int(len(counts) * p), len(counts) - 1)] if counts else 1
    cuts = [q(.25), q(.5), q(.75)]

    def level(n):
        return 0 if n == 0 else 1 if n <= cuts[0] else 2 if n <= cuts[1] else 3 if n <= cuts[2] else 4

    days = []
    for c in cal:
        dd = dt.date.fromisoformat(c["date"])
        days.append({"date": c["date"], "count": c["count"], "level": level(c["count"]),
                     "weekday": (dd.weekday() + 1) % 7, "month_name": dd.strftime("%b")})

    # Streaks
    longest, run, run_start, best_range = 0, 0, None, "no streak yet"
    for d in days:
        if d["count"]:
            run += 1
            run_start = run_start or d["date"]
            if run > longest:
                longest, best_range = run, f"{nice_date(run_start)} – {nice_date(d['date'])}"
        else:
            run, run_start = 0, None
    cur, i = 0, len(days) - 1
    if i >= 0 and days[i]["count"] == 0:
        i -= 1  # today not counted yet doesn't break the streak
    end = days[i]["date"] if i >= 0 else None
    while i >= 0 and days[i]["count"]:
        cur += 1
        i -= 1
    cur_range = f"{nice_date(days[i + 1]['date'])} – {nice_date(end)}" if cur else "start one today"

    wd = [0] * 7
    for d in days:
        wd[d["weekday"]] += d["count"]
    wd_names = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    months = collections.Counter()
    for d in days:
        months[d["date"][:7]] += d["count"]
    busiest = max(months, key=months.get) if months and max(months.values()) else None
    best = max(days, key=lambda d: d["count"]) if days else {"count": 0, "date": None}
    weekly = [sum(d["count"] for d in days[k:k + 7]) for k in range(max(len(days) - 364, 0), len(days), 7)][-52:]

    joined = u["created_at"]
    yearly = sorted((int(k), v) for k, v in raw.get("yearly", {}).items())
    year_total = sum(d["count"] for d in days)

    return {
        "now": now, "login": u["login"], "name": u["name"] or u["login"], "bio": u.get("bio"),
        "location": u.get("location"), "followers": u["followers"], "public_repos": u["public_repos"],
        "joined": joined, "years": max(now.year - int(joined[:4]), 1),
        "stars": sum(r["stargazers_count"] for r in owned), "forks": sum(r["forks_count"] for r in owned),
        "year_total": year_total, "year_commits": raw.get("commits_year"), "prs": raw.get("prs"),
        "issues": raw.get("issues"), "contributed_to": raw.get("contributed_to"),
        "all_time": sum(v for _, v in yearly) if yearly else year_total, "yearly": yearly or [(now.year, year_total)],
        "languages": langs, "lang_repos": len([n for n, l in raw["languages"].items() if l]),
        "lang_total_kb": kb(sum(size.values())),
        "calendar": days, "active_days": sum(1 for d in days if d["count"]),
        "best_day": {"count": best["count"], "label": nice_date(best["date"]) if best["date"] else "—"},
        "busiest_month": dt.date.fromisoformat(busiest + "-01").strftime("%b %Y") if busiest else "—",
        "streak_now": cur, "streak_now_range": cur_range, "streak_max": longest, "streak_max_range": best_range,
        "weekday_totals": wd, "top_weekday": wd_names[wd.index(max(wd))] if any(wd) else "—",
        "weekly": weekly, "weekly_avg": sum(weekly) / max(len(weekly), 1), "active_weeks": sum(1 for x in weekly if x),
        "stamp": now.strftime("%d %b %Y, %H:%M UTC"), "stamp_short": now.strftime("%d %b %Y"),
        "owned": owned, "shown": shown, "raw": raw,
    }


def project_data(m):
    by_name = {r["name"]: r for r in m["owned"]}
    out = []
    for f in CFG.get("featured", []):
        r = by_name.get(f["repo"])
        if not r:
            print(f"warning: featured repo {f['repo']} not found, skipping")
            continue
        ls = m["raw"]["languages"].get(r["name"], {})
        tot = sum(ls.values()) or 1
        langs = sorted(((k, v / tot) for k, v in ls.items() if v), key=lambda x: -x[1])
        if not langs and r["language"]:
            langs = [(r["language"], 1.0)]
        features = f.get("features") or [r["description"] or "Repository on GitHub"]
        out.append({**f, "r": r, "stars": r["stargazers_count"], "langs": langs, "features": features,
                    "subtitle": f"{USER}/{r['name']}", "updated": "updated " + ago(r["pushed_at"], m["now"])})
    return out


# ------------------------------------------------------------------ README

def pic(path, alt, width="100%"):
    return (f'<picture><source media="(prefers-color-scheme: light)" srcset="./assets/light/{path}.svg">'
            f'<img src="./assets/dark/{path}.svg" width="{width}" alt="{cards.esc(alt)}"></picture>')


def badge(label, logo, color, url=None, style="for-the-badge"):
    q = urllib.request.quote
    logo_color = "black" if color.upper() in ("FFD21E", "F7DF1E", "61DAFB", "3FCF8E") else "white"
    img = f'<img src="https://img.shields.io/badge/{q(label.replace("-", "--"))}-{color}?style={style}&logo={logo}&logoColor={logo_color}" alt="{label}">'
    return f'<a href="{url}">{img}</a>' if url else img


def describe(r):
    notes = CFG.get("notes", {})
    if r["name"] in notes:
        return notes[r["name"]]
    if r.get("description"):
        return r["description"]
    lang = r.get("language")
    if parse(r["pushed_at"]).year <= 2023 and lang in ("HTML", "CSS", "JavaScript", None):
        return "Early web-development practice"
    return f"{lang} project" if lang else "Repository"


def activity(m):
    lines, seen = [], set()
    verbs = {"CreateEvent": "Created", "PublicEvent": "Open-sourced", "WatchEvent": "Starred",
             "ForkEvent": "Forked", "ReleaseEvent": "Published a release in", "IssuesEvent": "Opened an issue in",
             "PullRequestEvent": "Opened a pull request in", "DeleteEvent": None, "MemberEvent": None}
    for e in m["raw"]["events"]:
        repo = e["repo"].split("/", 1)[-1]
        verb = verbs.get(e["type"], "Pushed to" if e["type"] == "PushEvent" else None)
        if e["type"] == "CreateEvent" and e["payload"].get("ref_type") != "repository":
            verb = "Pushed to"
        if e["type"] in ("IssuesEvent", "PullRequestEvent") and e["payload"].get("action") != "opened":
            continue
        if not verb:
            continue
        key = (verb, repo, e["created_at"][:10])
        if key in seen:
            continue
        seen.add(key)
        lines.append(f"| {ago(e['created_at'], m['now'])} | {verb} [{repo}](https://github.com/{e['repo']}) |")
        if len(lines) == 6:
            break
    return lines


def readme(m, projects):
    L = []
    L.append(f'<a href="https://github.com/{USER}">{pic("hero", m["name"] + " — " + ", ".join(CFG.get("roles", [])))}</a>')
    L.append("")
    L.append('<p align="center">' + " ".join(badge(l["label"], l["logo"], l["color"], l["url"]) for l in CFG.get("links", [])) + "</p>")
    L.append("")
    L.append(f'<p align="center">{CFG.get("intro", "")}</p>')
    L.append("")
    recent = [r for r in sorted(m["shown"], key=lambda r: r["pushed_at"], reverse=True)][:3]
    if recent:
        L.append('<p align="center"><b>Working on now:</b> ' + " · ".join(
            f'<a href="{r["html_url"]}">{r["name"]}</a> <sub>({ago(r["pushed_at"], m["now"])})</sub>' for r in recent) + "</p>")
        L.append("")

    L.append("## Featured projects")
    L.append("")
    sections = CFG.get("sections") or [{"id": None, "title": "", "blurb": ""}]
    for s in sections:
        group = [p for p in projects if p.get("section") == s["id"] or s["id"] is None]
        if not group:
            continue
        if s["title"]:
            L.append(f"### {s['title']}")
            L.append(f"<sub>{s.get('blurb', '')}</sub>")
            L.append("")
        L.append("<p>")
        for p in group:
            L.append(f'<a href="{p["r"]["html_url"]}">{pic("projects/" + p["repo"], p["title"] + ": " + "; ".join(p["features"]), "49%")}</a>')
        L.append("</p>")
        L.append("")

    featured = {p["repo"] for p in projects}
    rest = sorted([r for r in m["shown"] if r["name"] not in featured] +
                  [r for r in m["raw"]["repos"] if r["fork"] and r["name"] not in set(CFG.get("hide", []))],
                  key=lambda r: r["pushed_at"], reverse=True)
    L.append(f"<details><summary><b>All other repositories ({len(rest)})</b> — auto-listed, newest first</summary>")
    L.append("")
    L.append("| Repository | What it is | Language | ★ | Updated |")
    L.append("|:--|:--|:--|:-:|:--|")
    for r in rest:
        fork = " <sub>fork</sub>" if r["fork"] else ""
        L.append(f"| [{r['name']}]({r['html_url']}){fork} | {describe(r)} | {r['language'] or '—'} | {r['stargazers_count']} | {ago(r['pushed_at'], m['now'])} |")
    L.append("")
    L.append("</details>")
    L.append("")

    L.append("## Tech stack")
    L.append("")
    L.append('<p>' + " ".join(badge(n, logo, c, style="flat-square") for n, logo, c in CFG.get("tech", [])) + "</p>")
    L.append("")

    L.append("## GitHub stats")
    L.append("")
    for name, alt in [("stats", "GitHub statistics: repositories, stars, forks, followers, contributions, commits, pull requests and issues"),
                      ("languages", "Language breakdown across all public repositories"),
                      ("heatmap", "Contribution calendar for the last 12 months"),
                      ("streaks", "Current and longest contribution streaks, active days and weekday rhythm"),
                      ("trend", "Contributions per year and weekly activity trend")]:
        L.append(pic(name, alt))
        L.append("")

    acts = activity(m)
    if acts:
        L.append("## Recent activity")
        L.append("")
        L.append("| When | What |")
        L.append("|:--|:--|")
        L.extend(acts)
        L.append("")

    L.append("---")
    L.append(f'<sub>This profile rebuilds itself every 6 hours from the GitHub API — last run <b>{m["stamp"]}</b>. '
             f'Project names and features live in <a href="./profile.json">profile.json</a>; everything else is automatic. '
             f'<a href="https://github.com/{USER}/{USER}/actions/workflows/profile.yml">Workflow ↗</a></sub>')
    L.append("")
    return "\n".join(L)


# ------------------------------------------------------------------ main

def write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def main(argv):
    raw = None
    if "--offline" in argv:
        raw = json.loads(pathlib.Path(argv[argv.index("--offline") + 1]).read_text(encoding="utf-8"))
    else:
        raw = fetch()
    if "--dump" in argv:
        pathlib.Path(argv[argv.index("--dump") + 1]).write_text(json.dumps(raw, indent=1), encoding="utf-8")

    m = compute(raw)
    projects = project_data(m)

    # Render everything in memory first so a failure never leaves half-written assets.
    files = {}
    for mode, th in cards.THEMES.items():
        base = f"assets/{mode}/"
        files[base + "hero.svg"] = cards.hero(m, CFG, th)
        files[base + "stats.svg"] = cards.stats(m, th)
        files[base + "languages.svg"] = cards.languages(m, th)
        files[base + "heatmap.svg"] = cards.heatmap(m, th)
        files[base + "streaks.svg"] = cards.streaks(m, th)
        files[base + "trend.svg"] = cards.trend(m, th)
        for p in projects:
            files[f"{base}projects/{p['repo']}.svg"] = cards.project(p, th)
    files["README.md"] = readme(m, projects)

    for mode in cards.THEMES:  # drop cards for projects removed from profile.json
        folder = ROOT / "assets" / mode / "projects"
        if folder.exists():
            for f in folder.glob("*.svg"):
                if f"assets/{mode}/projects/{f.name}" not in files:
                    f.unlink()
    for rel in OBSOLETE:
        p = ROOT / rel
        if p.is_dir():
            shutil.rmtree(p)
        elif p.exists():
            p.unlink()
    for rel, content in files.items():
        write(ROOT / rel, content)
    print(f"Built {len(files)} files · {len(m['owned'])} repos · {len(projects)} featured · {m['year_total']} contributions this year")


if __name__ == "__main__":
    main(sys.argv[1:])
