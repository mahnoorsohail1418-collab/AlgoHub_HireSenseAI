"""
rejection_message.py

Frontend demo support file - NOT part of the original Module 1/2 task list.

WHY THIS EXISTS:
For the HR-facing workflow: once a candidate is marked "not selected" for
a role, this turns their already-generated roadmap into a ready-to-send
message - explaining why, and pointing them toward the specific skills
and resources that would make them competitive next time.

This does NOT call the AI again - it reuses the roadmap already generated
by roadmap_generator.py and just formats it into prose. No new content is
invented here beyond simple template sentences.
"""


def _fallback_suggestion(skill: str) -> str:
    """
    Not every skill has a verified resource in the database yet. Rather
    than leaving that skill with no guidance at all in the message, this
    gives an honest, still-useful fallback - it does NOT invent a fake
    course/link (that would violate the whole point of only recommending
    verified resources), it just suggests a generic, always-true next
    step: build something real with it, and go find official docs
    yourself, since we can't vouch for a specific one right now.
    """
    return f"No verified resource on file for {skill} yet - in the meantime, a solid next step is building a small personal project that actually uses {skill}, and checking {skill}'s official documentation or a well-known course platform (e.g. Coursera, freeCodeCamp) directly."


def build_rejection_message(candidate_name: str, target_job: str, roadmap_result: dict) -> str:
    gaps = roadmap_result.get("skill_gaps", [])
    critical_gaps = [g["skill"] for g in gaps if g.get("priority") == "critical"]
    nice_to_have_gaps = [g["skill"] for g in gaps if g.get("priority") == "nice-to-have"]

    gap_line = ""
    if critical_gaps:
        gap_line = f"In particular, strengthening {', '.join(critical_gaps)} would make the biggest difference for this kind of role."
    elif nice_to_have_gaps:
        gap_line = f"A few supporting skills worth adding: {', '.join(nice_to_have_gaps)}."

    resources_by_skill = {}
    for r in roadmap_result.get("recommended_resources", []):
        resources_by_skill.setdefault(r["skill"], []).append(r)

    phase_blocks = []
    for phase in roadmap_result.get("roadmap", []):
        if not phase.get("skills"):
            continue
        lines = [f"  {phase['phase_number']}. {phase['phase_name']}"]
        if phase.get("goal"):
            lines.append(f"     Goal: {phase['goal']}")
        for skill in phase["skills"]:
            lines.append(f"     - {skill}")
            skill_resources = resources_by_skill.get(skill, [])
            if skill_resources:
                for res in skill_resources[:2]:  # cap at 2 links per skill, keeps the email readable
                    lines.append(f"         -> {res['resource_name']}: {res['resource_url']}")
            else:
                lines.append(f"         -> {_fallback_suggestion(skill)}")
        phase_blocks.append("\n".join(lines))

    roadmap_block = "\n\n".join(phase_blocks) if phase_blocks else "  (No specific gaps identified.)"

    message = f"""Dear {candidate_name},

Thank you for applying for the {target_job} position, and for taking the time to share your background with us.

After reviewing your application, we've decided not to move forward at this time. This isn't a reflection of your potential - it simply means your current profile isn't the closest match for this specific role right now. {gap_line}

To help with your next steps, here's a personalized roadmap based on the specific gaps we identified, including free resources for each skill:

{roadmap_block}

We'd genuinely encourage you to apply again once you've had a chance to build on these areas. Wishing you the best in your job search.

Best regards,
The Hiring Team"""

    return message
