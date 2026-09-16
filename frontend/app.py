"""
app.py

HireSense AI - HR screening demo backend.

WORKFLOW:
  1. POST /api/analyze-bulk   - upload multiple resumes at once. Runs ONLY
     Module 1 parsing + skill-gap scoring + role auto-detection for every
     candidate. Zero AI calls here - purely deterministic, so this is
     instant and safe no matter how many resumes are uploaded at once.
     Returns a ranked table of candidates.
  2. POST /api/rescore/<id>  - if HR overrides the auto-detected role for
     a candidate, recompute their score/gaps against the new role. Also
     zero AI calls.
  3. POST /api/reject/<id>   - ONLY when HR actually rejects a specific
     candidate does this call the real roadmap generator (the ~4 AI
     calls happen here, one candidate at a time) and build a ready-to-
     send rejection message from the result.

Candidate data lives in a simple in-memory dict for the lifetime of the
demo session - there's no database, this is a local single-session tool.
"""

import os
import sys
import traceback
import uuid

from flask import Flask, jsonify, request, send_from_directory

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend_modules"))

from section_splitter import split_into_sections              # noqa: E402
from candidate_profile import build_candidate_profile           # noqa: E402
from target_jobs import TARGET_JOBS, compute_skill_gaps, detect_target_job, recover_skills_from_full_text, top_skills_for_display, NO_CLEAR_MATCH, add_position  # noqa: E402
from profile_adapter import to_module2_profile                   # noqa: E402
from fast_pipeline import generate_roadmap_fast                   # noqa: E402
from roadmap_generator import MOCK_MODE                           # noqa: E402
from rejection_message import build_rejection_message              # noqa: E402
from selection_message import build_selection_message                # noqa: E402
from column_aware_extract import extract_column_aware_text          # noqa: E402

try:
    import pdfplumber
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False

app = Flask(__name__, static_folder="static", template_folder="templates")
app.config["MAX_CONTENT_LENGTH"] = 40 * 1024 * 1024  # 40 MB total upload limit

# In-memory candidate store for this demo session.
CANDIDATES = {}


def _extract_text(file_storage) -> str:
    filename = file_storage.filename.lower()
    if filename.endswith(".txt"):
        return file_storage.read().decode("utf-8", errors="ignore")
    if filename.endswith(".pdf"):
        if not PDF_SUPPORT:
            raise RuntimeError("PDF support isn't installed on the server (pip install pdfplumber).")
        with pdfplumber.open(file_storage) as pdf:
            return extract_column_aware_text(pdf)
    raise ValueError("Only .pdf or .txt resumes are supported.")


def _score_candidate(candidate_id: str, target_job: str) -> dict:
    entry = CANDIDATES[candidate_id]
    m2_profile = entry["module2_profile"]
    candidate_skills = entry["candidate_skills"]

    if target_job == NO_CLEAR_MATCH:
        # Genuinely no overlap with any tracked role - report that
        # honestly instead of scoring against an arbitrary fallback role.
        gap_result = {"matched_skills": [], "skill_gaps": [], "skills_score": None, "final_score": None}
    else:
        gap_result = compute_skill_gaps(candidate_skills, target_job)

    entry["target_job"] = target_job
    entry["gap_result"] = gap_result

    return {
        "candidate_id": candidate_id,
        "name": m2_profile["name"],
        "years_experience": m2_profile["years_experience"],
        "target_job": target_job,
        "final_score": gap_result["final_score"],
        "skills_score": gap_result["skills_score"],
        "matched_skills": gap_result["matched_skills"],
        "skill_gaps": gap_result["skill_gaps"],
        "top_skills": top_skills_for_display(candidate_skills, priority_skills=[r["skill"] for r in TARGET_JOBS.get(target_job, [])]),
        "status": entry.get("status", "pending"),
    }


@app.route("/")
def index():
    return send_from_directory("templates", "index.html")


@app.route("/api/target-jobs", methods=["GET"])
def target_jobs():
    jobs_detail = [
        {"title": title, "skills": reqs}
        for title, reqs in TARGET_JOBS.items()
    ]
    return jsonify({"jobs": list(TARGET_JOBS.keys()), "jobs_detail": jobs_detail, "mock_mode": MOCK_MODE})


@app.route("/api/positions", methods=["POST"])
def create_position():
    data = request.get_json(force=True, silent=True) or {}
    title = (data.get("title") or "").strip()
    critical = data.get("critical_skills") or []
    nice_to_have = data.get("nice_to_have_skills") or []

    if not title:
        return jsonify({"error": "Position title is required."}), 400
    if not critical and not nice_to_have:
        return jsonify({"error": "Add at least one required skill."}), 400
    if title in TARGET_JOBS:
        return jsonify({"error": f'"{title}" already exists.'}), 400

    add_position(title, critical, nice_to_have)
    return jsonify({"title": title, "skills": TARGET_JOBS[title]})


@app.route("/api/analyze-bulk", methods=["POST"])
def analyze_bulk():
    files = request.files.getlist("resumes")
    if not files:
        return jsonify({"error": "No resumes were uploaded."}), 400

    results = []
    errors = []

    for file_storage in files:
        try:
            resume_text = _extract_text(file_storage)
            if not resume_text.strip():
                errors.append({"filename": file_storage.filename, "error": "Couldn't read any text from this file."})
                continue

            sections = split_into_sections(resume_text)
            profile = build_candidate_profile(sections)
            m2_profile = to_module2_profile(profile)
            candidate_skills = profile.get("skills", {}).get("all_skills", [])
            candidate_skills = recover_skills_from_full_text(resume_text, candidate_skills)

            latest_title = ""
            if profile.get("career_history"):
                latest_title = profile["career_history"][0].get("job_title", "") or ""
            profile_text = sections.get("personal_info", "")

            suggested_job = detect_target_job(candidate_skills, profile_text, latest_title)

            candidate_id = str(uuid.uuid4())
            CANDIDATES[candidate_id] = {
                "module1_profile": profile,
                "module2_profile": m2_profile,
                "candidate_skills": candidate_skills,
                "resume_filename": file_storage.filename,
                "status": "pending",
            }

            results.append(_score_candidate(candidate_id, suggested_job))

        except Exception as exc:  # noqa: BLE001
            traceback.print_exc()
            errors.append({"filename": getattr(file_storage, "filename", "unknown"), "error": str(exc)})

    results.sort(key=lambda r: r["final_score"] if r["final_score"] is not None else -1, reverse=True)
    return jsonify({"candidates": results, "errors": errors, "mock_mode": MOCK_MODE})


@app.route("/api/rescore/<candidate_id>", methods=["POST"])
def rescore(candidate_id):
    if candidate_id not in CANDIDATES:
        return jsonify({"error": "Unknown candidate - try re-uploading."}), 404

    target_job = request.json.get("target_job") if request.is_json else request.form.get("target_job")
    if target_job not in TARGET_JOBS:
        return jsonify({"error": "Please choose a valid target role."}), 400

    return jsonify(_score_candidate(candidate_id, target_job))


@app.route("/api/select/<candidate_id>", methods=["POST"])
def select_candidate(candidate_id):
    if candidate_id not in CANDIDATES:
        return jsonify({"error": "Unknown candidate - try re-uploading."}), 404

    entry = CANDIDATES[candidate_id]
    entry["status"] = "selected"

    m2_profile = entry["module2_profile"]
    target_job = entry.get("target_job", "")
    matched_skills = entry.get("gap_result", {}).get("matched_skills", [])

    message = build_selection_message(m2_profile["name"], target_job, matched_skills)
    entry["selection_message"] = message

    return jsonify({"candidate_id": candidate_id, "status": "selected", "selection_message": message})


@app.route("/api/reject/<candidate_id>", methods=["POST"])
def reject_candidate(candidate_id):
    """
    The only endpoint that calls the real AI. Runs the full roadmap
    generator for this one candidate, then builds a ready-to-send
    rejection message from the result.
    """
    if candidate_id not in CANDIDATES:
        return jsonify({"error": "Unknown candidate - try re-uploading."}), 404

    entry = CANDIDATES[candidate_id]
    if "gap_result" not in entry:
        return jsonify({"error": "This candidate hasn't been scored against a role yet."}), 400

    gap_result = entry["gap_result"]
    target_job = entry["target_job"]
    m2_profile = entry["module2_profile"]

    try:
        if target_job == NO_CLEAR_MATCH:
            # No point generating an AI roadmap toward a role that was
            # never actually a fit - be upfront about that instead.
            roadmap_result = {"skill_gaps": [], "roadmap": [], "recommended_resources": [],
                               "resume_improvements": [], "career_summary": "", "current_level": ""}
            message = (
                f"Dear {m2_profile['name']},\n\n"
                f"Thank you for your interest and for taking the time to apply.\n\n"
                f"After reviewing your background, we didn't find a close match with any of the "
                f"technical roles we're currently screening for. This doesn't reflect on your "
                f"overall experience - it simply means this particular opening isn't the right fit "
                f"based on the specific skills we're evaluating for.\n\n"
                f"We'd encourage you to look into roles that more closely align with your background, "
                f"and we wish you the best in your search.\n\n"
                f"Best regards,\nThe Hiring Team"
            )
        elif gap_result["skill_gaps"]:
            roadmap_result = generate_roadmap_fast(
                candidate_profile=m2_profile,
                ats_analysis={"skills_score": gap_result["skills_score"], "final_score": gap_result["final_score"]},
                skill_gaps=gap_result["skill_gaps"],
                career_goal=target_job,
                target_job=target_job,
                level="Beginner" if m2_profile["years_experience"] < 2 else "Intermediate",
            )
            message = build_rejection_message(m2_profile["name"], target_job, roadmap_result)
        else:
            roadmap_result = {"skill_gaps": [], "roadmap": [], "recommended_resources": [], "resume_improvements": [], "career_summary": "", "current_level": ""}
            message = build_rejection_message(m2_profile["name"], target_job, roadmap_result)

        entry["status"] = "rejected"
        entry["roadmap_result"] = roadmap_result
        entry["rejection_message"] = message

        return jsonify({
            "candidate_id": candidate_id,
            "status": "rejected",
            "roadmap": roadmap_result,
            "rejection_message": message,
        })

    except Exception as exc:  # noqa: BLE001
        traceback.print_exc()
        return jsonify({"error": str(exc)}), 500


if __name__ == "__main__":
    print("\nHireSense AI demo server starting...")
    print(f"MOCK_MODE is {'ON' if MOCK_MODE else 'OFF'} "
          f"({'set GEMINI_API_KEY to use the real AI' if MOCK_MODE else 'using real Gemini API calls'})")
    print("Open http://127.0.0.1:5000 in your browser.\n")
    app.run(debug=True, port=5000)
