"""
report_writer.py
================
Agent responsible for:
  1. Calling the Gemini API to generate a concise 2-page evaluation report
     (max ~400 words, 4 strict sections).
  2. Rendering that report into a polished PDF via Playwright (Chromium).

Public API
----------
generate_evaluation_report(score, total_questions, wrong_answers) -> str | None
    Returns a Markdown string from the LLM.

generate_playwright_pdf_report(
    candidate_name, markdown_text, section_scores,
    avg_scores, weighted_score, total_correct, total_questions,
    assessment_date
) -> str
    Builds an HTML page, embeds the Base64 chart, and uses Playwright to
    save it as a PDF.  Returns the absolute path of the saved file.

Naming convention
-----------------
    {candidate_name}_Self-Assessment_Report.pdf
    (spaces in the name are replaced with underscores)
"""

from __future__ import annotations

import os
import re
import time
import pathlib
from datetime import datetime, timezone
from dotenv import load_dotenv
from google import genai
from google.genai import types

from app.utils.chart_generator import generate_score_chart_base64

load_dotenv()

client   = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
MODEL_ID = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")

# ─── Paths ───────────────────────────────────────────────────────────────────
_AGENT_DIR   = pathlib.Path(__file__).resolve().parent   # backend/app/agents/
_BACKEND_DIR = _AGENT_DIR.parent.parent                   # backend/
_REPORTS_DIR = _BACKEND_DIR / "generated_reports"


# ─────────────────────────────────────────────────────────────────────────────
# 1.  LLM report generation
# ─────────────────────────────────────────────────────────────────────────────

def generate_evaluation_report(
    score: int,
    total_questions: int,
    wrong_answers: list[dict],
) -> str | None:
    """
    Calls the Gemini API to produce a concise, structured evaluation report.

    The prompt enforces:
      - Maximum 2 pages / ~400 words total output.
      - Exactly 4 sections: Executive Summary, Key Strengths,
        Top 2-3 Blind Spots, Actionable Learning Resources.

    Returns the raw Markdown string, or None if all models fail.
    """
    wrong_answers_formatted = ""
    for i, wa in enumerate(wrong_answers, 1):
        section_info = f" [Section: {wa.get('section_name')}]" if wa.get("section_name") else ""
        wrong_answers_formatted += (
            f"\nQuestion {i}{section_info}:\n"
            f"- Text: {wa.get('question_text')}\n"
            f"- User Answer: {wa.get('user_answer')}\n"
            f"- Correct Answer: {wa.get('correct_answer')}\n"
            f"- Explanation: {wa.get('explanation', 'N/A')}\n"
        )

    success_rate = (score / total_questions * 100) if total_questions > 0 else 0

    prompt = f"""
You are a senior Data Science Career Coach writing a CONCISE professional evaluation report.

Candidate Assessment:
- Score: {score} / {total_questions} ({success_rate:.1f}% success rate)

Incorrect Answers:
{wrong_answers_formatted}

STRICT OUTPUT RULES — you MUST follow all of these:
1. Total output must be UNDER 400 WORDS (fits on 2 PDF pages). Be direct, not verbose.
2. Use EXACTLY these 4 Markdown section headers, in this order:
   ## Executive Summary
   ## Key Strengths
   ## Top Blind Spots
   ## Actionable Learning Resources
3. "Executive Summary": 2-3 sentences max. State score, overall impression.
4. "Key Strengths": Bullet list (max 4 bullets) of topics the candidate handled well.
5. "Top Blind Spots": Bullet list of 2-3 weak areas identified from wrong answers. Each bullet names the topic and gives a one-sentence explanation of the gap.
6. "Actionable Learning Resources": Bullet list of 3-4 specific, practical recommendations (e.g., "Practice window functions in Mode Analytics SQL editor", "Read Chapter 7 of ISLR on regularization"). No vague advice.
7. Do NOT include any other sections, headers, or preamble outside these 4.
8. Do NOT repeat the candidate's score anywhere except the Executive Summary.
"""

    models_to_try = [
        ("Gemini 3.5 Flash",      "gemini-3.5-flash"),
        ("Gemini 2.5 Flash",      "gemini-2.5-flash"),
        ("Gemini 2.5 Flash Lite", "gemini-2.5-flash-lite"),
    ]
    max_retries = 3

    print("\n[report_writer] Generating AI evaluation report...")

    for i, (display_name, model_id) in enumerate(models_to_try):
        print(f"  Trying {display_name}...")
        for attempt in range(max_retries):
            try:
                response = client.models.generate_content(
                    model=model_id,
                    contents=prompt,
                    config=types.GenerateContentConfig(temperature=0.55),
                )
                print(f"  [report_writer] Success via {display_name}")
                return response.text
            except Exception as e:
                error_msg = str(e).lower()
                is_transient = any(
                    t in error_msg
                    for t in ["503", "429", "quota", "unavailable", "timeout", "rate limit", "overloaded"]
                )
                if attempt < max_retries - 1 and is_transient:
                    time.sleep(2 ** attempt)
                else:
                    status_str  = "Error"
                    status_match = re.search(r"(\d{3})", str(e))
                    if status_match:
                        status_str = status_match.group(1)
                    elif "quota" in error_msg:
                        status_str = "Quota Exceeded"
                    elif "timeout" in error_msg:
                        status_str = "Timeout"
                    print(f"  {display_name} unavailable ({status_str})")
                    if i < len(models_to_try) - 1:
                        print(f"  Switching to {models_to_try[i + 1][0]}...")
                    break

    print("[report_writer] All models failed — returning None.")
    return None


# ─────────────────────────────────────────────────────────────────────────────
# 2.  HTML template builder
# ─────────────────────────────────────────────────────────────────────────────

# Inline SVG logo for "Cognitive Assessment"
_LOGO_SVG = """
<svg width="38" height="38" viewBox="0 0 38 38" fill="none" xmlns="http://www.w3.org/2000/svg">
  <rect width="38" height="38" rx="9" fill="#3B82F6"/>
  <!-- Brain outline icon -->
  <path d="M19 8C14.03 8 10 12.03 10 17c0 3.17 1.63 5.96 4.1 7.61V28h9.8v-3.39C26.37 22.96 28 20.17 28 17c0-4.97-4.03-9-9-9z"
        fill="none" stroke="white" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>
  <line x1="19" y1="8" x2="19" y2="13" stroke="white" stroke-width="1.4" stroke-linecap="round"/>
  <line x1="13" y1="17" x2="16" y2="17" stroke="white" stroke-width="1.4" stroke-linecap="round"/>
  <line x1="22" y1="17" x2="25" y2="17" stroke="white" stroke-width="1.4" stroke-linecap="round"/>
  <line x1="15" y1="28" x2="23" y2="28" stroke="white" stroke-width="1.6" stroke-linecap="round"/>
  <line x1="16.5" y1="31" x2="21.5" y2="31" stroke="white" stroke-width="1.4" stroke-linecap="round"/>
</svg>
"""


def _markdown_to_html_body(md: str) -> str:
    """
    Lightweight Markdown -> HTML converter for the 4-section report format.
    Handles: ## H2, - bullets, **bold**, and plain paragraphs.
    """
    lines  = md.splitlines()
    html   = []
    in_ul  = False

    def _close_ul():
        nonlocal in_ul
        if in_ul:
            html.append("</ul>")
            in_ul = False

    def _inline(text: str) -> str:
        """Convert **bold** to <strong>."""
        return re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)

    for line in lines:
        stripped = line.strip()

        if stripped.startswith("## "):
            _close_ul()
            heading = _inline(stripped[3:].strip())
            html.append(f'<h2 class="section-heading">{heading}</h2>')

        elif stripped.startswith("# "):
            _close_ul()
            heading = _inline(stripped[2:].strip())
            html.append(f'<h1 class="report-title">{heading}</h1>')

        elif re.match(r"^[-*+]\s+", stripped):
            text = re.sub(r"^[-*+]\s+", "", stripped)
            if not in_ul:
                html.append('<ul class="bullet-list">')
                in_ul = True
            html.append(f"<li>{_inline(text)}</li>")

        elif stripped == "":
            _close_ul()
            html.append('<div class="spacer"></div>')

        else:
            _close_ul()
            html.append(f'<p class="body-para">{_inline(stripped)}</p>')

    _close_ul()
    return "\n".join(html)


def _build_html_report(
    candidate_name: str,
    markdown_text: str,
    chart_b64: str,
    weighted_score: int,
    total_correct: int,
    total_questions: int,
    assessment_date: str,
    generated_on: str,
) -> str:
    """
    Assembles the complete HTML string that Playwright will render to PDF.
    Uses inline CSS only (no external resources — critical for Playwright).
    """
    body_html   = _markdown_to_html_body(markdown_text)
    success_pct = (total_correct / total_questions * 100) if total_questions > 0 else 0
    pass_label  = "Qualified" if success_pct >= 60 else "Needs Improvement"
    pass_color  = "#16A34A" if success_pct >= 60 else "#DC2626"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>{candidate_name} — Self-Assessment Report</title>
  <style>
    /* ── Reset & base ─────────────────────────────────────────────────── */
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    html {{ font-size: 13px; }}
    body {{
      font-family: -apple-system, "Segoe UI", Helvetica, Arial, sans-serif;
      background: #fff;
      color: #1E293B;
      line-height: 1.6;
    }}

    /* ── Page wrapper ─────────────────────────────────────────────────── */
    .page {{
      width: 794px;        /* A4 at 96 dpi */
      margin: 0 auto;
      padding: 0;
    }}

    /* ── Cover header band ────────────────────────────────────────────── */
    .cover-band {{
      background: linear-gradient(135deg, #0F172A 0%, #1E3A5F 100%);
      padding: 38px 48px 32px;
      color: #fff;
      position: relative;
      overflow: hidden;
    }}
    .cover-band::after {{
      content: "";
      position: absolute;
      top: 0; right: 0; bottom: 0;
      width: 6px;
      background: #3B82F6;
    }}
    .brand-row {{
      display: flex;
      align-items: center;
      gap: 12px;
      margin-bottom: 28px;
    }}
    .brand-name {{
      font-size: 0.85rem;
      font-weight: 700;
      letter-spacing: 0.12em;
      color: #93C5FD;
      text-transform: uppercase;
    }}
    .brand-sub {{
      font-size: 0.72rem;
      color: #64748B;
      letter-spacing: 0.06em;
      margin-top: 2px;
    }}
    .report-heading {{
      font-size: 2rem;
      font-weight: 800;
      letter-spacing: -0.02em;
      line-height: 1.15;
      color: #fff;
      margin-bottom: 6px;
    }}
    .report-subheading {{
      font-size: 0.8rem;
      color: #94A3B8;
      margin-bottom: 28px;
    }}

    /* ── Score cards row ──────────────────────────────────────────────── */
    .score-cards {{
      display: flex;
      gap: 14px;
    }}
    .score-card {{
      background: rgba(255,255,255,0.07);
      border: 1px solid rgba(255,255,255,0.12);
      border-radius: 10px;
      padding: 14px 22px;
      min-width: 130px;
    }}
    .score-card .label {{
      font-size: 0.62rem;
      font-weight: 700;
      letter-spacing: 0.1em;
      text-transform: uppercase;
      color: #94A3B8;
      margin-bottom: 4px;
    }}
    .score-card .value {{
      font-size: 1.55rem;
      font-weight: 800;
      color: #fff;
      letter-spacing: -0.02em;
    }}
    .score-card .sublabel {{
      font-size: 0.62rem;
      color: #64748B;
      margin-top: 2px;
    }}
    .status-badge {{
      display: inline-block;
      font-size: 0.7rem;
      font-weight: 700;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      padding: 4px 12px;
      border-radius: 999px;
      background: {pass_color}22;
      color: {pass_color};
      border: 1px solid {pass_color}55;
      margin-top: 6px;
    }}

    /* ── Meta row ─────────────────────────────────────────────────────── */
    .meta-row {{
      background: #F8FAFC;
      border-bottom: 1px solid #E2E8F0;
      padding: 10px 48px;
      display: flex;
      gap: 32px;
      font-size: 0.7rem;
      color: #64748B;
    }}
    .meta-row strong {{ color: #334155; }}

    /* ── Content body ─────────────────────────────────────────────────── */
    .content {{
      padding: 32px 48px 40px;
    }}

    /* ── Chart section ────────────────────────────────────────────────── */
    .chart-section {{
      margin-bottom: 32px;
      text-align: center;
    }}
    .chart-section img {{
      max-width: 100%;
      border-radius: 8px;
      border: 1px solid #E2E8F0;
    }}

    /* ── Report body typography ───────────────────────────────────────── */
    .section-heading {{
      font-size: 1.0rem;
      font-weight: 700;
      color: #0F172A;
      margin: 24px 0 8px;
      padding-bottom: 5px;
      border-bottom: 2px solid #3B82F6;
      display: inline-block;
    }}
    .report-title {{
      font-size: 1.2rem;
      font-weight: 800;
      color: #0F172A;
      margin-bottom: 8px;
    }}
    .body-para {{
      font-size: 0.82rem;
      color: #334155;
      margin-bottom: 8px;
      line-height: 1.65;
    }}
    .bullet-list {{
      margin: 6px 0 10px 18px;
      padding: 0;
    }}
    .bullet-list li {{
      font-size: 0.82rem;
      color: #334155;
      margin-bottom: 4px;
      line-height: 1.6;
    }}
    .bullet-list li::marker {{ color: #3B82F6; font-size: 1.1em; }}
    .spacer {{ height: 4px; }}

    /* ── Footer ───────────────────────────────────────────────────────── */
    .footer {{
      background: #F8FAFC;
      border-top: 1px solid #E2E8F0;
      padding: 12px 48px;
      font-size: 0.68rem;
      color: #94A3B8;
      text-align: center;
    }}
  </style>
</head>
<body>
<div class="page">

  <!-- ── Cover band ──────────────────────────────────────────── -->
  <div class="cover-band">
    <div class="brand-row">
      {_LOGO_SVG}
      <div>
        <div class="brand-name">PrepVector</div>
        <div class="brand-sub">Cognitive Assessment Platform</div>
      </div>
    </div>

    <div class="report-heading">AI Evaluation Report</div>
    <div class="report-subheading">Data Science Expert — Self-Assessment</div>

    <div class="score-cards">
      <div class="score-card">
        <div class="label">Candidate</div>
        <div class="value" style="font-size:1.1rem; padding-top:4px;">{candidate_name}</div>
      </div>
      <div class="score-card">
        <div class="label">Final Score</div>
        <div class="value">{weighted_score}<span style="font-size:0.9rem;font-weight:500;"> / 70</span></div>
        <div class="sublabel">weighted points</div>
      </div>
      <div class="score-card">
        <div class="label">Correct Answers</div>
        <div class="value">{total_correct}<span style="font-size:0.9rem;font-weight:500;"> / {total_questions}</span></div>
        <div class="sublabel">questions</div>
        <div class="status-badge">{pass_label}</div>
      </div>
    </div>
  </div>

  <!-- ── Meta row ────────────────────────────────────────────── -->
  <div class="meta-row">
    <span><strong>Assessment Date:</strong> {assessment_date}</span>
    <span><strong>Report Generated:</strong> {generated_on}</span>
    <span><strong>Role:</strong> Data Science Expert</span>
  </div>

  <!-- ── Content ─────────────────────────────────────────────── -->
  <div class="content">

    <!-- Chart -->
    <div class="chart-section">
      <img src="{chart_b64}" alt="Section Performance Chart"/>
    </div>

    <!-- AI Report body -->
    {body_html}

  </div>

  <!-- ── Footer ──────────────────────────────────────────────── -->
  <div class="footer">
    Generated by PrepVector Cognitive Career Assessment System &nbsp;|&nbsp; Confidential
  </div>

</div>
</body>
</html>
"""


# ─────────────────────────────────────────────────────────────────────────────
# 3.  Playwright PDF renderer
# ─────────────────────────────────────────────────────────────────────────────

def generate_playwright_pdf_report(
    candidate_name: str,
    markdown_text: str,
    section_scores: dict | None = None,
    avg_scores: dict | None = None,
    weighted_score: int = 0,
    total_correct: int = 0,
    total_questions: int = 35,
    assessment_date: str = "",
) -> str:
    """
    Generates a polished PDF report using Playwright (Chromium).

    Runs synchronously — call generate_playwright_pdf_report_async() from
    async contexts so this executes safely in a threadpool worker via
    asyncio.to_thread() (required on Windows where ProactorEventLoop raises
    NotImplementedError for subprocess creation inside the event loop).

    Returns the absolute path of the saved PDF file.
    """
    from playwright.sync_api import sync_playwright

    _REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    now          = datetime.now(timezone.utc)
    generated_on = now.strftime("%B %d, %Y at %H:%M UTC")
    if not assessment_date:
        assessment_date = now.strftime("%B %d, %Y")

    # 1. Build the Base64 chart
    chart_b64 = generate_score_chart_base64(
        section_scores=section_scores or {},
        avg_scores=avg_scores,
    )

    # 2. Build the HTML string
    html_content = _build_html_report(
        candidate_name  = candidate_name or "Candidate",
        markdown_text   = markdown_text,
        chart_b64       = chart_b64,
        weighted_score  = weighted_score,
        total_correct   = total_correct,
        total_questions = total_questions,
        assessment_date = assessment_date,
        generated_on    = generated_on,
    )

    # 3. Naming convention: {candidate_name}_Self-Assessment_Report.pdf
    safe_name = re.sub(r"[^\w\s-]", "", candidate_name or "Candidate").strip()
    safe_name = re.sub(r"\s+", "_", safe_name)
    filename  = f"{safe_name}_Self-Assessment_Report.pdf"
    out_path  = _REPORTS_DIR / filename

    # 4. Render with Playwright (sync — offloaded to thread by the async wrapper)
    print("[report_writer] Launching Playwright to render PDF...")
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page    = browser.new_page()

        # Set the HTML content directly (no temp file needed)
        page.set_content(html_content, wait_until="networkidle")

        # PDF options: A4, no additional margins (we handle padding in CSS)
        page.pdf(
            path=str(out_path),
            format="A4",
            print_background=True,
            margin={"top": "0mm", "bottom": "0mm", "left": "0mm", "right": "0mm"},
        )
        browser.close()

    print(f"[report_writer] PDF saved -> {out_path}")
    return str(out_path.resolve())


# ─────────────────────────────────────────────────────────────────────────────
# 4.  Async threadpool wrapper
#     Runs sync Playwright in a background thread — safe on Windows
#     (ProactorEventLoop cannot create subprocesses inside the event loop).
# ─────────────────────────────────────────────────────────────────────────────

import asyncio

async def generate_playwright_pdf_report_async(*args, **kwargs) -> str:
    """Runs synchronous Playwright PDF generation in a background thread."""
    return await asyncio.to_thread(generate_playwright_pdf_report, *args, **kwargs)


# ─────────────────────────────────────────────────────────────────────────────
# 5.  Legacy shim (kept for backwards-compatibility)
#     submit_answers.py calls generate_pdf_report() — redirect to async wrapper.
# ─────────────────────────────────────────────────────────────────────────────

async def generate_pdf_report(
    markdown_text: str,
    candidate_name: str = "Candidate",
    assessment_date: str = "",
    weighted_score: int = 0,
    total_correct: int = 0,
    total_questions: int = 35,
    section_scores: dict | None = None,
    avg_scores: dict | None = None,
) -> str:
    """
    Backwards-compatible async wrapper: offloads sync Playwright to a thread.
    """
    return await generate_playwright_pdf_report_async(
        candidate_name  = candidate_name,
        markdown_text   = markdown_text,
        section_scores  = section_scores,
        avg_scores      = avg_scores,
        weighted_score  = weighted_score,
        total_correct   = total_correct,
        total_questions = total_questions,
        assessment_date = assessment_date,
    )
