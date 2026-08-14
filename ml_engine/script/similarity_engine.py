"""
similarity_engine.py

This script compares a resume to a job description and tells you
how similar they are, as a percentage.

How it works, in simple terms:
1. We take the resume text and the job description text.
2. We turn each one into a list of numbers (an "embedding") using an
   AI model called SBERT (Sentence-BERT). Similar meanings produce
   similar numbers.
3. We compare the two lists of numbers using "cosine similarity" -
   a way to measure how close two sets of numbers are.
4. We turn that into a percentage score and print a simple result.
"""

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# Step 1: Load the AI model.
# "all-MiniLM-L6-v2" is a small, fast SBERT-style model - good for this task.
# The first time you run this, it will download the model (needs internet).
model = SentenceTransformer('all-MiniLM-L6-v2')

# Step 2: Put in your resume text and job description text.
# For now these are just typed directly into the script.
# Later, this can be replaced with text read from a real file.
resume_text = """
Experienced software engineer with 4 years of experience in Python,
data analysis, and machine learning. Skilled in building REST APIs,
working with SQL databases, and collaborating in agile teams.
"""

job_description_text = """
We are looking for a Software Engineer with strong Python skills,
experience in machine learning, and the ability to build and maintain
REST APIs. Familiarity with SQL and agile development is a plus.
"""

# Step 3: Turn both texts into embeddings (lists of numbers).
resume_embedding = model.encode([resume_text])
job_embedding = model.encode([job_description_text])

# Step 4: Compare the two embeddings using cosine similarity.
# This returns a score between 0 and 1.
similarity_score = cosine_similarity(resume_embedding, job_embedding)[0][0]

# Step 5: Turn the score into a percentage.
similarity_percentage = round(similarity_score * 100, 1)

# Step 6: Give a simple recommendation based on the score.
if similarity_percentage >= 75:
    recommendation = "Good Match"
elif similarity_percentage >= 50:
    recommendation = "Moderate Match"
else:
    recommendation = "Weak Match"

# Step 7: Print the results in a clean, readable format.
print("Resume Similarity Score")
print("Software Engineer JD")
print(f"{similarity_percentage}%")
print(f"Recommendation: {recommendation}")
