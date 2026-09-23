"""Persistence for data/jobs.json: dedupe, track first/last seen, prune stale postings."""
import hashlib
import json
import os
from datetime import date, timedelta

PRUNE_AFTER_DAYS = 21  # drop postings not seen in any run for this long (likely closed)


def _job_id(job: dict) -> str:
    ext_id = job.get("external_id")
    if ext_id:
        return ext_id
    raw = f"{job.get('source')}|{job.get('company')}|{job.get('title')}|{job.get('url')}"
    return hashlib.sha1(raw.encode()).hexdigest()


def load_jobs(path: str) -> list[dict]:
    if not os.path.exists(path):
        return []
    with open(path) as f:
        return json.load(f)


def save_jobs(path: str, jobs: list[dict]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(jobs, f, indent=2)
        f.write("\n")


def merge(existing: list[dict], new_batch: list[dict], today: str | None = None) -> tuple[list[dict], list[dict]]:
    """Merge freshly fetched jobs into the existing store.

    Returns (merged_jobs, newly_added_jobs). Postings not re-seen in
    PRUNE_AFTER_DAYS are dropped (they've likely been filled/closed).
    """
    today = today or date.today().isoformat()
    by_id = {_job_id(j): j for j in existing}
    newly_added = []

    for job in new_batch:
        jid = _job_id(job)
        if jid in by_id:
            by_id[jid]["last_seen"] = today
            # keep posted_at/location fresh in case the listing was edited
            by_id[jid]["posted_at"] = job.get("posted_at", by_id[jid].get("posted_at", ""))
            by_id[jid]["location"] = job.get("location", by_id[jid].get("location", ""))
        else:
            record = dict(job)
            record["id"] = jid
            record["first_seen"] = today
            record["last_seen"] = today
            by_id[jid] = record
            newly_added.append(record)

    cutoff = (date.today() - timedelta(days=PRUNE_AFTER_DAYS)).isoformat()
    merged = [j for j in by_id.values() if j["last_seen"] >= cutoff]
    merged.sort(key=lambda j: j.get("first_seen", ""), reverse=True)

    return merged, newly_added
