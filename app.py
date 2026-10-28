from flask import Flask, render_template, request, jsonify
import sqlite3
from pathlib import Path
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "jobs.db"
CSV_PATH = BASE_DIR / "jobs.csv"

app = Flask(__name__)

SAMPLE_JOBS = [
    ("Junior Python Developer", "Technology", "Indore", "Python, Flask, SQL, REST APIs", "Build and maintain Python applications and APIs.", "0-1 years", "https://www.linkedin.com/jobs/"),
    ("Machine Learning Intern", "AI & Data", "Remote", "Python, machine learning, pandas, scikit-learn, statistics", "Support model development, data cleaning, experiments, and evaluation.", "Fresher", "https://www.linkedin.com/jobs/"),
    ("Data Analyst Intern", "AI & Data", "Indore", "SQL, Excel, Python, pandas, data visualization", "Analyze datasets and turn business questions into useful insights.", "Fresher", "https://www.linkedin.com/jobs/"),
    ("Frontend Developer Intern", "Engineering", "Remote", "HTML, CSS, JavaScript, responsive design, React", "Create accessible and responsive web interfaces.", "Fresher", "https://www.linkedin.com/jobs/"),
    ("Full Stack Developer Intern", "Engineering", "Bhopal", "JavaScript, Python, Flask, SQL, HTML, CSS, APIs", "Build features across the frontend and backend of web applications.", "Fresher", "https://www.linkedin.com/jobs/"),
    ("Cloud Support Associate", "Cloud & DevOps", "Remote", "Linux, networking, cloud computing, Python, troubleshooting", "Help diagnose infrastructure and deployment issues.", "0-1 years", "https://www.linkedin.com/jobs/"),
    ("Data Science Intern", "AI & Data", "Remote", "Python, pandas, NumPy, statistics, visualization, scikit-learn", "Explore datasets and prototype predictive models.", "Fresher", "https://www.linkedin.com/jobs/"),
    ("QA Automation Intern", "Engineering", "Indore", "Python, JavaScript, testing, debugging, Git", "Write automated tests and help improve product quality.", "Fresher", "https://www.linkedin.com/jobs/"),
    ("Backend Developer Intern", "Engineering", "Bhopal", "Python, Flask, databases, SQL, APIs, Git", "Design backend routes, database queries, and API integrations.", "Fresher", "https://www.linkedin.com/jobs/"),
    ("UI/UX Design Intern", "Design", "Remote", "Figma, wireframing, prototyping, user research, CSS", "Create clear user flows, wireframes, and interface prototypes.", "Fresher", "https://www.linkedin.com/jobs/"),
    ("Cybersecurity Trainee", "Security", "Remote", "Networking, Linux, security fundamentals, Python", "Assist with security checks, monitoring, and documentation.", "Fresher", "https://www.linkedin.com/jobs/"),
    ("DevOps Intern", "Cloud & DevOps", "Remote", "Linux, Git, Docker, CI/CD, cloud, scripting", "Support build pipelines, deployments, and infrastructure automation.", "Fresher", "https://www.linkedin.com/jobs/"),
]

def connect_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with connect_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                category TEXT NOT NULL,
                location TEXT NOT NULL,
                skills TEXT NOT NULL,
                description TEXT NOT NULL,
                experience TEXT NOT NULL,
                apply_url TEXT NOT NULL
            )
        """)
        count = conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
        if count == 0:
            conn.executemany(
                "INSERT INTO jobs (title, category, location, skills, description, experience, apply_url) VALUES (?, ?, ?, ?, ?, ?, ?)",
                SAMPLE_JOBS
            )
        conn.execute("""
            CREATE TABLE IF NOT EXISTS searches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                skills TEXT NOT NULL,
                education TEXT,
                location TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

def get_jobs_df():
    with connect_db() as conn:
        rows = conn.execute("SELECT * FROM jobs ORDER BY title").fetchall()
    return pd.DataFrame([dict(row) for row in rows])

def recommend_jobs(skills, education, location, limit=8):
    jobs = get_jobs_df()
    if jobs.empty:
        return []

    user_text = " ".join([skills.strip(), education.strip()])
    job_texts = (jobs["title"] + " " + jobs["category"] + " " + jobs["skills"] + " " + jobs["description"] + " " + jobs["experience"]).tolist()

    # TF-IDF + cosine similarity provides a simple, explainable baseline.
    corpus = [user_text] + job_texts
    vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
    matrix = vectorizer.fit_transform(corpus)
    raw_scores = cosine_similarity(matrix[0:1], matrix[1:]).flatten()

    # Small location preference boost; location is a preference, not a qualification.
    final_scores = []
    preferred = location.strip().lower()
    for idx, score in enumerate(raw_scores):
        job_location = str(jobs.iloc[idx]["location"]).lower()
        adjusted = float(score)
        if preferred and (preferred in job_location or job_location == "remote"):
            adjusted = min(1.0, adjusted + 0.06)
        final_scores.append(adjusted)

    order = sorted(range(len(final_scores)), key=lambda i: final_scores[i], reverse=True)[:limit]
    results = []
    for idx in order:
        row = jobs.iloc[idx].to_dict()
        row["match"] = round(final_scores[idx] * 100)
        row["skills_list"] = [s.strip() for s in str(row["skills"]).split(",") if s.strip()]
        results.append(row)
    return results

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/recommend", methods=["POST"])
def api_recommend():
    payload = request.get_json(silent=True) or {}
    skills = str(payload.get("skills", ""))[:2000].strip()
    education = str(payload.get("education", ""))[:300].strip()
    location = str(payload.get("location", ""))[:100].strip()

    if len(skills) < 2:
        return jsonify({"error": "Please enter at least a couple of skills to get recommendations."}), 400

    with connect_db() as conn:
        conn.execute(
            "INSERT INTO searches (skills, education, location) VALUES (?, ?, ?)",
            (skills, education, location)
        )

    recommendations = recommend_jobs(skills, education, location)
    return jsonify({"recommendations": recommendations, "count": len(recommendations)})

@app.route("/api/stats")
def api_stats():
    with connect_db() as conn:
        total_jobs = conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
        categories = conn.execute("SELECT COUNT(DISTINCT category) FROM jobs").fetchone()[0]
        searches = conn.execute("SELECT COUNT(*) FROM searches").fetchone()[0]
    return jsonify({"jobs": total_jobs, "categories": categories, "searches": searches})

if __name__ == "__main__":
    init_db()
    # Local development only. Do not use Flask's debug server as a public production server.
    app.run(debug=True)
