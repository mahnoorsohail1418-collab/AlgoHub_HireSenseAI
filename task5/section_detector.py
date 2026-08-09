import re

# Common section headings and the alternate names they might appear as in a resume.
# The key is the "standard" name we'll use, the list is words/phrases that count as
# a match for that section.
SECTION_HEADINGS = {
    "contact_information": ["contact", "contact information", "contact info"],
    "professional_summary": ["summary", "professional summary", "profile", "about me", "objective"],
    "education": ["education", "academic background"],
    "experience": ["experience", "professional experience", "work experience",
                   "employment history", "work history"],
    "technical_skills": ["skills", "technical skills", "core competencies", "key skills"],
    "projects": ["projects", "project experience"],
    "certifications": ["certifications", "certificates", "licenses", "certification"],
}


def is_heading(line, headings_dict):
    """
    Checks if a line looks like one of our known section headings.
    Returns the standard section name if it matches, otherwise None.
    A line counts as a heading if:
      - it's short (headings are usually just 1-4 words, not full sentences)
      - once lowercased and stripped of punctuation, it matches one of our known names
    """
    clean_line = re.sub(r'[^a-zA-Z ]', '', line).strip().lower()

    if len(clean_line.split()) > 5:
        return None  # too long to be a heading, probably a normal sentence

    for standard_name, variants in headings_dict.items():
        if clean_line in variants:
            return standard_name

    return None


def detect_sections(text):
    """
    Goes through the resume text line by line and splits it into sections
    based on recognized headings. Returns a dictionary like:
    {
        "professional_summary": "...",
        "education": "...",
        "experience": "...",
        ...
    }
    Any text before the first recognized heading is stored under "header"
    (this is usually the name/contact info at the top of the resume).
    """
    lines = text.split('\n')
    sections = {}
    current_section = "header"
    sections[current_section] = []

    for line in lines:
        heading_match = is_heading(line, SECTION_HEADINGS)
        if heading_match:
            current_section = heading_match
            if current_section not in sections:
                sections[current_section] = []
        else:
            sections[current_section].append(line)

    # Join each section's lines back into a single block of text
    for section in sections:
        sections[section] = '\n'.join(sections[section]).strip()

    return sections


if __name__ == "__main__":
    input_file = "resume_01_cleaned.txt"

    with open(input_file, "r", encoding="utf-8") as f:
        text = f.read()

    sections = detect_sections(text)

    print("Sections Detected:", len(sections))
    print("-" * 40)
    for section_name, content in sections.items():
        print(f"\n=== {section_name.upper()} ===")
        preview = content[:200] + "..." if len(content) > 200 else content
        print(preview if preview else "(empty)")

    # Also save the detected sections into a text file for easy checking
    with open("sections_detected.txt", "w", encoding="utf-8") as f:
        for section_name, content in sections.items():
            f.write(f"=== {section_name.upper()} ===\n")
            f.write(content + "\n\n")

    print("\nOutput Saved: sections_detected.txt")
