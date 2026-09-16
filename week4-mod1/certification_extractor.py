"""
certification_extractor.py

Week 4, Module 1, Task 3 - Extract Certifications

WHAT THIS DOES:
Takes the raw text of a resume's Certifications section (one certification
per line, with or without bullet markers) and pulls out, for each one:
  - name       (the certification itself)
  - issuer     (who issued it - may be missing)
  - year       (issue year - may be missing)
  - expiration (expiration year, if a range is given - may be missing)

WHY THIS IS HARDER THAN IT LOOKS:
Real resumes write certifications very inconsistently - see cert_test_data.json
for 5 different real-world formats. There's no single reliable pattern, so
this uses a few HEURISTICS instead of one strict format:
  1. Find any 4-digit years in the line - these are almost always issue/
     expiration dates, not part of the certification name.
  2. Split the remaining text on common separators (comma, dash, pipe) to
     separate the certification name from an issuer, if one is present.
  3. Assume the FIRST segment is always the certification name (this is
     true in every format seen so far).
  4. Assume a SECOND text segment (not a year) is the issuer.
"""

import json
import re

YEAR_PATTERN = re.compile(r"\b(19|20)\d{2}\b")


def _strip_bullet(line: str) -> str:
    return re.sub(r"^[\-\*\u2022]\s*", "", line.strip())


def extract_years(text: str) -> list:
    return [int(m.group()) for m in YEAR_PATTERN.finditer(text)]


def parse_certification_line(line: str) -> dict:
    line = _strip_bullet(line)
    if not line:
        return None

    years = extract_years(line)

    # Remove "issued", "expires", parentheses, and years from the text,
    # so what's left is just the name + possible issuer.
    text_no_years = YEAR_PATTERN.sub("", line)
    text_no_years = re.sub(r"\b(issued|expires?)\s*:?\s*", "", text_no_years, flags=re.IGNORECASE)
    text_no_years = re.sub(r"[()]", "", text_no_years)
    text_no_years = re.sub(r"\s*-\s*$", "", text_no_years)  # trailing dash left over from a year range
    text_no_years = text_no_years.strip(" ,-|")

    # Split remaining text into name + issuer. FIX (found during testing):
    # splitting on " - " too eagerly broke certification names that contain
    # a dash themselves, e.g. "AWS Certified Solutions Architect - Associate"
    # got wrongly split into name="AWS Certified Solutions Architect" and
    # issuer="Associate", when "- Associate" is actually part of the real
    # certification title. Fix: prefer comma or pipe as the separator
    # (these are never part of a certification's own name in this data),
    # and only fall back to " - " when neither is present.
    if "," in text_no_years:
        segments = text_no_years.split(",")
    elif "|" in text_no_years:
        segments = text_no_years.split("|")
    elif " - " in text_no_years:
        segments = text_no_years.split(" - ")
    else:
        segments = [text_no_years]
    segments = [s.strip() for s in segments if s.strip()]

    name = segments[0] if segments else line
    issuer = segments[1] if len(segments) > 1 else None

    year = years[0] if years else None
    expiration = years[1] if len(years) > 1 else None

    return {
        "name": name,
        "issuer": issuer,
        "year": year,
        "expiration": expiration,
    }


def extract_certifications(raw_text: str) -> list:
    lines = raw_text.strip().split("\n")
    results = []
    for line in lines:
        parsed = parse_certification_line(line)
        if parsed:
            results.append(parsed)
    return results


def run_tests(data_path: str = "cert_test_data.json"):
    with open(data_path, "r") as f:
        data = json.load(f)

    for case in data["test_cases"]:
        print(f"\n=== {case['resume_id']} ===")
        certs = extract_certifications(case["raw_certifications_text"])
        for c in certs:
            print(f"  Name: {c['name']}")
            print(f"    Issuer: {c['issuer']}")
            print(f"    Year: {c['year']}   Expiration: {c['expiration']}")


if __name__ == "__main__":
    run_tests()
