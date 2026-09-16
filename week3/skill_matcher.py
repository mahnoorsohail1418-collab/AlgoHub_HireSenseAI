"""
skill_matcher.py

Task 2 - Skill Match Score

SCORING RULE (documented, as required):
Required and preferred skills are scored SEPARATELY, then combined with
unequal weights - required skills dominate the final score because in a
real ATS, missing a required skill is often a hard filter (candidate gets
rejected), while missing a preferred skill just makes them slightly less
competitive.

  1. REQUIRED SKILL SCORE (80% weight)
     matched_required_count / total_required_count
     e.g. 8 matched out of 10 required = 0.8

  2. PREFERRED SKILL SCORE (20% weight)
     matched_preferred_count / total_preferred_count
     Same formula, but on the preferred list.

FINAL SCORE = 0.8 * required_score + 0.2 * preferred_score

We chose an 80/20 split (not 50/50) specifically because required skills
are usually non-negotiable in real job postings, while preferred skills are
a "nice to have" that should only nudge the score, not dominate it.
"""

import json
import re


# ---------------------------------------------------------------------------
# Step 2: normalize skill text so 'Python', 'python', ' Python ' all match
# ---------------------------------------------------------------------------

def normalize_skill(skill: str) -> str:
    """
    FIX (found while reviewing Task 6 output): the original version deleted
    punctuation like "/" entirely, which squashed "Agile/Scrum experience"
    into the unreadable "agilescrum experience". Now separators like "/",
    "-", and "," are turned into spaces FIRST, so words stay separated.
    """
    text = skill.lower().strip()
    text = re.sub(r"[/\-,()]", " ", text)       # separators -> space
    text = re.sub(r"[^a-z0-9+#. ]", "", text)   # drop anything else non-skill-like
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _normalized_set(skills: list) -> set:
    return {normalize_skill(s) for s in skills}


# ---------------------------------------------------------------------------
# Skill synonyms / "implies" map (fix for a limitation found during testing):
# exact-string matching missed real matches like a resume listing "MySQL"
# when a job requires "SQL" - knowing MySQL does mean you know SQL. This
# maps a SPECIFIC tool -> the GENERAL skill(s) it counts as proof of.
# Note this is one-directional: having "MySQL" proves "SQL" knowledge, but
# having generic "SQL" does NOT prove specific "MySQL" experience.
# ---------------------------------------------------------------------------

SKILL_IMPLIES = {
    "mysql": {"sql"},
    "postgresql": {"sql"},
    "postgres": {"sql"},
    "sql server": {"sql"},
    "sqlite": {"sql"},
    "mongodb": {"nosql"},
    "node.js": {"nodejs", "javascript"},
    "nodejs": {"node.js", "javascript"},
    "reactjs": {"react"},
    "react.js": {"react"},
}


def _expand_with_implied_skills(resume_kw: set) -> set:
    """Given a resume's normalized skill set, add any general skills that
    are implied by a more specific skill already in the set."""
    expanded = set(resume_kw)
    for skill in resume_kw:
        if skill in SKILL_IMPLIES:
            expanded |= SKILL_IMPLIES[skill]
    return expanded


# ---------------------------------------------------------------------------
# Step 3 & 4: required and preferred scores, kept separate
# ---------------------------------------------------------------------------

def _score_against(resume_skills: list, target_skills: list) -> dict:
    resume_set = _normalized_set(resume_skills)
    resume_set_expanded = _expand_with_implied_skills(resume_set)
    target_set = _normalized_set(target_skills)

    if not target_set:
        return {"score": 1.0, "matched": [], "matched_via_alias": [], "missing": []}

    direct_matched = target_set & resume_set
    all_matched = target_set & resume_set_expanded
    matched_via_alias = all_matched - direct_matched
    missing = target_set - all_matched

    score = round(len(all_matched) / len(target_set), 3)
    return {
        "score": score,
        "matched": sorted(direct_matched),
        "matched_via_alias": sorted(matched_via_alias),
        "missing": sorted(missing),
    }


def required_skill_score(resume_skills: list, required_skills: list) -> dict:
    return _score_against(resume_skills, required_skills)


def preferred_skill_score(resume_skills: list, preferred_skills: list) -> dict:
    return _score_against(resume_skills, preferred_skills)


# ---------------------------------------------------------------------------
# Step 5 & 6: combine into one weighted score + track matched/missing skills
# ---------------------------------------------------------------------------

REQUIRED_WEIGHT = 0.8
PREFERRED_WEIGHT = 0.2


def skill_match(resume: dict, job_description: dict) -> dict:
    resume_skills = resume.get("skills", [])
    required_skills = job_description.get("required_skills", [])
    preferred_skills = job_description.get("preferred_skills", [])

    req_result = required_skill_score(resume_skills, required_skills)
    pref_result = preferred_skill_score(resume_skills, preferred_skills)

    final_score = round(
        REQUIRED_WEIGHT * req_result["score"] + PREFERRED_WEIGHT * pref_result["score"],
        3,
    )

    total_matched_req = len(req_result["matched"]) + len(req_result["matched_via_alias"])
    total_matched_pref = len(pref_result["matched"]) + len(pref_result["matched_via_alias"])

    explanation = (
        f"Required skills matched: {total_matched_req}/{len(required_skills)} "
        f"({req_result['score']*100:.0f}%), including "
        f"{len(req_result['matched_via_alias'])} matched via a related tool. "
        f"Preferred skills matched: {total_matched_pref}/{len(preferred_skills)} "
        f"({pref_result['score']*100:.0f}%). "
        f"Final skill score = {REQUIRED_WEIGHT}*{req_result['score']} + "
        f"{PREFERRED_WEIGHT}*{pref_result['score']} = {final_score}."
    )

    return {
        "score": final_score,
        "required_score": req_result["score"],
        "preferred_score": pref_result["score"],
        "total_required_skills": sorted(_normalized_set(required_skills)),
        "matched_required": req_result["matched"],
        "matched_required_via_alias": req_result["matched_via_alias"],
        "missing_required": req_result["missing"],
        "total_preferred_skills": sorted(_normalized_set(preferred_skills)),
        "matched_preferred": pref_result["matched"],
        "matched_preferred_via_alias": pref_result["matched_via_alias"],
        "missing_preferred": pref_result["missing"],
        "explanation": explanation,
    }


# ---------------------------------------------------------------------------
# Step 7: test against the 3 sample pairs
# ---------------------------------------------------------------------------

def run_tests(data_path: str = "ats_test_data.json"):
    with open(data_path, "r") as f:
        data = json.load(f)

    for pair in data["pairs"]:
        result = skill_match(pair["resume"], pair["job_description"])
        print(f"\n=== {pair['pair_id']} (expected: {pair['expected_match_quality']}) ===")
        print(f"Score: {result['score']}")
        print(f"  Total required skills ({len(result['total_required_skills'])}): {result['total_required_skills']}")
        print(f"  required_score: {result['required_score']}, preferred_score: {result['preferred_score']}")
        print(f"  Matched required (direct): {result['matched_required']}")
        print(f"  Matched required (via related tool): {result['matched_required_via_alias']}")
        print(f"  Missing required: {result['missing_required']}")
        print(f"  Total preferred skills ({len(result['total_preferred_skills'])}): {result['total_preferred_skills']}")
        print(f"  Matched preferred: {result['matched_preferred']}")
        print(f"  Missing preferred: {result['missing_preferred']}")
        print(f"  {result['explanation']}")


if __name__ == "__main__":
    run_tests()
