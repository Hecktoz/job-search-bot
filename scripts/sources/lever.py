"""Fetch postings from a company's public Lever job board.

Public, unauthenticated endpoint -- no API key needed:
  https://api.lever.co/v0/postings/<slug>?mode=json
"""
import requests

TIMEOUT = 20


def fetch(company_name: str, slug: str) -> list[dict]:
    url = f"https://api.lever.co/v0/postings/{slug}?mode=json"
    resp = requests.get(url, timeout=TIMEOUT)
    if resp.status_code != 200:
        raise RuntimeError(f"lever:{slug} -> HTTP {resp.status_code}")

    jobs = []
    for item in resp.json():
        categories = item.get("categories") or {}
        jobs.append(
            {
                "source": "lever",
                "company": company_name,
                "title": (item.get("text") or "").strip(),
                "location": categories.get("location", ""),
                "url": item.get("hostedUrl", ""),
                "posted_at": item.get("createdAt", ""),
                "external_id": f"lever:{slug}:{item.get('id')}",
            }
        )
    return jobs
