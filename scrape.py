#!/usr/bin/env python3
"""
Tracks "DSA Trainer" job postings in India from LinkedIn's public,
logged-out job search. No login, no credentials, no authenticated
session is ever used -- only the guest job-search endpoint that LinkedIn
serves to anonymous visitors.

Run on a schedule (see .github/workflows/dsa-trainer-job-watch.yml).
"""
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path
from datetime import datetime, timezone

from bs4 import BeautifulSoup

REPO_DIR = Path(__file__).resolve().parent
JOBS_JSON = REPO_DIR / "jobs.json"
JOBS_MD = REPO_DIR / "jobs.md"

KEYWORDS = "DSA Trainer"
LOCATION = "India"
GUEST_SEARCH_URL = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
PAGE_SIZE = 10
MAX_PAGES = 6  # LinkedIn's guest endpoint stops returning new results after ~40-60 for a given query
REQUEST_DELAY_SECONDS = 2

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


def fetch_page(start: int) -> str:
    params = {"keywords": KEYWORDS, "location": LOCATION, "start": start}
    url = f"{GUEST_SEARCH_URL}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="replace")


def parse_cards(html: str):
    soup = BeautifulSoup(html, "html.parser")
    cards = soup.select("div.base-card")
    listings = []
    for card in cards:
        title_el = card.select_one("h3.base-search-card__title")
        company_el = card.select_one("h4.base-search-card__subtitle")
        location_el = card.select_one("span.job-search-card__location")
        time_el = card.select_one("time")
        link_el = card.select_one("a.base-card__full-link")
        if not (title_el and link_el):
            continue
        url = link_el["href"].split("?")[0].strip()
        match = re.search(r"-(\d+)$", url)
        job_id = match.group(1) if match else url
        listings.append(
            {
                "id": job_id,
                "title": title_el.get_text(strip=True),
                "company": company_el.get_text(strip=True) if company_el else "",
                "location": location_el.get_text(strip=True) if location_el else "",
                "posted": time_el.get_text(strip=True) if time_el else "",
                "url": url,
            }
        )
    return listings


def fetch_all_listings():
    all_listings = {}
    for page in range(MAX_PAGES):
        start = page * PAGE_SIZE
        try:
            html = fetch_page(start)
        except Exception as exc:  # noqa: BLE001
            print(f"[warn] fetch failed at start={start}: {exc}", file=sys.stderr)
            break
        listings = parse_cards(html)
        if not listings:
            break
        new_on_this_page = 0
        for job in listings:
            if job["id"] not in all_listings:
                all_listings[job["id"]] = job
                new_on_this_page += 1
        if new_on_this_page == 0:
            # LinkedIn started repeating results -- we've reached the end
            break
        time.sleep(REQUEST_DELAY_SECONDS)
    return list(all_listings.values())


def load_existing():
    if JOBS_JSON.exists():
        return json.loads(JOBS_JSON.read_text(encoding="utf-8"))
    return []


def write_outputs(jobs):
    jobs_sorted = sorted(jobs, key=lambda j: j["first_seen_utc"], reverse=True)
    JOBS_JSON.write_text(json.dumps(jobs_sorted, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    lines = [
        "| Title | Company | Location | Posted | Link | First seen |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for j in jobs_sorted:
        lines.append(
            f"| {j['title']} | {j['company']} | {j['location']} | {j['posted']} "
            f"| [link]({j['url']}) | {j['first_seen_utc']} |"
        )
    JOBS_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    existing = load_existing()
    existing_ids = {j["id"] for j in existing}

    fetched = fetch_all_listings()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    new_jobs = []
    for job in fetched:
        if job["id"] not in existing_ids:
            job["first_seen_utc"] = now
            new_jobs.append(job)
            existing_ids.add(job["id"])

    if not fetched:
        print("RESULT: fetch_failed_or_empty new=0 total=%d" % len(existing))
        return

    all_jobs = existing + new_jobs
    write_outputs(all_jobs)

    print(f"RESULT: ok new={len(new_jobs)} total={len(all_jobs)}")
    for j in new_jobs:
        print(f"NEW: {j['title']} | {j['company']} | {j['location']} | {j['url']}")


if __name__ == "__main__":
    main()
