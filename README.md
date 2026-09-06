# India DSA Trainer — Job Tracker

This repository auto-tracks "DSA Trainer" job postings in India on LinkedIn.

## Live page

**https://yogesh889.github.io/DSA_Trainer_Online/** — always shows the
current list of tracked jobs.

## How it works

Two GitHub Actions workflows, both running on GitHub's own infrastructure
(not affected by any third-party network restrictions):

- **`dsa-trainer-job-watch.yml`** — runs `scrape.py` every ~5 hours. Fetches
  LinkedIn's public, logged-out guest job-search endpoint for keywords
  "DSA Trainer" filtered to location "India", records any newly seen
  listings, and regenerates `jobs.json`, `jobs.md`, and `index.html`
  (the live page). Only commits when something actually changed.
- **`email-report.yml`** — runs `generate_report.py` roughly every 5 days.
  Builds a PDF summary (new listings since the last report, or the full
  list if none) and emails it via Gmail SMTP.

No LinkedIn login, credentials, cookies, or authenticated session is ever
used anywhere in this pipeline — only publicly viewable, unauthenticated
pages are accessed.

You can trigger either workflow manually from the repo's **Actions** tab
("Run workflow").

### Freshness window

Only listings whose LinkedIn "posted X ago" text falls between **1 day**
and **~1 month (31 days)** old are kept. Every run re-checks this against
each listing's current posted text and drops anything that's aged past a
month (or was somehow under a day). A listing only starts being tracked
once it's at least a day old, so brand-new postings appear on the next
run or two, not instantly.

### Known limitation: individual "hiring a DSA trainer" posts

LinkedIn's normal feed/post search (as opposed to the structured Jobs
section) requires a logged-in session for guests — it redirects
unauthenticated requests straight to a login wall. Since this project
intentionally never logs in or uses credentials, that content isn't
reachable and isn't included here. Only postings in LinkedIn's public
Jobs section are tracked.

## Setup (one-time, done by the repo owner)

1. ~~Enable GitHub Pages~~ — done.
2. **Enable email reports**: create a Gmail
   [App Password](https://myaccount.google.com/apppasswords) (requires
   2-Step Verification), then add two repo secrets under Settings →
   Secrets and variables → Actions:
   - `SMTP_USER` — the Gmail address to send from
   - `SMTP_PASS` — the app password (not your normal Gmail password)

   Until these secrets exist, `email-report.yml` will fail — that's
   expected and harmless (the job-watch workflow is independent of it).

## Files

- `scrape.py` — fetches, parses, dedupes, and writes `jobs.json`,
  `jobs.md`, and `index.html`.
- `generate_report.py` — builds the PDF and sends the email report;
  tracks what's already been reported in `report_state.json`.
- `jobs.json` — machine-readable list of every unique listing found so far.
- `jobs.md` — the same list as a human-readable markdown table, newest first.
- `index.html` — the live page, regenerated every scraper run.

Each job entry records the title, company, location, LinkedIn's raw
posted-time text, the job URL, and the UTC timestamp when this tracker
first saw it.
