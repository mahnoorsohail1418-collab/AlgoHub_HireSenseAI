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

# FIX (found during real-resume testing): some resumes (often LinkedIn
# exports) don't give calendar dates at all for each job - just a
# relative duration like "1 year", "6 months", or "current" for the
# ongoing role. DATE_RANGE_PATTERN can't match these (there's no year
# number at all), so without this, every job on this kind of resume
# silently gets start_date/end_date = None and "years of experience"
# comes out as 0 - even for someone with a decade of real experience.
DURATION_PATTERN = re.compile(
    r"(\d+(?:\.\d+)?)\s*(years?|yrs?|months?|mos?)\b", re.IGNORECASE
)


def _parse_duration_to_months(text: str) -> float:
    total_months = 0.0
    for amount, unit in DURATION_PATTERN.findall(text):
        amount = float(amount)
        if unit.lower().startswith(("year", "yr")):
            total_months += amount * 12
        else:
            total_months += amount
    return total_months

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
    "scientist", "researcher", "architect",
]


def _looks_like_job_title(text: str) -> bool:
    lowered = text.lower()
    return any(keyword in lowered for keyword in JOB_TITLE_KEYWORDS)


def parse_header(header: str) -> dict:
    date_match = DATE_RANGE_PATTERN.search(header)
    duration_months = None

    if date_match:
        start_date = date_match.group(1).strip()
        end_date = date_match.group(2).strip()
        header_no_dates = header[:date_match.start()] + header[date_match.end():]
    else:
        start_date, end_date = None, None
        header_no_dates = header
        # No calendar date range - check for a standalone relative
        # duration instead (e.g. "1 year", "6 months") so this job still
        # contributes to a total years-of-experience estimate.
        duration_match = DURATION_PATTERN.search(header)
        if duration_match:
            duration_months = _parse_duration_to_months(header)
            header_no_dates = (header[:duration_match.start()] + header[duration_match.end():]).strip()
        else:
            # A bare "current"/"present" marker (no number attached) has
            # no measurable duration, but still needs stripping out -
            # otherwise it gets treated as a literal company/title
            # segment when the header is split below.
            header_no_dates = re.sub(r"\b(current|present|ongoing)\b", "", header, flags=re.IGNORECASE).strip()

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
        "duration_months": duration_months,
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

    # FIX (found during real-resume testing): some resumes put the job
    # title, date range, and company each on their own separate line
    # (e.g. "Title" / "Jan 2025 - May 2025" / "Company") instead of one
    # combined header line ("Title | Company | Jan 2025 - May 2025").
    # The old code only ever checked line 0 for a date, so this layout
    # always came back with start_date/end_date = None, which silently
    # broke "years of experience" for every job using this format.
    # Now it scans the first few lines for wherever the date actually
    # is, and folds everything up to that point (plus a short trailing
    # line that's likely the company name) into the header.
    HEADER_SCAN_LIMIT = 3
    date_line_idx = None
    for i, line in enumerate(lines[:HEADER_SCAN_LIMIT]):
        is_marker_line = (
            DATE_RANGE_PATTERN.search(line)
            or DURATION_PATTERN.search(line)
            or line.strip().lower() in {"current", "present", "ongoing"}
        )
        if is_marker_line:
            date_line_idx = i
            break

    if date_line_idx is not None and date_line_idx > 0:
        header_lines = lines[:date_line_idx + 1]
        remaining = lines[date_line_idx + 1:]
        if remaining and len(remaining[0]) < 80 and not remaining[0].strip().startswith(("-", "\u2022", "*")):
            header_lines.append(remaining[0])
            remaining = remaining[1:]
        header = " | ".join(header_lines)
        body = " ".join(remaining).strip()
    else:
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
    # line in it looks like the start of a new job entry, that's a
    # strong signal multiple jobs got merged. This checks for a calendar
    # date range OR a relative duration marker ("1 year", "current") --
    # some resumes (often LinkedIn exports) use only the latter, with no
    # calendar date anywhere, so checking dates alone missed this case
    # entirely. Falls back to splitting right before every such line
    # instead of relying on blank lines.
    if len(blocks) == 1:
        lines = text.splitlines()
        header_line_indices = [
            i for i, line in enumerate(lines)
            if DATE_RANGE_PATTERN.search(line)
            or DURATION_PATTERN.search(line)
            or line.strip().lower() in {"current", "present", "ongoing"}
        ]
        if len(header_line_indices) > 1:
            # The marker line (date/duration) isn't always the first line
            # of the entry - some resumes (like Cristian's) put the
            # company name on the line just before it ("Company" / "1
            # year" / "Title"). Shift the split point back one line when
            # that preceding line looks like a short company name rather
            # than the tail end of the previous job's own description.
            starts = []
            for idx, marker_idx in enumerate(header_line_indices):
                candidate_start = marker_idx
                if marker_idx > 0:
                    prev_line = lines[marker_idx - 1].strip()
                    prev_already_claimed = idx > 0 and marker_idx - 1 <= header_line_indices[idx - 1]
                    if (not prev_already_claimed and prev_line and len(prev_line) < 60
                            and not prev_line.startswith(("-", "\u2022", "*"))):
                        candidate_start = marker_idx - 1
                starts.append(candidate_start)

            blocks = []
            for idx, start in enumerate(starts):
                end = starts[idx + 1] if idx + 1 < len(starts) else len(lines)
                if start < end:
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
