"""
semantic_matcher_v2.py

Task 1 - Improve Semantic Matching

WHAT CHANGED FROM WEEK 2's similarity_engine.py:
Week 2 compared the ENTIRE resume text against the ENTIRE job description
text as one big blob, using a single embedding for each. That's "blind"
comparison - a resume's Education section could accidentally boost
similarity to a job's Responsibilities section just because they happen
to share generic words, even if the actual SKILLS don't match at all.

This version breaks both documents into COMPONENTS first:
  - skills        (resume skills list  vs  JD required + preferred skills)
  - experience     (resume job bullets  vs  JD responsibilities/description)
  - education      (resume degree/field  vs  JD required education)

Each component pair gets its OWN embedding + cosine similarity score.
Then we combine the three component scores into one overall semantic
score using documented weights.

WEIGHTING RULE (documented):
  skills:     0.4   (most predictive of fit for most roles)
  experience: 0.4   (equally predictive - what they've actually DONE)
  education:  0.2   (less predictive on its own - many roles care more
                      about skills/experience than the specific degree)

These weights are a starting judgment call, same as the ones used in
skill_matcher.py and education_matcher.py - meant to be tuned later
based on Task 7's evaluation against human labels.
"""

import json
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# Load the model ONCE at module level (reused from Week 2's choice of model)
# so we don't reload it for every single comparison - reloading it per call
# would be extremely slow.
_model = SentenceTransformer("all-MiniLM-L6-v2")


# ---------------------------------------------------------------------------
# Step 1: break the resume and job description into comparable components
# ---------------------------------------------------------------------------

def get_resume_components(resume: dict) -> dict:
    skills_text = ", ".join(resume.get("skills", []))

    experience_bullets = []
    for job in resume.get("experience", []):
        experience_bullets.append(job.get("title", ""))
        experience_bullets.extend(job.get("bullets", []))
    experience_text = ". ".join(experience_bullets)

    education = resume.get("education", [{}])[0]
    education_text = f"{education.get('degree', '')} in {education.get('field', '')}"

    return {
        "skills": skills_text,
        "experience": experience_text,
        "education": education_text,
    }


def get_job_components(job_description: dict) -> dict:
    all_skills = job_description.get("required_skills", []) + job_description.get("preferred_skills", [])
    skills_text = ", ".join(all_skills)

    responsibilities = job_description.get("responsibilities", [])
    description = job_description.get("description", "")
    experience_text = description + ". " + ". ".join(responsibilities)

    required_edu = job_description.get("required_education", {})
    education_text = f"{required_edu.get('degree_level', '')} in {required_edu.get('field', '')}"

    return {
        "skills": skills_text,
        "experience": experience_text,
        "education": education_text,
    }


# ---------------------------------------------------------------------------
# Step 2: cosine similarity between one resume component and one JD component
# ---------------------------------------------------------------------------

def component_similarity(text_a: str, text_b: str) -> float:
    if not text_a.strip() or not text_b.strip():
        return 0.0

    embeddings = _model.encode([text_a, text_b])
    score = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
    return round(float(score), 3)


# ---------------------------------------------------------------------------
# Step 3: combine component scores into one weighted semantic score
# ---------------------------------------------------------------------------

WEIGHTS = {
    "skills": 0.4,
    "experience": 0.4,
    "education": 0.2,
}


def semantic_match(resume: dict, job_description: dict) -> dict:
    resume_parts = get_resume_components(resume)
    job_parts = get_job_components(job_description)

    component_scores = {}
    for component in ("skills", "experience", "education"):
        component_scores[component] = component_similarity(
            resume_parts[component], job_parts[component]
        )

    final_score = round(
        sum(WEIGHTS[c] * component_scores[c] for c in component_scores),
        3,
    )

    explanation = (
        f"Skills similarity: {component_scores['skills']} (weight {WEIGHTS['skills']}). "
        f"Experience similarity: {component_scores['experience']} (weight {WEIGHTS['experience']}). "
        f"Education similarity: {component_scores['education']} (weight {WEIGHTS['education']}). "
        f"Final semantic score = {final_score}."
    )

    return {
        "score": final_score,
        "component_scores": component_scores,
        "explanation": explanation,
    }


# ---------------------------------------------------------------------------
# Step 4: test against the 3 sample pairs
# ---------------------------------------------------------------------------

def run_tests(data_path: str = "ats_test_data.json"):
    with open(data_path, "r") as f:
        data = json.load(f)

    for pair in data["pairs"]:
        result = semantic_match(pair["resume"], pair["job_description"])
        print(f"\n=== {pair['pair_id']} (expected: {pair['expected_match_quality']}) ===")
        print(f"Score: {result['score']}")
        print(f"  component_scores: {result['component_scores']}")
        print(f"  {result['explanation']}")


if __name__ == "__main__":
    run_tests()
