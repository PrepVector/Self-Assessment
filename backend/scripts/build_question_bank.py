"""
build_question_bank.py
======================
Pre-generates a structured JSON question pool for all 7 Data Science Expert
sections across 3 difficulty levels using the Gemini API with Groq as an
ultimate backup.
"""

import os
import sys
import json
import time
import pathlib

from dotenv import load_dotenv
from google import genai
from google.genai import types
from groq import Groq
from pydantic import BaseModel, Field

# ─── 0. Bootstrap ─────────────────────────────────────────────────────────────

SCRIPT_DIR  = pathlib.Path(__file__).resolve().parent          # backend/scripts/
BACKEND_DIR = SCRIPT_DIR.parent                                # backend/
DATA_DIR    = BACKEND_DIR / "data"
OUTPUT_FILE = DATA_DIR / "question_bank.json"

load_dotenv(BACKEND_DIR / ".env")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GROQ_API_KEY   = os.getenv("GROQ_API_KEY")
GROQ_MODEL     = "llama-3.3-70b-versatile"
SLEEP_SECONDS  = 15

GEMINI_MODELS: list[tuple[str, str]] = [
    ("gemini-3.5-flash",      "Tier-1 Primary   · Gemini 3.5 Flash"),
    ("gemini-2.5-flash",      "Tier-2 Fallback  · Gemini 2.5 Flash"),
    ("gemini-2.5-flash-lite", "Tier-3 Fallback  · Gemini 2.5 Flash-Lite"),
]

if not GEMINI_API_KEY:
    print("❌  GEMINI_API_KEY not found in environment. Aborting.")
    sys.exit(1)

if not GROQ_API_KEY:
    print("⚠️   GROQ_API_KEY not found — Groq (Tier-4) fallback will be unavailable.")

client      = genai.Client(api_key=GEMINI_API_KEY)
client_groq = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

# ─── 1. Curriculum ────────────────────────────────────────────────────────────

# 🎯 TARGET MODE: Only regenerating SQL — all other sections preserved
SECTIONS = [
    "SQL",
    # "Python",
    # "Pandas",
    # "Data Visualization",
    # "Applied Statistics",
    # "Machine Learning",
    # "A/B Testing",
]

DIFFICULTY_TARGETS = {
    "Easy":     8,
    "Moderate": 8,
    "Advanced": 5,
}

IMAGE_ELIGIBLE_SECTIONS = {"Data Visualization", "Machine Learning", "Applied Statistics"}

# ─── 2. Pydantic schemas ──────────────────────────────────────────────────────

class Question(BaseModel):
    id:             str           = Field(description="Unique ID, e.g., 'sql_easy_q1'")
    difficulty:     str           = Field(description="Must be 'Easy', 'Moderate', or 'Advanced'")
    text:           str           = Field(
        description=(
            "The question text. MUST include code snippets or practical scenarios where "
            "applicable. All SQL/code/regex must be in triple-backtick blocks. "
            "NATURAL LINE BREAKS AND INDENTATION MUST BE PRESERVED INSIDE CODE BLOCKS. "
            "All inline variable names must be in single backticks. All math symbols must "
            "use LaTeX dollar-sign notation."
        )
    )
    options:        list[str]     = Field(description="Exactly 4 multiple choice options. Can be code outputs.")
    correct_answer: str           = Field(description="The exact text of the correct option")
    explanation:    str           = Field(
        description=(
            "Detailed explanation of why the answer is correct and the others are wrong. "
            "Apply the same formatting rules as 'text': triple backticks for code "
            "(PRESERVING LINE BREAKS), LaTeX for math, Markdown tables for tabular data."
        )
    )
    image_path:     str | None    = Field(
        default=None,
        description=(
            "If the question requires a visual plot/chart to be answered, provide a "
            "descriptive local filename like 'kmeans_elbow.png'. Otherwise, return null."
        )
    )

class QuestionBatch(BaseModel):
    section_name: str            = Field(description="The Data Science Expert topic being tested")
    difficulty:   str            = Field(description="Difficulty level of all questions in this batch")
    questions:    list[Question] = Field(description="Questions at the specified difficulty level")

# ─── 3. Prompt builder ────────────────────────────────────────────────────────

def build_prompt(section: str, difficulty: str, target_count: int) -> str:
    section_id = section.lower().replace(" ", "_")

    # ── Strict Difficulty Rubric ──
    rubric = {
        "Easy":     "EASY RUBRIC: Basic concepts, 1-step logic, standard syntax. Typical solve time under 2 mins. NO complex loops, NO deep architectural edge cases.",
        "Moderate": "MODERATE RUBRIC: 2-3 step logic. Includes standard list comprehensions, basic decorators, dictionary manipulation, and standard exception handling.",
        "Advanced": "ADVANCED RUBRIC: Highest cognitive load. Multi-step reasoning, production edge cases, memory management, complex closures, deep class inheritance, or generator optimization.",
    }
    active_rubric = rubric.get(difficulty, "")

    if section == "Python":
        domain_rules = (
            "DOMAIN ISOLATION (CRITICAL): You are FORBIDDEN from importing or referencing "
            "Pandas or NumPy in any question or code snippet. Focus PURELY on core Python "
            "logic: built-in data structures (list, dict, set, tuple), comprehensions, "
            "generators, itertools, functools, collections, exception handling, decorators, "
            "closures, and memory management."
        )
    elif section == "SQL":
        domain_rules = (
            "DOMAIN ISOLATION & SQL STYLING RULES (CRITICAL):\n"
            "\u2022 Every SQL query MUST be enclosed inside a proper GitHub-Flavored Markdown fenced code block beginning with ```sql and ending with ```.\n"
            "\u2022 The SQL code block MUST terminate immediately after the final SQL clause or semicolon.\n"
            "\u2022 Never place English explanations, hints, or question text inside the SQL code block.\n"
            "\u2022 SQL keywords MUST always be uppercase (SELECT, FROM, WHERE, GROUP BY, HAVING, ORDER BY, CASE, WHEN, THEN, ELSE, END, COALESCE, NULLIF, ROW_NUMBER, OVER, PARTITION BY, CAST).\n"
            "\u2022 Format SQL professionally with proper indentation.\n"
            "\u2022 NEVER flatten complex SQL into a single line.\n"
            "\u2022 Use realistic analytics and data-science scenarios (customers, orders, experiments, transactions, predictions, logs, datasets).\n"
            "\u2022 Include practical SQL topics such as NULL handling, COALESCE, NULLIF, GROUP BY, HAVING, JOINs, CTEs, ROW_NUMBER(), PARTITION BY, deduplication, string cleaning, type casting, and aggregations.\n"
            "\u2022 Never leave literal text such as 'sql SELECT ...' inside prose. The query must appear only inside a fenced SQL block.\n"
            "\n"
            "INCORRECT:\n"
            "```sql SELECT * FROM users WHERE age > 30;```\n"
            "\n"
            "CORRECT:\n"
            "```sql\n"
            "SELECT *\n"
            "FROM users\n"
            "WHERE age > 30;\n"
            "```\n"
        )
    else:
        domain_rules = (
            f"Focus deeply on realistic, scenario-based {section} problems that a "
            "working data scientist would encounter. Emphasize practical edge cases, "
            "common pitfalls, and production-grade decision-making."
        )

    if section in IMAGE_ELIGIBLE_SECTIONS:
        image_rule = (
            "RULE 6 — IMAGE PLACEHOLDERS: For at least 2 of your questions, set `image_path` "
            "to a descriptive .png filename. Write the question text as if the candidate is "
            "LOOKING AT that chart (e.g., 'Analyze the residual plot shown below')."
        )
    else:
        image_rule = "RULE 6 — IMAGE PLACEHOLDERS: Set `image_path` to null for ALL questions."

    # Build the correct/incorrect indentation examples as plain string variables
    # to avoid any ambiguity inside the outer f-string.
    correct_example = (
        "```python\n"
        "def preprocess(text):\n"
        "    tokens = text.lower().split()\n"
        "    return [t for t in tokens if t.isalpha()]\n"
        "```"
    )
    incorrect_example = (
        "```python\n"
        "def preprocess(text): tokens = text.lower().split(); return [t for t in tokens if t.isalpha()]\n"
        "```"
    )

    prompt = (
        "You are a Senior Technical Recruiter creating a rigorous assessment for a Data Science Expert.\n"
        "\n"
        "YOUR TASK:\n"
        f"Generate exactly {target_count} {difficulty} multiple-choice questions for the topic: "
        f"**{section}** (ID prefix: `{section_id}`).\n"
        "\n"
        "DIFFICULTY CALIBRATION:\n"
        f"{active_rubric}\n"
        "\n"
        "DOMAIN RULES:\n"
        f"{domain_rules}\n"
        "\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "STRICT FORMATTING RULES — VIOLATIONS WILL INVALIDATE THE OUTPUT\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "\n"
        "RULE 1 — MARKDOWN STRICTNESS:\n"
        "  • ALL SQL queries and Python code MUST be enclosed in standard triple-backtick fenced code blocks.\n"
        "  • ALL inline variable names MUST be wrapped in single backticks.\n"
        "\n"
        "RULE 2 — MATHEMATICS (LaTeX):\n"
        "  • ALL mathematical symbols MUST use LaTeX notation wrapped in dollar signs (e.g., $\\sigma$).\n"
        "  • ALL standalone equations MUST use double dollar signs on their own line.\n"
        "\n"
        "RULE 3 — CODE FORMATTING & INDENTATION (CRITICAL):\n"
        "  • You MUST preserve natural line breaks and strict indentation inside all code blocks.\n"
        "  • NEVER compress multi-line Python or SQL code into a single line.\n"
        "  • Each logical statement MUST appear on its own line, indented correctly.\n"
        "\n"
        "  CORRECT Python formatting:\n"
        f"  {correct_example}\n"
        "\n"
        "  INCORRECT Python formatting (DO NOT DO THIS):\n"
        f"  {incorrect_example}\n"
        "\n"
        "RULE 4 — OPTION QUALITY:\n"
        "  • Each question MUST have exactly 4 options.\n"
        "  • All distractors must be plausible but clearly wrong upon careful analysis.\n"
        "  • Options that are code outputs MUST preserve exact whitespace and formatting.\n"
        "\n"
        "RULE 5 — IDs:\n"
        f"  • Every question `id` MUST follow the pattern: `{section_id}_{{difficulty_lower}}_q{{N}}`\n"
        "    where N starts at 1 (e.g., `python_easy_q1`, `python_easy_q2`, ...).\n"
        "\n"
        f"{image_rule}\n"
        "\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "QUESTION QUALITY RULES\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "\n"
        "SQL INTERNAL VALIDATION (apply before returning each SQL question):\n"
        "  \u2022 Every SQL block begins exactly with ```sql (on its own line).\n"
        "  \u2022 Every SQL block ends exactly with ``` (on its own line).\n"
        "  \u2022 Every SQL block contains multiple properly indented SQL lines.\n"
        "  \u2022 No English prose appears inside any SQL fence.\n"
        "  \u2022 Indentation is preserved; SQL keywords are uppercase.\n"
        "\n"
        "NO DUPLICATED OPTIONS IN CODE:\n"
        "  You are STRICTLY FORBIDDEN from embedding or commenting answer choices\n"
        "  (Option A / Option B / Option C / Option D) inside any SQL or Python code block.\n"
        "  Code blocks must contain ONLY executable SQL/Python.\n"
        "  All answer choices must exist exclusively inside the JSON \"options\" array.\n"
        "\n"
        "STANDARDIZED QUESTION WORDING:\n"
        "  Use consistent interview-style openings, for example:\n"
        "    \"Consider the following SQL query:\"\n"
        "    \"What will be returned by the following SQL query?\"\n"
        "    \"Given the following SQL statement:\"\n"
        "    \"Analyze the following SQL query:\"\n"
        "\n"
        "REALISTIC SQL ONLY:\n"
        "  Never generate toy SQL examples such as SELECT * FROM table;\n"
        "  Prefer realistic schemas: customers, orders, transactions, employees,\n"
        "  sales, products, predictions, logs, experiments, clickstream, campaigns.\n"
        "\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "OUTPUT FORMAT\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "Return a single JSON object matching the `QuestionBatch` schema exactly.\n"
        "Do NOT wrap the JSON in markdown code fences.\n"
        "Do NOT add any commentary before or after the JSON.\n"
    )
    return prompt

# ─── 4. Generation (Gemini → Groq fallback) ───────────────────────────────────

def generate_batch(section: str, difficulty: str, target_count: int) -> QuestionBatch | None:
    prompt = build_prompt(section, difficulty, target_count)

    # ── Try each Gemini tier ──
    for model_id, label in GEMINI_MODELS:
        print(f"  🔷 Trying {label} …")
        try:
            response = client.models.generate_content(
                model=model_id,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=QuestionBatch,
                    temperature=0.7,
                ),
            )
            batch = QuestionBatch.model_validate_json(response.text)
            print(f"  ✅ {label} succeeded — {len(batch.questions)} questions generated.")
            return batch
        except Exception as exc:
            print(f"  ⚠️  {label} failed: {exc}")
            time.sleep(SLEEP_SECONDS)

    # ── Tier-4: Groq fallback ──
    if client_groq:
        print(f"  🟠 Trying Tier-4 Fallback · Groq ({GROQ_MODEL}) …")
        try:
            chat = client_groq.chat.completions.create(
                model=GROQ_MODEL,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.7,
            )
            raw = chat.choices[0].message.content
            # Groq sometimes omits root-level keys — inject them before validation
            parsed_raw = json.loads(raw)
            parsed_raw["section_name"] = section
            parsed_raw["difficulty"] = difficulty
            batch = QuestionBatch.model_validate(parsed_raw)
            print(f"  ✅ Groq succeeded — {len(batch.questions)} questions generated.")
            return batch
        except Exception as exc:
            print(f"  ❌ Groq also failed: {exc}")

    print(f"  ❌ ALL tiers failed for {section} / {difficulty}. Skipping.")
    return None

# ─── 5. Main ──────────────────────────────────────────────────────────────────

def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    meta_data = {}
    # ── Safe Load: preserve existing sections not being regenerated ──
    if OUTPUT_FILE.exists():
        try:
            with OUTPUT_FILE.open("r", encoding="utf-8") as f:
                full_data = json.load(f)
                # CRITICAL FIX: Extract only the 'sections' object
                bank = full_data.get("sections", {})
                meta_data = full_data.get("meta", {})
            print(f"📂 Loaded existing question_bank.json — will update only: {SECTIONS}")
        except json.JSONDecodeError:
            print("⚠️  Existing question_bank.json is malformed — starting fresh.")
            bank = {}
    else:
        print("📂 No existing question_bank.json found — creating from scratch.")
        bank = {}

    total_sections = len(SECTIONS)
    for sec_idx, section in enumerate(SECTIONS, 1):
        print(f"\n{'═'*60}")
        print(f"📚 Section {sec_idx}/{total_sections}: {section}")
        print(f"{'═'*60}")

        section_data: dict[str, list] = {}

        for difficulty, target_count in DIFFICULTY_TARGETS.items():
            print(f"\n  🎯 Difficulty: {difficulty} ({target_count} questions)")
            batch = generate_batch(section, difficulty, target_count)

            if batch:
                questions_as_dicts = [q.model_dump() for q in batch.questions]
                section_data[difficulty] = questions_as_dicts
                print(f"  💾 Stored {len(questions_as_dicts)} questions for {section} / {difficulty}")
            else:
                section_data[difficulty] = []

            time.sleep(SLEEP_SECONDS)

        # Only update the sections we're regenerating — leave all others intact
        bank[section] = section_data

    # ── Write output ──
    # CRITICAL FIX: Repackage the data into the correct schema
    output_data = {
        "meta": meta_data,
        "sections": bank
    }
    
    with OUTPUT_FILE.open("w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print(f"\n{'═'*60}")
    print(f"✅ question_bank.json saved → {OUTPUT_FILE}")
    print(f"   Sections in file: {list(bank.keys())}")
    print(f"{'═'*60}\n")


if __name__ == "__main__":
    main()