"""
fast_pipeline.py

Frontend demo support file - NOT part of the original Module 1/2 task list.

WHY THIS EXISTS:
roadmap_generator.py's generate_roadmap() calls Prompt A, then B, then C,
then D, one after another. But A, B, and D don't actually depend on each
other's output - only C depends on B finishing first (it needs the skill
gap reasons to sequence into phases). Running A, B, and D one-by-one
wastes time waiting on each other for no reason.

This runs A, B, and D concurrently (using threads, since these are I/O-
bound network calls, not CPU work), then runs C right after B resolves.
Same prompts, same functions, same outputs as generate_roadmap() - this
file changes nothing about WHAT gets asked or returned, only the ORDER
calls are fired in, to cut down the wait on a live demo.
"""

from concurrent.futures import ThreadPoolExecutor

from roadmap_generator import (
    run_prompt_a,
    run_prompt_b_batch,
    run_prompt_c,
    run_prompt_d,
)
from recommendation_engine import recommend_resources


def generate_roadmap_fast(candidate_profile: dict, ats_analysis: dict, skill_gaps: list,
                           career_goal: str, target_job: str, level: str = "Beginner") -> dict:
    with ThreadPoolExecutor(max_workers=3) as pool:
        future_a = pool.submit(run_prompt_a, candidate_profile, ats_analysis, career_goal)
        future_b = pool.submit(run_prompt_b_batch, skill_gaps, target_job)
        future_d = pool.submit(run_prompt_d, candidate_profile)

        prompt_a_result = future_a.result()
        reasons_by_skill = future_b.result()
        resume_improvements = future_d.result()

    skill_gaps_with_reasons = [
        {
            "skill": gap["skill"],
            "priority": gap["priority"],
            "reason": reasons_by_skill.get(gap["skill"], "No explanation available."),
        }
        for gap in skill_gaps
    ]

    # C genuinely needs B's output first, so it can't be parallelized in.
    roadmap_phases = run_prompt_c(skill_gaps_with_reasons, career_goal)

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

    return {
        "career_summary": prompt_a_result.get("career_direction", ""),
        "current_level": prompt_a_result.get("current_level", "Unknown"),
        "strongest_areas": prompt_a_result.get("strongest_areas", []),
        "skill_gaps": skill_gaps_with_reasons,
        "roadmap": roadmap_phases,
        "recommended_resources": recommended_resources,
        "resume_improvements": resume_improvements,
    }
