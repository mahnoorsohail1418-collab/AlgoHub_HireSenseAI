"""
roadmap_generator.py

Week 4, Module 2, Task 4 - Personalized Roadmap

WHAT THIS DOES:
Ties together everything built so far in Module 2:
  1. Takes a candidate's profile + their ACTUAL detected skill gaps
     (never invented - this is the whole point of the task doc's note:
     "based on actual detected gaps, not a generic AI-generated career plan")
  2. Runs Prompt A (career analysis) through Claude
  3. Runs Prompt B (skill gap explanation) once per missing skill
  4. Runs Prompt C (roadmap generation) to sequence the skills into the
     5 fixed phases: Fundamentals / Intermediate Skills / Advanced Skills
     / Projects / Job Preparation
  5. Attaches REAL resources to each skill using recommendation_engine.py
     (never lets the LLM invent a course or URL)
  6. Assembles everything into the exact shape defined in
     roadmap_schema.json

MOCK MODE:
Calling the real Gemini API requires a free API key the student sets up
locally (GEMINI_API_KEY environment variable, from Google AI Studio - no
credit card required) - this can't be tested without one. To verify the
ASSEMBLY logic works correctly regardless (the part that doesn't depend
on what the LLM says), this file has a MOCK_MODE that skips the real API
call and uses a stubbed response instead. Once a real API key is set,
MOCK_MODE=False runs it for real with no other code changes needed.
"""

import json
import os
import time

from recommendation_engine import recommend_resources

MOCK_MODE = os.environ.get("GEMINI_API_KEY") is None

if not MOCK_MODE:
    from google import genai
    from google.genai import types
    from google.genai import errors as genai_errors
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

MODEL = "gemini-3.5-flash-lite"  # switched again: gemini-2.5-flash-lite
# was retired for new users, Google's own error told us to use this one.
# If this model's quota also gets exhausted, try "gemini-2.5-flash" next -
# each model name has its own independent daily allowance.


def _parse_json_response(raw_text: str, fallback: dict):
    """
    Parses the model's JSON response. Even when explicitly told not to,
    models sometimes wrap JSON in ```json ... ``` markdown fences - this
    strips those before parsing. Falls back to a safe default rather than
    crashing if the response still isn't valid JSON.
    """
    text = raw_text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        print(f"  WARNING: could not parse JSON response, using fallback. Raw text was:\n{raw_text[:200]}")
        return fallback


def call_llm(system_prompt: str, user_prompt: str, max_retries: int = 4) -> str:
    if MOCK_MODE:
        raise RuntimeError(
            "MOCK_MODE is on because no GEMINI_API_KEY was found. "
            "This function should not be called directly in mock mode - "
            "use the _mock_* functions instead."
        )

    # FIX: the free tier occasionally returns a transient 503 "high demand"
    # error - this isn't a real bug, so retry with a short backoff instead
    # of crashing the whole roadmap generation over one busy moment.
    last_error = None
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model=MODEL,
                contents=user_prompt,
                config=types.GenerateContentConfig(system_instruction=system_prompt),
            )
            return response.text
        except genai_errors.ServerError as e:
            last_error = e
            wait_seconds = 2 ** attempt  # 1, 2, 4, 8 seconds
            print(f"  (Gemini busy, retrying in {wait_seconds}s... attempt {attempt + 1}/{max_retries})")
            time.sleep(wait_seconds)

    raise RuntimeError(f"Gemini API still unavailable after {max_retries} retries: {last_error}")


# ---------------------------------------------------------------------------
# Step 1: Prompt A - Career Analysis
# ---------------------------------------------------------------------------

PROMPT_A_SYSTEM = (
    "You are a career analysis assistant. Analyze ONLY the information "
    "given - do not invent skills or experience not present. Base "
    "'current level' on years of experience and required-skills-matched "
    "count from the ATS analysis provided."
)


def run_prompt_a(candidate_profile: dict, ats_analysis: dict, career_goal: str) -> dict:
    if MOCK_MODE:
        return _mock_prompt_a(candidate_profile, career_goal)

    user_prompt = (
        f"Candidate profile:\n{json.dumps(candidate_profile, indent=2)}\n\n"
        f"ATS analysis:\n{json.dumps(ats_analysis, indent=2)}\n\n"
        f"Career goal: {career_goal}\n\n"
        "Respond with ONLY valid JSON (no markdown code fences, no extra "
        "text) in exactly this shape:\n"
        '{"current_level": "Entry-level|Junior|Mid-level|Senior", '
        '"strongest_areas": ["...", "..."], '
        '"weak_areas": ["...", "..."], '
        '"career_direction": "1-2 sentences"}'
    )
    raw_response = call_llm(PROMPT_A_SYSTEM, user_prompt)
    return _parse_json_response(raw_response, fallback={
        "current_level": "Unknown", "strongest_areas": [], "weak_areas": [], "career_direction": "",
    })


def _mock_prompt_a(candidate_profile: dict, career_goal: str) -> dict:
    years = candidate_profile.get("years_experience", 0)
    level = "Entry-level" if years < 2 else "Junior" if years < 4 else "Mid-level"
    return {
        "current_level": level,
        "strongest_areas": [
            f"Solid foundation in {', '.join(candidate_profile.get('skills', [])[:2])}",
        ],
        "weak_areas": [
            f"Missing core skills for {career_goal}",
        ],
        "career_direction": f"Focus on closing skill gaps toward {career_goal}.",
    }


# ---------------------------------------------------------------------------
# Step 2: Prompt B - Skill Gap Explanation
# FIX (found during testing): the free tier only allows 20 requests/day
# PER MODEL. Calling this once per missing skill (5 separate calls for a
# 5-skill roadmap) burned through the daily quota after just 2-3 test
# runs. Batched into ONE call for all skills instead - cuts total calls
# per roadmap generation from 8 down to 4.
# ---------------------------------------------------------------------------

PROMPT_B_SYSTEM = (
    "For EACH skill given, explain in 2-3 sentences why that missing "
    "skill matters for the target job. Do not recommend resources. "
    "IMPORTANT - read carefully: a skill name can SOUND technically "
    "plausible (using real, familiar jargon like 'distributed', 'vector', "
    "'sharding', 'pipeline', etc.) while still not being a real, "
    "established skill or technology. Sounding technical is NOT the same "
    "as being real. Before writing a reason, ask yourself: can I name a "
    "specific, well-known source for this exact term - a known creator, "
    "official documentation, a widely-used library/framework with this "
    "exact name, or a standard textbook/course that teaches it under this "
    "exact name? If you cannot point to something concrete like that, "
    "treat the term as unrecognized, EVEN IF it sounds plausible or is "
    "built from real technical vocabulary. In that case, say so explicitly "
    "(e.g. 'I don't recognize this as an established skill/technology') "
    "instead of writing a confident, detailed-sounding explanation. Do not "
    "guess, do not fabricate, and do not let technical-sounding phrasing "
    "substitute for actual recognition. "
    "Respond with ONLY valid JSON (no markdown fences, no extra text) - "
    "a JSON array of objects: "
    '[{"skill": "...", "reason": "..."}, ...] - one object per skill, '
    "in the same order given."
)


def run_prompt_b_batch(skill_gaps: list, target_job: str) -> dict:
    """Returns a dict mapping skill name -> reason string."""
    if MOCK_MODE:
        return {g["skill"]: _mock_prompt_b(g["skill"], target_job, g["priority"]) for g in skill_gaps}

    user_prompt = (
        f"Target job: {target_job}\n\n"
        f"Skills to explain (with priority):\n{json.dumps(skill_gaps, indent=2)}\n\n"
        "For each skill above, explain specifically why it matters for a "
        f"{target_job} role."
    )
    raw_response = call_llm(PROMPT_B_SYSTEM, user_prompt)
    fallback = [{"skill": g["skill"], "reason": _mock_prompt_b(g["skill"], target_job, g["priority"])} for g in skill_gaps]
    parsed = _parse_json_response(raw_response, fallback=fallback)
    if not isinstance(parsed, list):
        parsed = fallback
    return {item["skill"]: item["reason"] for item in parsed}


def _mock_prompt_b(missing_skill: str, target_job: str, priority: str) -> str:
    urgency = "is a core requirement" if priority == "critical" else "strengthens your candidacy"
    return f"{missing_skill} {urgency} for {target_job} roles, since it's commonly used in day-to-day work for this kind of position."


# ---------------------------------------------------------------------------
# Step 3: Prompt C - Roadmap Generation (5 fixed phases)
# ---------------------------------------------------------------------------

PHASE_NAMES = ["Fundamentals", "Intermediate Skills", "Advanced Skills", "Projects", "Job Preparation"]

PROMPT_C_SYSTEM = (
    "Organize the given priority_skills list into exactly 5 fixed phases: "
    "Fundamentals, Intermediate Skills, Advanced Skills, Projects, Job "
    "Preparation. Every skill placed must come from the priority_skills "
    "list - do not invent skills. Critical skills should generally appear "
    "in earlier phases than nice-to-have skills."
)


def run_prompt_c(priority_skills: list, career_goal: str) -> list:
    if MOCK_MODE:
        return _mock_prompt_c(priority_skills)

    user_prompt = (
        f"Career goal: {career_goal}\n"
        f"Priority skills: {json.dumps(priority_skills, indent=2)}\n\n"
        "Organize into the 5 fixed phases. Respond with ONLY valid JSON "
        "(no markdown code fences, no extra text) - a JSON array of "
        "exactly 5 objects, in this shape:\n"
        '[{"phase_number": 1, "phase_name": "Fundamentals", '
        '"skills": ["..."], "goal": "one sentence"}, ... ]\n'
        f"The phase_name values MUST be exactly, in order: {PHASE_NAMES}"
    )
    raw_response = call_llm(PROMPT_C_SYSTEM, user_prompt)
    parsed = _parse_json_response(raw_response, fallback=_mock_prompt_c(priority_skills))
    return parsed if isinstance(parsed, list) else _mock_prompt_c(priority_skills)


def _mock_prompt_c(priority_skills: list) -> list:
    """
    Simple, deterministic mock sequencing: critical skills fill earlier
    phases first, nice-to-have skills fill later phases, spread evenly
    across the 5 fixed phase names. This is NOT meant to be a smart
    sequencer - it just proves the assembly pipeline works end-to-end
    while MOCK_MODE is on.
    """
    critical = [s for s in priority_skills if s["priority"] == "critical"]
    nice_to_have = [s for s in priority_skills if s["priority"] == "nice-to-have"]
    ordered = critical + nice_to_have

    phases = []
    for i, phase_name in enumerate(PHASE_NAMES):
        phases.append({"phase_number": i + 1, "phase_name": phase_name, "skills": [], "goal": ""})

    # Spread skills across the first N phases (skip "Projects" and
    # "Job Preparation" for skill assignment - those get generic goals)
    learn_phases = phases[:3]
    for i, skill in enumerate(ordered):
        learn_phases[i % 3]["skills"].append(skill["skill"])

    for p in phases:
        if p["skills"]:
            p["goal"] = f"Build working knowledge of {', '.join(p['skills'])}."
        elif p["phase_name"] == "Projects":
            p["goal"] = "Apply the newly learned skills in one real project."
        elif p["phase_name"] == "Job Preparation":
            p["goal"] = "Update resume and portfolio, prepare for interviews."

    return phases


PROMPT_D_SYSTEM = (
    "You give concrete, specific feedback on a resume AS A DOCUMENT - "
    "formatting, missing sections, vague bullet points, lack of "
    "quantified achievements. Do NOT repeat skill gaps here - that's a "
    "separate concern. Only comment on how the resume itself is written "
    "and structured. Base every suggestion on something actually present "
    "or actually missing in the profile given - do not invent details "
    "about the candidate that aren't there."
)


def run_prompt_d(candidate_profile: dict) -> list:
    if MOCK_MODE:
        return _mock_prompt_d(candidate_profile)

    user_prompt = (
        f"Candidate profile:\n{json.dumps(candidate_profile, indent=2)}\n\n"
        "Give 2-4 concrete, specific suggestions for improving this "
        "resume as a document (not skill gaps). Respond with ONLY valid "
        "JSON (no markdown fences, no extra text) - a JSON array of "
        "strings, e.g. [\"suggestion 1\", \"suggestion 2\"]"
    )
    raw_response = call_llm(PROMPT_D_SYSTEM, user_prompt)
    parsed = _parse_json_response(raw_response, fallback=_mock_prompt_d(candidate_profile))
    return parsed if isinstance(parsed, list) else _mock_prompt_d(candidate_profile)


def _mock_prompt_d(candidate_profile: dict) -> list:
    suggestions = []
    if not candidate_profile.get("projects"):
        suggestions.append("Add a Projects section - none was found in the current profile.")
    if candidate_profile.get("years_experience", 0) < 1:
        suggestions.append("Consider adding more detail to internship/part-time roles to strengthen the experience section.")
    if not suggestions:
        suggestions.append("Quantify at least one achievement per role with a specific number or metric.")
    return suggestions


# ---------------------------------------------------------------------------
# Step 4 + 5: attach real resources, assemble final schema-shaped output
# ---------------------------------------------------------------------------

def generate_roadmap(candidate_profile: dict, ats_analysis: dict, skill_gaps: list,
                      career_goal: str, target_job: str, level: str = "Beginner") -> dict:

    prompt_a_result = run_prompt_a(candidate_profile, ats_analysis, career_goal)

    skill_gaps_with_reasons = []
    reasons_by_skill = run_prompt_b_batch(skill_gaps, target_job)
    for gap in skill_gaps:
        skill_gaps_with_reasons.append({
            "skill": gap["skill"],
            "priority": gap["priority"],
            "reason": reasons_by_skill.get(gap["skill"], "No explanation available."),
        })

    roadmap_phases = run_prompt_c(skill_gaps_with_reasons, career_goal)

    # Attach real, verified resources to every skill mentioned anywhere in the roadmap
    recommended_resources = []
    all_roadmap_skills = {s for phase in roadmap_phases for s in phase.get("skills", [])}
    for skill in all_roadmap_skills:
        rec = recommend_resources(skill, level)
        for r in rec["recommended"]:
            recommended_resources.append({
                "skill": skill,
                "resource_name": r["name"],
                "resource_url": r["url"],
                "resource_type": r["type"],
            })

    resume_improvements = run_prompt_d(candidate_profile)

    return {
        "career_summary": prompt_a_result.get("career_direction", ""),
        "current_level": prompt_a_result.get("current_level", "Unknown"),
        "skill_gaps": skill_gaps_with_reasons,
        "roadmap": roadmap_phases,
        "recommended_resources": recommended_resources,
        "resume_improvements": resume_improvements,
    }


def run_tests():
    candidate_profile = {
        "name": "Test Candidate",
        "skills": ["Python", "SQL", "Pandas"],
        "years_experience": 1.5,
    }
    ats_analysis = {"skills_score": 0.4, "final_score": 0.55}
    skill_gaps = [
        {"skill": "Statistics", "priority": "critical"},
        {"skill": "Scikit-learn", "priority": "critical"},
        {"skill": "Deep Learning", "priority": "critical"},
        {"skill": "PyTorch", "priority": "nice-to-have"},
        {"skill": "MLOps", "priority": "nice-to-have"},
    ]

    result = generate_roadmap(
        candidate_profile, ats_analysis, skill_gaps,
        career_goal="Machine Learning Engineer",
        target_job="Machine Learning Engineer",
        level="Beginner",
    )

    print(f"MOCK_MODE: {MOCK_MODE}\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    run_tests()
