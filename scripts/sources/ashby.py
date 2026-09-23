"""Fetch postings from a company's public Ashby job board.

Public, unauthenticated endpoint -- no API key needed:
  https://api.ashbyhq.com/posting-api/job-board/<slug>
"""
import requests

TIMEOUT = 20


def fetch(company_name: str, slug: str) -> list[dict]:
    url = f"https://api.ashbyhq.com/posting-api/job-board/{slug}"
    resp = requests.get(url, timeout=TIMEOUT)
    if resp.status_code != 200:
        raise RuntimeError(f"ashby:{slug} -> HTTP {resp.status_code}")

    jobs = []
    for item in resp.json().get("jobs", []):
        jobs.append(
            {
                "source": "ashby",
                "company": company_name,
                "title": (item.get("title") or "").strip(),
                "location": item.get("location", ""),
                "url": item.get("jobUrl", ""),
                "posted_at": item.get("publishedAt", ""),
                "external_id": f"ashby:{slug}:{item.get('id')}",
            }
        )
    return jobs
