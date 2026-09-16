"""
education_extractor.py

Week 4, Module 1, Task 4 (support) - Extract Education

WHAT THIS DOES:
Takes the raw text of a resume's Education section (one school per block,
blocks separated by a blank line, same convention as Experience/Projects)
and pulls out, for each entry:
  - institution
  - degree
  - start_date
  - end_date
  - gpa          (may be missing)
  - details      (coursework, honors, minor, etc. - whatever prose is left)

APPROACH (mirrors experience_extractor.py closely, since the header shape
- "thing | other thing (date range)" - is the same convention resumes use
for jobs):
  1. Split into blocks on blank lines.
  2. Pull the date range off the header with the same DATE_RANGE_PATTERN
     used for jobs.
  3. Split the remaining header on "|" or " - " into two segments. Since
     institution/degree ordering varies just as much as job title/company
     ordering, reuse the same "does this segment look like a degree"
     heuristic instead of assuming a fixed order.
  4. In the body, pull out GPA specifically (it has a very recognizable
     "GPA: X.X" or "GPA: X.X/4.0" shape) before treating the rest as
     free-text details.
"""

import json
import re

DATE_RANGE_PATTERN = re.compile(
    r"\(?"
    r"((?:[A-Za-z]+\s+)?\d{4})"
    r"\s*-\s*"
    r"((?:[A-Za-z]+\s+)?\d{4}|Present|Current|present|current|Expected\s+\d{4})"
    r"\)?"
)

# A lone graduation year with no range, e.g. "(2023)", also common on
# resumes that only list when a degree was completed.
SINGLE_YEAR_PATTERN = re.compile(r"\(?\b(\d{4})\b\)?")

# FIX (found during testing): using a [\d.] character class for the GPA
# value greedily swallowed the sentence's trailing period too (e.g.
# "GPA: 3.8/4.0. Relevant Coursework..." was captured as "3.8/4.0."
# instead of "3.8/4.0"), since "." is itself inside that character
# class. Anchoring each number as digits-then-optional-single-decimal
# fixes it without touching the "3.8/4.0" slash format.
GPA_PATTERN = re.compile(
    r"GPA\s*:?\s*(\d+(?:\.\d+)?(?:\s*/\s*\d+(?:\.\d+)?)?)",
    re.IGNORECASE,
)

# Words that show up in a degree name but almost never in a school's
# name - used the same way JOB_TITLE_KEYWORDS is used in
# experience_extractor.py, to detect "Institution - Degree" ordering and
# correct it rather than assuming the first segment is always the degree.
DEGREE_KEYWORDS = [
    "b.s.", "b.a.", "m.s.", "m.a.", "mba", "ph.d.", "bachelor", "master",
    "associate", "diploma", "certificate", "minor", "degree",
]


def _looks_like_degree(text: str) -> bool:
    lowered = text.lower()
    return any(keyword in lowered for keyword in DEGREE_KEYWORDS)


def parse_header(header: str) -> dict:
    date_match = DATE_RANGE_PATTERN.search(header)
    if date_match:
        start_date = date_match.group(1).strip()
        end_date = date_match.group(2).strip()
        header_no_dates = header[:date_match.start()] + header[date_match.end():]
    else:
        # Fall back to a single graduation year if no range was found.
        single_match = SINGLE_YEAR_PATTERN.search(header)
        if single_match:
            start_date = None
            end_date = single_match.group(1).strip()
            header_no_dates = header[:single_match.start()] + header[single_match.end():]
        else:
            start_date, end_date = None, None
            header_no_dates = header

    header_no_dates = header_no_dates.strip(" ()|-,")

    if "|" in header_no_dates:
        parts = [p.strip() for p in header_no_dates.split("|") if p.strip()]
    elif " - " in header_no_dates:
        parts = [p.strip() for p in header_no_dates.split(" - ") if p.strip()]
    elif "," in header_no_dates:
        parts = [p.strip() for p in header_no_dates.split(",") if p.strip()]
    else:
        parts = [header_no_dates.strip()] if header_no_dates.strip() else []

    first = parts[0] if parts else None
    second = parts[1] if len(parts) > 1 else None

    # Default assumption: first segment is the degree, second is the
    # institution (mirrors "Title | Company" being the more common
    # order in experience_extractor.py). Swap if that looks backwards.
    degree, institution = first, second
    if degree and institution:
        if _looks_like_degree(institution) and not _looks_like_degree(degree):
            degree, institution = institution, degree

    return {
        "institution": institution,
        "degree": degree,
        "start_date": start_date,
        "end_date": end_date,
    }


def parse_body(body: str) -> dict:
    gpa_match = GPA_PATTERN.search(body)
    gpa = gpa_match.group(1).strip() if gpa_match else None
    details = body

    if gpa_match:
        details = (body[:gpa_match.start()] + body[gpa_match.end():])

    details = re.sub(r"\s+", " ", details).strip(" .")

    return {"gpa": gpa, "details": details}


def parse_education_block(block: str) -> dict:
    lines = [l for l in block.strip().split("\n") if l.strip()]
    if not lines:
        return None

    header = lines[0]
    body = " ".join(lines[1:]).strip()

    result = parse_header(header)
    result.update(parse_body(body))
    return result


def extract_education(raw_text: str) -> list:
    blocks = re.split(r"\n\s*\n", raw_text.strip())
    results = []
    for block in blocks:
        parsed = parse_education_block(block)
        if parsed:
            results.append(parsed)
    return results


def run_tests(data_path: str = "education_test_data.json"):
    with open(data_path, "r") as f:
        data = json.load(f)

    for case in data["test_cases"]:
        print(f"\n=== {case['resume_id']} ===")
        entries = extract_education(case["raw_education_text"])
        for e in entries:
            print(f"  Degree: {e['degree']}   Institution: {e['institution']}")
            print(f"    Dates: {e['start_date']} -> {e['end_date']}   GPA: {e['gpa']}")
            print(f"    Details: {e['details'][:90]}...")


if __name__ == "__main__":
    run_tests()
