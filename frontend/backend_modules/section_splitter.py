"""
section_splitter.py

Week 4, Module 1 (support file) - Raw Resume -> Section Dict

WHAT THIS DOES:
Bridges the gap between "one whole resume as text" (what you get out of
a PDF) and the raw_sections dict that candidate_profile.py expects:

    {
        "personal_info": "...",
        "education": "...",
        "experience": "...",
        "skills": "...",
        "projects": "...",
        "certifications": "...",
    }

APPROACH:
  1. "personal_info" is a special case: it's not marked by a header at
     all, it's simply whatever text comes BEFORE the first recognized
     section header (name, contact line, etc. always sit at the top).
  2. Every other section is found by scanning for a header keyword,
     either alone on its own line ("EXPERIENCE") or leading a line that
     also contains content ("Skills: Python, SQL...") - both styles were
     seen in the real resume batch during Task 5 testing, so both are
     handled here.
  3. Leading emoji/icon bullets (e.g. "🧩 PROJECTS") are stripped before
     matching, since some modern resume templates use them and they'd
     otherwise block every header match.
"""

import re
from typing import Dict

SECTION_HEADERS = {
    "education": [
        "education", "academic background", "academic history"
    ],
    "experience": [
        "experience", "work experience", "professional experience",
        "employment history", "career history", "internship",
        "internships", "internship experience"
    ],
    "skills": [
        "skills", "technical skills", "core competencies"
    ],
    "projects": [
        "projects", "personal projects", "academic projects", "key projects",
        "independent projects", "side projects", "key enterprise projects",
        "notable projects", "selected projects", "projects & research"
    ],
    "certifications": [
        "certifications", "certification", "certificates", "certificate",
        "licenses & certifications", "professional certifications"
    ],
}


def _collapse_letter_spacing(text: str) -> str:
    """
    Some resume PDF templates render section headers with visual letter
    spacing (e.g. "E X P E R I E N C E" instead of "EXPERIENCE"), which
    pdfplumber extracts with a literal space between every letter. Left
    as-is, "e x p e r i e n c e" will never match the keyword
    "experience", so the header - and the whole section under it - goes
    undetected. If a line is made up entirely of single-character tokens
    (ignoring blanks), this collapses those tokens back into words so
    normal keyword matching still works.
    """
    tokens = text.split(" ")
    letters = [t for t in tokens if t]
    if letters and all(len(t) == 1 for t in letters):
        return "".join(tokens)
    return text


def split_into_sections(resume_text: str) -> Dict[str, str]:
    """
    Splits a raw resume into the section dict candidate_profile.py needs.
    Any section not found is simply absent from the dict - the extractors
    and build_candidate_profile() already handle missing keys gracefully
    (they default to None/[]/{} rather than erroring).
    """
    lines = resume_text.splitlines()

    keyword_to_section = {}
    for section, keywords in SECTION_HEADERS.items():
        for kw in keywords:
            keyword_to_section[kw] = section
    sorted_keywords = sorted(keyword_to_section.keys(), key=len, reverse=True)

    # FIX: some templates letter-space headers unevenly (e.g. ligature/
    # kerning artifacts glue a pair of letters together, so "EDUCATION"
    # comes out as "E D U C AT I O N" - not perfectly one-space-per-letter).
    # _collapse_letter_spacing() only catches the perfectly even case, so
    # as a second-pass fallback, this compares the line and each keyword
    # with ALL whitespace stripped - "educ ation"/"e d u c at i o n" and
    # "education" both become "education", regardless of exactly where
    # the spaces landed.
    squished_keyword_to_section = {
        re.sub(r"\s+", "", kw): section for kw, section in keyword_to_section.items()
    }

    boundaries = []  # (line_index, section_name, inline_remainder_or_None)
    for i, line in enumerate(lines):
        clean = line.strip().lower().rstrip(":")
        clean = re.sub(r"^[^a-z0-9]+", "", clean)  # strip emoji/icon bullets
        clean = _collapse_letter_spacing(clean)

        if clean in keyword_to_section:
            boundaries.append((i, keyword_to_section[clean], None))
            continue

        squished = re.sub(r"\s+", "", clean)
        if squished and squished in squished_keyword_to_section:
            boundaries.append((i, squished_keyword_to_section[squished], None))
            continue

        for kw in sorted_keywords:
            if clean.startswith(kw + " "):
                remainder = line.strip()[len(kw):].strip(" :")
                boundaries.append((i, keyword_to_section[kw], remainder))
                break

    sections = {}

    # Personal info = everything before the first detected header
    first_boundary_line = boundaries[0][0] if boundaries else len(lines)
    personal_info = "\n".join(lines[:first_boundary_line]).strip()
    if personal_info:
        sections["personal_info"] = personal_info

    for idx, (start_line, section_name, inline_remainder) in enumerate(boundaries):
        end_line = boundaries[idx + 1][0] if idx + 1 < len(boundaries) else len(lines)
        body_lines = lines[start_line + 1:end_line]
        if inline_remainder:
            body_lines = [inline_remainder] + body_lines
        body = "\n".join(body_lines).strip()
        if section_name not in sections or len(body) > len(sections[section_name]):
            sections[section_name] = body

    return sections


if __name__ == "__main__":
    import json

    sample_resume = """
Mahnor Sohail
mahnor.sohail@example.com | +92 300 1234567 | linkedin.com/in/mahnorsohail

Education
BS Computer Science
FAST NUCES, 2024

Skills
Python, SQL, Pandas, Machine Learning, Git

Experience
ML Engineer at ABC Corp
Jan 2022 - Present
Built ML pipelines using Python, PyTorch and Docker for production models.

Projects
Resume Parser Tool
A Python tool that extracts structured data from resumes using regex and NLP.
https://github.com/example/resume-parser

Certifications
AWS Cloud Practitioner - AWS - 2026
Deep Learning Specialization - Coursera 2023
"""
    print(json.dumps(split_into_sections(sample_resume), indent=2))
