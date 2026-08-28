"""
education_matcher.py

Task 4 - Education Matching

SCORING RULE (documented, as required):
Education match is split into two independent sub-scores, then combined:

  1. LEVEL SCORE (50% weight)
     Does the candidate's degree meet or exceed the level the job requires?
     Levels are ranked: high school (0) < associate (1) < bachelor's (2)
     < master's (3) < phd (4).
       - Meets or exceeds required level -> 1.0
       - Exactly one level below required -> 0.5 (partial credit - close, but
         under-qualified on paper; many real postings still accept this)
       - Two or more levels below required -> 0.0

  2. FIELD SCORE (50% weight)
     Is the candidate's field of study relevant to what the job wants?
     We compare keyword overlap between the resume's field and the job's
     required field (after removing common filler words like "and", "or",
     "related", "field", "science", "in", "of", "the").
       - 2 or more shared meaningful keywords -> 1.0 (strong match)
       - exactly 1 shared meaningful keyword   -> 0.5 (related field)
       - 0 shared meaningful keywords          -> 0.0 (unrelated field)

FINAL SCORE = 0.5 * level_score + 0.5 * field_score

We weight level and field equally on purpose: a candidate who is
under-qualified on paper but in the right field is roughly as much of a risk
as a candidate who has the right degree level but is in a totally unrelated
field. Neither factor alone should dominate the decision.
"""

import json

# ---------------------------------------------------------------------------
# Step 2: degree-level ranking
# ---------------------------------------------------------------------------

DEGREE_RANK = {
    "high school": 0,
    "associate": 1,
    "bachelor's": 2,
    "master's": 3,
    "phd": 4,
}

# Words we ignore when comparing "field of study" strings, so that pure
# filler words don't accidentally count as a "match". NOTE: we deliberately
# do NOT strip domain words like "science" or "management" - a first attempt
# at this stripped them out and it flattened every field_score to look the
# same (see write-up below), so only true connector/filler words go here.
STOPWORDS = {
    "and", "or", "related", "field", "fields", "in", "of", "the", "a",
}


def normalize_degree(degree_string: str) -> str:
    """
    Map messy resume/job text like 'Bachelor of Science' or "Master's degree"
    down to one of the canonical keys in DEGREE_RANK.
    Falls back to 'bachelor's' if nothing is recognized, since that's the
    most common minimum requirement - avoids crashing on unexpected input.
    """
    text = degree_string.lower()

    if "phd" in text or "ph.d" in text or "doctor" in text:
        return "phd"
    if "master" in text:
        return "master's"
    if "bachelor" in text:
        return "bachelor's"
    if "associate" in text:
        return "associate"
    if "high school" in text:
        return "high school"

    return "bachelor's"  # safe default


# ---------------------------------------------------------------------------
# Step 3: level-match function
# ---------------------------------------------------------------------------

def level_score(resume_degree: str, required_level: str) -> float:
    resume_key = normalize_degree(resume_degree)
    required_key = normalize_degree(required_level)

    resume_rank = DEGREE_RANK[resume_key]
    required_rank = DEGREE_RANK[required_key]

    gap = required_rank - resume_rank

    if gap <= 0:
        return 1.0   # meets or exceeds requirement
    elif gap == 1:
        return 0.5   # one level short
    else:
        return 0.0   # two or more levels short


# ---------------------------------------------------------------------------
# Step 4: field-relevance function
# ---------------------------------------------------------------------------

def _keywords(text: str) -> set:
    # Strip punctuation (commas, slashes, parentheses) so words like
    # "(Economics)" match plain "economics".
    for ch in [",", "/", "(", ")"]:
        text = text.replace(ch, " ")
    words = text.lower().split()
    return {w for w in words if w not in STOPWORDS and len(w) > 2}


def field_score(resume_field: str, required_field: str) -> float:
    """
    v2 rule (fixed after testing revealed a flaw): instead of a raw shared-
    word COUNT (which scored an exact 1-word match, e.g. "Marketing" vs
    "Marketing", the same as a coincidental 1-word overlap between two
    unrelated fields, e.g. "Agribusiness Economics" vs "Data Science...
    Economics"), we now score the overlap as a PERCENTAGE of the smaller
    field's keyword set. A short, exact field name can now reach a full
    1.0, while a long field name that only coincidentally shares one word
    out of many is correctly scored low.
    """
    resume_kw = _keywords(resume_field)
    required_kw = _keywords(required_field)

    if not resume_kw or not required_kw:
        return 0.0

    shared = resume_kw & required_kw
    smaller_set_size = min(len(resume_kw), len(required_kw))

    return round(len(shared) / smaller_set_size, 3)


# ---------------------------------------------------------------------------
# Step 5: combined education_match() function
# ---------------------------------------------------------------------------

def education_match(resume: dict, job_description: dict) -> dict:
    # Use the candidate's highest / most recent listed degree (first entry)
    resume_edu = resume["education"][0]
    required_edu = job_description["required_education"]

    lvl_score = level_score(resume_edu["degree"], required_edu["degree_level"])
    fld_score = field_score(resume_edu["field"], required_edu["field"])

    final_score = round(0.5 * lvl_score + 0.5 * fld_score, 3)

    explanation = (
        f"Resume degree: '{resume_edu['degree']}' in '{resume_edu['field']}'. "
        f"Required: '{required_edu['degree_level']}' in '{required_edu['field']}'. "
        f"Level score = {lvl_score} (degree level vs. requirement), "
        f"Field score = {fld_score} (keyword overlap in field of study). "
        f"Final education score = {final_score}."
    )

    return {
        "score": final_score,
        "level_score": lvl_score,
        "field_score": fld_score,
        "explanation": explanation,
    }


# ---------------------------------------------------------------------------
# Step 6: test against the 3 sample pairs
# ---------------------------------------------------------------------------

def run_tests(data_path: str = "ats_test_data.json"):
    with open(data_path, "r") as f:
        data = json.load(f)

    for pair in data["pairs"]:
        result = education_match(pair["resume"], pair["job_description"])
        print(f"\n=== {pair['pair_id']} (expected: {pair['expected_match_quality']}) ===")
        print(f"Score: {result['score']}")
        print(f"  level_score: {result['level_score']}, field_score: {result['field_score']}")
        print(f"  {result['explanation']}")


if __name__ == "__main__":
    run_tests()
