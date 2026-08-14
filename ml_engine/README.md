# Resume AI Project — Week 2

## Overview

Week 1 of this project focused on parsing resumes — extracting text and identifying sections from PDF files. Week 2 builds on that foundation by introducing the AI components needed to compare a resume against a job description and generate a meaningful match score.

## System Workflow

```
Resume JSON
     │
     ▼
Feature Extraction
     │
     ▼
Sentence Embeddings
     │
     ▼
Similarity Engine
     │
     ▼
ATS Score
     │
     ▼
Skill Gap Analysis
     │
     ▼
Roadmap Generator
```

The resume is parsed into structured data, key details are extracted, and both the resume and job description are converted into embeddings (numerical representations of meaning). These embeddings are compared to produce a similarity score, which will later support skill gap analysis and roadmap generation in future iterations of the project.

## Tasks Completed

**1. ATS Resume Scoring Research**
Researched how Applicant Tracking Systems evaluate and rank resumes, the difference between keyword matching and semantic matching, common mistakes that lower ATS scores, and how AI can improve the accuracy and fairness of resume evaluation.
Deliverable: `ATS_Scoring_Research.pdf`

**2. Embeddings & Semantic Search Research**
Researched how embeddings represent meaning numerically, the role of sentence transformers and vector databases, how cosine similarity measures closeness between two pieces of text, and why semantic search outperforms simple keyword matching.
Deliverable: `Semantic_Search_Research.pdf`

**3. AI Development Environment Setup**
Set up a Python-based development environment using Jupyter Notebook, including the core libraries required for this project: NumPy, Pandas, scikit-learn, Sentence Transformers, Transformers, PyTorch, and Matplotlib. Verified the installation and documented the setup process.
Deliverables: `requirements.txt`, `Environment_Setup_Guide.txt`

**4. Resume vs Job Description Similarity Prototype**
Developed a Python script that loads a resume and a job description, generates sentence embeddings for each using a Sentence-BERT-based model, calculates their cosine similarity, and outputs a match percentage along with a recommendation.
Deliverable: `similarity_engine.py`

**5. AI Model Comparison**
Compared four language models — BERT, Sentence-BERT (SBERT), MiniLM, and DistilBERT — across purpose, advantages, limitations, speed, and accuracy. SBERT was identified as the most suitable model for this project's similarity engine, given its purpose-built design for comparing sentence-level meaning.
Deliverable: `Model_Comparison_Report.pdf`

**6. ATS Scoring Pipeline Architecture**
Designed a flowchart illustrating the full processing pipeline, from initial resume parsing through to final feedback and roadmap generation.
Deliverable: `ATS_Scoring_Architecture.pdf`

**7. GitHub Contribution**
Committed all Week 2 work to the `feature/ml-foundation` branch, using clear, descriptive commit messages for each contribution.

## Project Structure

```
resume-ai-project/
├── docs/
│   ├── ATS_Scoring_Research.pdf
│   ├── Semantic_Search_Research.pdf
│   ├── Model_Comparison_Report.pdf
│   ├── ATS_Scoring_Architecture.pdf
│   └── Environment_Setup_Guide.txt
├── src/
│   └── similarity_engine.py
├── requirements.txt
└── README.md
```

## Running the Similarity Engine

1. Activate the virtual environment:
   ```
   venv\Scripts\activate.bat
   ```
2. Run the script:
   ```
   python src\similarity_engine.py
   ```
3. The script outputs a similarity percentage between the sample resume and job description, along with a recommendation (Good Match, Moderate Match, or Weak Match).

## Summary

By the end of Week 2, the project includes a working understanding of ATS scoring and semantic matching, a fully configured AI development environment, and a functioning prototype capable of comparing a resume to a job description. This provides the foundation for the next phase of the project: skill gap analysis and roadmap generation.
