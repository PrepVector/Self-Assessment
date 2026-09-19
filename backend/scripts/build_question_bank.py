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
import re

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

# 🎯 TARGET MODE: Only regenerating Data Visualization — all other buckets preserved
SECTIONS = [
    # "SQL",
    # "Python",
    # "Pandas",
    "Data Visualization",
    # "Applied Statistics",
    # "Machine Learning",
    # "A/B Testing",
]

# Sections that must NOT be modified by this run (locked)
LOCKED_SECTIONS = {
    "SQL",
    "Python",
    "Pandas",
    "Applied Statistics",
    "A/B Testing",
    "Machine Learning",
    "meta",
}

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

# ─── 3a. Batch Validation ─────────────────────────────────────────────────────

_LEAKAGE_PHRASES = [
    "let me", "i need to", "it seems", "re-evaluating", "corrected version",
    "corrected json", "correction:", "miscalculation", "internal reasoning",
    "apologize", "regenerate", "here's the corrected", "json",
    "rewrite", "here is the json", "as an ai",
]

# Trigger phrases that require a non-null image_path
_VISUAL_TRIGGERS = [
    "shown below",
    "following plot",
    "following figure",
    "residual plot",
    "heatmap",
    "confusion matrix",
    "decision boundary",
    "roc curve",
    "pca plot",
    "learning curve",
    "calibration curve",
    "feature importance plot",
    "bias-variance plot",
]

# LaTeX commands that must never appear inside fenced code blocks
_LATEX_IN_CODE_PATTERNS = [
    r"\\alpha",
    r"\\beta",
    r"\\sigma",
    r"\\theta",
    r"\\mu",
    r"\\lambda",
    r"\\gamma",
]

# Prose code leakage patterns — executable keywords leaking into plain text
# Each tuple is (language_label, pattern_list)
_PROSE_CODE_LEAKAGE_PATTERNS = [
    (
        "python",
        [
            r"\bpython\s+import\b",
            r"\bpython\s+from\b",
            r"\bpython\s+def\b",
            r"\bpython\s+class\b",
            r"\bpython\s+np\.",
            r"\bpython\s+pd\.",
            r"\bpython\s+stats\.",
            r"\bpython\s+scipy\b",
            r"\bpython\s+statsmodels\b",
            r"\bpython\s+model\s*=",
            r"\bpython\s+clf\s*=",
            r"\bpython\s+estimator\s*=",
            r"\bpython\s+pipeline\s*=",
            r"\bpython\s+X\s*=",
            r"\bpython\s+y\s*=",
        ],
    ),
    (
        "sql",
        [
            r"\bsql\s+SELECT\b",
            r"\bsql\s+WITH\b",
            r"\bsql\s+INSERT\b",
            r"\bsql\s+UPDATE\b",
            r"\bsql\s+DELETE\b",
            r"\bsql\s+CREATE\b",
            r"\bsql\s+ALTER\b",
            r"\bsql\s+DROP\b",
        ],
    ),
]

# Malformed math / escape sequences to reject in prose
_BAD_MATH_PATTERNS = [
    r"\$\$\$",            # triple dollar
    r"\\times\s+alpha",   # broken: \times alpha instead of \times \alpha
]


def _extract_fenced_blocks(text: str) -> list[str]:
    """Return the body content of every fenced code block found in *text*."""
    pattern = re.compile(r"```[^\n`]*\n(.*?)```", re.DOTALL)
    return pattern.findall(text)

def _extract_python_blocks(text: str) -> list[str]:
    """Return the body content of every python fenced code block."""
    pattern = re.compile(r"```python\b[^\n]*\n(.*?)```", re.DOTALL)
    return pattern.findall(text)

def _strip_fenced_blocks(text: str) -> str:
    """Return *text* with all fenced code blocks removed (leaving only prose)."""
    return re.sub(r"```.*?```", "", text, flags=re.DOTALL)

def validate_batch(batch: QuestionBatch, target_count: int) -> None:
    """Raise ValueError with a descriptive message if the batch fails any check."""

    # 1. Question count
    if len(batch.questions) != target_count:
        raise ValueError(
            f"Incomplete batch generation — expected {target_count}, "
            f"got {len(batch.questions)}"
        )
    print("    ✓ Question count validated")

    for q in batch.questions:
        # 2. Unique options
        if len(set(q.options)) != 4:
            raise ValueError(
                f"Duplicate options detected in question '{q.id}'"
            )

        # 3. Correct answer present in options exactly once
        if not q.correct_answer or q.options.count(q.correct_answer) != 1:
            raise ValueError(
                f"Invalid correct answer in question '{q.id}' — "
                f"'{q.correct_answer}' must appear exactly once in options"
            )

        # 4. Prompt leakage in text or explanation
        combined = (q.text + " " + q.explanation).lower()
        for phrase in _LEAKAGE_PHRASES:
            if phrase in combined:
                raise ValueError(
                    f"Prompt leakage detected in question '{q.id}' — found phrase: '{phrase}'"
                )

        # 5. Malformed explanation (embedded JSON object, duplicate fences,
        #    or a nested full question block)
        exp = q.explanation
        if '{"id"' in exp or '"correct_answer"' in exp:
            raise ValueError(
                f"Malformed explanation detected in question '{q.id}' — "
                "explanation contains an embedded JSON object"
            )
        if exp.count("```") > 6:          # generous ceiling for legit code snippets
            raise ValueError(
                f"Malformed explanation detected in question '{q.id}' — "
                "excessive markdown fences suggest duplicated content"
            )

        # ── Markdown fence validation ────────────────────────────────────────

        for field_name, field_text in [("text", q.text), ("explanation", q.explanation)]:

            def _fence_error(rule: str, match: re.Match) -> ValueError:
                """Build a rich, debuggable fence error with context snippet."""
                start = max(0, match.start() - 40)
                end   = min(len(field_text), match.end() + 80)
                snippet = repr(field_text[start:end])
                return ValueError(
                    f"Malformed Markdown fence detected.\n"
                    f"\n  Question : {q.id}"
                    f"\n  Field    : {field_name}"
                    f"\n  Rule     : {rule}"
                    f"\n  Snippet  : {snippet}"
                )

            # 6a. Code appears on the SAME LINE as the language tag
            #     Matches:  ```python import ...   or   ```sql SELECT
            #     Does NOT match: ```python\nimport ...  (newline after tag is valid)
            m = re.search(r"```(?:python|sql)[ \t]+\S", field_text)
            if m:
                raise _fence_error("6a (Inline fence — code on same line as language tag)", m)

            # 6b. Trailing space immediately after language tag (before newline)
            #     DISABLED: Explanation prose may legitimately produce trailing spaces
            #     after a language tag in some rendering contexts; this caused false
            #     positives for valid Data Visualization outputs.
            # m = re.search(r"```(?:python|sql) +(?=\n|$)", field_text)
            # if m:
            #     raise _fence_error("6b (Trailing space after language tag)", m)

            # 6c. Malformed language tag — extra characters appended to python/sql tag
            #     Catches:  ```python2, ```sqlABC, ```pythonimport, ```sqlSELECT
            #     Accepts:  ```python\n  ```sql\n  (newline immediately after tag = valid)
            #     Accepts:  ```json, ```bash etc. (non-project langs ignored; only python/sql checked)
            m = re.search(r"```(?:python|sql)(?![\n\r]|$)", field_text)
            if m:
                raise _fence_error("6c (Malformed language tag — unexpected characters after python/sql)", m)

            # 6d. Unclosed fenced blocks
            fence_count = field_text.count("```")
            if fence_count % 2 != 0:
                raise ValueError(
                    f"Malformed Markdown fence detected.\n"
                    f"\n  Question : {q.id}"
                    f"\n  Field    : {field_name}"
                    f"\n  Rule     : 6d (Unclosed fence — odd number of ``` markers)"
                    f"\n  Count    : {fence_count} backtick-fence markers found"
                )

            # 6e. Empty Python code blocks
            for block in _extract_python_blocks(field_text):
                if not block.strip():
                    raise ValueError("Empty Python code block detected.")

            # 6f. Prose code leakage
            prose_only = _strip_fenced_blocks(field_text)
            for lang_label, patterns in _PROSE_CODE_LEAKAGE_PATTERNS:
                for pat in patterns:
                    if re.search(pat, prose_only, re.IGNORECASE):
                        raise ValueError("Prose code leakage detected.")

            # 6g. LaTeX found inside Python code blocks
            for block_body in _extract_python_blocks(field_text):
                for latex_pat in _LATEX_IN_CODE_PATTERNS:
                    if re.search(latex_pat, block_body):
                        raise ValueError("LaTeX found inside Python code block.")

            # 6h. Malformed math / escape sequences in prose
            for bad_pat in _BAD_MATH_PATTERNS:
                if re.search(bad_pat, prose_only):
                    raise ValueError("Malformed math symbols or escape sequences detected.")

        # ── Image / prose validation ─────────────────────────────────────────

        # 7. Raw filename (.png / .jpg / .jpeg) must never appear inside prose fields
        for field_name, field_text in [("text", q.text), ("explanation", q.explanation)]:
            if re.search(r"\.(png|jpg|jpeg)\b", field_text, re.IGNORECASE):
                raise ValueError("Raw filename found in prose.")

        # 8. Image consistency — visual trigger → image_path must be set
        # Only the question stem determines whether an image is required.
        # The explanation may naturally mention visual terms (ROC curve, heatmap,
        # etc.) without requiring an image_path.
        text_lower = q.text.lower()
        for trigger in _VISUAL_TRIGGERS:
            if trigger in text_lower:
                if not q.image_path:
                    raise ValueError("Missing image_path for referenced visual.")
                break

        # ── ASCII table guard ─────────────────────────────────────────────────

        # 9. Reject ASCII-style tables
        for field_name, field_text in [("text", q.text), ("explanation", q.explanation)]:
            lines = field_text.splitlines()
            pipe_rows = [ln.strip() for ln in lines if ln.strip().startswith("|")]
            if len(pipe_rows) >= 3:
                has_separator = any(re.match(r"\|[\s\-:]+(\|[\s\-:]+)+\|", row) for row in pipe_rows)
                if not has_separator:
                    raise ValueError(
                        f"ASCII/malformed table detected in question '{q.id}' field '{field_name}' — "
                        "use GitHub-Flavored Markdown tables with a separator row"
                    )

    print("    ✓ Unique options validated")
    print("    ✓ Correct answer validated")
    print("    ✓ Prompt leakage check passed")
    print("    ✓ Markdown fence validation passed")
    print("    ✓ Prose code leakage check passed")
    print("    ✓ LaTeX-in-code isolation check passed")
    print("    ✓ Math escape sequence check passed")
    print("    ✓ Image prose validation passed")
    print("    ✓ Image consistency validation passed")
    print("    ✓ Table format validation passed")

# ─── 3b. File-safe section ID helper ─────────────────────────────────────────

def _section_to_id_prefix(section: str) -> str:
    """
    Convert a section name to a filesystem-safe lowercase ID prefix.

    "A/B Testing"        → "ab_testing"
    "Applied Statistics" → "applied_statistics"
    "Data Visualization" → "data_visualization"
    """
    safe = re.sub(r"[^a-zA-Z0-9\s]", "", section)   # strip slashes, hyphens, etc.
    return safe.strip().lower().replace(" ", "_")

# ─── 3. Prompt builder ────────────────────────────────────────────────────────

def build_prompt(section: str, difficulty: str, target_count: int) -> str:
    section_id = _section_to_id_prefix(section)

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
    elif section == "Pandas":
        domain_rules = (
            "DOMAIN ISOLATION & STYLING RULES (CRITICAL):\n"
            "  • Focus exclusively on the pandas library using `import pandas as pd`.\n"
            "  • Cover DataFrames, Series, indexing (.loc/.iloc), filtering, sorting, merges, joins, concat, groupby, pivot_table, melt, explode, apply, vectorization, datetime handling, missing values, duplicates, string operations, categorical data, and reshaping.\n"
            "  • Use realistic datasets such as sales, employees, students, products, customers, transactions, experiments, or sensor readings instead of abstract placeholders whenever possible.\n"
            "  • Every code example MUST be enclosed inside a proper ```python fenced code block.\n"
            "  • Code blocks must contain ONLY executable Python code. Never include explanations, option labels, comments like 'Option A', or English prose inside the fenced block.\n"
            "  • Every snippet must be syntactically valid Python that can execute after importing pandas.\n"
            "  • Preserve natural indentation exactly.\n"
            "  • NEVER flatten chained pandas operations into a single line.\n"
            "    INCORRECT formatting:\n"
            "    ```python\n"
            "    result = df.groupby('category').sum().reset_index().sort_values('total')\n"
            "    ```\n"
            "    CORRECT formatting:\n"
            "    ```python\n"
            "    result = (\n"
            "        df.groupby('category')\n"
            "          .sum()\n"
            "          .reset_index()\n"
            "          .sort_values('total')\n"
            "    )\n"
            "    ```\n"
            "  • Prefer readable multi-line DataFrame creation.\n"
            "  • TABLE RENDERING: Whenever a DataFrame output must be shown, render it using GitHub-Flavored Markdown (GFM) tables.\n"
            "  • NEVER imitate notebook output or console output using aligned spaces or ASCII tables.\n"
        )
    elif section == "SQL":
        domain_rules = (
            "DOMAIN ISOLATION & SQL STYLING RULES (CRITICAL):\n"
            "• Every SQL query MUST be enclosed inside a proper GitHub-Flavored Markdown fenced code block beginning with ```sql and ending with ```.\n"
            "• The SQL code block MUST terminate immediately after the final SQL clause or semicolon.\n"
            "• Never place English explanations, hints, or question text inside the SQL code block.\n"
            "• SQL keywords MUST always be uppercase (SELECT, FROM, WHERE, GROUP BY, HAVING, ORDER BY, CASE, WHEN, THEN, ELSE, END, COALESCE, NULLIF, ROW_NUMBER, OVER, PARTITION BY, CAST).\n"
            "• Format SQL professionally with proper indentation.\n"
            "• NEVER flatten complex SQL into a single line.\n"
            "• Use realistic analytics and data-science scenarios (customers, orders, experiments, transactions, predictions, logs, datasets).\n"
            "• Include practical SQL topics such as NULL handling, COALESCE, NULLIF, GROUP BY, HAVING, JOINs, CTEs, ROW_NUMBER(), PARTITION BY, deduplication, string cleaning, type casting, and aggregations.\n"
            "• Never leave literal text such as 'sql SELECT ...' inside prose. The query must appear only inside a fenced SQL block.\n"
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
    elif section == "Applied Statistics":
        domain_rules = (
            "DOMAIN ISOLATION & STYLING RULES (CRITICAL):\n"
            "  • Focus on real-world statistics including probability distributions, hypothesis testing, t-tests, ANOVA, regression diagnostics, confidence intervals, p-values, z-scores, Bayesian reasoning, sampling, bootstrap, and regression assumptions.\n"
            "  • Any Python examples MUST use proper fenced ```python blocks with standard libraries such as scipy.stats, numpy, pandas, or statsmodels.\n"
            "  • Every fenced code block must begin exactly as:\n"
            "      ```python\n"
            "      import ...\n"
            "      ...\n"
            "      ```\n"
            "    Never generate inline fences such as ```python import numpy....\n"
            "  • IMAGE HANDLING:\n"
            "      - If a question references 'shown below', 'the following plot', 'the following figure', 'the following residual plot', or similar wording, image_path MUST contain a deterministic filename.\n"
            "      - Never mention .png, .jpg or filenames inside visible prose.\n"
            "      - Use natural wording such as 'Examine the residual plot shown below.'\n"
            "  • All tables must be GitHub-Flavored Markdown tables.\n"
            "  • Never generate ASCII tables.\n"
        )
    elif section == "A/B Testing":
        domain_rules = (
            "DOMAIN ISOLATION & STYLING RULES (CRITICAL):\n"
            "  • Focus on practical A/B testing topics: Sample Size Determination, Statistical Power, Minimum Detectable Effect (MDE), Type I & Type II Errors, t-tests, Chi-Square Tests, Sequential Testing, CUPED, Sample Ratio Mismatch (SRM), Delta Method, Multi-Armed Bandits, Bayesian Testing, Network Interference, and Experimentation Best Practices.\n"
            "  • CODE VS MATH ISOLATION:\n"
            "      - Python code blocks MUST use literal Python identifiers such as alpha = 0.05, beta = 0.20, power = 0.80.\n"
            "      - NEVER use LaTeX symbols such as \\alpha, \\beta, \\sigma or \\theta inside a fenced code block.\n"
            "      - Mathematical notation belongs ONLY in normal prose using LaTeX.\n"
            "  • Every code example MUST be inside a properly fenced markdown block beginning on its own fresh line.\n"
            "  • Never write inline forms such as ```python import ...\n"
            "  • Never allow prose to continue immediately after a closing fence.\n"
            "  • Keep explanations concise, technically dense and approximately 120\u2013180 words for optimal readability.\n"
            "  • All tables must use GitHub-Flavored Markdown (GFM). Never generate ASCII tables.\n"
        )
    elif section == "Machine Learning":
        domain_rules = (
            "DOMAIN ISOLATION & STYLING RULES (CRITICAL):\n"
            "  • Focus on practical engineering concepts: ROC-AUC, Precision vs Recall, Recall vs Specificity, class imbalance, threshold tuning, calibration, feature importance, SHAP/LIME interpretation, hyperparameter tuning, bias-variance tradeoff, regularization, cross-validation leakage, ensemble methods, PCA, clustering, decision boundaries, model evaluation, and probability interpretation.\n"
            "  • Avoid textbook-definition questions such as 'What is supervised learning?'. Test engineering intuition and model reasoning instead.\n"
            "  • If Python code is used, it must use standard libraries (numpy, pandas, scikit-learn, scipy, matplotlib) and MUST be inside a properly fenced ```python markdown block beginning on its own line.\n"
            "  • Never place raw code immediately after the word 'python' inside normal prose.\n"
            "  • Mathematical notation belongs in prose using LaTeX. Never place LaTeX expressions inside Python code blocks.\n"
            "  • IMAGE HANDLING: Questions referring to ROC curves, confusion matrices, learning curves, PCA plots, feature importance plots, decision boundaries, calibration plots, bias-variance plots or similar visuals MUST populate image_path. Never mention raw .png or .jpg filenames inside question text or explanations.\n"
            "  • Tables must use GitHub-Flavored Markdown only."
        )
    elif section == "Data Visualization":
        domain_rules = (
            "DOMAIN ISOLATION & STYLING RULES (CRITICAL):\n"
            "  • Focus on practical Data Visualization concepts rather than textbook definitions.\n"
            "  • Cover chart selection, scatter plots, line charts, bar charts, histograms, boxplots, violin plots, heatmaps, pairplots, ROC curves, confusion matrices, PCA plots, residual plots, feature importance plots, calibration plots, learning curves, overplotting, color theory, perceptual design, misleading charts, matplotlib, seaborn and plotly.\n"
            "  • Prefer real-world engineering scenarios instead of trivia.\n"
            "  • Code snippets MUST use matplotlib.pyplot, seaborn or plotly only.\n"
            "  • Every code snippet MUST be inside a properly fenced markdown block beginning with a fresh newline:\n"
            "       ```python\n"
            "       ...code...\n"
            "       ```\n"
            "  • Never place raw code immediately after the word 'python'.\n"
            "  • Mathematical expressions belong in prose using LaTeX only. Never place LaTeX inside Python code.\n"
            "  • IMAGE HANDLING:\n"
            "      - If the user must inspect a visualization, populate image_path.\n"
            "      - Never place filenames (.png/.jpg/.jpeg) inside the question text.\n"
            "      - Refer naturally using phrases such as 'shown below', 'displayed below', or 'shown in the figure'.\n"
            "      - Use deterministic filenames such as: dataviz_easy_q2_histogram.png, dataviz_advanced_q1_roc_curve.png.\n"
            "  • Multi-line code belongs ONLY in the question stem or explanation. Never place full code blocks inside answer options. Small inline code such as `ax.set_xscale('log')` is acceptable inside options.\n"
            "  • Tables must use GitHub-Flavored Markdown only."
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
        "  • NEVER place the language tag and code on the same line (e.g., ```python import ... is FORBIDDEN).\n"
        "  • A fenced block MUST always open on one line and code MUST begin on the NEXT line.\n"
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
        "    where N starts at 1 (e.g., `ab_testing_easy_q1`, `ab_testing_easy_q2`, ...).\n"
        f"  • The prefix MUST be exactly `{section_id}` — NEVER use slashes or special characters in IDs.\n"
        "\n"
        f"{image_rule}\n"
        "\n"
        "RULE 7 — RAW FILENAMES FORBIDDEN IN PROSE:\n"
        "  • NEVER mention .png, .jpg, or any image filename inside the question text or explanation.\n"
        "  • Use natural language wording such as 'the residual plot shown below' instead.\n"
        "\n"
        "RULE 8 — TABLES:\n"
        "  • ALL tabular data MUST be rendered as GitHub-Flavored Markdown (GFM) tables.\n"
        "  • GFM tables MUST include a header row and a separator row using dashes (e.g., | --- | --- |).\n"
        "  • NEVER use ASCII-style tables (aligned spaces, box-drawing characters, or console output style).\n"
        "\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "QUESTION QUALITY RULES\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "\n"
        "• INTERNAL VALIDATION RULE:\n"
        "Before returning each question, internally verify that:\n"
        "\n"
        "  1. Every fenced code block opens with a language tag on its own line (e.g., ```python) "
        "and code begins on the very next line — never on the same line as the tag.\n"
        "  2. Every opened fenced block (```) is properly closed with a matching ```.\n"
        "  3. No fenced block is empty (code must appear between the opening and closing fences).\n"
        "  4. Python code is properly indented — multi-line statements are NOT collapsed to one line.\n"
        "  5. No raw filenames (.png, .jpg) appear anywhere inside the question text or explanation.\n"
        "  6. Every referenced visual (shown below / following plot / following figure / "
        "residual plot / heatmap / confusion matrix) has a non-null image_path set.\n"
        "  7. Every table is a valid GitHub-Flavored Markdown table with a header and separator row.\n"
        "  8. No prompt-leakage phrases appear (e.g., 'let me', 'i need to', 'regenerate', "
        "'rewrite', 'correction:', 'apologize', 'internal reasoning', 'here is the json', "
        "'as an ai', 'here\'s the corrected', 'json').\n"
        "  9. All four options are unique — no duplicate option text.\n"
        " 10. The explanation does not contradict the correct answer.\n"
        " 11. No LaTeX symbols (\\alpha, \\beta, \\sigma, \\theta, \\mu, \\lambda, \\gamma) appear inside code blocks.\n"
        f" 12. The question `id` uses only alphanumeric characters and underscores — NO slashes. Prefix must be `{section_id}`.\n"
        "\n"
        "If ANY of these checks fails for a question, discard that question and generate a "
        "replacement before returning the batch. Do NOT return a question that fails any check.\n"
        "\n"
        "• NO DUPLICATED OPTIONS IN CODE:\n"
        "You are FORBIDDEN from listing or commenting \"Option A\", \"Option B\", \"Option C\", or \"Option D\" inside code snippets or comments.\n"
        "\n"
        "• STANDARDIZED WORDING:\n"
        "Use consistent openings such as:\n"
        "\n"
        "\"Consider the following pandas DataFrame:\"\n"
        "\"What will be the output of the following operation?\"\n"
        "\"Consider the following data manipulation task:\"\n"
        "\n"
        "• SINGLE CORRECT ANSWER:\n"
        "Every question MUST have exactly ONE objectively correct answer.\n"
        "Do not create multi-select questions.\n"
        "Do not create questions where multiple options are technically correct.\n"
        "Incorrect options should be plausible but unambiguously wrong.\n"
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
    """
    Attempt to generate and fully validate a question batch.

    Fail-fast semantics: if ANY validation check fails the entire batch is
    discarded and the next model tier is retried. Partial / malformed data is
    NEVER written to disk.
    """
    prompt = build_prompt(section, difficulty, target_count)

    # ── Per-model validation retry limits ──────────────────────────────────────
    _GEMINI_MAX_ATTEMPTS: dict[str, int] = {
        "gemini-3.5-flash":      3,
        "gemini-2.5-flash":      3,
        "gemini-2.5-flash-lite": 2,
    }

    # ── Try each Gemini tier ──
    for model_id, label in GEMINI_MODELS:
        max_attempts = _GEMINI_MAX_ATTEMPTS.get(model_id, 3)

        for attempt in range(1, max_attempts + 1):
            print(f"\n  🔷 {label}\n     Attempt {attempt}/{max_attempts}")
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
                response_text = response.text
                if not response_text:
                    raise ValueError("Empty response from Gemini API")
                batch = QuestionBatch.model_validate_json(response_text)
                print(f"  ✅ {label} succeeded — {len(batch.questions)} questions generated.")
                # ── Validation guardrail ──
                validate_batch(batch, target_count)
                return batch
            except ValueError as val_err:
                # Validation failure → retry the SAME model
                print(f"\n  ⚠  Validation failed:\n     {val_err}")
                if attempt < max_attempts:
                    print(f"\n     Retrying {label}...")
                    time.sleep(SLEEP_SECONDS)
                else:
                    print("\n  ⛔ Validation retries exhausted.\n     Switching to next Gemini model...")
                    time.sleep(SLEEP_SECONDS)
            except Exception as exc:
                # Infrastructure/API failure → skip remaining retries for this model
                print(f"  ⚠️  {label} failed: {exc}")
                time.sleep(SLEEP_SECONDS)
                break  # move directly to the next model tier

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
            raw = ""  # pre-initialize so except handlers can always reference it
            raw = chat.choices[0].message.content
            
            # ── Minimal normalization step ──
            raw_clean = raw.strip()
            
            # Remove markdown wrappers if present
            raw_clean = re.sub(r"^```(?:json)?\s*", "", raw_clean)
            raw_clean = re.sub(r"\s*```$", "", raw_clean)
            
            # Strip harmless commentary before/after the JSON payload
            start_idx = next((i for i, c in enumerate(raw_clean) if c in "{["), -1)
            end_idx = next((i for i in range(len(raw_clean) - 1, -1, -1) if raw_clean[i] in "}]"), -1)
            if start_idx != -1 and end_idx != -1 and end_idx >= start_idx:
                raw_clean = raw_clean[start_idx:end_idx+1]
                
            parsed_raw = json.loads(raw_clean)
            
            # Normalize schema roots
            if isinstance(parsed_raw, list):
                parsed_raw = {"questions": parsed_raw}
            elif isinstance(parsed_raw, dict):
                for alt_key in ["Questions", "items", "quiz", "data"]:
                    if alt_key in parsed_raw and "questions" not in parsed_raw:
                        parsed_raw["questions"] = parsed_raw.pop(alt_key)
            
            # Groq sometimes omits root-level keys — inject them before validation
            if isinstance(parsed_raw, dict):
                parsed_raw["section_name"] = section
                parsed_raw["difficulty"] = difficulty

            # Normalize Groq's common hallucinated field names at the question level
            if "questions" in parsed_raw:
                for q in parsed_raw["questions"]:
                    if "question" in q and "text" not in q:
                        q["text"] = q.pop("question")
                    if "answer" in q and "correct_answer" not in q:
                        q["correct_answer"] = q.pop("answer")

            try:
                batch = QuestionBatch.model_validate(parsed_raw)
                print(f"  ✅ Groq succeeded — {len(batch.questions)} questions generated.")
                # ── Validation guardrail (fail-fast) ──
                validate_batch(batch, target_count)
                return batch
            except ValueError as val_err:
                print(f"  ⚠  Validation failed (Groq):")
                print(f"     === RAW RESPONSE ===\n{raw}")
                print(f"     === NORMALIZED PAYLOAD ===\n{json.dumps(parsed_raw, indent=2)}")
                print(f"     === VALIDATION ERROR ===\n{val_err}")
                
        except json.JSONDecodeError as json_err:
            print(f"  ⚠  Validation failed (Groq) — JSON Decode Error:\n     === RAW RESPONSE ===\n{raw}\n     === ERROR ===\n{json_err}")
        except ValueError as val_err:
            print(f"  ⚠  Validation failed (Groq):\n     {val_err}")
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

            # ── Guard: ensure LOCKED sections are not accidentally overwritten ──
            for locked_sec in LOCKED_SECTIONS:
                if locked_sec in SECTIONS:
                    print(
                        f"⛔  SAFETY ABORT: '{locked_sec}' is in both SECTIONS (active) "
                        "and LOCKED_SECTIONS. Remove it from LOCKED_SECTIONS before proceeding."
                    )
                    sys.exit(1)

            print(f"📂 Loaded existing question_bank.json — will update only: {SECTIONS}")
        except json.JSONDecodeError:
            print("⚠️  Existing question_bank.json is malformed — starting fresh.")
            bank = {}
    else:
        print("📂 No existing question_bank.json found — creating from scratch.")
        bank = {}

    # ── Collect fully-validated batches BEFORE touching disk (fail-fast) ──────
    updates: dict[str, dict[str, list]] = {}

    total_sections = len(SECTIONS)
    for sec_idx, section in enumerate(SECTIONS, 1):
        print(f"\n{'═'*60}")
        print(f"📚 Section {sec_idx}/{total_sections}: {section}")
        print(f"{'═'*60}")

        # Start from the existing section data so untouched buckets are preserved
        section_data: dict[str, list] = dict(bank.get(section, {}))

        for difficulty, target_count in DIFFICULTY_TARGETS.items():
            print(f"\n  🎯 Difficulty: {difficulty} ({target_count} questions)")
            batch = generate_batch(section, difficulty, target_count)

            if batch:
                questions_as_dicts = [q.model_dump() for q in batch.questions]
                section_data[difficulty] = questions_as_dicts
                print(f"  💾 Staged {len(questions_as_dicts)} questions for {section} / {difficulty}")
            else:
                # Do NOT overwrite existing valid data with an empty list
                existing = section_data.get(difficulty)
                if existing:
                    print(f"  ⚠️  Generation failed — keeping existing {len(existing)} questions for {section} / {difficulty}")
                else:
                    section_data[difficulty] = []

            time.sleep(SLEEP_SECONDS)

        updates[section] = section_data

    # ── Only update the sections we're regenerating — leave all others intact ──
    for section, section_data in updates.items():
        bank[section] = section_data

    # ── Write output (single atomic write after ALL validation passes) ─────────
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