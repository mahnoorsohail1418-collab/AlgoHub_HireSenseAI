"""
projects_extractor.py

Week 4, Module 1, Task 2 - Extract Projects

WHAT THIS DOES:
Takes the raw text of a resume's Projects section (one project per block,
separated by a blank line) and pulls out, for each project:
  - name
  - date        (projects are usually a single date/season, not a range,
                  unlike jobs - so this is one field, not start/end)
  - description
  - technologies (a list)
  - links        (a list - resumes write these as bare URLs, "GitHub: ...",
                  "Link: ...", "Demo: ...", etc.)

APPROACH (builds on the same pattern as experience_extractor.py):
1. Split the section into blocks on blank lines.
2. The first line is the header (name + optional subtitle + date).
3. Pull the trailing "(...)" off the header as the date.
4. If the header has a "|" or " - ", the FIRST segment is the project
   name; a second segment (if present) is just extra context, folded
   into the description rather than dropped.
5. In the body, find any URLs (with or without an explicit "Link:" /
   "GitHub:" / "Demo:" label) and pull them out as links.
6. Find a "Technologies:" / "Tools:" / "Stack:" line the same way the
   experience extractor does.
"""

import json
import re

TRAILING_DATE_PATTERN = re.compile(r"\(([^)]+)\)\s*$")

TECH_LINE_PATTERN = re.compile(
    r"(Technologies|Tools|Stack)\s*:\s*(.+?)(?:\.|$)",
    re.IGNORECASE,
)

# FIX (found during testing): some resumes describe technologies in plain
# prose without a colon, e.g. "Built with Python and scikit-learn." - the
# colon-based pattern above missed this entirely, leaving technologies: []
# even though the tech names were right there in the text.
TECH_PROSE_PATTERN = re.compile(
    r"Built with\s+(.+?)(?:\.|$)",
    re.IGNORECASE,
)


def _split_tech_list(text: str) -> list:
    # Handles both "Python, spaCy, PyMuPDF" and "Python and scikit-learn"
    parts = re.split(r",|\band\b", text)
    return [p.strip() for p in parts if p.strip()]

# Matches bare URLs (github.com/x, myproject.vercel.app) as well as
# full https:// URLs, with an optional label like "GitHub:" or "Demo:"
# right before it (the label is captured so it can be stripped from the
# description too, but the label text itself isn't kept as part of the URL).
LINK_PATTERN = re.compile(
    r"(?:\b(?:Link|GitHub|Demo|Repo|Website)\s*:\s*)?"
    r"((?:https?://)?(?:[\w-]+\.)+(?:com|io|app|dev|net|org)(?:/[^\s,.]*)?)",
    re.IGNORECASE,
)


def _strip_bullet(line: str) -> str:
    return re.sub(r"^[\-\*\u2022]\s*", "", line.strip())


def parse_header(header: str) -> dict:
    header = _strip_bullet(header)
    date_match = TRAILING_DATE_PATTERN.search(header)
    if date_match:
        date = date_match.group(1).strip()
        header_no_date = header[:date_match.start()].strip()
    else:
        date = None
        header_no_date = header.strip()

    # FIX (found during testing): resumes commonly separate a project's
    # name from its description with an en dash ("Skintelli \u2013 Developing
    # a smart app..."), not just "|" or " - ". Checking " - " (hyphen)
    # before the en dash risked matching a hyphen that's actually PART of
    # the project name/subtitle (e.g. "Final Year Project - Phase I"),
    # cutting the name short. Preferring "|", then the en/em dash, then
    # falling back to " - " last avoids that.
    if "|" in header_no_date:
        parts = [p.strip() for p in header_no_date.split("|") if p.strip()]
    elif "\u2013" in header_no_date or "\u2014" in header_no_date:
        parts = [p.strip() for p in re.split(r"\s*[\u2013\u2014]\s*", header_no_date, maxsplit=1) if p.strip()]
    elif " - " in header_no_date:
        parts = [p.strip() for p in header_no_date.split(" - ") if p.strip()]
    else:
        parts = [header_no_date] if header_no_date else []

    name = parts[0] if parts else None
    context = parts[1] if len(parts) > 1 else None

    return {"name": name, "date": date, "context": context}


def parse_body(body: str) -> dict:
    # Links first, so their labels don't get mistaken for description text
    links = [m.group(1) for m in LINK_PATTERN.finditer(body)]
    body_no_links = LINK_PATTERN.sub("", body)

    tech_match = TECH_LINE_PATTERN.search(body_no_links)
    technologies = []
    description = body_no_links

    if tech_match:
        technologies = _split_tech_list(tech_match.group(2))
        description = (body_no_links[:tech_match.start()] + body_no_links[tech_match.end():]).strip()
    else:
        prose_match = TECH_PROSE_PATTERN.search(body_no_links)
        if prose_match:
            technologies = _split_tech_list(prose_match.group(1))
            description = (body_no_links[:prose_match.start()] + body_no_links[prose_match.end():]).strip()

    description = re.sub(r"\s+", " ", description).strip(" .")

    return {"description": description, "technologies": technologies, "links": links}


def parse_project_block(block: str) -> dict:
    lines = [l for l in block.strip().split("\n") if l.strip()]
    if not lines:
        return None

    header = lines[0]
    body = " ".join(lines[1:]).strip()

    result = parse_header(header)
    body_parsed = parse_body(body)

    # Fold the header's "context" segment (if any) into the description
    # rather than dropping it, since the task only asks for name/
    # description/technologies/links - not a separate subtitle field.
    if result["context"]:
        body_parsed["description"] = f"{result['context']}. {body_parsed['description']}".strip(" .")
    del result["context"]

    result.update(body_parsed)
    return result


def extract_projects(raw_text: str) -> list:
    text = raw_text.strip()
    if not text:
        return []

    blocks = re.split(r"\n\s*\n", text)

    # FIX (found during testing): some resumes' PDF-to-text conversion
    # drops the blank line between projects entirely, merging several
    # bullet-marked projects into a single block (with only the first
    # project recognized and the rest dumped into its description).
    # Unlike jobs, individual projects here don't carry their own date,
    # so fall back to splitting on bullet markers instead of date-range
    # lines.
    #
    # Two bullet fallbacks, tried in order:
    #  1. Bullet at the start of a line (the common case).
    #  2. Bullet character ANYWHERE in the text, even glued onto the end
    #     of the previous sentence with no line break at all (seen in
    #     real PDFs, e.g. "...via GitHub.\u2022 Python: Facial Emotion...") --
    #     "\u2022" specifically is safe to split on anywhere since it never
    #     legitimately appears mid-sentence, unlike "-" or "*".
    if len(blocks) == 1:
        text_bullet_positions = [m.start() for m in re.finditer(r"\u2022", text)]
        if len(text_bullet_positions) > 1:
            # Prefer this: catches every "\u2022", including ones glued onto
            # the end of the previous sentence with no line break at all.
            blocks = []
            for idx, start in enumerate(text_bullet_positions):
                end = text_bullet_positions[idx + 1] if idx + 1 < len(text_bullet_positions) else len(text)
                blocks.append(text[start:end])
        else:
            # Fallback for resumes using "-" or "*" as bullets instead of
            # "\u2022" -- less safe to match anywhere, so only at line-start.
            lines = text.splitlines()
            bullet_line_indices = [
                i for i, line in enumerate(lines) if re.match(r"^\s*[\-\*]", line)
            ]
            if len(bullet_line_indices) > 1:
                blocks = []
                for idx, start in enumerate(bullet_line_indices):
                    end = bullet_line_indices[idx + 1] if idx + 1 < len(bullet_line_indices) else len(lines)
                    blocks.append("\n".join(lines[start:end]))

    results = []
    for block in blocks:
        parsed = parse_project_block(block)
        if parsed:
            results.append(parsed)
    return results


def run_tests(data_path: str = "projects_test_data.json"):
    with open(data_path, "r") as f:
        data = json.load(f)

    for case in data["test_cases"]:
        print(f"\n=== {case['resume_id']} ===")
        projects = extract_projects(case["raw_projects_text"])
        for p in projects:
            print(f"  Name: {p['name']}   Date: {p['date']}")
            print(f"    Technologies: {p['technologies']}")
            print(f"    Links: {p['links']}")
            print(f"    Description: {p['description'][:90]}...")


if __name__ == "__main__":
    run_tests()
