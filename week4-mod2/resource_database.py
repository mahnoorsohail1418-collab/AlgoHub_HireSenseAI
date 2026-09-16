"""
resource_database.py

A small VERIFIED resource database - every URL here is a real, stable,
well-known resource (official docs, established learning platforms).
This exists specifically so recommendation_engine.py never has to ask an
LLM to invent a course name or link (see Task 6, hallucination testing).

Each skill maps to exactly 3 stages, matching the example format:
  1. Fundamentals   - learn the basics
  2. Hands-on Lab   - practice interactively
  3. Project         - build something real with it

New skills can be added here over time - if a skill isn't in this
database, recommendation_engine.py should say so honestly rather than
inventing a resource for it.
"""

RESOURCE_DB = {
    "docker": [
        {"stage": "Fundamentals", "name": "Docker Get Started Guide", "url": "https://docs.docker.com/get-started/", "type": "documentation"},
        {"stage": "Hands-on Lab", "name": "Docker Interactive Playground", "url": "https://killercoda.com/docker", "type": "practice"},
        {"stage": "Project", "name": "Project Ideas (filter: Docker)", "url": "https://roadmap.sh/projects", "type": "practice"},
    ],
    "kubernetes": [
        {"stage": "Fundamentals", "name": "Kubernetes Basics Tutorial", "url": "https://kubernetes.io/docs/tutorials/kubernetes-basics/", "type": "documentation"},
        {"stage": "Hands-on Lab", "name": "Kubernetes Interactive Playground", "url": "https://killercoda.com/kubernetes", "type": "practice"},
        {"stage": "Project", "name": "Kubernetes Official Tutorials", "url": "https://kubernetes.io/docs/tutorials/", "type": "practice"},
    ],
    "sql": [
        {"stage": "Fundamentals", "name": "W3Schools SQL Tutorial", "url": "https://www.w3schools.com/sql/", "type": "course"},
        {"stage": "Hands-on Lab", "name": "SQLZoo Interactive Exercises", "url": "https://sqlzoo.net/", "type": "practice"},
        {"stage": "Project", "name": "Mode SQL Tutorial (real datasets)", "url": "https://mode.com/sql-tutorial/", "type": "practice"},
    ],
    "python": [
        {"stage": "Fundamentals", "name": "The Python Tutorial (official docs)", "url": "https://docs.python.org/3/tutorial/", "type": "documentation"},
        {"stage": "Hands-on Lab", "name": "HackerRank Python Domain", "url": "https://www.hackerrank.com/domains/python", "type": "practice"},
        {"stage": "Project", "name": "Project-Based Learning (Python list)", "url": "https://github.com/practical-tutorials/project-based-learning", "type": "practice"},
    ],
    "aws": [
        {"stage": "Fundamentals", "name": "AWS Cloud Practitioner Essentials", "url": "https://aws.amazon.com/training/digital/aws-cloud-practitioner-essentials/", "type": "course"},
        {"stage": "Hands-on Lab", "name": "AWS Hands-On Tutorials", "url": "https://aws.amazon.com/getting-started/hands-on/", "type": "practice"},
        {"stage": "Project", "name": "AWS Getting Started Projects", "url": "https://aws.amazon.com/getting-started/projects/", "type": "practice"},
    ],
    "rest apis": [
        {"stage": "Fundamentals", "name": "REST API Best Practices", "url": "https://www.freecodecamp.org/news/rest-api-best-practices/", "type": "documentation"},
        {"stage": "Hands-on Lab", "name": "Public APIs (practice list)", "url": "https://github.com/public-apis/public-apis", "type": "practice"},
        {"stage": "Project", "name": "Project Ideas (filter: API)", "url": "https://roadmap.sh/projects", "type": "practice"},
    ],
    "git": [
        {"stage": "Fundamentals", "name": "Pro Git Book (free, official)", "url": "https://git-scm.com/book/en/v2", "type": "book"},
        {"stage": "Hands-on Lab", "name": "Learn Git Branching (interactive)", "url": "https://learngitbranching.js.org/", "type": "practice"},
        {"stage": "Project", "name": "GitHub Skills", "url": "https://github.com/skills", "type": "practice"},
    ],
    "javascript": [
        {"stage": "Fundamentals", "name": "MDN JavaScript Guide", "url": "https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide", "type": "documentation"},
        {"stage": "Hands-on Lab", "name": "JavaScript30 (free course)", "url": "https://javascript30.com/", "type": "course"},
        {"stage": "Project", "name": "Project-Based Learning (JS list)", "url": "https://github.com/practical-tutorials/project-based-learning", "type": "practice"},
    ],
    "excel": [
        {"stage": "Fundamentals", "name": "Microsoft Excel Help & Learning", "url": "https://support.microsoft.com/en-us/excel", "type": "documentation"},
        {"stage": "Hands-on Lab", "name": "ExcelJet Formula Practice", "url": "https://exceljet.net/", "type": "practice"},
        {"stage": "Project", "name": "Kaggle Learn (data + spreadsheets)", "url": "https://www.kaggle.com/learn", "type": "practice"},
    ],
    "tableau": [
        {"stage": "Fundamentals", "name": "Tableau Official Training", "url": "https://www.tableau.com/learn/training", "type": "course"},
        {"stage": "Hands-on Lab", "name": "Tableau eLearning", "url": "https://www.tableau.com/learn/training/elearning", "type": "course"},
        {"stage": "Project", "name": "Tableau Public Gallery (for inspiration + practice datasets)", "url": "https://public.tableau.com/en-us/gallery", "type": "practice"},
    ],
    "react": [
        {"stage": "Fundamentals", "name": "React Official Docs - Quick Start", "url": "https://react.dev/learn", "type": "documentation"},
        {"stage": "Hands-on Lab", "name": "Scrimba Learn React (interactive)", "url": "https://scrimba.com/learn/learnreact", "type": "course"},
        {"stage": "Project", "name": "Project-Based Learning (React list)", "url": "https://github.com/practical-tutorials/project-based-learning", "type": "practice"},
    ],
    "node.js": [
        {"stage": "Fundamentals", "name": "Node.js Official Guides", "url": "https://nodejs.org/en/learn/getting-started/introduction-to-nodejs", "type": "documentation"},
        {"stage": "Hands-on Lab", "name": "freeCodeCamp Back End Development & APIs", "url": "https://www.freecodecamp.org/learn/back-end-development-and-apis/", "type": "course"},
        {"stage": "Project", "name": "Project Ideas (filter: Node/API)", "url": "https://roadmap.sh/projects", "type": "practice"},
    ],
    "mongodb": [
        {"stage": "Fundamentals", "name": "MongoDB Manual - Getting Started", "url": "https://www.mongodb.com/docs/manual/tutorial/getting-started/", "type": "documentation"},
        {"stage": "Hands-on Lab", "name": "MongoDB University (free courses)", "url": "https://learn.mongodb.com/", "type": "course"},
        {"stage": "Project", "name": "Project Ideas (filter: database)", "url": "https://roadmap.sh/projects", "type": "practice"},
    ],
    "java": [
        {"stage": "Fundamentals", "name": "Oracle Java Tutorials (official)", "url": "https://docs.oracle.com/javase/tutorial/", "type": "documentation"},
        {"stage": "Hands-on Lab", "name": "HackerRank Java Domain", "url": "https://www.hackerrank.com/domains/java", "type": "practice"},
        {"stage": "Project", "name": "Project-Based Learning (Java list)", "url": "https://github.com/practical-tutorials/project-based-learning", "type": "practice"},
    ],
    "c++": [
        {"stage": "Fundamentals", "name": "LearnCpp.com (free full course)", "url": "https://www.learncpp.com/", "type": "course"},
        {"stage": "Hands-on Lab", "name": "HackerRank C++ Domain", "url": "https://www.hackerrank.com/domains/cpp", "type": "practice"},
        {"stage": "Project", "name": "Project-Based Learning (C++ list)", "url": "https://github.com/practical-tutorials/project-based-learning", "type": "practice"},
    ],
    "linux": [
        {"stage": "Fundamentals", "name": "Linux Journey (free interactive)", "url": "https://linuxjourney.com/", "type": "course"},
        {"stage": "Hands-on Lab", "name": "OverTheWire Bandit Wargame", "url": "https://overthewire.org/wargames/bandit/", "type": "practice"},
        {"stage": "Project", "name": "Project Ideas (filter: systems/CLI)", "url": "https://roadmap.sh/projects", "type": "practice"},
    ],
    "machine learning": [
        {"stage": "Fundamentals", "name": "Google Machine Learning Crash Course", "url": "https://developers.google.com/machine-learning/crash-course", "type": "course"},
        {"stage": "Hands-on Lab", "name": "Kaggle Learn", "url": "https://www.kaggle.com/learn", "type": "course"},
        {"stage": "Project", "name": "Kaggle Competitions", "url": "https://www.kaggle.com/competitions", "type": "practice"},
    ],
    "pandas": [
        {"stage": "Fundamentals", "name": "pandas Official Getting Started Guide", "url": "https://pandas.pydata.org/docs/getting_started/index.html", "type": "documentation"},
        {"stage": "Hands-on Lab", "name": "Kaggle Learn - Pandas Course", "url": "https://www.kaggle.com/learn/pandas", "type": "course"},
        {"stage": "Project", "name": "Kaggle Datasets (practice with real data)", "url": "https://www.kaggle.com/datasets", "type": "practice"},
    ],
    "statistics": [
        {"stage": "Fundamentals", "name": "Khan Academy Statistics & Probability", "url": "https://www.khanacademy.org/math/statistics-probability", "type": "course"},
        {"stage": "Hands-on Lab", "name": "Khan Academy Practice Exercises (same course)", "url": "https://www.khanacademy.org/math/statistics-probability", "type": "practice"},
        {"stage": "Project", "name": "Kaggle Datasets (apply statistics to real data)", "url": "https://www.kaggle.com/datasets", "type": "practice"},
    ],
    "scrum": [
        {"stage": "Fundamentals", "name": "The Official Scrum Guide", "url": "https://www.scrum.org/resources/scrum-guide", "type": "documentation"},
        {"stage": "Hands-on Lab", "name": "Atlassian Agile Coach", "url": "https://www.atlassian.com/agile", "type": "practice"},
        {"stage": "Project", "name": "Scrum Open Assessment (free, official)", "url": "https://www.scrum.org/open-assessments/scrum-open", "type": "practice"},
    ],
    "scikit-learn": [
        {"stage": "Fundamentals", "name": "scikit-learn Official User Guide", "url": "https://scikit-learn.org/stable/user_guide.html", "type": "documentation"},
        {"stage": "Hands-on Lab", "name": "Kaggle Learn - Intro to Machine Learning", "url": "https://www.kaggle.com/learn/intro-to-machine-learning", "type": "course"},
        {"stage": "Project", "name": "Kaggle Competitions", "url": "https://www.kaggle.com/competitions", "type": "practice"},
    ],
    "deep learning": [
        {"stage": "Fundamentals", "name": "Practical Deep Learning (fast.ai, free)", "url": "https://course.fast.ai/", "type": "course"},
        {"stage": "Hands-on Lab", "name": "Kaggle Learn - Intro to Deep Learning", "url": "https://www.kaggle.com/learn/intro-to-deep-learning", "type": "course"},
        {"stage": "Project", "name": "Kaggle Competitions", "url": "https://www.kaggle.com/competitions", "type": "practice"},
    ],
    "pytorch": [
        {"stage": "Fundamentals", "name": "PyTorch Official Tutorials", "url": "https://pytorch.org/tutorials/", "type": "documentation"},
        {"stage": "Hands-on Lab", "name": "PyTorch Learn the Basics (interactive)", "url": "https://pytorch.org/tutorials/beginner/basics/intro.html", "type": "practice"},
        {"stage": "Project", "name": "PyTorch Examples (official repo)", "url": "https://github.com/pytorch/examples", "type": "practice"},
    ],
    "mlops": [
        {"stage": "Fundamentals", "name": "Google Cloud MLOps Guide", "url": "https://cloud.google.com/architecture/mlops-continuous-delivery-and-automation-pipelines-in-machine-learning", "type": "documentation"},
        {"stage": "Hands-on Lab", "name": "Made With ML (free MLOps course)", "url": "https://madewithml.com/", "type": "course"},
        {"stage": "Project", "name": "Project Ideas (filter: MLOps)", "url": "https://roadmap.sh/projects", "type": "practice"},
    ],
}
