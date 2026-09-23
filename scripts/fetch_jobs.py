#!/usr/bin/env python3
"""Daily job-scan entry point.

Pulls postings from every configured source, keeps only titles matching
config/keywords.yml, merges them into data/jobs.json (deduped, with
first_seen/last_seen tracking), and prints a run summary.

Usage: python scripts/fetch_jobs.py
Env vars (all optional -- missing ones just disable that source):
  ADZUNA_APP_ID, ADZUNA_APP_KEY   -- https://developer.adzuna.com/
  SERPAPI_KEY                     -- https://serpapi.com/
"""
import os
import sys

import yaml

sys.path.insert(0, os.path.dirname(__file__))

import filters
import storage
from sources import adzuna, ashby, github_feed, google_jobs_serpapi, greenhouse, lever

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KEYWORDS_PATH = os.path.join(ROOT, "config", "keywords.yml")
COMPANIES_PATH = os.path.join(ROOT, "config", "companies.yml")
SOURCES_PATH = os.path.join(ROOT, "config", "sources.yml")
JOBS_PATH = os.path.join(ROOT, "data", "jobs.json")


def fetch_all(companies: list[dict], github_feeds: list[dict]) -> list[dict]:
    raw_jobs = []

    for c in companies:
        fetcher = {"greenhouse": greenhouse, "lever": lever, "ashby": ashby}.get(c["ats"])
        if fetcher is None:
            print(f"  [skip] {c['name']}: unknown ats '{c['ats']}'")
            continue
        try:
            jobs = fetcher.fetch(c["name"], c["slug"])
            raw_jobs.extend(jobs)
            print(f"  [ok]   {c['name']} ({c['ats']}): {len(jobs)} postings")
        except Exception as e:
            print(f"  [fail] {c['name']} ({c['ats']}): {e}")

    for feed in github_feeds:
        try:
            jobs = github_feed.fetch(feed["name"], feed["repo"], feed["branch"], feed["path"])
            raw_jobs.extend(jobs)
            print(f"  [ok]   {feed['name']} (github feed): {len(jobs)} active postings")
        except Exception as e:
            print(f"  [fail] {feed['name']} (github feed): {e}")

    for label, fetcher in [("adzuna", adzuna), ("google_jobs", google_jobs_serpapi)]:
        try:
            jobs = fetcher.fetch()
            if jobs:
                raw_jobs.extend(jobs)
                print(f"  [ok]   {label}: {len(jobs)} postings")
            else:
                print(f"  [skip] {label}: no API key set")
        except Exception as e:
            print(f"  [fail] {label}: {e}")

    return raw_jobs


def main() -> None:
    keywords = filters.load_keywords(KEYWORDS_PATH)
    with open(COMPANIES_PATH) as f:
        companies = yaml.safe_load(f)["companies"]
    with open(SOURCES_PATH) as f:
        github_feeds = yaml.safe_load(f)["github_internship_feeds"]

    print(f"Fetching from {len(companies)} ATS boards, {len(github_feeds)} community feeds, + aggregator APIs...")
    raw_jobs = fetch_all(companies, github_feeds)
    print(f"\nFetched {len(raw_jobs)} raw postings total.")

    matched = []
    for j in raw_jobs:
        if not filters.matches(j["title"], keywords):
            continue
        if not filters.is_us_location(j.get("location")):
            continue
        if isinstance(j["location"], list):
            j["location"] = "; ".join(j["location"])
        j["category"] = filters.categorize(j["title"])
        matched.append(j)
    print(f"{len(matched)} match the internship/role keyword filter and are US-based.")

    existing = storage.load_jobs(JOBS_PATH)
    merged, newly_added = storage.merge(existing, matched)
    storage.save_jobs(JOBS_PATH, merged)

    print(f"\nStore now holds {len(merged)} active postings (pruned anything stale).")
    print(f"{len(newly_added)} NEW postings since the last run:")
    for j in newly_added:
        print(f"  - [{j['company']}] {j['title']} ({j['source']}) -> {j['url']}")


if __name__ == "__main__":
    main()
