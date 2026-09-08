"""
experience_extractor.py

Week 4, Module 1, Task 1 - Improve Experience Extraction

WHAT THIS DOES:
Takes the raw text of a resume's Experience section (one job per block,
blocks separated by a blank line) and pulls out, for each job:
  - job_title
  - company
  - start_date
  - end_date
  - description
  - technologies (a list)

APPROACH:
1. Split the section into blocks (one per job) on blank lines.
   FALLBACK (added after Task 5 testing): if blank-line splitting only
   finds ONE block but that block contains multiple date-range lines,
   the PDF likely lost its blank lines during text extraction -- so
   instead, split right before each line that contains a date range.
2. The FIRST line of each block is the "header" (title/company/dates).
   Everything after that is the "body" (description + technologies).
3. Find the date range in the header using a regex (handles "-", "\u2013",
   and "\u2014" as the separator, since real resumes use all three), then
   remove it so what's left is just title + company text.
4. Split the remaining header text on "|" first if present (most explicit
   format), otherwise fall back to " - " or ",".
5. In the body, look for a "Technologies:" / "Tools:" / "Stack:" line and
   pull that out separately from the description.
"""

import json
import re

DATE_RANGE_PATTERN = re.compile(
    r"\(?"
    r"((?:[A-Za-z]+\s+)?\d{4})"
    r"\s*[-\u2013\u2014]\s*"
    r"((?:[A-Za-z]+\s+)?\d{4}|Present|Current|present|current)"
    r"\)?"
)

TECH_LINE_PATTERN = re.compile(
    r"(Technologies|Tools|Stack)\s*:\s*(.+?)(?:\.|$)",
    re.IGNORECASE,
)

# Common words that show up in job titles but almost never in a company
# name. Used to detect "Company - Title" ordering (some resumes write it
# this way instead of "Title - Company") and correct it, rather than
# always assuming the first segment is the title.
JOB_TITLE_KEYWORDS = [
    "intern", "engineer", "assistant", "manager", "analyst", "coordinator",
    "developer", "officer", "specialist", "director", "associate", "lead",
    "consultant", "representative", "designer", "technician", "administrator",
]


def _looks_like_job_title(text: str) -> bool:
    lowered = text.lower()
    return any(keyword in lowered for keyword in JOB_TITLE_KEYWORDS)


def parse_header(header: str) -> dict:
    date_match = DATE_RANGE_PATTERN.search(header)
    if date_match:
        start_date = date_match.group(1).strip()
        end_date = date_match.group(2).strip()
        header_no_dates = header[:date_match.start()] + header[date_match.end():]
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

    job_title = parts[0] if parts else None
    company = parts[1] if len(parts) > 1 else None

    # FIX (found during testing): some resumes write "Company - Title"
    # instead of "Title - Company" (e.g. "University of Florida - Marketing
    # Assistant"), which got the two fields swapped. If the SECOND segment
    # looks like a job title and the first one doesn't, swap them.
    if job_title and company:
        if _looks_like_job_title(company) and not _looks_like_job_title(job_title):
            job_title, company = company, job_title

    return {
        "job_title": job_title,
        "company": company,
        "start_date": start_date,
        "end_date": end_date,
    }


def parse_body(body: str) -> dict:
    tech_match = TECH_LINE_PATTERN.search(body)
    technologies = []
    description = body

    if tech_match:
        tech_text = tech_match.group(2)
        technologies = [t.strip() for t in tech_text.split(",") if t.strip()]
        # Remove the "Technologies: ..." sentence from the description
        description = (body[:tech_match.start()] + body[tech_match.end():]).strip()

    description = description.strip(" .")

    return {
        "description": description,
        "technologies": technologies,
    }


def parse_experience_block(block: str) -> dict:
    lines = [l for l in block.strip().split("\n") if l.strip()]
    if not lines:
        return None

    header = lines[0]
    body = " ".join(lines[1:]).strip()

    result = parse_header(header)
    result.update(parse_body(body))
    return result


def extract_experience(raw_text: str) -> list:
    text = raw_text.strip()
    if not text:
        return []

    blocks = re.split(r"\n\s*\n", text)

    # FIX (found during testing): some resumes' PDF-to-text conversion
    # drops the blank line between jobs entirely, so the whole section
    # comes through as ONE block containing multiple jobs -- e.g. three
    # separate companies all merged into a single entry, with only the
    # very first company/date line recognized as the header and
    # everything else (including the other two jobs) dumped into that
    # one entry's description.
    #
    # Detection: if there's only one blank-line block but MORE than one
    # line in it matches a date range, that's a strong signal multiple
    # jobs got merged. Fall back to splitting right before every line
    # that contains a date range instead of relying on blank lines.
    if len(blocks) == 1:
        lines = text.splitlines()
        header_line_indices = [
            i for i, line in enumerate(lines) if DATE_RANGE_PATTERN.search(line)
        ]
        if len(header_line_indices) > 1:
            blocks = []
            for idx, start in enumerate(header_line_indices):
                end = header_line_indices[idx + 1] if idx + 1 < len(header_line_indices) else len(lines)
                blocks.append("\n".join(lines[start:end]))

    results = []
    for block in blocks:
        parsed = parse_experience_block(block)
        if parsed:
            results.append(parsed)
    return results


def run_tests(data_path: str = "experience_test_data.json"):
    with open(data_path, "r") as f:
        data = json.load(f)

    for case in data["test_cases"]:
        print(f"\n=== {case['resume_id']} ===")
        jobs = extract_experience(case["raw_experience_text"])
        for j in jobs:
            print(f"  Job Title: {j['job_title']}")
            print(f"    Company: {j['company']}")
            print(f"    Dates: {j['start_date']} -> {j['end_date']}")
            print(f"    Technologies: {j['technologies']}")
            print(f"    Description: {j['description'][:80]}...")


if __name__ == "__main__":
    run_tests()
