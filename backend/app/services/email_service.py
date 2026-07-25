"""
email_service.py
================
Async email delivery service using the Resend API.

Sends the candidate's AI-generated PDF assessment report as a direct
file attachment (not a link).

Environment variable required:
    RESEND_API_KEY  — obtained from resend.com dashboard

Usage:
    from app.services.email_service import send_report_email
    await send_report_email(to_email, candidate_name, pdf_path)
"""

import base64
import os
import pathlib

import resend


def _get_api_key() -> str:
    """Reads RESEND_API_KEY from the environment (set once per process)."""
    key = os.getenv("RESEND_API_KEY", "")
    if not key:
        raise EnvironmentError(
            "[email_service] RESEND_API_KEY is not set in the environment."
        )
    return key


async def send_report_email(
    to_email: str,
    candidate_name: str,
    pdf_path: str,
) -> None:
    """
    Send the assessment PDF report to the candidate via Resend.

    Args:
        to_email:       Recipient's email address.
        candidate_name: Candidate's display name (used in the email body).
        pdf_path:       Absolute path to the generated PDF file on disk.
    """
    # ── Configure Resend SDK ───────────────────────────────────────────────────
    resend.api_key = _get_api_key()

    # ── Read and encode the PDF ────────────────────────────────────────────────
    pdf_file = pathlib.Path(pdf_path)
    if not pdf_file.exists():
        raise FileNotFoundError(
            f"[email_service] PDF not found at path: {pdf_path}"
        )

    pdf_bytes = pdf_file.read_bytes()
    pdf_b64   = base64.b64encode(pdf_bytes).decode("utf-8")
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

<p>As the next step, our mentors can provide a personalized plan on how to best leverage the resources, especially on your areas of improvement. <a href="#">Book a free consultation call</a> with <strong>Siddarth R</strong>, a seasoned Senior Data Science Manager from Microsoft.</p>

<p>During this call, you'll have the chance to:</p>
<p>
  🌟 Have a detailed analysis of your self-assessment report.<br>
  🎯 Identify and conquer your blind spots with a personalized plan tailored just for you.<br>
  🔑 Make the right career choices with guidance from an expert.
</p>

<p><a href="#">Book a call now</a> to get started with your personalized upskilling journey!</p>

<p>If you have any queries, feel free to reach out to <a href="mailto:operations@prepvector.com">operations@prepvector.com</a>.<br>
Thank you :)</p>

<p>- Team PrepVector</p>"""

    # ── Build Resend params ────────────────────────────────────────────────────
    params: resend.Emails.SendParams = {
        "from": "PrepVector <onboarding@resend.dev>",
        "to":   [to_email],
        "subject": "Your Data Science Skill Assessment Report",
        "text": text_body,
        "html": html_body,
        "attachments": [
            {
                "filename": filename,
                "content":  pdf_b64,
            }
        ],
    }

    # ── Send ───────────────────────────────────────────────────────────────────
    try:
        result = resend.Emails.send(params)
        print(
            f"[email_service] ✅  Report email sent to '{to_email}' "
            f"(Resend ID: {result.get('id', 'n/a')})"
        )
    except Exception as exc:
        print(f"[email_service] ❌  Failed to send report email to '{to_email}': {exc}")
        raise
