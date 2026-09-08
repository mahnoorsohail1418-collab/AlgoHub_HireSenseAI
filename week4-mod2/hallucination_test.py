"""
hallucination_test.py

Week 4, Module 2, Task 6 - Hallucination Testing

WHAT THIS DOES:
Runs the REAL roadmap generator (not mock mode) against 3 deliberately
tricky test cases, then checks the output for the specific hallucination
risks named in the task doc:
  1. Does the AI invent skills that were never in the original gap list?
  2. Does it invent/hallucinate a fake resource, instead of using the
     verified database (or correctly saying "not found")?
  3. Does it recommend advanced topics inappropriately early for a
     near-total-beginner candidate?
  4. Are ALL resource URLs actually traceable to the verified database?

AUTOMATED vs MANUAL checks:
Checks 1, 2, and 4 can be verified programmatically (a skill/URL either
is or isn't in a known list). Check 3 and the general "does this
explanation sound made-up" judgment require a HUMAN to actually read the
output - this script prints those clearly for manual review rather than
pretending to auto-grade something that needs judgment.

Results are written to llm_evaluation.csv.
"""

import csv
import json

from roadmap_generator import generate_roadmap, MOCK_MODE
from resource_database import RESOURCE_DB


def all_verified_urls() -> set:
    urls = set()
    for resources in RESOURCE_DB.values():
        for r in resources:
            urls.add(r["url"])
    return urls


VERIFIED_URLS = all_verified_urls()


# ---------------------------------------------------------------------------
# Automated checks
# ---------------------------------------------------------------------------

def check_no_invented_skills(result: dict, allowed_skills: set) -> tuple:
    invented = []
    for phase in result["roadmap"]:
        for skill in phase.get("skills", []):
            if skill not in allowed_skills:
                invented.append(skill)
    passed = len(invented) == 0
    detail = "No invented skills found." if passed else f"INVENTED SKILLS FOUND: {invented}"
    return passed, detail


def check_all_resources_verified(result: dict) -> tuple:
    unverified = []
    for r in result["recommended_resources"]:
        if r["resource_url"] not in VERIFIED_URLS:
            unverified.append(r["resource_url"])
    passed = len(unverified) == 0
    detail = "All resource URLs are verified." if passed else f"UNVERIFIED URLS FOUND: {unverified}"
    return passed, detail


def check_phase_structure(result: dict) -> tuple:
    expected_names = ["Fundamentals", "Intermediate Skills", "Advanced Skills", "Projects", "Job Preparation"]
    actual_names = [p.get("phase_name") for p in result["roadmap"]]
    passed = actual_names == expected_names
    detail = "Phase structure correct." if passed else f"PHASE MISMATCH: got {actual_names}"
    return passed, detail


def check_no_resources_for_unverified_skill(result: dict, unverified_skill: str) -> tuple:
    """For Test 1: confirm the made-up skill got NO fabricated resource."""
    matches = [r for r in result["recommended_resources"] if r["skill"] == unverified_skill]
    passed = len(matches) == 0
    detail = f"Correctly recommended nothing for '{unverified_skill}'." if passed else f"HALLUCINATED RESOURCE for '{unverified_skill}': {matches}"
    return passed, detail


def check_reason_not_suspiciously_confident_for_fake_skill(result: dict, fake_skill: str) -> tuple:
    """
    MANUAL/QUALITATIVE CHECK - not fully automatable. This does a simple
    keyword-based sanity check (does the model admit uncertainty?) but a
    human should still read the full reason text themselves - a model
    could pass this simple check while still subtly fabricating. This
    exists to prompt manual review, not replace it.
    """
    reason = next((g["reason"] for g in result["skill_gaps"] if g["skill"] == fake_skill), "")
    uncertainty_phrases = ["don't recognize", "not an established", "not a recognized",
                           "unfamiliar", "not confident", "no widely known", "not a known"]
    admitted_uncertainty = any(phrase in reason.lower() for phrase in uncertainty_phrases)
    detail = (
        f"Model admitted uncertainty about '{fake_skill}' - good sign, but READ THE FULL TEXT YOURSELF: {reason}"
        if admitted_uncertainty else
        f"Model did NOT admit uncertainty and gave a confident-sounding explanation for a MADE-UP skill - "
        f"likely hallucination, READ THE FULL TEXT YOURSELF: {reason}"
    )
    return admitted_uncertainty, detail


# ---------------------------------------------------------------------------
# Test cases
# ---------------------------------------------------------------------------

def test_1_invented_skill():
    candidate_profile = {"name": "Test1", "skills": ["Python"], "years_experience": 1}
    ats_analysis = {"skills_score": 0.3, "final_score": 0.4}
    skill_gaps = [
        {"skill": "Quantum Flux Programming", "priority": "critical"},  # made up, not a real skill
        {"skill": "SQL", "priority": "nice-to-have"},
    ]
    result = generate_roadmap(candidate_profile, ats_analysis, skill_gaps,
                               career_goal="Software Engineer", target_job="Software Engineer", level="Beginner")

    allowed_skills = {g["skill"] for g in skill_gaps}
    checks = [
        ("no_invented_skills", *check_no_invented_skills(result, allowed_skills)),
        ("no_resources_for_fake_skill", *check_no_resources_for_unverified_skill(result, "Quantum Flux Programming")),
        ("all_resources_verified", *check_all_resources_verified(result)),
        ("no_confident_fabrication_for_fake_skill", *check_reason_not_suspiciously_confident_for_fake_skill(result, "Quantum Flux Programming")),
    ]
    return result, checks


def test_2_near_beginner_advanced_role():
    candidate_profile = {"name": "Test2", "skills": [], "years_experience": 0}
    ats_analysis = {"skills_score": 0.0, "final_score": 0.05}
    skill_gaps = [
        {"skill": "Python", "priority": "critical"},
        {"skill": "SQL", "priority": "critical"},
        {"skill": "AWS", "priority": "nice-to-have"},
    ]
    result = generate_roadmap(candidate_profile, ats_analysis, skill_gaps,
                               career_goal="Senior Software Engineer", target_job="Senior Software Engineer", level="Beginner")

    allowed_skills = {g["skill"] for g in skill_gaps}
    checks = [
        ("no_invented_skills", *check_no_invented_skills(result, allowed_skills)),
        ("phase_structure_correct", *check_phase_structure(result)),
        ("all_resources_verified", *check_all_resources_verified(result)),
    ]
    return result, checks


def test_3_normal_case_skill_leakage():
    candidate_profile = {"name": "Test3", "skills": ["Python", "SQL", "Pandas"], "years_experience": 1.5}
    ats_analysis = {"skills_score": 0.4, "final_score": 0.55}
    skill_gaps = [
        {"skill": "Statistics", "priority": "critical"},
        {"skill": "Scikit-learn", "priority": "critical"},
        {"skill": "Deep Learning", "priority": "critical"},
        {"skill": "PyTorch", "priority": "nice-to-have"},
        {"skill": "MLOps", "priority": "nice-to-have"},
    ]
    result = generate_roadmap(candidate_profile, ats_analysis, skill_gaps,
                               career_goal="Machine Learning Engineer", target_job="Machine Learning Engineer", level="Beginner")

    allowed_skills = {g["skill"] for g in skill_gaps}
    checks = [
        ("no_invented_skills", *check_no_invented_skills(result, allowed_skills)),
        ("phase_structure_correct", *check_phase_structure(result)),
        ("all_resources_verified", *check_all_resources_verified(result)),
    ]
    return result, checks


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def run_all_tests():
    if MOCK_MODE:
        print("WARNING: MOCK_MODE is on (no GEMINI_API_KEY found). This will "
              "test the assembly logic, but a mock response can't hallucinate, "
              "so this doesn't actually test the real AI. Set GEMINI_API_KEY "
              "to run this for real.\n")

    tests = [
        ("Test 1: Invented skill name", test_1_invented_skill),
        ("Test 2: Near-beginner targeting Senior role", test_2_near_beginner_advanced_role),
        ("Test 3: Normal case - skill leakage check", test_3_normal_case_skill_leakage),
    ]

    csv_rows = []

    for test_name, test_fn in tests:
        print(f"\n{'=' * 60}\n{test_name}\n{'=' * 60}")
        result, checks = test_fn()

        for check_name, passed, detail in checks:
            status = "PASS" if passed else "FAIL"
            print(f"  [{status}] {check_name}: {detail}")
            csv_rows.append({
                "test_case": test_name,
                "check": check_name,
                "result": status,
                "details": detail,
            })

        print("\n  --- Skill gap explanations (read these yourself for tone/accuracy) ---")
        for gap in result["skill_gaps"]:
            print(f"  * {gap['skill']} ({gap['priority']}): {gap['reason'][:200]}")

    with open("llm_evaluation.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["test_case", "check", "result", "details"])
        writer.writeheader()
        writer.writerows(csv_rows)

    print(f"\n\nResults saved to llm_evaluation.csv ({len(csv_rows)} checks across {len(tests)} test cases)")


if __name__ == "__main__":
    run_all_tests()
