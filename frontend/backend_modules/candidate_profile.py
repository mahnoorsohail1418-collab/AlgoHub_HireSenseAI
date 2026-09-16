"""
candidate_profile_builder.py

Week 4, Module 1, Task 4 - Combine Extractors into a Candidate Profile

WHAT THIS DOES:
Ties all the individual section extractors together into the single
Candidate Profile shape:

    Candidate Profile
    |- Personal Information
    |- Education
    |- Experience
    |- Skills
    |- Projects
    |- Certifications
    L- Career History

INPUT:
A dict of raw section text, one key per resume section:

    {
        "personal_info": "...",
        "education": "...",
        "experience": "...",
        "skills": "...",
        "projects": "...",
        "certifications": "...",
    }

Any key can be omitted or empty - a resume without a Certifications
section, for example, should still produce a valid profile with
certifications: [].

DESIGN NOTE ON "CAREER HISTORY":
Unlike the other six branches, "Career History" isn't something a resume
has as its own raw-text section - it's a summary VIEW of the Experience
data. So rather than parsing it separately (which would just mean writing
a second, redundant parser for the exact same text), this builds it by:
  1. Running the raw experience text through experience_extractor.py once.
  2. Projecting each job down to just {job_title, company, start_date,
     end_date} - i.e. stripping the description/technologies, since
     "history" implies a timeline, not the full detail already available
     under Experience.
  3. Sorting most-recent-first, using a small helper that turns
     "Present"/"Current" and "Month Year"/"Year" strings into a
     comparable sort key.
This keeps the two branches consistent by construction (they can never
disagree about what jobs exist) instead of risking drift between two
independently-parsed copies of the same data.
"""

import json
import re

from personal_info_extractor import extract_personal_info
from education_extractor import extract_education
from experience_extractor import extract_experience
from skills_extractor import extract_skills
from projects_extractor import extract_projects
from certification_extractor import extract_certifications

MONTHS = {
    "jan": 1, "january": 1, "feb": 2, "february": 2, "mar": 3, "march": 3,
    "apr": 4, "april": 4, "may": 5, "jun": 6, "june": 6, "jul": 7, "july": 7,
    "aug": 8, "august": 8, "sep": 9, "sept": 9, "september": 9, "oct": 10,
    "october": 10, "nov": 11, "november": 11, "dec": 12, "december": 12,
}


def _date_sort_key(date_str):
    """
    Turns a date string ("Present", "June 2021", "2021", or None) into a
    (year, month) tuple for sorting, so ongoing jobs always sort first
    and missing dates never crash the sort.
    """
    if not date_str:
        return (0, 0)
    text = date_str.strip().lower()
    if text in ("present", "current"):
        return (9999, 12)

    month = 0
    match = re.search(r"[a-zA-Z]+", text)
    if match:
        month = MONTHS.get(match.group(0).lower(), 0)

    year_match = re.search(r"\d{4}", text)
    year = int(year_match.group(0)) if year_match else 0

    return (year, month)


def _build_career_history(raw_experience_text: str) -> list:
    jobs = extract_experience(raw_experience_text) if raw_experience_text else []
    history = [
        {
            "job_title": job["job_title"],
            "company": job["company"],
            "start_date": job["start_date"],
            "end_date": job["end_date"],
            # FIX: some resumes give a relative duration ("1 year", "6
            # months") instead of calendar dates - carry this through so
            # years-of-experience estimation can still use it as a
            # fallback when no calendar date exists at all.
            "duration_months": job.get("duration_months"),
        }
        for job in jobs
    ]
    history.sort(key=lambda j: _date_sort_key(j["end_date"]), reverse=True)
    return history


def build_candidate_profile(raw_sections: dict) -> dict:
    personal_info_text = raw_sections.get("personal_info", "")
    education_text = raw_sections.get("education", "")
    experience_text = raw_sections.get("experience", "")
    skills_text = raw_sections.get("skills", "")
    projects_text = raw_sections.get("projects", "")
    certifications_text = raw_sections.get("certifications", "")

    return {
        "personal_information": (
            extract_personal_info(personal_info_text) if personal_info_text else None
        ),
        "education": (
            extract_education(education_text) if education_text else []
        ),
        "experience": (
            extract_experience(experience_text) if experience_text else []
        ),
        "skills": (
            extract_skills(skills_text) if skills_text
            else {"categories": {}, "all_skills": []}
        ),
        "projects": (
            extract_projects(projects_text) if projects_text else []
        ),
        "certifications": (
            extract_certifications(certifications_text) if certifications_text else []
        ),
        "career_history": _build_career_history(experience_text),
    }


def run_tests(data_path: str = "candidate_profile_test_data.json"):
    with open(data_path, "r") as f:
        data = json.load(f)

    for case in data["test_cases"]:
        print(f"\n{'=' * 60}")
        print(f"=== {case['resume_id']} ===")
        print(f"{'=' * 60}")
        profile = build_candidate_profile(case["raw_sections"])
        print(json.dumps(profile, indent=2))


if __name__ == "__main__":
    run_tests()
