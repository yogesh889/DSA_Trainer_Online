# DSA Trainer Online — Job Tracker

This repository auto-tracks "online DSA Trainer" job postings on LinkedIn.

A scheduled cloud agent runs every ~5 hours, fetches LinkedIn's public,
logged-out job search results for the phrase "online DSA Trainer", and
records any newly seen listings here. No LinkedIn login, credentials,
cookies, or authenticated session is ever used — only publicly viewable,
unauthenticated pages are accessed.

## Files

- `jobs.json` — machine-readable list of every unique listing found so far.
- `jobs.md` — the same list as a human-readable markdown table, newest first.

Each entry records the job title, company, location, LinkedIn's raw
posted-time text, the job URL, and the UTC timestamp when this tracker
first saw it.
