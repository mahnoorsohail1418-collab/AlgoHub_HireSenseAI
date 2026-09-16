"""
run_evaluation.py
Week 4 - Module 1, Task 5: Parser Robustness Testing

Runs the full pipeline (section_splitter -> candidate_profile.py, which
itself calls all 6 extractors) against a folder of real resumes and logs
per-resume results to parser_evaluation_v2.csv.

Usage:
    python3 run_evaluation.py ./resumes

Reads both .txt and .pdf resumes from the given folder (PDF support
requires: pip install pdfplumber).
"""

import csv
import os
import sys

from section_splitter import split_into_sections
from candidate_profile import build_candidate_profile

try:
    import pdfplumber
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False


def _extract_pdf_text(path: str) -> str:
    with pdfplumber.open(path) as pdf:
        return "\n".join(page.extract_text() or "" for page in pdf.pages)


def load_resumes(folder_path: str):
    """Yields (filename, text) for every .txt or .pdf resume in the folder."""
    for filename in sorted(os.listdir(folder_path)):
        full_path = os.path.join(folder_path, filename)
        lower = filename.lower()
        if lower.endswith(".txt"):
            with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                yield filename, f.read()
        elif lower.endswith(".pdf"):
            if not PDF_SUPPORT:
                print(f"Skipping {filename}: install pdfplumber to read PDFs "
                      f"(pip install pdfplumber)")
                continue
            try:
                yield filename, _extract_pdf_text(full_path)
            except Exception:
                yield filename, ""  # let evaluate_resume log the downstream failure


def _is_empty(value) -> bool:
    """
    Field-emptiness check tuned to this candidate_profile.py's actual
    return shapes:
      - personal_information: None or a dict (never empty-but-present)
      - education / experience / projects / certifications / career_history: list
      - skills: dict with an "all_skills" list inside
    """
    if value is None:
        return True
    if isinstance(value, (list, dict)) and not value:
        return True
    if isinstance(value, dict) and "all_skills" in value:
        return len(value["all_skills"]) == 0
    return False


def evaluate_resume(filename: str, text: str) -> dict:
    """
    Runs the pipeline on one resume and returns a CSV row plus the full
    profile (used for the JSON dump). Wrapped in try/except so one bad
    resume doesn't kill the whole batch -- a crash IS a finding for
    Task 5, not something to hide.
    """
    try:
        sections = split_into_sections(text)
        profile = build_candidate_profile(sections)

        field_status = {field: not _is_empty(value) for field, value in profile.items()}
        missing = [f for f, ok in field_status.items() if not ok]
        extracted = [f for f, ok in field_status.items() if ok]

        row = {
            "resume_id": filename,
            "status": "parsed",
            "sections_detected": ", ".join(sorted(sections.keys())) or "none",
            "fields_extracted": ", ".join(extracted) if extracted else "none",
            "fields_missing": ", ".join(missing) if missing else "none",
            "num_experience_entries": len(profile.get("experience") or []),
            "num_project_entries": len(profile.get("projects") or []),
            "num_certification_entries": len(profile.get("certifications") or []),
            "notes": "",
        }
        return row, profile
    except Exception as e:
        row = {
            "resume_id": filename,
            "status": "ERROR",
            "sections_detected": "",
            "fields_extracted": "",
            "fields_missing": "all",
            "num_experience_entries": 0,
            "num_project_entries": 0,
            "num_certification_entries": 0,
            "notes": f"{type(e).__name__}: {e}",
        }
        return row, None


def run_evaluation(folder_path: str, output_csv: str = "parser_evaluation_v2.csv",
                    output_json: str = "parser_evaluation_v2.json"):
    rows = []
    profiles = {}  # filename -> full extracted profile, for the JSON dump

    for filename, text in load_resumes(folder_path):
        row, profile = evaluate_resume(filename, text)
        rows.append(row)
        if profile is not None:
            profiles[filename] = profile

    if not rows:
        print(f"No .txt or .pdf resumes found in {folder_path}")
        return

    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    # Full per-resume detail (every extracted field, not just the CSV
    # summary columns) -- open this file to see exactly what was pulled
    # out of any individual resume.
    import json
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(profiles, f, indent=2)

    total = len(rows)
    errors = sum(1 for r in rows if r["status"] == "ERROR")
    print(f"Evaluated {total} resumes -> {output_csv}  (summary)")
    print(f"                          -> {output_json}  (full JSON detail per resume)")
    print(f"  {total - errors} parsed successfully, {errors} errored")

    from collections import Counter
    missing_tally = Counter()
    for r in rows:
        if r["fields_missing"] not in ("none", "all"):
            for field in r["fields_missing"].split(", "):
                missing_tally[field] += 1
    if missing_tally:
        print("  Most commonly missing fields:")
        for field, count in missing_tally.most_common():
            print(f"    {field}: missing in {count}/{total} resumes")


if __name__ == "__main__":
    folder = sys.argv[1] if len(sys.argv) > 1 else "./resumes"
    run_evaluation(folder)
