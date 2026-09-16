"""
target_jobs.py

Frontend demo support file - NOT part of the original Module 1/2 task list.

WHY THIS EXISTS:
The real pipeline (candidate_profile.py -> roadmap_generator.py) always
took `skill_gaps` as a manually-typed-in input in every test case - there
was no code anywhere that actually compared a candidate's real skills
against what a target job needs. For a live "upload your resume and see
your roadmap" demo, something has to fill that gap automatically.

This is a deliberately small, fixed list (not a live job-market lookup)
so the demo is predictable and reliable. Every skill listed here exists
in resource_database.py, so every detected gap is guaranteed to resolve
to a real, verified resource - never an empty result on stage.
"""

import re

TARGET_JOBS = {
    "Machine Learning Engineer": [
        {"skill": "Python", "priority": "critical"},
        {"skill": "Statistics", "priority": "critical"},
        {"skill": "Scikit-learn", "priority": "critical"},
        {"skill": "Deep Learning", "priority": "critical"},
        {"skill": "PyTorch", "priority": "nice-to-have"},
        {"skill": "MLOps", "priority": "nice-to-have"},
    ],
    "Backend Engineer": [
        {"skill": "Python", "priority": "critical"},
        {"skill": "SQL", "priority": "critical"},
        {"skill": "REST APIs", "priority": "critical"},
        {"skill": "Docker", "priority": "nice-to-have"},
        {"skill": "AWS", "priority": "nice-to-have"},
    ],
    "Frontend Engineer": [
        {"skill": "JavaScript", "priority": "critical"},
        {"skill": "React", "priority": "critical"},
        {"skill": "Git", "priority": "nice-to-have"},
    ],
    "Data Analyst": [
        {"skill": "SQL", "priority": "critical"},
        {"skill": "Excel", "priority": "critical"},
        {"skill": "Statistics", "priority": "critical"},
        {"skill": "Pandas", "priority": "nice-to-have"},
        {"skill": "Tableau", "priority": "nice-to-have"},
    ],
    "DevOps Engineer": [
        {"skill": "Docker", "priority": "critical"},
        {"skill": "Kubernetes", "priority": "critical"},
        {"skill": "Linux", "priority": "critical"},
        {"skill": "AWS", "priority": "nice-to-have"},
        {"skill": "Scrum", "priority": "nice-to-have"},
    ],
    "Full Stack Developer": [
        {"skill": "JavaScript", "priority": "critical"},
        {"skill": "React", "priority": "critical"},
        {"skill": "Node.js", "priority": "critical"},
        {"skill": "SQL", "priority": "nice-to-have"},
        {"skill": "MongoDB", "priority": "nice-to-have"},
    ],
}


def compute_skill_gaps(candidate_skills: list, target_job: str) -> dict:
    """
    Compares the candidate's actual extracted skills against the fixed
    requirement list for the chosen target job.

    Returns both the gaps (what to feed into roadmap_generator.py) and a
    simple match score (what to feed into ats_analysis), computed the
    same way regardless of target job so the score is comparable across
    demos.

    FIX (found during real-resume testing): some PDF layouts - especially
    multi-column templates - extract with words run together on one line
    instead of clean one-skill-per-line text (e.g. "LANGUAGES Python C++"
    as a single string). An exact match against the candidate's skill
    list would silently miss "Python" entirely in that case, even though
    it's clearly there. Matching now checks whether each required skill
    appears as a whole word ANYWHERE in the candidate's extracted skill
    text, not just as its own separate list entry - this survives messy
    extraction without falsely matching partial words (e.g. "java" won't
    match inside "javascript").
    """
    required = TARGET_JOBS.get(target_job, [])
    candidate_blob = " ".join(candidate_skills).lower()

    gaps = []
    matched = []
    for req in required:
        pattern = r"\b" + re.escape(req["skill"].lower()) + r"\b"
        if re.search(pattern, candidate_blob):
            matched.append(req["skill"])
        else:
            gaps.append({"skill": req["skill"], "priority": req["priority"]})

    total = len(required) if required else 1
    critical_total = sum(1 for r in required if r["priority"] == "critical") or 1
    critical_matched = sum(
        1 for r in required if r["priority"] == "critical" and r["skill"] in matched
    )

    skills_score = round(len(matched) / total, 2)
    # Weight critical skills more heavily in the final score, since
    # missing a "nice-to-have" matters less than missing a core skill.
    final_score = round((0.7 * (critical_matched / critical_total)) + (0.3 * skills_score), 2)

    return {
        "matched_skills": matched,
        "skill_gaps": gaps,
        "skills_score": skills_score,
        "final_score": final_score,
    }


# ---------------------------------------------------------------------------
# Auto-detecting the target role from the resume itself
# ---------------------------------------------------------------------------

# Keywords/synonyms that hint at each role, checked against the resume's
# profile summary and most recent job title. This is deliberately simple
# (keyword matching, not ML) so it's predictable and explainable in a demo.
ROLE_KEYWORDS = {
    "Machine Learning Engineer": ["machine learning", "ml engineer", "deep learning", "data scientist", "ai engineer", "ai & ml", "ai/ml"],
    "Backend Engineer": ["backend", "back-end", "back end", "server-side", "api developer"],
    "Frontend Engineer": ["frontend", "front-end", "front end", "ui developer", "react developer"],
    "Data Analyst": ["data analyst", "business analyst", "reporting analyst", "bi analyst"],
    "DevOps Engineer": ["devops", "site reliability", "sre", "platform engineer", "infrastructure engineer"],
    "Full Stack Developer": ["full stack", "full-stack", "fullstack"],
}


def add_position(title: str, critical_skills: list, nice_to_have_skills: list = None) -> None:
    """
    Lets a company define its own open positions instead of only using
    the 6 built-in presets. Adds directly into TARGET_JOBS, so every
    existing function (compute_skill_gaps, detect_target_job) picks up
    company-defined positions automatically with no other changes needed.
    """
    nice_to_have_skills = nice_to_have_skills or []
    TARGET_JOBS[title] = (
        [{"skill": s.strip(), "priority": "critical"} for s in critical_skills if s.strip()]
        + [{"skill": s.strip(), "priority": "nice-to-have"} for s in nice_to_have_skills if s.strip()]
    )


NO_CLEAR_MATCH = "No clear match"


def detect_target_job(candidate_skills: list, profile_text: str, latest_job_title: str = "") -> str:
    """
    Guesses which role a candidate is targeting, so HR doesn't have to
    open every resume just to pick a dropdown value. This is a best-guess
    suggestion, not a hard classification.

    Two-step heuristic, in priority order:
      1. Keyword match against the profile summary + most recent job
         title (most direct signal - if someone's resume literally says
         "Backend Engineer", that's a strong hint).
      2. Fall back to whichever preset role the candidate's actual skills
         overlap with the most, if no keyword hint was found at all.

    FIX (found from real-resume testing): if a candidate has genuinely
    zero overlap with EVERY preset role (e.g. a manufacturing/aerospace
    engineer with no tech skills at all), the old fallback still picked
    "a best guess" - which meant always landing on whichever job happened
    to be first when every score tied at zero, making it look like a
    real role was detected when nothing was. This now returns
    NO_CLEAR_MATCH instead of pretending a specific role fits.
    """
    haystack = f"{profile_text} {latest_job_title}".lower()

    for job, keywords in ROLE_KEYWORDS.items():
        if any(kw in haystack for kw in keywords):
            # FIX (found from real-resume testing): a resume can mention a
            # role in passing - "coursework in machine learning", "AI
            # engineering" as a minor elective - without that actually
            # being the candidate's real background. Don't trust a
            # keyword hint alone if the candidate has ZERO actual skill
            # overlap with that role too; require at least some real
            # evidence before committing to it.
            check = compute_skill_gaps(candidate_skills, job)
            if check["skills_score"] > 0:
                return job

    best_job, best_score = None, -1
    best_matched_count = 0
    for job in sorted(TARGET_JOBS):  # alphabetical - deterministic, not just dict insertion order
        result = compute_skill_gaps(candidate_skills, job)
        if result["skills_score"] > best_score:
            best_job, best_score = job, result["skills_score"]
            best_matched_count = len(result["matched_skills"])

    # FIX (found from real-resume testing): one incidental skill match
    # (e.g. a controls engineer who happens to mention "Linux" once)
    # isn't real evidence someone is targeting that role - it produced a
    # confident-looking but essentially arbitrary guess. Require at
    # least 2 matched skills AND a meaningful score before committing to
    # a specific role; otherwise be upfront that nothing really fits.
    if best_matched_count < 2 or best_score < 0.3:
        return NO_CLEAR_MATCH

    return best_job


# ---------------------------------------------------------------------------
# Recovering skills that landed in the wrong section
# ---------------------------------------------------------------------------

# Every skill name that appears in any preset role's requirements - the
# known, correctly-cased vocabulary we actually score against.
def _all_known_skills() -> list:
    """Recomputed live (not cached) so company-added positions' skills are included too."""
    return sorted({req["skill"] for reqs in TARGET_JOBS.values() for req in reqs})


def _is_category_header(skill: str) -> bool:
    """
    Skills sections often have a category label on its own line (e.g.
    "LANGUAGES", "MACHINE / DEEP LEARNING") with no colon, which
    skills_extractor.py then treats as just another item since it can't
    tell a label apart from a real skill by text shape alone. This is a
    display-only filter (it doesn't touch what's used for scoring) that
    excludes the common category-header patterns so the "Top Skills"
    column shows actual skills, not section labels.
    """
    if skill.upper() != skill:
        return False  # real skill names are almost never pure uppercase multi-letter text
    words = skill.split()
    if len(words) >= 2:
        return True  # compound all-caps labels like "MACHINE / DEEP LEARNING"
    return skill.upper() in {
        "LANGUAGES", "TOOLS", "SKILLS", "TECHNOLOGIES", "FRAMEWORKS",
        "LIBRARIES", "PLATFORMS", "DATABASES", "OTHER", "NLP",
    }


def top_skills_for_display(candidate_skills: list, limit: int = 8, priority_skills: list = None) -> list:
    """
    priority_skills (typically the current target role's required skills)
    are shown first when present, so a genuinely relevant/matched skill
    never gets silently bumped off the visible list by less relevant
    ones just because of extraction order.
    """
    clean = [s for s in candidate_skills if not _is_category_header(s)]
    seen = set()
    deduped = []
    for s in clean:
        if s.lower() not in seen:
            seen.add(s.lower())
            deduped.append(s)

    if priority_skills:
        priority_lower = {p.lower() for p in priority_skills}
        prioritized = [s for s in deduped if s.lower() in priority_lower]
        rest = [s for s in deduped if s.lower() not in priority_lower]
        deduped = prioritized + rest

    return deduped[:limit]


def recover_skills_from_full_text(resume_text: str, existing_skills: list) -> list:
    """
    FIX (found during real-resume testing): on some resumes, a column-
    layout PDF puts the technical skill list in a sidebar that gets
    extracted out of order relative to its own "SKILLS" header (see
    column_aware_extract.py for the full explanation). When that
    happens, section_splitter.py attributes the real skill list to the
    wrong section entirely, and the dedicated skills extraction comes
    back empty or incomplete - even though the actual skill names are
    still sitting somewhere in the raw resume text, just under the
    wrong heading.

    This scans the ENTIRE resume text (not just whatever ended up under
    the "skills" section) for any of the known, scoreable skill names,
    and adds any found to the candidate's skill list. This doesn't
    invent anything - it only recovers skills that are genuinely present
    as literal text in the resume, recovering real signal that a section-
    boundary bug would otherwise have hidden from scoring entirely.
    """
    blob = resume_text.lower()
    existing_lower = {s.lower() for s in existing_skills}

    recovered = list(existing_skills)
    for skill in _all_known_skills():
        if skill.lower() in existing_lower:
            continue
        pattern = r"\b" + re.escape(skill.lower()) + r"\b"
        if re.search(pattern, blob):
            recovered.append(skill)

    return recovered
