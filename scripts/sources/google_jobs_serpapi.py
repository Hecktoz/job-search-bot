"""Fetch postings from Google Jobs via SerpApi.

Google Jobs indexes structured job-posting markup published by many sites
-- including LinkedIn, Indeed, and Glassdoor -- so this is a legitimate way
to surface listings that originated on those platforms without scraping
them directly. Needs a SERPAPI_KEY env var (SerpApi has a free trial tier);
if unset, fetch() returns an empty list so the rest of the pipeline runs
fine without this source.
"""
import os

import requests

TIMEOUT = 20

QUERIES = [
    "data scientist intern",
    "data engineer intern",
    "machine learning intern",
    "AI engineer intern",
]


def fetch() -> list[dict]:
    api_key = os.environ.get("SERPAPI_KEY")
    if not api_key:
        return []

    jobs = []
    for query in QUERIES:
        params = {
            "engine": "google_jobs",
            "q": query,
            "location": "United States",
            "api_key": api_key,
        }
        resp = requests.get("https://serpapi.com/search.json", params=params, timeout=TIMEOUT)
        if resp.status_code != 200:
            raise RuntimeError(f"serpapi google_jobs:'{query}' -> HTTP {resp.status_code}")

        for item in resp.json().get("jobs_results", []):
            apply_link = ""
            apply_options = item.get("apply_options") or []
            if apply_options:
                apply_link = apply_options[0].get("link", "")

            job_id = item.get("job_id", f"{item.get('title')}-{item.get('company_name')}")
            jobs.append(
                {
                    "source": "google_jobs",
                    "company": item.get("company_name", "Unknown"),
                    "title": (item.get("title") or "").strip(),
                    "location": item.get("location", ""),
                    "url": apply_link or item.get("share_link", ""),
                    "posted_at": (item.get("detected_extensions") or {}).get("posted_at", ""),
                    "external_id": f"google_jobs:{job_id}",
                }
            )
    return jobs
