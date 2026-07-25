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
from app.config.report_defaults import DEFAULT_BENCHMARKS, get_performance_status

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
    weighted_score: int,
    total_correct: int,
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

    success_rate = (total_correct / total_questions * 100) if total_questions > 0 else 0

    prompt = f"""
You are a senior Data Science Career Coach writing a CONCISE professional evaluation report.

Candidate Assessment:
- Correct Answers: {total_correct} / {total_questions} ({success_rate:.1f}% accuracy)
- Weighted Score: {weighted_score} / 70

Incorrect Answers:
{wrong_answers_formatted}

STRICT OUTPUT RULES — you MUST follow all of these:
1. Total output must be UNDER 400 WORDS (fits on 2 PDF pages). Be direct, not verbose.
2. Use EXACTLY these 4 Markdown section headers, in this order:
   ## Executive Summary
   ## Key Strengths
   ## Top Blind Spots
   ## Actionable Learning Resources
3. "Executive Summary": 2-3 sentences max. Reference both the correct-answer count and weighted score.
4. "Key Strengths": Bullet list (max 4 bullets) of topics the candidate handled well.
5. "Top Blind Spots": Bullet list of 2-3 weak areas identified from wrong answers. Each bullet names the topic and gives a one-sentence explanation of the gap.
6. "Actionable Learning Resources": Bullet list of 3-4 specific, practical recommendations (e.g., "Practice window functions in Mode Analytics SQL editor", "Read Chapter 7 of ISLR on regularization"). No vague advice.
7. Do NOT include any other sections, headers, or preamble outside these 4.
8. Do NOT repeat the score data anywhere except the Executive Summary.
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
  <path d="M19 8C14.03 8 10 12.03 10 17c0 3.17 1.63 5.96 4.1 7.61V28h9.8v-3.39C26.37 22.96 28 20.17 28 17c0-4.97-4.03-9-9-9z"
        fill="none" stroke="white" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>
  <line x1="19" y1="8" x2="19" y2="13" stroke="white" stroke-width="1.4" stroke-linecap="round"/>
  <line x1="13" y1="17" x2="16" y2="17" stroke="white" stroke-width="1.4" stroke-linecap="round"/>
  <line x1="22" y1="17" x2="25" y2="17" stroke="white" stroke-width="1.4" stroke-linecap="round"/>
  <line x1="15" y1="28" x2="23" y2="28" stroke="white" stroke-width="1.6" stroke-linecap="round"/>
  <line x1="16.5" y1="31" x2="21.5" y2="31" stroke="white" stroke-width="1.4" stroke-linecap="round"/>
</svg>
"""


def _markdown_to_html_sections(md: str) -> dict[str, str]:
    """
    Parse the 4-section Markdown report into a dict keyed by section heading.
    Returns: {
        "Executive Summary": "<html>",
        "Key Strengths":     "<html>",
        "Top Blind Spots":   "<html>",
        "Actionable Learning Resources": "<html>",
    }
    Falls back to a single "body" key if the sections are not found.
    """
    EXPECTED = [
        "Executive Summary",
        "Key Strengths",
        "Top Blind Spots",
        "Actionable Learning Resources",
    ]

    def _inline(text: str) -> str:
        return re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)

    def _render_lines(raw_lines: list[str]) -> str:
        html   = []
        in_ul  = False
        for line in raw_lines:
            s = line.strip()
            if not s:
                if in_ul:
                    html.append("</ul>")
                    in_ul = False
                continue
            if re.match(r"^[-*+]\s+", s):
                text = re.sub(r"^[-*+]\s+", "", s)
                if not in_ul:
                    html.append('<ul class="bullet-list">')
                    in_ul = True
                html.append(f"<li>{_inline(text)}</li>")
            else:
                if in_ul:
                    html.append("</ul>")
                    in_ul = False
                html.append(f'<p class="body-para">{_inline(s)}</p>')
        if in_ul:
            html.append("</ul>")
        return "\n".join(html)

    lines   = md.splitlines()
    current = None
    buckets: dict[str, list[str]] = {k: [] for k in EXPECTED}

    for line in lines:
        stripped = line.strip()
        matched  = False
        if stripped.startswith("## "):
            heading = stripped[3:].strip()
            for key in EXPECTED:
                if key.lower() in heading.lower():
                    current = key
                    matched = True
                    break
        if not matched and current:
            buckets[current].append(line)

    return {k: _render_lines(v) for k, v in buckets.items()}


def _star_rating(score_pct: float) -> str:
    """Return 1-5 filled/empty star SVG based on 0-100 percentage."""
    filled = round(score_pct / 20)   # 0-100 → 0-5 stars
    stars  = ""
    for i in range(5):
        color = "#F59E0B" if i < filled else "#CBD5E1"
        stars += f'<svg style="display:inline;" width="14" height="14" viewBox="0 0 24 24" fill="{color}"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/></svg>'
    return stars


def _build_attempt_stats_table(
    section_scores: dict,
    wrong_answers_by_section: dict[str, list[dict]],
    questions_per_section: dict[str, int],
) -> str:
    """
    Build an HTML table: Section | Total Q | Attempted | Correct | Incorrect | Skipped | Accuracy.
    Skipped = questions with an empty/missing user_answer.
    """
    rows = []
    SECTIONS = list(section_scores.keys()) if section_scores else list(questions_per_section.keys())

    for section in SECTIONS:
        total_q    = questions_per_section.get(section, 5)
        wrong_list = wrong_answers_by_section.get(section, [])
        # Separate skipped (empty answer) from incorrect (wrong answer submitted)
        skipped   = sum(1 for wa in wrong_list if not wa.get("user_answer", "").strip())
        incorrect = len(wrong_list) - skipped
        correct   = total_q - len(wrong_list)   # = total - (incorrect + skipped)
        attempted = total_q - skipped
        accuracy  = (correct / attempted * 100) if attempted > 0 else 0.0

        rows.append(
            f"<tr>"
            f"<td style='text-align:left;font-weight:600;'>{section}</td>"
            f"<td>{total_q}</td>"
            f"<td>{attempted}</td>"
            f"<td style='color:#16A34A;font-weight:700;'>{correct}</td>"
            f"<td style='color:#DC2626;font-weight:700;'>{incorrect}</td>"
            f"<td style='color:#F59E0B;font-weight:700;'>{skipped}</td>"
            f"<td>{accuracy:.0f}%</td>"
            f"</tr>"
        )

    return (
        '<table class="data-table">'
        "<thead><tr>"
        "<th style='text-align:left;'>Section</th>"
        "<th>Total Q</th><th>Attempted</th>"
        "<th>Correct</th><th>Incorrect</th><th>Skipped</th>"
        "<th>Accuracy</th>"
        "</tr></thead><tbody>"
        + "".join(rows)
        + "</tbody></table>"
    )


def _build_benchmark_table(
    section_scores: dict,
    avg_scores: dict,
) -> str:
    """Build the Skill Rating & Benchmark comparison table."""
    rows = []
    for section, cval in section_scores.items():
        cval  = float(cval)
        aval  = float(avg_scores.get(section, DEFAULT_BENCHMARKS.get(section, 5.0)))
        delta = cval - aval
        delta_str  = f"+{delta:.1f}" if delta >= 0 else f"{delta:.1f}"
        delta_color = "#16A34A" if delta >= 0 else "#DC2626"
        label, badge_color = get_performance_status(cval, aval)
        rows.append(
            f"<tr>"
            f"<td style='text-align:left;font-weight:600;'>{section}</td>"
            f"<td>{cval:.0f} / 10</td>"
            f"<td>{aval:.1f}</td>"
            f"<td style='color:{delta_color};font-weight:700;'>{delta_str}</td>"
            f"<td><span class='status-badge-sm' style='background:{badge_color};'>{label}</span></td>"
            f"</tr>"
        )

    return (
        '<table class="data-table">'
        "<thead><tr>"
        "<th style='text-align:left;'>Section</th>"
        "<th>Your Score</th><th>Reference Benchmark (Demo)</th>"
        "<th>Delta</th><th>Status</th>"
        "</tr></thead><tbody>"
        + "".join(rows)
        + "</tbody></table>"
    )


def _build_resource_grid(resources_html: str) -> str:
    """
    Wrap bullet-list resource items into 2-column grid cards.
    Each <li> becomes a .resource-card with a checkmark tag.
    """
    items = re.findall(r"<li>(.*?)</li>", resources_html, re.DOTALL)
    if not items:
        return resources_html   # fallback — render as-is

    cards = []
    for item in items:
        item = item.strip()
        cards.append(
            f'<div class="resource-card">'
            f'<div class="resource-card-title">{item}</div>'
            f'<span class="resource-tag">&#10003; Action Item</span>'
            f"</div>"
        )
    return f'<div class="resource-grid">{chr(10).join(cards)}</div>'


def _build_html_report(
    candidate_name: str,
    markdown_text: str,
    chart_b64: str,
    weighted_score: int,
    total_correct: int,
    total_questions: int,
    assessment_date: str,
    generated_on: str,
    section_scores: dict | None = None,
    avg_scores: dict | None = None,
    wrong_answers_by_section: dict | None = None,
    questions_per_section: dict | None = None,
) -> str:
    """
    Assembles the complete HTML string that Playwright will render to PDF.
    Uses inline CSS only (no external resources — critical for Playwright).

    Document flow:
      1. Header Cover Band
      2. Performance Snapshot Card
      3. Section Performance Chart
      4. Skill Rating & Benchmark Table
      5. Attempt Statistics Breakdown Table
      6. Executive Summary Card
      7. Key Strengths
      8. Top Blind Spots
      9. Actionable Learning Resources Grid
     10. Professional Footer
    """
    section_scores         = section_scores or {}
    avg_scores             = avg_scores or DEFAULT_BENCHMARKS
    wrong_answers_by_sect  = wrong_answers_by_section or {}
    questions_per_sect     = questions_per_section or {s: 5 for s in section_scores}

    success_pct = (weighted_score / 70 * 100) if weighted_score else 0
    pass_label  = "Qualified"        if success_pct >= 60 else "Needs Improvement"
    pass_color  = "#16A34A"          if success_pct >= 60 else "#DC2626"

    # ── Derived snapshot stats ────────────────────────────────────────────────
    stars_html = _star_rating(success_pct)
    strongest  = max(section_scores, key=section_scores.get) if section_scores else "N/A"
    weakest    = min(section_scores, key=section_scores.get) if section_scores else "N/A"

    # ── Tables ────────────────────────────────────────────────────────────────
    benchmark_table = _build_benchmark_table(section_scores, avg_scores) if section_scores else ""
    attempt_table   = _build_attempt_stats_table(
        section_scores, wrong_answers_by_sect, questions_per_sect
    ) if section_scores else ""

    # ── LLM section HTML ─────────────────────────────────────────────────────
    sections_html  = _markdown_to_html_sections(markdown_text)
    exec_body      = sections_html.get("Executive Summary", "")
    strengths_body = sections_html.get("Key Strengths", "")
    blindspots_body= sections_html.get("Top Blind Spots", "")
    resources_raw  = sections_html.get("Actionable Learning Resources", "")
    resources_body = _build_resource_grid(resources_raw)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>{candidate_name} — Self-Assessment Report</title>
  <style>
    /* ── Reset & base ─────────────────────────────────────────────────── */
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    html {{ font-size: 14.5px; }}
    body {{
      font-family: -apple-system, "Segoe UI", Helvetica, Arial, sans-serif;
      background: #fff;
      color: #1E293B;
      line-height: 1.6;
    }}

    /* ── Page wrapper ─────────────────────────────────────────────────── */
    .page {{
      width: 794px;
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
      font-size: 0.85rem; font-weight: 700;
      letter-spacing: 0.12em; color: #93C5FD; text-transform: uppercase;
    }}
    .brand-sub {{
      font-size: 0.72rem; color: #64748B;
      letter-spacing: 0.06em; margin-top: 2px;
    }}
    .report-heading {{
      font-size: 2rem; font-weight: 800;
      letter-spacing: -0.02em; line-height: 1.15;
      color: #fff; margin-bottom: 6px;
    }}
    .report-subheading {{
      font-size: 0.8rem; color: #94A3B8; margin-bottom: 28px;
    }}

    /* ── Score cards row ──────────────────────────────────────────────── */
    .score-cards {{ display: flex; gap: 14px; }}
    .score-card {{
      background: rgba(255,255,255,0.07);
      border: 1px solid rgba(255,255,255,0.12);
      border-radius: 10px; padding: 14px 22px; min-width: 130px;
    }}
    .score-card .label {{
      font-size: 0.62rem; font-weight: 700; letter-spacing: 0.1em;
      text-transform: uppercase; color: #94A3B8; margin-bottom: 4px;
    }}
    .score-card .value {{
      font-size: 1.55rem; font-weight: 800;
      color: #fff; letter-spacing: -0.02em;
    }}
    .score-card .sublabel {{ font-size: 0.62rem; color: #64748B; margin-top: 2px; }}
    .status-badge {{
      display: inline-block; font-size: 0.7rem; font-weight: 700;
      letter-spacing: 0.08em; text-transform: uppercase;
      padding: 4px 12px; border-radius: 999px;
      background: {pass_color}22; color: {pass_color};
      border: 1px solid {pass_color}55; margin-top: 6px;
    }}

    /* ── Meta row ─────────────────────────────────────────────────────── */
    .meta-row {{
      background: #F8FAFC; border-bottom: 1px solid #E2E8F0;
      padding: 10px 48px; display: flex; gap: 32px;
      font-size: 0.7rem; color: #64748B;
    }}
    .meta-row strong {{ color: #334155; }}

    /* ── Content body ─────────────────────────────────────────────────── */
    .content {{ padding: 28px 48px 40px; }}

    /* ── Print Media Page Break Rules ────────────────────────────────── */
    .data-table, .data-table tr, .resource-card, .exec-summary-card, .snapshot-container {{
      page-break-inside: avoid;
      break-inside: avoid;
    }}
    .chart-section {{
      page-break-inside: avoid;
      break-inside: avoid;
      margin-bottom: 38px;
      text-align: center;
    }}
    .chart-section img {{
      max-width: 100%; border-radius: 8px; border: 1px solid #E2E8F0;
    }}
    h2.section-heading {{
      page-break-after: avoid;
      break-after: avoid;
    }}

    /* ── Section headings ─────────────────────────────────────────────── */
    .section-heading {{
      font-size: 0.92rem; font-weight: 700; color: #0F172A;
      margin: 22px 0 10px; padding-bottom: 5px;
      border-bottom: 2px solid #3B82F6; display: inline-block;
    }}
    .report-title {{
      font-size: 1.4rem; font-weight: 800; color: #0F172A; margin-bottom: 8px;
    }}
    .body-para {{
      font-size: 0.88rem; color: #334155;
      margin-bottom: 8px; line-height: 1.6;
    }}
    .bullet-list {{ margin: 6px 0 10px 18px; padding: 0; }}
    .bullet-list li {{
      font-size: 0.88rem; color: #334155;
      margin-bottom: 4px; line-height: 1.6;
    }}
    .bullet-list li::marker {{ color: #3B82F6; font-size: 1.1em; }}
    .spacer {{ height: 4px; }}

    /* ── Performance Snapshot Card ────────────────────────────────────── */
    .snapshot-container {{
      display: flex;
      justify-content: space-between;
      background: #F8FAFC;
      border: 1px solid #E2E8F0;
      border-radius: 10px;
      padding: 14px 20px;
      margin: 20px 0 24px;
    }}
    .snapshot-item {{ text-align: center; }}
    .snapshot-label {{
      font-size: 0.65rem; color: #64748B;
      text-transform: uppercase; font-weight: 700;
    }}
    .snapshot-value {{
      font-size: 1.1rem; color: #0F172A;
      font-weight: 800; margin-top: 2px;
    }}

    /* ── Executive Summary Highlight Card ────────────────────────────── */
    .exec-summary-card {{
      background: #EFF6FF;
      border-left: 4px solid #3B82F6;
      border-radius: 6px;
      padding: 16px 20px;
      margin-bottom: 24px;
    }}
    .exec-summary-card h2 {{
      font-size: 0.95rem; color: #1E40AF;
      margin-bottom: 6px; border-bottom: none;
      display: block; padding-bottom: 0;
    }}

    /* ── Styled Data Tables ───────────────────────────────────────────── */
    .data-table {{
      width: 100%; border-collapse: collapse;
      margin-bottom: 32px; font-size: 0.85rem;
    }}
    .data-table th {{
      background: #F1F5F9; color: #0F172A;
      font-weight: 700; padding: 10px 12px;
      border: 1px solid #CBD5E1; text-align: center;
    }}
    .data-table td {{
      padding: 9px 12px; border: 1px solid #E2E8F0;
      text-align: center; color: #334155;
    }}
    .data-table tr:nth-child(even) td {{ background: #FAFAFA; }}
    .status-badge-sm {{
      font-size: 0.65rem; font-weight: 700;
      padding: 2px 8px; border-radius: 12px;
      color: #fff; display: inline-block;
    }}

    /* ── Actionable Resources Card Grid ──────────────────────────────── */
    .resource-grid {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 16px;
      margin-top: 14px;
    }}
    .resource-card {{
      background: #F8FAFC;
      border: 1px solid #E2E8F0;
      border-radius: 8px;
      padding: 16px;
      display: flex;
      flex-direction: column;
      height: 100%;
    }}
    .resource-card-title {{
      font-weight: 800; color: #0F172A;
      font-size: 0.9rem; margin-bottom: 8px;
    }}
    .resource-tag {{
      display: inline-block;
      background: #DBEAFE; color: #1E40AF;
      font-size: 0.75rem; font-weight: 600;
      padding: 4px 8px; border-radius: 4px;
      margin-bottom: 8px; align-self: flex-start;
    }}

    /* ── Footer (fixed at bottom) ─────────────────────────────────────── */
    .footer {{
      position: fixed;
      bottom: 0;
      width: 100%;
      background: #F8FAFC; border-top: 1px solid #E2E8F0;
      padding: 12px 48px; font-size: 0.68rem;
      color: #94A3B8; text-align: center;
    }}
  </style>
</head>
<body>
<div class="page">

  <!-- 1. Cover Band -->
  <div class="cover-band">
    <div class="brand-row">
      {_LOGO_SVG}
      <div>
        <div class="brand-name">PrepVector</div>
        <div class="brand-sub">Cognitive Assessment Platform</div>
      </div>
    </div>
    <div class="report-heading">AI Evaluation Report</div>
    <div class="report-subheading">Data Science Expert &mdash; Self-Assessment</div>
    <div class="score-cards">
      <div class="score-card">
        <div class="label">Candidate</div>
        <div class="value" style="font-size:1.0rem;padding-top:4px;">{candidate_name}</div>
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

  <!-- Meta row -->
  <div class="meta-row">
    <span><strong>Assessment Date:</strong> {assessment_date}</span>
    <span><strong>Report Generated:</strong> {generated_on}</span>
    <span><strong>Role:</strong> Data Science Expert</span>
  </div>

  <!-- Content -->
  <div class="content">

    <!-- 2. Performance Snapshot Card -->
    <div class="snapshot-container">
      <div class="snapshot-item">
        <div class="snapshot-label">Overall Rating</div>
        <div class="snapshot-value">{stars_html}</div>
      </div>
      <div class="snapshot-item">
        <div class="snapshot-label">Success Rate</div>
        <div class="snapshot-value">{success_pct:.1f}%</div>
      </div>
      <div class="snapshot-item">
        <div class="snapshot-label">Weighted Score</div>
        <div class="snapshot-value">{weighted_score} / 70</div>
      </div>
      <div class="snapshot-item">
        <div class="snapshot-label">Top Skill</div>
        <div class="snapshot-value" style="font-size:0.88rem;">{strongest}</div>
      </div>
      <div class="snapshot-item">
        <div class="snapshot-label">Needs Immediate Attention</div>
        <div class="snapshot-value" style="font-size:0.88rem;">{weakest}</div>
      </div>
    </div>

    <!-- 3. Section Performance Chart -->
    <div class="chart-section">
      <img src="{chart_b64}" alt="Section Performance Chart"/>
    </div>

    <!-- 4. Skill Rating & Benchmark Table -->
    <div class="section-heading">Skill Rating &amp; Benchmark</div>
    {benchmark_table}

    <!-- 5. Attempt Statistics Breakdown -->
    <div class="section-heading">Attempt Statistics Breakdown</div>
    {attempt_table}

    <!-- 6. Executive Summary Card -->
    <div class="exec-summary-card">
      <h2>Executive Summary</h2>
      {exec_body}
    </div>

    <!-- 7. Key Strengths -->
    <div class="section-heading">Key Strengths</div>
    {strengths_body}

    <!-- 8. Top Blind Spots -->
    <div class="section-heading">Top Blind Spots</div>
    {blindspots_body}

    <!-- 9. Actionable Learning Resources -->
    <div class="section-heading">Actionable Learning Resources</div>
    {resources_body}

  </div>

  <!-- 10. Footer -->
  <div class="footer">
    Page 1 of 2 &nbsp;|&nbsp; Generated: {generated_on} &nbsp;|&nbsp; Version v1.0 &nbsp;|&nbsp; Confidential &nbsp;|&nbsp; PrepVector Cognitive Career Assessment System
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
    wrong_answers_by_section: dict | None = None,
    questions_per_section: dict | None = None,
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
        candidate_name           = candidate_name or "Candidate",
        markdown_text            = markdown_text,
        chart_b64                = chart_b64,
        weighted_score           = weighted_score,
        total_correct            = total_correct,
        total_questions          = total_questions,
        assessment_date          = assessment_date,
        generated_on             = generated_on,
        section_scores           = section_scores,
        avg_scores               = avg_scores,
        wrong_answers_by_section = wrong_answers_by_section,
        questions_per_section    = questions_per_section,
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
    wrong_answers_by_section: dict | None = None,
    questions_per_section: dict | None = None,
) -> str:
    """
    Backwards-compatible async wrapper: offloads sync Playwright to a thread.
    """
    return await generate_playwright_pdf_report_async(
        candidate_name           = candidate_name,
        markdown_text            = markdown_text,
        section_scores           = section_scores,
        avg_scores               = avg_scores,
        weighted_score           = weighted_score,
        total_correct            = total_correct,
        total_questions          = total_questions,
        assessment_date          = assessment_date,
        wrong_answers_by_section = wrong_answers_by_section,
        questions_per_section    = questions_per_section,
    )

