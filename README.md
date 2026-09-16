# HireSense AI

An end-to-end AI-powered resume screening and career roadmap system — built to parse resumes, score candidates against job descriptions using semantic similarity, and generate personalized upskilling roadmaps, all wrapped in a working web frontend for HR screening.

HireSense AI was built incrementally over a four-week sprint, with each week adding a new layer to the pipeline: first extracting clean structured data from raw resume PDFs, then researching and building the matching/scoring engine, then hardening the parser into a real reusable module, and finally wrapping everything in an AI roadmap generator and a usable web frontend for HR reviewers.

## Overview

Manual resume screening doesn't scale, and most existing ATS tools are keyword-matching black boxes that reject qualified candidates over formatting or phrasing. HireSense AI takes a different approach:

1. **Parse** — extract clean, structured data out of messy real-world resume PDFs (personal info, education, experience, skills, certifications, projects).
2. **Match** — compare the candidate's resume against a job description using semantic similarity and embeddings, not just keyword overlap.
3. **Evaluate** — score the candidate across multiple weighted dimensions (skills, experience, education) to produce an interpretable evaluation report.
4. **Guide** — for candidates who fall short, generate a personalized, LLM-powered roadmap showing exactly what to learn to close the gap for that specific role.
5. **Decide** — surface all of this in a bulk-screening frontend where an HR reviewer can go through candidates and select or reject them directly.

The project also treats reliability as a first-class concern: the roadmap generator is paired with dedicated hallucination testing so that AI-generated career advice doesn't invent skills, courses, or claims that aren't grounded in reality.

## Why This Project

Most "AI resume screeners" either (a) do simple keyword matching dressed up as AI, or (b) hand everything to an LLM and hope for the best, with no evaluation of whether its outputs are trustworthy. HireSense AI was built to sit in between those two extremes: use classical NLP and embeddings for the parts that need to be deterministic and explainable (parsing, section detection, scoring), and use an LLM only where generation genuinely adds value (the roadmap), with explicit testing around where that generation could go wrong.

## Project Structure

AlgoHub_HireSenseAI/
├── weekly tasks_1/                  # Week 1 — PDF resume parser foundations
│   ├── task1.docx ... task6/        #   incremental tasks building the pipeline
│   └── resume_parser_project_task7/ #   final combined Week 1 deliverable
├── week2/                           # Week 2 — ATS scoring research
│   ├── similarity_engine.py
│   ├── resume.txt / job_description.txt
│   └── similarity_output.txt
├── week3/                           # Week 3 — ATS evaluation engine
│   ├── ats_engine_v2.py
│   ├── skill_matcher.py / skill_gap_engine.py
│   ├── experience_matcher.py / education_matcher.py
│   ├── semantic_matcher_v2.py
│   ├── ats_evaluation.ipynb
│   └── deleiverable/                #   packaged Week 3 deliverable
├── week4-mod1/                      # Week 4, Module 1 — full resume parser
│   ├── resume_parser_v3.py
│   ├── candidate_profile.py
│   ├── personal_info_extractor.py
│   ├── education_extractor.py
│   ├── experience_extractor.py
│   ├── certification_extractor.py
│   ├── projects_extractor.py
│   ├── skills_extractor.py
│   ├── section_splitter.py
│   ├── run_evaluation.py / parser_evaluation_v2.{csv,json}
│   └── MODULE_1_DOCUMENTATION.docx
├── week4-mod2/                      # Week 4, Module 2 — AI roadmap generator
│   ├── roadmap_generator.py / roadmap_schema.json
│   ├── recommendation_engine.py / resource_database.py
│   ├── hallucination_test.py / llm_evaluation.csv
│   ├── prompt_a_career_analysis.txt
│   ├── prompt_b_skill_gap_explanation.txt
│   ├── prompt_c_roadmap_generation.txt
│   ├── module2_task1_design.md
│   └── ai_testing_report.pdf
├── frontend/                        # Working web app (Flask)
│   ├── app.py
│   ├── backend_modules/             #   shared parsing/scoring/roadmap logic
│   ├── templates/index.html
│   └── static/  (script.js, style.css)
├── pictures_mvp/                    # Demo screenshots (1.png – 7.png)
└── testing resumes/                 # Sample resumes used for testing (resume_01–05.pdf)


## Weekly Progress

### Week 1 — PDF Resume Parser
The foundational pipeline that everything else builds on. This week focused on getting clean, usable text out of real resume PDFs before any matching or scoring could happen.

- **Text extraction** — pulling raw text out of PDF resumes using PDF-parsing libraries, and comparing library options for extraction quality (see `Library_Comparison.pdf`)
- **Section detection** — identifying section boundaries within a resume (education, experience, skills, projects, etc.) so downstream steps know what they're looking at
- **Text cleaning** — normalizing whitespace, fixing broken line breaks, and stripping the artifacts PDF extraction tends to leave behind
- **Edge-case handling** — dealing with empty files, malformed PDFs, and other inputs that would otherwise break the pipeline
- Delivered as a series of incremental tasks (`task1` → `task6`), each building on the last, culminating in a combined deliverable (`resume_parser_project_task7`)

### Week 2 — ATS Scoring Research
Before building a full scoring engine, this week was about figuring out *how* resumes and job descriptions should be compared.

- **Similarity engine prototype** (`similarity_engine.py`) — a first working version comparing a resume against a job description
- **Semantic search & embeddings research** — investigating embedding-based approaches over naive keyword matching, so that a resume mentioning "led a team of engineers" can match a job description asking for "leadership experience" even without exact word overlap
- **Transformer model comparison** — evaluating candidate transformer models for generating those embeddings, weighing accuracy against speed
- **Scoring pipeline architecture** — designing how similarity scores would flow into the evaluation engine built the following week

### Week 3 — ATS Evaluation Engine
Turns the research from Week 2 into a real, multi-dimensional evaluation engine.

- `ats_engine_v2.py` — the core engine that orchestrates scoring across all dimensions
- `skill_matcher.py` / `skill_gap_engine.py` — matches candidate skills against required skills and identifies gaps
- `experience_matcher.py` — evaluates relevant experience against role requirements
- `education_matcher.py` — evaluates education background against role requirements
- `semantic_matcher_v2.py` — the semantic/embedding-based similarity layer from Week 2's research, now productionized
- `ats_evaluation.ipynb` — a notebook used to test and iterate on the engine interactively
- Outputs a structured `evaluation_report.pdf` per candidate, and a packaged version of the whole module lives in `deleiverable/`

### Week 4 — Module 1: Resume Parser
Where the Week 1 prototype becomes a real, reusable, testable module.

- `resume_parser_v3.py` — the third iteration of the parser, now more robust than the Week 1 version
- `candidate_profile.py` — assembles all extracted fields into a single structured candidate profile
- Dedicated extractors, each with their own test data for validation:
  - `personal_info_extractor.py`
  - `education_extractor.py`
  - `experience_extractor.py`
  - `certification_extractor.py`
  - `projects_extractor.py`
  - `skills_extractor.py`
- `section_splitter.py` — a refined version of Week 1's section-detection logic
- `run_evaluation.py` — runs the parser against a labeled dataset and produces `parser_evaluation_v2.csv` / `.json` to quantify accuracy
- `MODULE_1_DOCUMENTATION.docx` — full write-up of the module's design and usage

### Week 4 — Module 2: AI Roadmap Generator
For candidates who don't fully meet a role's requirements, this module turns their skill gaps into an actionable learning plan.

- `roadmap_generator.py` — generates a structured, personalized roadmap (validated against `roadmap_schema.json`) using an LLM
- `recommendation_engine.py` — decides what to recommend based on the candidate's specific gaps
- `resource_database.py` — a curated database of learning resources the roadmap draws from, so recommendations are grounded rather than invented
- **Prompt engineering** — three distinct prompts for different stages of the pipeline: `prompt_a_career_analysis.txt`, `prompt_b_skill_gap_explanation.txt`, and `prompt_c_roadmap_generation.txt`
- **Hallucination testing** (`hallucination_test.py`, `llm_evaluation.csv`) — systematically checks whether the LLM invents skills, resources, or claims that don't hold up, since career advice that sounds confident but is wrong is worse than no advice at all
- `module2_task1_design.md` — design notes for the module
- `ai_testing_report.pdf` — write-up of the hallucination testing results

## Frontend

The `frontend/` folder contains the working HireSense AI web application — the piece that ties every backend module (parser, evaluation engine, roadmap generator) together into something an actual HR reviewer can use, built with Flask.

**Key features:**

- **Bulk resume screening** — upload and process multiple resumes against a single job description in one pass, instead of reviewing candidates one at a time
- **Auto role detection** — automatically infers the target role from the job description text, so the reviewer doesn't have to manually tag every posting
- **Structured candidate profiles** — every uploaded resume is parsed into the same structured format (personal info, education, experience, skills, certifications, projects) for consistent side-by-side comparison
- **AI roadmap generation** — for candidates who fall short of the bar, the frontend surfaces a personalized upskilling roadmap instead of just a rejection
- **Select/reject workflow** — reviewers can select or reject each candidate directly in the UI, with generated selection/rejection messages (`selection_message.py`, `rejection_message.py`) ready to send

**How it's organized:**

- `app.py` — the Flask application and route handlers
- `backend_modules/` — the shared logic powering the frontend, pulling together the parser (`resume_parser_v3.py` and its extractors), the evaluation engine (`recommendation_engine.py`), the roadmap generator (`roadmap_generator.py`, `resource_database.py`), and frontend-specific helpers like `column_aware_extract.py`, `fast_pipeline.py`, `profile_adapter.py`, and `target_jobs.py`
- `templates/index.html` — the main page template
- `static/script.js` / `static/style.css` — frontend interactivity and styling

### Running the frontend

**Prerequisites:** Python 3.x installed and available on your PATH.

```bash
# 1. Navigate to the frontend directory
cd frontend

# 2. (Recommended) create and activate a virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # macOS/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the app
python app.py
```

Then open the app in your browser at the local address printed in the terminal (typically `http://127.0.0.1:5000`).

**Basic usage once it's running:**

1. Upload a job description (or paste the text in).
2. Upload one or more candidate resumes (PDF).
3. The app parses each resume, scores it against the job description, and displays a ranked, structured breakdown per candidate.
4. For candidates below the threshold, view their generated skill roadmap.
5. Select or reject each candidate — the app generates an appropriate message either way.

## Screenshots

See `pictures_mvp/` (`1.png` – `7.png`) for demo screenshots walking through the application — from job description upload through to the select/reject decision screen.

## Testing

- `testing resumes/` — five sample resumes (`resume_01.pdf` – `resume_05.pdf`) used to exercise the parsing and scoring pipeline end to end
- `week4-mod1/parser_evaluation_v2.csv` / `.json` — quantitative evaluation of parser accuracy against labeled test data
- `week4-mod2/llm_evaluation.csv` and `hallucination_test.py` — evaluation of the roadmap generator's outputs, specifically checking for hallucinated or ungrounded claims
- `week3/ats_evaluation.ipynb` — interactive notebook for testing and iterating on the scoring engine

## Design Documents

For deeper technical detail beyond this README, see:

- `week4-mod1/MODULE_1_DOCUMENTATION.docx` — full design and usage docs for the resume parser module
- `week4-mod2/module2_task1_design.md` — design notes for the roadmap generator
- `week4-mod2/ai_testing_report.pdf` — write-up of hallucination testing methodology and results
- `week3/deleiverable/evaluation_report.pdf` — sample output of the ATS evaluation engine

## Tech Stack

- **Language:** Python
- **Backend/Web framework:** Flask
- **Frontend:** HTML, CSS, vanilla JavaScript
- **NLP/ML:** Semantic similarity & embeddings, transformer-based models for text comparison
- **Parsing:** PDF text extraction, custom section-detection and text-cleaning pipeline
- **AI Generation:** LLM-based roadmap generation, with prompt-engineered stages and dedicated hallucination testing
- **Data formats:** JSON (structured profiles, roadmap schema), CSV (evaluation results)

## Roadmap / Future Work

Some natural next steps for the project beyond its current MVP state:

- Expand test resume coverage to more formats and layouts (multi-column, non-standard section headers)
- Add authentication and multi-user support to the frontend for real HR team use
- Persist candidate evaluations to a database instead of in-memory/session state
- Expand hallucination testing coverage across more roadmap prompt variations
- Add configurable scoring weights so reviewers can tune how skills vs. experience vs. education are prioritized per role

## Author

Mahnoor Sohail
