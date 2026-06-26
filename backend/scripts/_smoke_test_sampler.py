"""
_smoke_test_sampler.py
======================
Quick sanity-check for the 2-2-1 stratified sampler and Clean-70 scoring model.

Run from the backend/ directory:
    python scripts/_smoke_test_sampler.py

Expected output:
  Sections : 7/7
  Questions: 35/35
  Each section shows exactly [Easy, Easy, ...shuffled mix...]
  index[0] of every section is always 'Easy'
  Points check: Easy=1, Moderate=2, Advanced=4
  Max possible score: 70  (7 sections x (2x1 + 2x2 + 1x4) = 7 x 10)
  Sampler OK
"""

import json
import random
import pathlib

BANK_PATH = pathlib.Path("data/question_bank.json")
bank = json.loads(BANK_PATH.read_text(encoding="utf-8"))
sections_order = bank["meta"]["sections"]

# ── Clean-70 constants ────────────────────────────────────────────────────────
POINTS_MAP = {"Easy": 1, "Moderate": 2, "Advanced": 4}
DIFFICULTY_QUOTA = {"Easy": 2, "Moderate": 2, "Advanced": 1}

# ── Sampler (mirrors generate_quiz._sample_section) ───────────────────────────
def sample_section(section_name: str, section_pool: dict) -> dict:
    sampled_by_difficulty: dict[str, list] = {}

    for difficulty, quota in DIFFICULTY_QUOTA.items():
        pool = section_pool.get(difficulty, [])
        chosen = random.sample(pool, min(quota, len(pool)))
        points_value = POINTS_MAP.get(difficulty, 1)
        chosen = [{**q, "points": points_value} for q in chosen]
        sampled_by_difficulty[difficulty] = chosen

    easy_qs = sampled_by_difficulty.get("Easy", [])
    moderate_qs = sampled_by_difficulty.get("Moderate", [])
    advanced_qs = sampled_by_difficulty.get("Advanced", [])

    if easy_qs:
        anchor_idx = random.randrange(len(easy_qs))
        anchor = easy_qs[anchor_idx]
        remaining_easy = [q for i, q in enumerate(easy_qs) if i != anchor_idx]
    else:
        anchor = None
        remaining_easy = []

    tail = remaining_easy + moderate_qs + advanced_qs
    random.shuffle(tail)

    questions = ([anchor] + tail) if anchor is not None else tail
    return {"section_name": section_name, "questions": questions}


# ── Build quiz ────────────────────────────────────────────────────────────────
quiz_sections = []
for section_name in sections_order:
    pool = bank["sections"].get(section_name, {})
    quiz_sections.append(sample_section(section_name, pool))

# ── Validation ────────────────────────────────────────────────────────────────
total_q = sum(len(s["questions"]) for s in quiz_sections)
max_score = sum(q["points"] for s in quiz_sections for q in s["questions"])

print(f"Sections : {len(quiz_sections)}/7")
print(f"Questions: {total_q}/35")
print(f"Max possible score: {max_score}  (expected 70 = 7 sections x 10 pts each)")
print()

all_ok = True
for s in quiz_sections:
    qs = s["questions"]
    diffs  = [q["difficulty"] for q in qs]
    points = [q["points"] for q in qs]

    first_diff   = diffs[0] if diffs else "N/A"
    first_ok     = first_diff == "Easy"
    easy_count   = diffs.count("Easy")
    mod_count    = diffs.count("Moderate")
    adv_count    = diffs.count("Advanced")
    quota_ok     = (easy_count == 2 and mod_count == 2 and adv_count == 1)
    points_ok    = all(
        POINTS_MAP.get(d) == p for d, p in zip(diffs, points)
    )

    status = "[OK] " if (first_ok and quota_ok and points_ok) else "[!!]"
    if not (first_ok and quota_ok and points_ok):
        all_ok = False

    print(
        f"  {status} {s['section_name']}: "
        f"diffs={diffs}, points={points}, "
        f"first={first_diff!r} (anchor={'OK' if first_ok else 'FAIL'}), "
        f"quota={'OK' if quota_ok else 'FAIL'}, "
        f"points_map={'OK' if points_ok else 'FAIL'}"
    )

print()
print("Sampler OK" if (total_q == 35 and len(quiz_sections) == 7 and all_ok) else "MISMATCH - CHECK OUTPUT ABOVE")
