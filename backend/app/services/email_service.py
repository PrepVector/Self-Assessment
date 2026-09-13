"""
email_service.py
================
Async email delivery service using Hostinger SMTP via aiosmtplib.

Sends the candidate's AI-generated PDF assessment report as a direct
file attachment (not a link).

Environment variables required:
    SMTP_HOST      — SMTP server hostname (e.g. smtp.hostinger.com)
    SMTP_PORT      — SMTP port (465 for implicit TLS)
    SMTP_USERNAME  — Full sender email address used to authenticate
    SMTP_PASSWORD  — SMTP account password
    SMTP_FROM      — Display sender address (e.g. "PrepVector <no-reply@prepvector.com>")

Usage:
    from app.services.email_service import send_report_email
    await send_report_email(to_email, candidate_name, pdf_path)
"""

import os
import pathlib
from email.message import EmailMessage

import aiosmtplib


async def send_report_email(
    to_email: str,
    candidate_name: str,
    pdf_path: str,
) -> None:
    """
    Send the assessment PDF report to the candidate via Hostinger SMTP.

    Args:
        to_email:       Recipient's email address.
        candidate_name: Candidate's display name (used in the email body).
        pdf_path:       Absolute path to the generated PDF file on disk.
    """
    # ── Load SMTP configuration from environment ───────────────────────────────
    smtp_host     = os.getenv("SMTP_HOST", "")
    smtp_port     = int(os.getenv("SMTP_PORT", "465"))
    smtp_username = os.getenv("SMTP_USERNAME", "")
    smtp_password = os.getenv("SMTP_PASSWORD", "")
    smtp_from     = os.getenv("SMTP_FROM", "")

    # ── Read the PDF ───────────────────────────────────────────────────────────
    pdf_file = pathlib.Path(pdf_path)
    if not pdf_file.exists():
        raise FileNotFoundError(
            f"[email_service] PDF not found at path: {pdf_path}"
        )

    pdf_bytes = pdf_file.read_bytes()
    filename  = pdf_file.name  # e.g. "report_John_Doe_20260725.pdf"

    # ── Build email body ───────────────────────────────────────────────────────
    text_body = f"""Hi {candidate_name},

Thank you for completing the self-assessment and taking the next step towards your career journey.

Your skill assessment report attached with this email contains:
- Comparison with industry skill ratings.
- Strong skills and areas of improvement as a data scientist.
- A list of resources to get started.

As the next step, our mentors can provide a personalized plan on how to best leverage the resources, especially on your areas of improvement. Book a free consultation call with Siddarth R, a seasoned Senior Data Science Manager from Microsoft.

During this call, you'll have the chance to:
* Have a detailed analysis of your self-assessment report.
* Identify and conquer your blind spots with a personalized plan tailored just for you.
* Make the right career choices with guidance from an expert.

Book a call now to get started with your personalized upskilling journey!

If you have any queries, feel free to reach out to operations@prepvector.com.
Thank you :)

- Team PrepVector"""

    html_body = f"""<p>Hi {candidate_name},</p>

<p>Thank you for completing the self-assessment and taking the next step towards your career journey.</p>

<p><strong>Your skill assessment report attached with this email contains:</strong></p>
<p>
  - Comparison with industry skill ratings.<br>
  - Strong skills and areas of improvement as a data scientist.<br>
  - A list of resources to get started.
</p>

<p>As the next step, our mentors can provide a personalized plan on how to best leverage the resources, especially on your areas of improvement. <a href="https://calendly.com/siddarthr-mba/30min">Book a free consultation call</a> with <strong>Siddarth R</strong>, a seasoned Senior Data Science Manager from Microsoft.</p>

<p>During this call, you'll have the chance to:</p>
<p>
  🌟 Have a detailed analysis of your self-assessment report.<br>
  🎯 Identify and conquer your blind spots with a personalized plan tailored just for you.<br>
  🔑 Make the right career choices with guidance from an expert.
</p>

<p><a href="https://calendly.com/siddarthr-mba/30min">Book a call now</a> to get started with your personalized upskilling journey!</p>

<p>If you have any queries, feel free to reach out to <a href="mailto:operations@prepvector.com">operations@prepvector.com</a>.<br>
Thank you :)</p>

<p>- Team PrepVector</p>"""

    # ── Construct EmailMessage ─────────────────────────────────────────────────
    msg = EmailMessage()
    msg["From"]    = smtp_from
    msg["To"]      = to_email
    msg["Subject"] = "Your Data Science Skill Assessment Report"
    msg.set_content(text_body)
    msg.add_alternative(html_body, subtype="html")
    msg.add_attachment(
        pdf_bytes,
        maintype="application",
        subtype="pdf",
        filename=filename,
    )

    # ── Send via Hostinger SMTP (implicit TLS, port 465) ──────────────────────
    try:
        await aiosmtplib.send(
            msg,
            hostname=smtp_host,
            port=smtp_port,
            username=smtp_username,
            password=smtp_password,
            use_tls=True,
        )
        print(
            f"[email_service] ✅  Report email sent to '{to_email}' "
            f"via {smtp_host}:{smtp_port}"
        )
    except Exception as exc:
        print(f"[email_service] ❌  Failed to send report email to '{to_email}': {exc}")
        raise
