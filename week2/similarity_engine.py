"""
similarity_engine.py

Compares a resume to a job description and displays a similarity score.

Steps:
1. Load the resume text from a file.
2. Load the job description text from a file.
3. Generate sentence embeddings for both using an AI model (SBERT/MiniLM).
4. Calculate cosine similarity between the two embeddings.
5. Display the similarity score and a match recommendation.
"""

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


def load_text(file_path):
    """Loads and returns the text content of a file."""
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


def main():
    # Step 1: Load the resume text from a file.
    resume_text = load_text("resume.txt")

    # Step 2: Load the job description text from a file.
    job_description_text = load_text("job_description.txt")

    # Step 3: Generate sentence embeddings using an AI model.
    model = SentenceTransformer("all-MiniLM-L6-v2")
    resume_embedding = model.encode([resume_text])
    job_embedding = model.encode([job_description_text])

    # Step 4: Calculate cosine similarity between the two embeddings.
    similarity_score = cosine_similarity(resume_embedding, job_embedding)[0][0]
    similarity_percentage = round(similarity_score * 100, 1)

    # Step 5: Determine the recommendation based on the score.
    if similarity_percentage >= 75:
        recommendation = "Good Match"
    elif similarity_percentage >= 50:
        recommendation = "Moderate Match"
    else:
        recommendation = "Weak Match"

    # Display the similarity score in the required format.
    print("Resume Similarity Score")
    print("Entry-Level Software Engineer JD")
    print(f"{similarity_percentage}%")
    print("Recommendation:")
    print(recommendation)


if __name__ == "__main__":
    main()
