# Internship Job Search Bot

Daily-refreshing tracker for data scientist / data engineer / AI engineer /
machine learning internships (and close variants). A scheduled job runs in
GitHub Actions once a day, pulls fresh postings, filters them by title, and
commits the results back to this repo. You view the results in a small local
dashboard.

## How it sources jobs

| Source | How | Needs a key? |
|---|---|---|
| Company ATS boards (Greenhouse, Lever, Ashby) | Public, unauthenticated JSON endpoints per company | No |
| [SimplifyJobs/Summer2027-Internships](https://github.com/SimplifyJobs/Summer2027-Internships) | Community-maintained internship tracker; a bot updates its `listings.json` many times a day as people submit postings via PRs | No |
| [vanshb03/Summer2027-Internships](https://github.com/vanshb03/Summer2027-Internships) | Same idea, a second independently-maintained tracker (some overlap with Simplify, some unique postings) | No |
| Adzuna | Aggregator API that indexes many boards | Yes (free tier) |
| Google Jobs | Via SerpApi -- Google indexes structured job postings published by LinkedIn, Indeed, Glassdoor, etc., so this surfaces listings that originated there without scraping those sites directly | Yes (free trial tier) |

The two GitHub-tracker feeds are the highest-volume source by far (several
hundred matching, active, US-based internships at any given time, refreshed
continuously by their communities) and need zero setup. Together with the
ATS boards, the bot works fully out of the box with **no API keys at all**.

LinkedIn, Indeed, Glassdoor, and Handshake don't have public job-search APIs
and scraping them means fighting login walls and bot-detection, which this
project intentionally avoids (it risks your account getting flagged, and
breaks most of their Terms of Service). Google Jobs is the practical
workaround for LinkedIn/Indeed/Glassdoor coverage; see "Optional: LinkedIn
alerts" below for a manual supplement, and "Handshake" for why it's left out.

Add more ATS-board companies any time by finding a company's careers page
and adding it to [`config/companies.yml`](config/companies.yml):
- Greenhouse: `boards.greenhouse.io/<slug>`
- Lever: `jobs.lever.co/<slug>`
- Ashby: `jobs.ashbyhq.com/<slug>`

Run `python scripts/check_companies.py` any time to see which configured
slugs currently resolve (companies migrate ATS providers over time).

The two GitHub-tracker repos get renamed every internship season (e.g.
`Summer2027-Internships` becomes `Summer2028-Internships` next cycle). If
a feed starts failing in the run logs, find the repo's current name on
GitHub and update it in [`config/sources.yml`](config/sources.yml).

## What counts as a match

Two filters are applied to every posting, in this order:

1. **Title** -- [`config/keywords.yml`](config/keywords.yml) controls this: a
   posting matches if its title contains a role term (data scientist, data
   engineer, ML engineer, AI engineer, applied scientist, etc.) **and** a
   level term (intern, internship, co-op, "summer 2026/2027"). Edit that
   file to widen or narrow the net -- no code changes needed.
2. **Location** -- only postings with at least one US location survive
   (`scripts/filters.py::is_us_location`). It checks for a US state
   abbreviation/name, "United States"/"USA", or "Remote in US(A)"; postings
   that list a non-US location (e.g. "Toronto, Canada", "London, UK") are
   dropped, *unless* the same posting also lists a US location (a multi-country
   posting counts as long as the US is one of the options). A bare "Remote"
   with no country given is treated as US, since essentially every source
   here is a US-headquartered company.

Every matched posting also gets a **category** label (Data Science, Data
Engineering, Machine Learning, AI Engineering, NLP, Computer Vision, Deep
Learning, or Research / Applied Science) based on which role term matched --
see `CATEGORY_RULES` in `scripts/filters.py`. That's what powers the "Role"
filter chips in the dashboard.

## One-time setup

1. **Push this to your own GitHub repo:**
   ```bash
   cd job-search-bot
   gh repo create job-search-bot --private --source=. --remote=origin
   git add -A
   git commit -m "Initial job search bot"
   git push -u origin main
   ```
2. **Allow the workflow to commit data back to the repo:** in the repo's
   GitHub settings -> Actions -> General -> Workflow permissions, select
   "Read and write permissions."
3. **(Optional) add API keys** as repo secrets (Settings -> Secrets and
   variables -> Actions) to enable the Adzuna and/or Google Jobs sources:
   - `ADZUNA_APP_ID`, `ADZUNA_APP_KEY` -- free at https://developer.adzuna.com/
   - `SERPAPI_KEY` -- free trial at https://serpapi.com/
   Skip this step and the bot still runs fine on ATS boards alone.
4. **Trigger the first run** without waiting for the daily schedule: go to
   the Actions tab -> "Daily job scan" -> "Run workflow." It commits
   `data/jobs.json` with the results.

The workflow ([`.github/workflows/daily_job_scan.yml`](.github/workflows/daily_job_scan.yml))
then runs automatically every day at 13:00 UTC. Change the cron line to
adjust the time.

## Viewing results (local dashboard)

```bash
git pull                      # get the latest data/jobs.json
python3 -m http.server 8899   # serve the repo so the dashboard can fetch data/jobs.json
```
Then open **http://localhost:8899/dashboard/** in your browser. It's a
static page -- search box, **Role** filter chips (Data Science, Data
Engineering, Machine Learning, AI Engineering, etc.) and **Source** filter
chips (ATS boards, GitHub trackers, Adzuna, Google Jobs), each independently
multi-selectable so you can combine several at once, plus a "new today"
toggle and sort -- with no build step. Just re-run `git pull` + refresh the
page whenever you want the latest.

## Running a scan manually / locally

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python scripts/fetch_jobs.py
```

## Optional: LinkedIn alerts

LinkedIn doesn't offer an API, but you can still get LinkedIn coverage
without scraping: set up a LinkedIn job alert for your target titles
(Jobs -> your search -> toggle "Job alert" on) and have it email you daily.
That's a native LinkedIn feature and stays entirely within their terms.

## Handshake

Handshake is gated behind your university's login, so there's no
general-purpose way to automate it safely. Recommended: save a Handshake
search with your filters and check it directly, or set up its built-in
email alerts the same way as LinkedIn above.

## Project layout

```
config/keywords.yml    role/level/exclude terms used to filter titles
config/companies.yml   ATS boards checked every run
config/sources.yml     community GitHub tracker repos checked every run
scripts/fetch_jobs.py  main entry point: fetch -> filter (title + US location) -> categorize -> merge -> save
scripts/sources/       one module per data source
scripts/filters.py     title matching, US-location detection, role categorization
scripts/storage.py     dedupe + first_seen/last_seen tracking + pruning
scripts/check_companies.py  validates companies.yml slugs
data/jobs.json         the running store (committed by the daily workflow)
dashboard/             static HTML/CSS/JS viewer for data/jobs.json (role + source filter chips)
.github/workflows/     the daily scheduled GitHub Action
```
