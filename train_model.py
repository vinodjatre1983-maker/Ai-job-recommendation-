"""
Small offline helper to inspect and validate the job catalogue with pandas.
The live recommendation model is fitted on demand in app.py.
Run: python train_model.py
"""
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
CSV_PATH = BASE_DIR / "jobs.csv"

def main():
    df = pd.read_csv(CSV_PATH)
    required = {"title", "category", "location", "skills", "description", "experience", "apply_url"}
    missing = required - set(df.columns)
    if missing:
        raise SystemExit(f"Missing required columns in jobs.csv: {', '.join(sorted(missing))}")
    print(f"Loaded {len(df)} jobs")
    print("\nJobs by category:")
    print(df.groupby("category")["title"].count().sort_values(ascending=False).to_string())
    print("\nFirst five jobs:")
    print(df[["title", "category", "location"]].head().to_string(index=False))

if __name__ == "__main__":
    main()
