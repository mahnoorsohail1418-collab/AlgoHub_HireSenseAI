"""
recommendation_engine.py

Week 4, Module 2, Task 5 - Resource Recommendation

WHAT THIS DOES:
Takes a missing skill + the candidate's current level/difficulty, and
returns recommended resources - PULLED ONLY from the verified
resource_database.py, never generated freely. This is what makes Task 6's
hallucination testing possible to pass: if a resource isn't in the
verified database, this returns nothing rather than inventing something.

LEVEL/DIFFICULTY RULE (documented):
Each skill has a fixed 3-stage progression (Fundamentals -> Hands-on Lab
-> Project). Which stages get shown depends on the candidate's level:
  - Beginner:     all 3 stages (start from the basics)
  - Intermediate: skip Fundamentals, show Hands-on Lab + Project
                  (assume the basics are already known)
  - Advanced:     just the Project stage (assume they can learn any
                  remaining fundamentals/practice on their own)
"""

import json
from resource_database import RESOURCE_DB

LEVEL_STAGES = {
    "beginner": ["Fundamentals", "Hands-on Lab", "Project"],
    "intermediate": ["Hands-on Lab", "Project"],
    "advanced": ["Project"],
}


def recommend_resources(missing_skill: str, level: str = "Beginner") -> dict:
    skill_key = missing_skill.strip().lower()
    level_key = level.strip().lower()

    stages_to_include = LEVEL_STAGES.get(level_key, LEVEL_STAGES["beginner"])

    if skill_key not in RESOURCE_DB:
        return {
            "missing_skill": missing_skill,
            "level": level,
            "recommended": [],
            "note": f"No verified resources found for '{missing_skill}'. "
                    f"Not recommending anything rather than inventing a resource.",
        }

    all_stages = RESOURCE_DB[skill_key]
    filtered = [r for r in all_stages if r["stage"] in stages_to_include]

    recommended = [
        {"step": i + 1, "stage": r["stage"], "name": r["name"], "url": r["url"], "type": r["type"]}
        for i, r in enumerate(filtered)
    ]

    return {
        "missing_skill": missing_skill,
        "level": level,
        "recommended": recommended,
        "note": None,
    }


def run_tests():
    test_cases = [
        {"missing_skill": "Docker", "level": "Beginner"},
        {"missing_skill": "AWS", "level": "Intermediate"},
        {"missing_skill": "Kubernetes", "level": "Advanced"},
        {"missing_skill": "COBOL", "level": "Beginner"},  # not in DB - should NOT invent
    ]

    for case in test_cases:
        result = recommend_resources(case["missing_skill"], case["level"])
        print(f"\nMissing Skill: {result['missing_skill']}")
        print(f"Level: {result['level']}")
        if result["note"]:
            print(f"  {result['note']}")
        else:
            print("Recommended:")
            for r in result["recommended"]:
                print(f"  {r['step']}. {r['name']}  ({r['stage']})")
                print(f"     {r['url']}")


if __name__ == "__main__":
    run_tests()
