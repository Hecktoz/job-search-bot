#!/usr/bin/env python3
"""Validate every slug in config/companies.yml against its ATS endpoint.

Run this after cloning (and any time you edit companies.yml) to see which
entries actually resolve. Companies migrate ATS providers over time, so
some seed entries may 404 -- that's expected, just remove or fix those.
"""
import os
import sys

import requests
import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COMPANIES_PATH = os.path.join(ROOT, "config", "companies.yml")

ENDPOINTS = {
    "greenhouse": "https://boards-api.greenhouse.io/v1/boards/{slug}/jobs",
    "lever": "https://api.lever.co/v0/postings/{slug}?mode=json",
    "ashby": "https://api.ashbyhq.com/posting-api/job-board/{slug}",
}


def main() -> None:
    with open(COMPANIES_PATH) as f:
        companies = yaml.safe_load(f)["companies"]

    ok, bad = [], []
    for c in companies:
        template = ENDPOINTS.get(c["ats"])
        if not template:
            bad.append(c)
            continue
        url = template.format(slug=c["slug"])
        try:
            resp = requests.get(url, timeout=15)
            if resp.status_code != 200:
                bad.append(c)
                continue
            body = resp.json()
            count = len(body.get("jobs", [])) if isinstance(body, dict) else len(body)
            ok.append((c, count))
        except Exception:
            bad.append(c)

    print(f"OK ({len(ok)}):")
    for c, count in ok:
        print(f"  {c['name']:20s} {c['ats']:10s} {c['slug']:20s} -> {count} postings")

    if bad:
        print(f"\nBROKEN / needs fixing ({len(bad)}) -- remove or correct these in companies.yml:")
        for c in bad:
            print(f"  {c['name']:20s} {c['ats']:10s} {c['slug']}")

    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
