# India DSA Trainer — Job Tracker

This repository auto-tracks "DSA Trainer" job postings in India on LinkedIn.

## Live page

**https://yogesh889.github.io/DSA_Trainer_Online/** — always shows the
current list of tracked jobs. (Requires GitHub Pages to be enabled once,
see Setup below.)

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

## Setup (one-time, done by the repo owner)

1. **Enable GitHub Pages**: Settings → Pages → Source: "Deploy from a
   branch" → Branch: `master` / `(root)` → Save. The live page above goes
   live a minute or two after that.
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
