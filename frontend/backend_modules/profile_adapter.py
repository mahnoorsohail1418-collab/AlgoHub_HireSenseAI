"""
profile_adapter.py

Frontend demo support file - NOT part of the original Module 1/2 task list.

WHY THIS EXISTS:
Module 1's build_candidate_profile() returns a rich, nested shape:
    {personal_information, education, experience, skills: {all_skills: [...]},
     projects, certifications, career_history}

Module 2's roadmap_generator.py prompts were always tested against a much
simpler, flat shape:
    {name, skills: [...], years_experience}

These two were never actually wired together before - every Module 2 test
built its own small hand-written profile dict. This file is the missing
adapter between the two, so a real parsed resume can flow straight into
the real roadmap generator.
"""

from datetime import date

from candidate_profile import _date_sort_key  # reuse the existing date parser


def _estimate_years_experience(career_history: list) -> float:
    """
    Module 1 never computes a single "years of experience" number - it
    only produces a list of jobs with start/end dates. This estimates it
    by finding the earliest start date across all jobs and comparing to
    today.

    FIX (found during real-resume testing): some resumes (often LinkedIn
    exports) never give a calendar date at all - just relative durations
    per job ("1 year", "6 months", "current"). The calendar-based method
    above always returns 0 for these, even for someone with a decade of
    real experience. If no calendar date was found anywhere, this sums
    up whatever relative durations WERE detected as a fallback estimate.
    Note this is necessarily a floor, not exact - an open-ended "current"
    role with no stated duration can't be counted, so the true total is
    likely higher than what this reports.
    """
    if not career_history:
        return 0.0

    earliest_year = None
    for job in career_history:
        year, _ = _date_sort_key(job.get("start_date"))
        if year and (earliest_year is None or year < earliest_year):
            earliest_year = year

    if earliest_year:
        years = date.today().year - earliest_year
        return max(0.0, round(years, 1))

    total_months = sum(job.get("duration_months") or 0 for job in career_history)
    if total_months:
        return round(total_months / 12, 1)

    return 0.0


def to_module2_profile(module1_profile: dict) -> dict:
    """
    Builds the flat {name, skills, years_experience} shape that
    run_prompt_a / run_prompt_d in roadmap_generator.py actually expect,
    from the real, richer output of build_candidate_profile().
    """
    personal = module1_profile.get("personal_information") or {}
    skills = module1_profile.get("skills") or {}
    career_history = module1_profile.get("career_history") or []

    return {
        "name": personal.get("name", "Candidate"),
        "skills": skills.get("all_skills", []),
        "years_experience": _estimate_years_experience(career_history),
        # kept for Prompt D (resume document feedback), which looks at
        # the raw profile shape, not the simplified one
        "projects": module1_profile.get("projects", []),
    }
