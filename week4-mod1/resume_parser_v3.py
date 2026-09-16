"""
resume_parser_v3.py
Week 4 - Module 1, Tasks 1-3 (combined entry point)

This is a thin wrapper, not a re-implementation. Your actual Task 1-3
logic already lives in your own files:
    - experience_extractor.py      (Task 1)
    - projects_extractor.py        (Task 2)
    - certification_extractor.py   (Task 3)

This file exists only because the assignment deliverables list names a
single "resume_parser_v3.py" file. Rather than duplicate your extraction
logic in a second place (which would risk the two copies drifting apart),
this just imports your three real extractors and exposes one combined
function, parse_resume(), that runs all three against a raw resume.

If asked to explain "resume_parser_v3.py" for this assignment, the honest
answer is: it's the combination of experience_extractor.py +
projects_extractor.py + certification_extractor.py, wired together here
and (for the full profile, including education/skills/personal info) in
candidate_profile.py.
"""

from typing import Dict

from section_splitter import split_into_sections
from experience_extractor import extract_experience
from projects_extractor import extract_projects
from certification_extractor import extract_certifications


def parse_resume(resume_text: str) -> Dict:
    """
    Runs Tasks 1-3 against a raw resume: splits it into sections, then
    extracts experience, projects, and certifications from each.
    """
    sections = split_into_sections(resume_text)
    return {
        "experience": extract_experience(sections.get("experience", "")),
        "projects": extract_projects(sections.get("projects", "")),
        "certifications": extract_certifications(sections.get("certifications", "")),
    }


if __name__ == "__main__":
    import json

    sample_resume = """
Mahnor Sohail
mahnor.sohail@example.com | +92 300 1234567

Experience
ML Engineer, ABC Corp (2022 - Present)
Built ML pipelines using Python, PyTorch and Docker for production models.
Technologies: Python, PyTorch, Docker

Projects
Resume Parser Tool (2024)
A Python tool that extracts structured data from resumes using regex and NLP.
Technologies: Python, spaCy
https://github.com/example/resume-parser

Certifications
AWS Cloud Practitioner - AWS - 2026
Deep Learning Specialization - Coursera - 2023
"""
    result = parse_resume(sample_resume)
    print(json.dumps(result, indent=2))
