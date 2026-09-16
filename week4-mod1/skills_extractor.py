"""
skills_extractor.py

Week 4, Module 1, Task 4 (support) - Extract Skills

WHAT THIS DOES:
Takes the raw text of a resume's Skills section and pulls out a
categorized breakdown, e.g.:
  {
    "categories": {
      "Languages": ["Python", "Java", "SQL"],
      "Frameworks": ["React", "Django"]
    },
    "all_skills": ["Python", "Java", "SQL", "React", "Django"]
  }

WHY THIS NEEDS TWO MODES:
Resumes list skills two very different ways:
  1. CATEGORIZED - one category per line, e.g. "Languages: Python, Java"
  2. FLAT - a single uncategorized comma/pipe/bullet separated list with
     no labels at all, e.g. "Python, Java, SQL, Git, Docker"
There's no reliable way to tell which format a given resume uses without
looking for the "Label:" shape first, so this checks each line for that
shape and only falls back to flat-list parsing if NO lines matched it -
mirrors the Technologies-line-then-prose-fallback approach already used
in projects_extractor.py.

APPROACH:
  1. Split into lines (skills sections are typically one category or one
     bullet per line, not blank-line-separated blocks like the other
     sections).
  2. For each line, check for a "Category: item, item, item" shape.
  3. If at least one line matched that shape, treat the whole section as
     categorized and only skip lines that didn't match.
  4. If NO lines matched, treat the entire section as one flat list and
     split on commas/bullets/pipes.
  5. Always also build a flat, de-duplicated "all_skills" list, since
     downstream consumers (e.g. a job-matching step) usually want a
     simple list regardless of how the resume grouped things.
"""

import json
import re

CATEGORY_LINE_PATTERN = re.compile(r"^([A-Za-z][A-Za-z /&]{1,30})\s*:\s*(.+)$")


def _strip_bullet(line: str) -> str:
    return re.sub(r"^[\-\*\u2022]\s*", "", line.strip())


def _split_items(text: str) -> list:
    parts = re.split(r",|\u2022|\|", text)
    return [p.strip() for p in parts if p.strip()]


def extract_skills(raw_text: str) -> dict:
    lines = [_strip_bullet(l) for l in raw_text.strip().split("\n") if l.strip()]

    categories = {}
    uncategorized = []

    for line in lines:
        match = CATEGORY_LINE_PATTERN.match(line)
        if match:
            category = match.group(1).strip()
            items = _split_items(match.group(2))
            categories[category] = items
        else:
            uncategorized.extend(_split_items(line))

    # No "Category:" lines found anywhere -> the whole section is a flat
    # list, so drop the (empty) categories dict rather than reporting one.
    if not categories:
        all_skills = uncategorized
        categories = {}
    else:
        # Categorized, but some line(s) didn't match the pattern (e.g. a
        # stray bullet with no label) - keep those under "Other" instead
        # of silently dropping them.
        if uncategorized:
            categories["Other"] = uncategorized
        all_skills = [item for items in categories.values() for item in items]

    # De-duplicate while preserving first-seen order.
    seen = set()
    deduped_all = []
    for skill in all_skills:
        key = skill.lower()
        if key not in seen:
            seen.add(key)
            deduped_all.append(skill)

    return {"categories": categories, "all_skills": deduped_all}


def run_tests(data_path: str = "skills_test_data.json"):
    with open(data_path, "r") as f:
        data = json.load(f)

    for case in data["test_cases"]:
        print(f"\n=== {case['resume_id']} ===")
        result = extract_skills(case["raw_skills_text"])
        print(f"  Categories: {result['categories']}")
        print(f"  All skills: {result['all_skills']}")


if __name__ == "__main__":
    run_tests()
