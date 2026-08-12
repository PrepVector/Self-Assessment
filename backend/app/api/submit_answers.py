"""
submit_answers.py
=================
Receives a completed quiz submission, calls the report writer agent, and
persists the result to a CSV log file (backend/data/user_assessments.csv).

MongoDB has been fully removed. All persistence is done via the standard
library csv module — no extra dependencies required.

Scoring model — "Clean 70" (2-2-1 ratio, weighted points):
  Easy     → 1 pt  | Moderate → 2 pts  | Advanced → 4 pts
  Per section max  : 2×1 + 2×2 + 1×4 = 10 pts
  Quiz total max   : 7 sections × 10 pts = 70 pts
  Pass threshold   : success_rate_pct >= 60  (i.e., ≥ 42 weighted points)

CSV columns written per submission:
  assessment_id, timestamp, name, email,
  sql_score, python_score, pandas_score, data_visualization_score,
  applied_statistics_score, machine_learning_score, ab_testing_score,
  total_score, total_possible, success_rate_pct, qualification_status
"""

import asyncio
import csv
import pathlib
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.agents.report_writer import (
    generate_evaluation_report,
    generate_pdf_report,
    build_report_data,
    generate_new_playwright_pdf_async,
)
from app.services.email_service import send_report_email
from app.services.google_sheets import append_assessment_row, update_email_by_assessment_id

router = APIRouter()

# ─── Path resolution ──────────────────────────────────────────────────────────
_SUBMIT_DIR  = pathlib.Path(__file__).resolve().parent          # backend/app/api/
_BACKEND_DIR = _SUBMIT_DIR.parent.parent                        # backend/
_CSV_PATH    = _BACKEND_DIR / "data" / "user_assessments.csv"
_REPORTS_DIR = _BACKEND_DIR / "generated_reports"

_CSV_HEADERS = [
    "assessment_id",
    "timestamp",
    "name",
    "email",
    "sql_score",
    "python_score",
    "pandas_score",
    "data_visualization_score",
    "applied_statistics_score",
    "machine_learning_score",
    "ab_testing_score",
    "total_score",
    "total_possible",
    "success_rate_pct",
    "qualification_status",
]

# Section name → CSV column mapping  (lower-cased, spaces→underscores)
_SECTION_COL = {
    "SQL":                  "sql_score",
    "Python":               "python_score",
    "Pandas":               "pandas_score",
    "Data Visualization":   "data_visualization_score",
    "Applied Statistics":   "applied_statistics_score",
    "Machine Learning":     "machine_learning_score",
    "A/B Testing":          "ab_testing_score",
}

# Clean-70 scoring: 7 sections × (2×1 + 2×2 + 1×4) = 7 × 10 = 70 weighted points
TOTAL_POSSIBLE  = 70     # max achievable weighted score
PASS_THRESHOLD  = 60.0   # success_rate_pct >= 60 → "Qualified" (>= 42 pts out of 70)

# ─── Pydantic models ──────────────────────────────────────────────────────────

class WrongAnswer(BaseModel):
    question_text:  str
    user_answer:    str
    correct_answer: str
    explanation:    Optional[str] = None
    section_name:   Optional[str] = None

class QuizSubmission(BaseModel):
    name:            Optional[str] = "Anonymous"
    email:           Optional[str] = ""
    score:           int
    total_questions: int
    wrong_answers:   List[WrongAnswer]
    # Section-level breakdown: { "SQL": 4, "Python": 3, ... }
    section_scores:  Optional[dict[str, int]] = None

# ─── CSV helpers ──────────────────────────────────────────────────────────────

def _ensure_csv() -> None:
    """Creates the CSV file with a header row if it doesn't exist yet."""
    _CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not _CSV_PATH.exists():
        with open(_CSV_PATH, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=_CSV_HEADERS)
            writer.writeheader()
        print(f"[submit_answers] Created CSV log at {_CSV_PATH}")


def _append_to_csv(row: dict) -> None:
    """Appends a single result row to user_assessments.csv."""
    _ensure_csv()
    with open(_CSV_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=_CSV_HEADERS, extrasaction="ignore")
        writer.writerow(row)
    print(f"[submit_answers] Assessment logged to {_CSV_PATH.name}")


def _build_csv_row(submission: QuizSubmission, assessment_id: str) -> dict:
    """Converts a QuizSubmission into a flat CSV row dict."""
    success_rate   = (submission.score / TOTAL_POSSIBLE * 100) if TOTAL_POSSIBLE > 0 else 0.0
    qualification  = "Qualified" if success_rate >= PASS_THRESHOLD else "Needs Improvement"

    # Derive per-section scores from the section_scores field (if provided),
    # or fall back to inferring them from the wrong_answers list.
    section_correct: dict[str, int] = {}

    if submission.section_scores:
        section_correct = {k: v for k, v in submission.section_scores.items()}
    else:
        # Fallback: count wrong answers per section, then compute correct = 5 - wrong.
        # NOTE: under the Clean-70 model the frontend should send section_scores
        # as weighted point totals (not simple correct-question counts).  This
        # fallback assumes 1 pt per wrong answer lost, which is a conservative
        # approximation when section_scores is unavailable.
        wrong_by_section: dict[str, int] = {}
        for wa in submission.wrong_answers:
            sn = wa.section_name or "Unknown"
            wrong_by_section[sn] = wrong_by_section.get(sn, 0) + 1

        for section in _SECTION_COL:
            wrong_count = wrong_by_section.get(section, 0)
            section_correct[section] = max(0, 5 - wrong_count)

    row = {
        "assessment_id":        assessment_id,
        "timestamp":            datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "name":                 submission.name or "Anonymous",
        "email":                submission.email or "",
        "total_score":          submission.score,
        "total_possible":       TOTAL_POSSIBLE,
        "success_rate_pct":     f"{success_rate:.1f}",
        "qualification_status": qualification,
    }

    # Populate per-section columns
    for section_name, col_name in _SECTION_COL.items():
        row[col_name] = section_correct.get(section_name, "")

    return row




# ─── Endpoint ─────────────────────────────────────────────────────────────────

# ─── Pydantic model for the email endpoint ────────────────────────────────────

class EmailPayload(BaseModel):
    email:         str
    assessment_id: str


@router.post("/submit-email")
async def submit_email_endpoint(payload: EmailPayload):
    candidate_name = "Candidate"
    _ensure_csv()
    rows = []
    updated = False

    # 1. Update CSV and capture the candidate's name
    with open(_CSV_PATH, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("assessment_id") == payload.assessment_id:
                row["email"] = payload.email.strip()
                candidate_name = row.get("name", "Candidate")
                updated = True
            rows.append(row)

    if updated:
        with open(_CSV_PATH, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=_CSV_HEADERS, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)
        print(f"[submit_email] Email updated in CSV for assessment_id={payload.assessment_id}")
        
        # Update Google Sheets
        try:
            await asyncio.to_thread(update_email_by_assessment_id, payload.assessment_id, payload.email.strip())
        except Exception as exc:
            print(f"[submit_email] ** Google Sheets update failed (non-fatal): {exc}")
    else:
        print(f"[submit_email] ⚠️ assessment_id={payload.assessment_id} not found in CSV")

    # 2. Reconstruct PDF path and dispatch email
    safe_name = candidate_name.replace(" ", "_")
    pdf_filename = f"{safe_name}_Self-Assessment_Report.pdf"
    pdf_path = _REPORTS_DIR / pdf_filename

    if pdf_path.exists():
        try:
            await send_report_email(
                to_email=payload.email.strip(),
                candidate_name=candidate_name,
                pdf_path=str(pdf_path)
            )
            print(f"[submit_email] Report emailed successfully to {payload.email.strip()}")
        except Exception as exc:
            print(f"[submit_email] ⚠️ Email delivery failed: {exc}")
    else:
        print(f"[submit_email] ⚠️ Could not find PDF to email at {pdf_path}")

    return {"status": "ok", "message": "Email processed."}


@router.post("/submit-answers")
async def submit_answers_endpoint(submission: QuizSubmission):
    """
    Receives a completed quiz submission.
    1. Generates a unique assessment_id for this session.
    2. Instantly appends a structured row to backend/data/user_assessments.csv.
    3. Builds Phase 1 reportData + Phase 2 PrepVector PDF (new primary pipeline).
    4. Falls back to legacy Markdown pipeline if the new pipeline fails.
    5. Returns assessment_id so the frontend can link the email submission later.
    """
    # 1. Generate a unique, human-readable session ID
    assessment_id = datetime.now().strftime("%Y%m%d_%H%M%S_") + uuid.uuid4().hex[:6]
    download_url: str | None = None

    # 2. SAVE TO CSV FIRST (Guarantees data is saved instantly!)
    try:
        row = _build_csv_row(submission, assessment_id)
        _append_to_csv(row)
        
        # 2.5 APPEND TO GOOGLE SHEETS
        try:
            await asyncio.to_thread(append_assessment_row, row, _CSV_HEADERS)
        except Exception as exc:
            print(f"[submit_answers] ** Google Sheets logging failed (non-fatal): {exc}")
            
    except Exception as exc:
        print(f"[submit_answers] ** CSV logging failed: {exc}")

    # 2a. Derive answer counts used by both the new and legacy pipelines
    total_answered = submission.total_questions
    total_wrong    = len(submission.wrong_answers)
    total_correct  = max(0, total_answered - total_wrong)

    # 2b. PHASE 1 + PHASE 2 — Build structured reportData, then render new PDF.
    #     Wrapped in a single try/except so any failure is non-fatal.
    try:
        wrong_answers_by_section_p1: dict[str, list[dict]] = {}
        for wa in submission.wrong_answers:
            sn = wa.section_name or "Unknown"
            wrong_answers_by_section_p1.setdefault(sn, []).append(wa.model_dump())

        questions_per_section_p1: dict[str, int] = {s: 5 for s in _SECTION_COL}

        report_data = build_report_data(
            candidate_name           = submission.name or "Anonymous",
            assessment_id            = assessment_id,
            weighted_score           = submission.score,
            total_correct            = total_correct,
            total_questions          = total_answered,
            section_scores           = submission.section_scores or {},
            wrong_answers_by_section = wrong_answers_by_section_p1,
            questions_per_section    = questions_per_section_p1,
        )
        _insight_count = len(report_data.get("skillInsights", {}))
        print(
            f"[submit_answers] Phase 1 reportData built -- "
            f"{len(report_data['skills'])} skills classified, "
            f"{_insight_count}/7 AI insights received."
        )

        # Phase 2: render the new PrepVector HTML template -> PDF
        pdf_path = await generate_new_playwright_pdf_async(
            report_data    = report_data,
            candidate_name = submission.name or "Candidate",
        )
        if pdf_path:
            filename     = pathlib.Path(pdf_path).name
            download_url = f"/api/download-report/{filename}"
            print(f"[submit_answers] New PrepVector PDF ready: {filename}")

    except Exception as exc:
        # Phase 1/2 failure must NEVER break CSV persistence or the response
        print(f"[submit_answers] ** Phase 1/2 pipeline failed (non-fatal): {exc}")

    # 3. Legacy Markdown pipeline — runs ONLY as fallback when the new pipeline failed.
    #    Kept intact per Phase 2 spec to allow easy rollback.
    report_markdown = ""
    if download_url is None:
        print("[submit_answers] Falling back to legacy Markdown/PDF pipeline...")
        try:
            wrong_answers_dicts = [wa.model_dump() for wa in submission.wrong_answers]
            report_markdown = generate_evaluation_report(
                weighted_score  = submission.score,
                total_correct   = total_correct,
                total_questions = submission.total_questions,
                wrong_answers   = wrong_answers_dicts,
            )
            if not report_markdown:
                raise ValueError("Empty report returned by AI.")
        except Exception as exc:
            print(f"[submit_answers] ** Report generation skipped/failed: {exc}")
            report_markdown = "Report generation delayed."

        # 3b. Convert legacy Markdown report to PDF
        try:
            if report_markdown and report_markdown != "Report generation delayed.":
                wrong_answers_by_section: dict[str, list[dict]] = {}
                for wa in submission.wrong_answers:
                    sn = wa.section_name or "Unknown"
                    wrong_answers_by_section.setdefault(sn, []).append(wa.model_dump())

                questions_per_section: dict[str, int] = {s: 5 for s in _SECTION_COL}

                legacy_pdf_path = await generate_pdf_report(
                    markdown_text            = report_markdown,
                    candidate_name           = submission.name or "Candidate",
                    weighted_score           = submission.score,
                    total_correct            = total_correct,
                    total_questions          = total_answered,
                    section_scores           = submission.section_scores or {},
                    wrong_answers_by_section = wrong_answers_by_section,
                    questions_per_section    = questions_per_section,
                )
                if legacy_pdf_path:
                    filename     = pathlib.Path(legacy_pdf_path).name
                    download_url = f"/api/download-report/{filename}"
        except Exception as pdf_exc:
            print(f"[submit_answers] ** Legacy PDF generation failed (non-fatal): {pdf_exc}")

    # 4. Return the response
    return {"assessment_id": assessment_id, "report": report_markdown, "download_url": download_url}