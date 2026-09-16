"""
personal_info_extractor.py

Week 4, Module 1, Task 4 (support) - Extract Personal Information

WHAT THIS DOES:
Takes the raw text of a resume's header/contact block (usually the top
2-3 lines of a resume, NOT separated into per-item blocks like the other
sections) and pulls out:
  - name
  - email
  - phone
  - location    (city/state - free text, since resumes format this many
                  different ways)
  - linkedin
  - github
  - portfolio   (catch-all for any other personal site/URL found)

APPROACH:
Unlike experience/projects/certifications, this section isn't a list of
repeated blocks - it's usually one small chunk of text with the name on
its own line and everything else (email, phone, location, links) mixed
together on one or two "contact lines" separated by "|", "•", or ",".
So instead of block-splitting, this:
  1. Treats the FIRST non-empty line as the name (resumes consistently
     put the candidate's name first, before any contact details).
  2. Runs targeted regexes for email/phone/linkedin/github over the
     REST of the text, since these have very recognizable shapes.
  3. Whatever text is left after removing the name line and all matched
     fields is treated as "location" (with separators cleaned up) - this
     mirrors how the other extractors treat "leftover text" as
     description, since resumes don't label the city/state explicitly.
"""

import json
import re

EMAIL_PATTERN = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")

# Phone numbers show up as (555) 123-4567, 555-123-4567, 555.123.4567,
# or with a country code like +1 555-123-4567.
PHONE_PATTERN = re.compile(
    r"(?:\+\d{1,2}\s*)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}"
)

LINKEDIN_PATTERN = re.compile(r"(?:https?://)?(?:www\.)?linkedin\.com/[^\s,|•]+", re.IGNORECASE)
GITHUB_PATTERN = re.compile(r"(?:https?://)?(?:www\.)?github\.com/[^\s,|•]+", re.IGNORECASE)

# Any other bare URL/domain that isn't linkedin or github - treated as a
# portfolio/personal site link (e.g. "janedoe.dev", "myportfolio.com").
OTHER_URL_PATTERN = re.compile(
    r"(?:https?://)?(?:www\.)?(?:[\w-]+\.)+(?:com|io|app|dev|net|org|me)(?:/[^\s,|•]*)?",
    re.IGNORECASE,
)


def _clean_leftover(text: str) -> str:
    text = re.sub(r"[|•]", ",", text)
    text = re.sub(r"\s*,\s*", ", ", text)
    text = text.strip(" ,")
    return text if text else None


def extract_personal_info(raw_text: str) -> dict:
    lines = [l.strip() for l in raw_text.strip().split("\n") if l.strip()]
    if not lines:
        return {
            "name": None, "email": None, "phone": None,
            "location": None, "linkedin": None, "github": None,
            "portfolio": None,
        }

    name = lines[0]
    rest = " ".join(lines[1:])

    email_match = EMAIL_PATTERN.search(rest)
    email = email_match.group(0) if email_match else None
    if email_match:
        rest = rest[:email_match.start()] + rest[email_match.end():]

    linkedin_match = LINKEDIN_PATTERN.search(rest)
    linkedin = linkedin_match.group(0) if linkedin_match else None
    if linkedin_match:
        rest = rest[:linkedin_match.start()] + rest[linkedin_match.end():]

    github_match = GITHUB_PATTERN.search(rest)
    github = github_match.group(0) if github_match else None
    if github_match:
        rest = rest[:github_match.start()] + rest[github_match.end():]

    phone_match = PHONE_PATTERN.search(rest)
    phone = phone_match.group(0).strip() if phone_match else None
    if phone_match:
        rest = rest[:phone_match.start()] + rest[phone_match.end():]

    # Anything left that still looks like a URL (a portfolio/personal
    # site) after linkedin/github/email have already been pulled out.
    portfolio_match = OTHER_URL_PATTERN.search(rest)
    portfolio = portfolio_match.group(0).strip() if portfolio_match else None
    if portfolio_match:
        rest = rest[:portfolio_match.start()] + rest[portfolio_match.end():]

    location = _clean_leftover(rest)

    return {
        "name": name,
        "email": email,
        "phone": phone,
        "location": location,
        "linkedin": linkedin,
        "github": github,
        "portfolio": portfolio,
    }


def run_tests(data_path: str = "personal_info_test_data.json"):
    with open(data_path, "r") as f:
        data = json.load(f)

    for case in data["test_cases"]:
        print(f"\n=== {case['resume_id']} ===")
        info = extract_personal_info(case["raw_personal_info_text"])
        for key, value in info.items():
            print(f"  {key}: {value}")


if __name__ == "__main__":
    run_tests()
