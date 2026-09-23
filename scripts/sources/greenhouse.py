"""Fetch postings from a company's public Greenhouse job board.

Public, unauthenticated endpoint -- no API key needed:
  https://boards-api.greenhouse.io/v1/boards/<slug>/jobs
"""
import requests

TIMEOUT = 20


def fetch(company_name: str, slug: str) -> list[dict]:
    url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=false"
    resp = requests.get(url, timeout=TIMEOUT)
    if resp.status_code != 200:
        raise RuntimeError(f"greenhouse:{slug} -> HTTP {resp.status_code}")

    jobs = []
    for item in resp.json().get("jobs", []):
        location = (item.get("location") or {}).get("name", "")
        jobs.append(
            {
                "source": "greenhouse",
                "company": company_name,
                "title": item.get("title", "").strip(),
                "location": location,
                "url": item.get("absolute_url", ""),
                "posted_at": item.get("updated_at", ""),
                "external_id": f"greenhouse:{slug}:{item.get('id')}",
            }
        )
    return jobs
