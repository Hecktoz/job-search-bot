"""Fetch postings from a community-maintained GitHub internship tracker.

Repos like SimplifyJobs/Summer2027-Internships and vanshb03/Summer2027-Internships
publish a `listings.json` that a GitHub Action bot updates many times a day as
people submit new postings via PRs/issues. Public raw file, no auth needed.
"""
from datetime import datetime, timezone

import requests

TIMEOUT = 20


def fetch(name: str, repo: str, branch: str, path: str) -> list[dict]:
    url = f"https://raw.githubusercontent.com/{repo}/{branch}/{path}"
    resp = requests.get(url, timeout=TIMEOUT)
    if resp.status_code != 200:
        raise RuntimeError(f"github_feed:{name} -> HTTP {resp.status_code}")

    jobs = []
    for item in resp.json():
        if not item.get("active", False):
            continue

        posted_at = ""
        ts = item.get("date_posted")
        if ts:
            posted_at = datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()

        jobs.append(
            {
                "source": f"github:{name}",
                "company": item.get("company_name", "Unknown"),
                "title": (item.get("title") or "").strip(),
                "location": item.get("locations", []),  # kept as list for US filtering
                "url": item.get("url", ""),
                "posted_at": posted_at,
                "external_id": f"github:{name}:{item.get('id')}",
            }
        )
    return jobs
