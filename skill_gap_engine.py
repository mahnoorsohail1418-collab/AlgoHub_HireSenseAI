"""
skill_gap_engine.py

Task 6 - Skill Gap Analysis

WHAT THIS DOES:
Reuses the matched/missing skill lists already produced by skill_matcher.py
(Task 2) and turns them into an actionable gap report - not just a score,
but WHICH skills are missing and how urgent each gap is.

CATEGORIZATION RULE (documented):
Every missing skill falls into exactly one of two categories:

  1. CRITICAL GAP - a MISSING REQUIRED skill.
     These are the skills the job description says are mandatory. Missing
     one of these is a real risk to the application - in many real ATS
     systems, missing a required skill is an automatic filter-out.

  2. NICE-TO-HAVE GAP - a MISSING PREFERRED skill.
     These skills would strengthen the application but aren't a hard
     requirement. Lower urgency than a critical gap.

Skills the candidate already HAS are not "gaps" at all and are excluded
from this report - this tool is specifically about what's MISSING.
"""

import json
from skill_matcher import skill_match


def skill_gap_analysis(resume: dict, job_description: dict) -> dict:
    match_result = skill_match(resume, job_description)

    critical_gaps = [
        {
            "skill": skill,
            "category": "Critical Gap",
            "reason": "This is a REQUIRED skill for the role that is missing from the resume. "
                      "This is likely to hurt the application significantly, since required "
                      "skills are often hard filters in real ATS systems.",
        }
        for skill in match_result["missing_required"]
    ]

    nice_to_have_gaps = [
        {
            "skill": skill,
            "category": "Nice-to-Have Gap",
            "reason": "This is a PREFERRED (not required) skill that is missing. "
                      "Having it would strengthen the application, but its absence "
                      "is not disqualifying on its own.",
        }
        for skill in match_result["missing_preferred"]
    ]

    return {
        "total_gaps": len(critical_gaps) + len(nice_to_have_gaps),
        "critical_gap_count": len(critical_gaps),
        "nice_to_have_gap_count": len(nice_to_have_gaps),
        "critical_gaps": critical_gaps,
        "nice_to_have_gaps": nice_to_have_gaps,
    }


def run_tests(data_path: str = "ats_test_data.json"):
    with open(data_path, "r") as f:
        data = json.load(f)

    for pair in data["pairs"]:
        result = skill_gap_analysis(pair["resume"], pair["job_description"])
        name = pair["resume"]["name"]
        job_title = pair["job_description"]["title"]

        print("\n" + "=" * 55)
        print(f"{name}  ->  {job_title}")
        print(f"Total gaps found: {result['total_gaps']}")

        print(f"\n  CRITICAL GAPS ({result['critical_gap_count']}):")
        if result["critical_gaps"]:
            for gap in result["critical_gaps"]:
                print(f"    - {gap['skill']}")
        else:
            print("    (none)")

        print(f"\n  NICE-TO-HAVE GAPS ({result['nice_to_have_gap_count']}):")
        if result["nice_to_have_gaps"]:
            for gap in result["nice_to_have_gaps"]:
                print(f"    - {gap['skill']}")
        else:
            print("    (none)")
    print("\n" + "=" * 55)


if __name__ == "__main__":
    run_tests()
