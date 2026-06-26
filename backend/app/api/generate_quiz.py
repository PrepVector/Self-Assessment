"""
generate_quiz.py
================
Serves a stratified random sample drawn from the pre-generated question bank
(backend/data/question_bank.json).

Sampling strategy — "Clean 70" model (35 questions total, one quiz per request):
  For each of the 7 sections:
    • 2 Easy     → points: 1 each
    • 2 Moderate → points: 2 each
    • 1 Advanced → points: 4 each
  Total per section: 5 questions  |  Max section score: 10
  Total quiz max score: 7 × (2×1 + 2×2 + 1×4) = 7 × 10 = 70

Confidence Builder (ordering):
  - One of the two Easy questions is always placed at index [0] so users
    start each section with an approachable question.
  - The remaining 4 questions are randomly shuffled after that first slot.

The returned JSON shape is IDENTICAL to the old Gemini-generated response so
that the React frontend requires zero changes beyond reading the `points` field.
"""

import json
import random
import pathlib

from fastapi import APIRouter, HTTPException

router = APIRouter()

# ─── Path resolution ──────────────────────────────────────────────────────────
# This file lives at  backend/app/api/generate_quiz.py
# The bank lives at   backend/data/question_bank.json
_API_DIR     = pathlib.Path(__file__).resolve().parent          # backend/app/api/
_BACKEND_DIR = _API_DIR.parent.parent                           # backend/
_BANK_PATH   = _BACKEND_DIR / "data" / "question_bank.json"

# ─── Load bank once at import time ────────────────────────────────────────────
def _load_bank() -> dict:
    if not _BANK_PATH.exists():
        raise FileNotFoundError(
            f"Question bank not found at {_BANK_PATH}. "
            "Run scripts/build_question_bank.py first."
        )
    with open(_BANK_PATH, encoding="utf-8") as f:
        return json.load(f)

try:
    _QUESTION_BANK = _load_bank()
    _SECTIONS_ORDER: list[str] = _QUESTION_BANK["meta"]["sections"]
    print(f"[generate_quiz] ✅  Question bank loaded — "
          f"{_QUESTION_BANK['meta']['total_questions']} questions across "
          f"{len(_SECTIONS_ORDER)} sections.")
except Exception as _exc:
    _QUESTION_BANK = None
    _SECTIONS_ORDER = []
    print(f"[generate_quiz] ⚠️  Could not load question bank: {_exc}")

# ─── "Clean 70" scoring model ─────────────────────────────────────────────────
# Difficulty label → points injected into each question object
_POINTS_MAP: dict[str, int] = {
    "Easy":     1,
    "Moderate": 2,
    "Advanced": 4,
}

# 2-2-1 ratio: exactly 2 Easy, 2 Moderate, 1 Advanced per section
_DIFFICULTY_QUOTA: dict[str, int] = {
    "Easy":     2,
    "Moderate": 2,
    "Advanced": 1,
}

# ─── Sampler ──────────────────────────────────────────────────────────────────

def _sample_section(section_name: str, section_pool: dict) -> dict:
    """
    Draws questions from a single section's pool according to the 2-2-1 quota.

    For every selected question a `points` integer field is injected:
      Easy → 1 | Moderate → 2 | Advanced → 4

    Ordering:
      Strict ascending difficulty order:
      Q1 = Easy
      Q2 = Easy
      Q3 = Moderate
      Q4 = Moderate
      Q5 = Advanced

    Returns a QuizSection-shaped dict matching the old Gemini schema.
    """
    # ── Step 1: sample by difficulty and inject `points` ──────────────────────
    sampled_by_difficulty: dict[str, list[dict]] = {}

    for difficulty, quota in _DIFFICULTY_QUOTA.items():
        pool = section_pool.get(difficulty, [])
        if len(pool) < quota:
            # Graceful degradation: take whatever exists rather than crashing
            chosen = pool[:]
        else:
            chosen = random.sample(pool, quota)

        points_value = _POINTS_MAP.get(difficulty, 1)
        # Inject `points` into a shallow copy so we never mutate the bank
        chosen = [{**q, "points": points_value} for q in chosen]
        sampled_by_difficulty[difficulty] = chosen

    # ── Step 2: Assemble final ordered list ───────────────────────────────────
    easy_questions = sampled_by_difficulty.get("Easy", [])
    moderate_questions = sampled_by_difficulty.get("Moderate", [])
    advanced_questions = sampled_by_difficulty.get("Advanced", [])

    ordered_questions = (
        easy_questions +
        moderate_questions +
        advanced_questions
    )

    return {
        "section_name": section_name,
        "questions": ordered_questions,
    }


def _build_quiz() -> dict:
    """
    Assembles a full 35-question quiz via stratified sampling.
    Output mirrors the old AssessmentQuiz Pydantic shape exactly:
        { "role": "Data Science Expert", "sections": [ {...}, ... ] }

    NOTE: This function should only be called after confirming _QUESTION_BANK
    is not None (the /generate-quiz endpoint enforces this guard).
    """
    if _QUESTION_BANK is None:
        return {"role": "Data Science Expert", "sections": []}

    bank_sections: dict = _QUESTION_BANK["sections"]
    sections_out: list[dict] = []

    for section_name in _SECTIONS_ORDER:
        section_pool = bank_sections.get(section_name, {})
        sections_out.append(_sample_section(section_name, section_pool))

    return {
        "role": "Data Science Expert",
        "sections": sections_out,
    }

# ─── Endpoint ─────────────────────────────────────────────────────────────────

@router.post("/generate-quiz")
def generate_quiz_endpoint():
    """
    Returns a freshly sampled 35-question Data Science Expert quiz drawn from
    the pre-generated question bank.  No Gemini API call is made at request time.

    Each question object now carries a `points` field (1 / 2 / 4) reflecting the
    Clean-70 scoring model so the frontend can display weighted scoring.
    """
    if _QUESTION_BANK is None:
        raise HTTPException(
            status_code=503,
            detail=(
                "Question bank is not available. "
                "Please run scripts/build_question_bank.py to generate it."
            ),
        )

    quiz = _build_quiz()

    if not quiz["sections"]:
        raise HTTPException(status_code=500, detail="Failed to sample quiz from question bank.")

    return quiz