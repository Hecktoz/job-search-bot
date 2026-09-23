"""Fetch postings from the Adzuna job search API.

Adzuna aggregates postings from many boards (including many that mirror
Indeed/LinkedIn listings). Free tier: https://developer.adzuna.com/
Needs ADZUNA_APP_ID + ADZUNA_APP_KEY env vars -- if unset, fetch() returns
an empty list so the rest of the pipeline runs fine without this source.
"""
import os

import requests

TIMEOUT = 20
COUNTRY = "us"
RESULTS_PER_PAGE = 50

# Kept short & broad on purpose -- our own keyword filter (config/keywords.yml)
# does the real precision filtering after results come back.
QUERIES = [
    "data scientist intern",
    "data engineer intern",
    "machine learning intern",
    "ai engineer intern",
]


def fetch() -> list[dict]:
    app_id = os.environ.get("ADZUNA_APP_ID")
    app_key = os.environ.get("ADZUNA_APP_KEY")
    if not app_id or not app_key:
        return []

    jobs = []
    for query in QUERIES:
        url = f"https://api.adzuna.com/v1/api/jobs/{COUNTRY}/search/1"
        params = {
            "app_id": app_id,
            "app_key": app_key,
            "what": query,
            "max_days_old": 2,
            "results_per_page": RESULTS_PER_PAGE,
            "content-type": "application/json",
        }
        resp = requests.get(url, params=params, timeout=TIMEOUT)
        if resp.status_code != 200:
            raise RuntimeError(f"adzuna:'{query}' -> HTTP {resp.status_code}")

        for item in resp.json().get("results", []):
            company = (item.get("company") or {}).get("display_name", "Unknown")
            location = (item.get("location") or {}).get("display_name", "")
            jobs.append(
                {
                    "source": "adzuna",
                    "company": company,
                    "title": (item.get("title") or "").strip(),
                    "location": location,
                    "url": item.get("redirect_url", ""),
                    "posted_at": item.get("created", ""),
                    "external_id": f"adzuna:{item.get('id')}",
                }
            )
    return jobs
