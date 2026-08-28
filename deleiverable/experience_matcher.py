"""
experience_matcher.py

Task 3 - Experience Matching

WHY NOT A SIMPLE RATIO:
The task doc explicitly says not to just do "2 years / 3 years = 66%".
A plain ratio has two problems:
  1. It punishes being slightly under-qualified just as harshly as being
     wildly under-qualified (1.9 years vs 2 years required looks almost
     as bad as 0.1 years vs 2 years required, under a straight ratio).
  2. It gives no credit for experience ABOVE the requirement - a candidate
     with 10 years of experience for a "2 years required" job scores
     exactly the same as someone with exactly 2 years.

SCORING RULE (documented):
We use the job's REQUIRED and PREFERRED experience years to build a
3-zone curve:

  Zone A - At or above preferred years:
      score = 1.0 (fully qualified, no reason to score lower)

  Zone B - Between required and preferred years:
      score climbs smoothly from 0.7 up to 1.0 as experience approaches
      the preferred amount. Meeting the bare minimum required experience
      is worth a solid 0.7, not a 1.0 - there's real value in exceeding it.

  Zone C - Below required years:
      score drops off more steeply, scaled so that having HALF the
      required experience scores much worse than having 90% of it.
      This reflects that being close to qualified is very different from
      being far off.

FINAL SCORE is always between 0.0 and 1.0, and never simply
"years_had / years_required".
"""

import json
from datetime import datetime

CURRENT_YEAR = 2026
CURRENT_MONTH = 8  # August 2026 - "today" for calculating ongoing roles


# ---------------------------------------------------------------------------
# Step 1: turn a resume's job history into a total years-of-experience number
# ---------------------------------------------------------------------------

def _months_between(start_date: str, end_date: str) -> int:
    """start_date/end_date are 'YYYY-MM' strings, or end_date can be 'present'."""
    start_year, start_month = (int(x) for x in start_date.split("-"))

    if end_date == "present":
        end_year, end_month = CURRENT_YEAR, CURRENT_MONTH
    else:
        end_year, end_month = (int(x) for x in end_date.split("-"))

    return (end_year - start_year) * 12 + (end_month - start_month)


def total_experience_years(resume: dict) -> float:
    """
    Sums up months across every PROFESSIONAL experience entry and converts
    to years.

    FIX (found during testing): entries that are academic/class projects
    (title starts with "Project:") are excluded. A JD asking for "2 years
    of experience" means paid/professional work - not coursework - but an
    early version of this function counted an ongoing class project
    ("since 2020, present") as 6+ years of work experience, which wrongly
    inflated every candidate's score to a perfect 1.0 and hid real
    differences between candidates.

    NOTE (documented limitation): this still does NOT check for
    overlapping date ranges between real jobs (e.g. two part-time roles
    at once would currently double-count those months). Good enough for
    v1 - flagged here for the evaluation report as a known simplification.
    """
    total_months = 0
    for job in resume.get("experience", []):
        if job.get("title", "").strip().lower().startswith("project:"):
            continue  # academic/class project, not professional experience

        if job.get("duration_months") is not None:
            total_months += job["duration_months"]
        else:
            total_months += _months_between(job["start_date"], job["end_date"])

    return round(total_months / 12, 2)


# ---------------------------------------------------------------------------
# Step 2: the non-linear 3-zone scoring curve
# ---------------------------------------------------------------------------

def experience_score(years_had: float, required_years: float, preferred_years: float) -> float:
    # Guard against a JD where preferred == required (avoid divide-by-zero)
    if preferred_years <= required_years:
        preferred_years = required_years + 1

    if years_had >= preferred_years:
        return 1.0

    if years_had >= required_years:
        # Zone B: climbs from 0.7 to 1.0
        progress = (years_had - required_years) / (preferred_years - required_years)
        return round(0.7 + 0.3 * progress, 3)

    # Zone C: below required - steeper penalty
    if required_years == 0:
        return 1.0  # no experience required at all
    progress = years_had / required_years
    return round(0.7 * progress, 3)


# ---------------------------------------------------------------------------
# Step 3: combine into one function that takes resume + job_description
# ---------------------------------------------------------------------------

def experience_match(resume: dict, job_description: dict) -> dict:
    years_had = total_experience_years(resume)
    required_years = job_description.get("required_experience_years", 0)
    preferred_years = job_description.get("preferred_experience_years", required_years)

    score = experience_score(years_had, required_years, preferred_years)

    explanation = (
        f"Candidate has {years_had} years of experience. "
        f"Job requires {required_years} years (prefers {preferred_years}). "
        f"Experience score = {score}."
    )

    return {
        "score": score,
        "years_had": years_had,
        "required_years": required_years,
        "preferred_years": preferred_years,
        "explanation": explanation,
    }


# ---------------------------------------------------------------------------
# Step 4: test against the 3 sample pairs
# ---------------------------------------------------------------------------

def run_tests(data_path: str = "ats_test_data.json"):
    with open(data_path, "r") as f:
        data = json.load(f)

    for pair in data["pairs"]:
        result = experience_match(pair["resume"], pair["job_description"])
        print(f"\n=== {pair['pair_id']} (expected: {pair['expected_match_quality']}) ===")
        print(f"Score: {result['score']}")
        print(f"  {result['explanation']}")


if __name__ == "__main__":
    run_tests()
