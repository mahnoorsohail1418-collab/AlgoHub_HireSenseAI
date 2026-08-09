import json
import re
import os
import pdfplumber

from clean_text import clean_text
from section_detector import detect_sections


def extract_email(text):
    """Finds the first email address in the text using a regex pattern."""
    match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
    return match.group(0) if match else None


def extract_phone(text):
    """
    Finds the first phone number in the text.
    Handles common formats like:
    555-123-4567, (555) 123-4567, +1-555-123-4567, 555.123.4567
    """
    match = re.search(
        r'(\+?\d{1,2}[\s.-]?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}',
        text
    )
    return match.group(0).strip() if match else None


def extract_name(text):
    """
    Guesses the candidate's name by assuming it's the first non-empty line
    of the resume (which is true for most standard resume layouts).
    """
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    if lines:
        # Skip a line if it's clearly a label like "Resume:" from a template header
        for line in lines:
            if not line.lower().startswith("resume") and not line.lower().startswith("font"):
                return line
    return None


def parse_resume(pdf_path, page_number=None):
    """
    Runs the full pipeline on a single PDF resume:
    extract -> clean -> detect sections -> pull contact info -> build JSON

    If page_number is given (starting at 0), only that page is processed —
    useful when testing with a file that has multiple resumes bundled together.
    Otherwise, every page in the PDF is processed.
    """
    # Step 1: Extract text from the PDF
    with pdfplumber.open(pdf_path) as pdf:
        raw_text = ""
        pages_to_read = [pdf.pages[page_number]] if page_number is not None else pdf.pages
        for page in pages_to_read:
            page_text = page.extract_text()
            if page_text:
                raw_text += page_text + "\n"

    # Step 2: Clean the extracted text
    cleaned = clean_text(raw_text)

    # Step 3: Detect resume sections
    sections = detect_sections(cleaned)

    # Step 4: Pull out name, email, phone
    name = extract_name(cleaned)
    email = extract_email(cleaned)
    phone = extract_phone(cleaned)

    # Step 5: Build the final structured JSON
    result = {
        "file_name": os.path.basename(pdf_path),
        "name": name,
        "email": email,
        "phone": phone,
        "sections": {
            "summary": sections.get("professional_summary", ""),
            "education": sections.get("education", ""),
            "experience": sections.get("experience", ""),
            "skills": sections.get("technical_skills", ""),
            "projects": sections.get("projects", ""),
            "certifications": sections.get("certifications", ""),
        }
    }

    return result


if __name__ == "__main__":
    pdf_path = "sample_resume.pdf"

    # Using page_number=2 (page 3) since sample_resume.pdf has 17 bundled resumes
    # and page 3 is the first real, clean resume in it (no table of contents).
    # If you're using your own single-resume PDF, just remove page_number=2
    # so it processes the whole file instead.
    parsed_data = parse_resume(pdf_path, page_number=2)

    output_file = "resume_01.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(parsed_data, f, indent=2)

    print("Resume Parsed Successfully")
    print(f"Name: {parsed_data['name']}")
    print(f"Email: {parsed_data['email']}")
    print(f"Phone: {parsed_data['phone']}")
    print(f"Sections Found: {list(parsed_data['sections'].keys())}")
    print(f"Output Saved: {output_file}")
