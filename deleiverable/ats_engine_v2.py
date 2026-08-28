"""
ats_engine_v2.py

Task 5 - Build ATS Score v2

This combines the four matchers built in Tasks 1-4 into ONE transparent
overall ATS score:
  - education_matcher.py   -> education_match()
  - skill_matcher.py       -> skill_match()
  - experience_matcher.py  -> experience_match()
  - semantic_matcher_v2.py -> semantic_match()

WEIGHTING RULE (documented):
  skills:      0.35   (most concrete, most verifiable signal of fit)
  experience:  0.25   (strong signal, but years worked is a rougher proxy
                        than an exact skill checklist)
  semantic:    0.25   (catches conceptual/contextual fit that keyword-based
                        skill matching alone can miss - e.g. synonyms,
                        related tools, rephrased responsibilities)
  education:   0.15   (real signal, but for most roles employers weight
                        actual skills/experience above the specific degree)

These weights are a documented starting judgment call - not derived from
data. Task 7 (evaluating against human labels) is where we'd come back and
tune these numbers if the combined score disagrees with human judgment.

FINAL SCORE = 0.35*skill + 0.25*experience + 0.25*semantic + 0.15*education
"""

import json

from education_matcher import education_match
from skill_matcher import skill_match
from experience_matcher import experience_match
from semantic_matcher_v2 import semantic_match


WEIGHTS = {
    "skills": 0.35,
    "experience": 0.25,
    "semantic": 0.25,
    "education": 0.15,
}


def recommendation_label(score: float) -> str:
    if score >= 0.75:
        return "Strong Match"
    elif score >= 0.5:
        return "Moderate Match"
    else:
        return "Weak Match"


def ats_score(resume: dict, job_description: dict) -> dict:
    edu_result = education_match(resume, job_description)
    skill_result = skill_match(resume, job_description)
    exp_result = experience_match(resume, job_description)
    sem_result = semantic_match(resume, job_description)

    sub_scores = {
        "education": edu_result["score"],
        "skills": skill_result["score"],
        "experience": exp_result["score"],
        "semantic": sem_result["score"],
    }

    final_score = round(
        WEIGHTS["skills"] * sub_scores["skills"]
        + WEIGHTS["experience"] * sub_scores["experience"]
        + WEIGHTS["semantic"] * sub_scores["semantic"]
        + WEIGHTS["education"] * sub_scores["education"],
        3,
    )

    label = recommendation_label(final_score)

    explanation = (
        f"Skills: {sub_scores['skills']} (x{WEIGHTS['skills']}) + "
        f"Experience: {sub_scores['experience']} (x{WEIGHTS['experience']}) + "
        f"Semantic: {sub_scores['semantic']} (x{WEIGHTS['semantic']}) + "
        f"Education: {sub_scores['education']} (x{WEIGHTS['education']}) "
        f"= {final_score} -> {label}"
    )

    return {
        "final_score": final_score,
        "recommendation": label,
        "sub_scores": sub_scores,
        "explanation": explanation,
        "details": {
            "education": edu_result,
            "skills": skill_result,
            "experience": exp_result,
            "semantic": sem_result,
        },
    }


def run_tests(data_path: str = "ats_test_data.json"):
    with open(data_path, "r") as f:
        data = json.load(f)

    for pair in data["pairs"]:
        result = ats_score(pair["resume"], pair["job_description"])
        name = pair["resume"]["name"]
        job_title = pair["job_description"]["title"]
        sub = result["sub_scores"]

        print("\n" + "=" * 55)
        print(f"{name}  ->  {job_title}")
        print(f"(expected: {pair['expected_match_quality']})")
        print(f"  Skills score:      {sub['skills']:.0%}   (weight {WEIGHTS['skills']:.0%})")
        print(f"  Experience score:  {sub['experience']:.0%}   (weight {WEIGHTS['experience']:.0%})")
        print(f"  Semantic score:    {sub['semantic']:.0%}   (weight {WEIGHTS['semantic']:.0%})")
        print(f"  Education score:   {sub['education']:.0%}   (weight {WEIGHTS['education']:.0%})")
        print(f"  FINAL ATS SCORE:   {result['final_score']:.0%}")
        print(f"  RECOMMENDATION:    {result['recommendation']}")
    print("\n" + "=" * 55)


if __name__ == "__main__":
    run_tests()
