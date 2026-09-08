# AI Career Roadmap Generator v1 — Input/Output Design

## Task 1: Design the AI Output

This defines the contract between the rest of the system and the LLM-powered
roadmap generator. Every later task (prompts, JSON schema, personalized
roadmap, resource recommendations) is built against this design.

---

## INPUT — what the system receives

**1. Candidate Profile**
From `candidate_profile.py` (Module 1) — education, skills, experience,
projects, certifications.

**2. ATS Analysis**
From the ATS Score v2 engine (Week 3, `ats_engine_v2.py`) — the skills,
experience, semantic, and education sub-scores plus the final combined
score, for the candidate against their target job.

**3. Missing Skills**
From `skill_gap_engine.py` (Week 3) — critical_gaps (missing required
skills) and nice_to_have_gaps (missing preferred skills).

**4. Career Goal**
A new input, not produced by any earlier module — the candidate's own
stated target (e.g. "Data Analyst", "Senior Software Engineer",
"transition into Product Management"). This is what makes the roadmap
personalized to what the candidate actually wants, not just what one job
posting says.

---

## OUTPUT — what the system must produce

**1. Career Assessment**
A short narrative summary of where the candidate stands overall, relative
to their stated career goal.

**2. Current Level**
Entry-level / Junior / Mid-level / Senior — based on years of experience
and how many required skills are already met.

**3. Skill Gaps**
The missing skills, restated in plain language the candidate can act on
(pulled directly from the Missing Skills input, not re-derived by the AI).

**4. Priority Skills**
Which of the skill gaps to tackle FIRST — critical gaps take priority over
nice-to-have gaps, inherited directly from Week 3's categorization.

**5. Learning Roadmap**
An ordered, step-by-step plan for closing the priority skill gaps.

**6. Recommended Resources**
Specific courses/resources for each roadmap step, pulled from a verified
resource database (Task 5) — not invented.

**7. Resume Improvements**
Concrete suggestions for how the candidate could improve their resume itself
(e.g. missing a projects section, no quantified achievements, a
certification worth adding) — this is new: earlier modules score and gap-
check the resume, but nothing until now gives the candidate feedback on the
resume as a document.

**8. Next Steps**
A short, concrete action list — what to do this week, not a long-term plan.

---

## Why this shape

- **Career Goal as an input** matters because it's the one piece of context
  no earlier module has — Week 3's ATS engine only knows about ONE specific
  job posting; Career Goal lets the roadmap speak to the candidate's actual
  direction, which may be broader than one posting.
- **Skill Gaps and Priority Skills are inherited from Week 3, not
  regenerated** — the AI explains and sequences already-verified gaps
  rather than re-discovering them, which is what makes Task 6's
  hallucination testing meaningful (less room for the AI to invent problems
  that don't exist).
- **Resume Improvements is new territory** — Modules 1-3 so far have only
  ever scored or extracted from the resume; this is the first output that
  gives the candidate direct, actionable feedback on the document itself.
- **Distinct labeled fields** (rather than one free-text response) is what
  makes Task 3's structured JSON schema possible — the backend can render
  each section separately in the UI instead of parsing free text.
