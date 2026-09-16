"""
selection_message.py

Frontend demo support file - NOT part of the original Module 1/2 task list.

WHY THIS EXISTS:
Mirrors rejection_message.py but for the other outcome: when HR marks a
candidate as selected, this turns their already-computed matched skills
into a ready-to-send congratulatory message, naming the specific skills
that made them a fit for this role.
"""


def build_selection_message(candidate_name: str, target_job: str, matched_skills: list) -> str:
    if matched_skills:
        if len(matched_skills) == 1:
            skills_line = f"your experience with {matched_skills[0]}"
        else:
            skills_line = f"your experience with {', '.join(matched_skills[:-1])} and {matched_skills[-1]}"
        highlight = f"In particular, {skills_line} really stood out to us."
    else:
        highlight = "Your overall background stood out to us."

    return f"""Dear {candidate_name},

Congratulations! We're pleased to let you know that you've been selected to move forward for the {target_job} position.

{highlight}

Our team will be in touch shortly with next steps. We're excited about the possibility of you joining us.

Best regards,
The Hiring Team"""
