# India DSA Trainer — Job Tracker

This repository auto-tracks "DSA Trainer" job postings in India on LinkedIn.

A GitHub Actions workflow (`.github/workflows/dsa-trainer-job-watch.yml`)
runs `scrape.py` every ~5 hours. It fetches LinkedIn's public, logged-out
guest job-search endpoint for keywords "DSA Trainer" filtered to location
"India", and records any newly seen listings here. No LinkedIn login,
credentials, cookies, or authenticated session is ever used — only publicly
viewable, unauthenticated pages are accessed. The workflow only commits
when something actually changed.

You can also trigger a run manually from the repo's Actions tab
("india-dsa-trainer-job-watch" → Run workflow).

## Files

- `scrape.py` — the scraper: fetches, parses, dedupes, and writes the two
  files below.
- `jobs.json` — machine-readable list of every unique listing found so far.
- `jobs.md` — the same list as a human-readable markdown table, newest first.

Each entry records the job title, company, location, LinkedIn's raw
posted-time text, the job URL, and the UTC timestamp when this tracker
first saw it.
