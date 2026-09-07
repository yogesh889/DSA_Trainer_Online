#!/usr/bin/env python3
"""
Builds a PDF summary of India DSA Trainer job listings and emails it to
the configured recipient. Meant to run every ~5 days
(see .github/workflows/email-report.yml).

Requires three GitHub Actions secrets (set by the repo owner, never seen by
Claude or committed to the repo):
  SMTP_USER        -- the Gmail address to send FROM
  SMTP_PASS        -- a Gmail App Password for that account (not the login password)
  RECIPIENT_EMAIL  -- the address to send the report TO
"""
import json
import os
import smtplib
from datetime import datetime, timezone
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

from fpdf import FPDF
from fpdf.enums import XPos, YPos

REPO_DIR = Path(__file__).resolve().parent
JOBS_JSON = REPO_DIR / "jobs.json"
STATE_JSON = REPO_DIR / "report_state.json"
PDF_PATH = REPO_DIR / "latest_report.pdf"

LIVE_PAGE_URL = "https://yogesh889.github.io/DSA_Trainer_Online/"
REPO_URL = "https://github.com/yogesh889/DSA_Trainer_Online"


def load_jobs():
    if JOBS_JSON.exists():
        return json.loads(JOBS_JSON.read_text(encoding="utf-8"))
    return []


def load_state():
    if STATE_JSON.exists():
        return json.loads(STATE_JSON.read_text(encoding="utf-8"))
    return {"last_reported_utc": "1970-01-01T00:00:00Z"}


def save_state(state):
    STATE_JSON.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")


def pdf_safe(text: str) -> str:
    """Core PDF fonts (Helvetica) only support latin-1; replace anything else."""
    return (text or "").encode("latin-1", "replace").decode("latin-1")


def build_pdf(all_jobs, new_jobs, generated_at: str) -> Path:
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "India DSA Trainer Jobs - LinkedIn Report", ln=True)

    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, f"Generated: {generated_at}", ln=True)
    pdf.cell(0, 6, f"Total listings tracked: {len(all_jobs)}", ln=True)
    pdf.cell(0, 6, f"New since last report: {len(new_jobs)}", ln=True)
    pdf.cell(0, 6, f"Live page: {LIVE_PAGE_URL}", ln=True)
    pdf.cell(0, 6, f"Repo: {REPO_URL}", ln=True)
    pdf.ln(6)

    listings = new_jobs if new_jobs else all_jobs
    heading = "New listings since last report" if new_jobs else "No new listings -- showing all currently tracked"
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, heading, ln=True)
    pdf.ln(2)

    pdf.set_font("Helvetica", "", 9)
    for j in listings:
        title = pdf_safe(j.get("title", ""))
        company = pdf_safe(j.get("company", ""))
        location = pdf_safe(j.get("location", ""))
        posted = pdf_safe(j.get("posted", ""))
        url = pdf_safe(j.get("url", ""))

        pdf.set_font("Helvetica", "B", 10)
        pdf.multi_cell(0, 5, title, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_font("Helvetica", "", 9)
        pdf.multi_cell(0, 5, f"{company} | {location} | posted {posted}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_text_color(0, 0, 200)
        pdf.multi_cell(0, 5, url, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_text_color(0, 0, 0)
        pdf.ln(3)

    pdf.output(str(PDF_PATH))
    return PDF_PATH


def send_email(pdf_path: Path, new_count: int, total_count: int):
    smtp_user = os.environ["SMTP_USER"]
    smtp_pass = os.environ["SMTP_PASS"]
    recipient_email = os.environ["RECIPIENT_EMAIL"]

    msg = MIMEMultipart()
    msg["From"] = smtp_user
    msg["To"] = recipient_email
    msg["Subject"] = f"India DSA Trainer jobs: {new_count} new ({total_count} total tracked)"

    body = (
        f"{new_count} new India DSA Trainer listing(s) found since the last report.\n"
        f"{total_count} total listings currently tracked.\n\n"
        f"Live page (always current): {LIVE_PAGE_URL}\n"
        f"Source repo: {REPO_URL}\n\n"
        "Full details attached as PDF."
    )
    msg.attach(MIMEText(body, "plain"))

    with open(pdf_path, "rb") as f:
        part = MIMEApplication(f.read(), _subtype="pdf")
        part.add_header("Content-Disposition", "attachment", filename=pdf_path.name)
        msg.attach(part)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(smtp_user, smtp_pass)
        server.sendmail(smtp_user, [recipient_email], msg.as_string())


def main():
    all_jobs = load_jobs()
    state = load_state()
    last_reported = state.get("last_reported_utc", "1970-01-01T00:00:00Z")

    new_jobs = [j for j in all_jobs if j.get("first_seen_utc", "") > last_reported]
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    pdf_path = build_pdf(all_jobs, new_jobs, generated_at)
    send_email(pdf_path, len(new_jobs), len(all_jobs))

    state["last_reported_utc"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    save_state(state)

    print(f"RESULT: emailed new={len(new_jobs)} total={len(all_jobs)}")


if __name__ == "__main__":
    main()
