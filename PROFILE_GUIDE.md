# How this profile works

Everything on the profile page is rebuilt automatically every 6 hours by
`.github/workflows/profile.yml`, which runs `scripts/build.py` with the repository's
built-in `GITHUB_TOKEN` (no personal token, no third-party stats server).

## What updates by itself

- Header: name, bio, location, repository/star/follower counts.
- GitHub stats: repos, stars, forks, followers, contributions and commits (12 months), pull requests, issues, all-time contributions.
- Languages: bytes of every language in every public non-fork repo, ranked by √size × √repo-count.
- Contribution heatmap, current/longest streak, active days, busiest weekday, yearly totals and weekly trend.
- Project cards: stars, language mix and "updated" time for each featured repo.
- "All other repositories" table: every public repo, newest first — new repos appear automatically.
- "Working on now" and "Recent activity" from your latest public events.
- Every card exists in dark and light versions and follows the visitor's GitHub theme.

## What you edit — `profile.json`

- `featured`: the project cards. Each has `repo`, `title`, `section`, `tag` and three short `features`.
  Add or remove an entry and the cards appear/disappear on the next run.
- `sections`: the headings the featured cards are grouped under.
- `notes`: one-line descriptions for repos in the "All other repositories" table.
  Repos without a note use their GitHub description, so filling in descriptions on GitHub works too.
- `roles`, `intro`, `links`, `tech`, `hide` (repos never listed), `language_ranking`.

Saving `profile.json` on GitHub triggers a rebuild within a minute. To rebuild by hand:
Actions → Build dynamic profile → Run workflow.

## Run locally

    GITHUB_TOKEN=... python3 scripts/build.py              # live
    python3 scripts/build.py --dump data.json               # live, and save the data
    python3 scripts/build.py --offline data.json            # rebuild from saved data

If the API fails the run stops before writing anything, so the last good version stays up.
GitHub can pause scheduled workflows on repositories with no activity for 60 days; the
bot's own commits normally keep it active, and manual runs always work.
