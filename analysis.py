import numpy as np
import pandas as pd

from db import get_connection

MIN_GROUP_SIZE = 5          # courses/questions with fewer responses are hidden (privacy)
RATING_MIN, RATING_MAX = 1, 5
FAVORABLE_FROM = 4          # ratings of 4 and 5 count as "favorable"


def load_feedback():
    """Read all ratings from MySQL into a Pandas table (joined with course and question names)."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT f.submission_id, f.course_id, c.course_name,
               f.question_id, q.question_text, f.rating, f.comment_optional
        FROM feedback f
        JOIN courses c ON c.course_id = f.course_id
        JOIN feedback_questions q ON q.question_id = f.question_id
        """
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    columns = ["submission_id", "course_id", "course_name",
              "question_id", "question_text", "rating", "comment"]
    df = pd.DataFrame(rows, columns=columns)

    # cleaning: keep only whole-number ratings inside the allowed range
    df["rating"] = pd.to_numeric(df["rating"], errors="coerce")
    df = df[df["rating"].between(RATING_MIN, RATING_MAX)]
    df = df.astype({"rating": "int64"})
    return df


def course_summary(df):
    """One row per course: students, ratings, average, median, spread, % favorable."""
    results = []
    for (course_id, course_name), group in df.groupby(["course_id", "course_name"]):
        students = group["submission_id"].nunique()      # how many students (forms)
        ratings = group["rating"].to_numpy()             # NumPy array of all ratings
        shown = students >= MIN_GROUP_SIZE               # privacy rule
        results.append({
            "course_id": int(course_id),
            "course_name": course_name,
            "students": int(students),
            "ratings": int(len(ratings)),
            "shown": bool(shown),
            "average": round(float(np.mean(ratings)), 2) if shown else None,
            "median": float(np.median(ratings)) if shown else None,
            "std": round(float(np.std(ratings, ddof=1)), 2) if shown else None,
            "favorable": round(float(np.mean(ratings >= FAVORABLE_FROM) * 100), 1) if shown else None,
        })
    return results


def course_detail(df, course_id):
    """Everything for one course page: distribution of ratings and average per question."""
    course_df = df[df["course_id"] == course_id]
    if course_df.empty:
        return None

    name = course_df["course_name"].iloc[0]
    students = int(course_df["submission_id"].nunique())
    detail = {"course_name": name, "students": students, "min_group": MIN_GROUP_SIZE,
              "shown": students >= MIN_GROUP_SIZE, "distribution": [], "questions": [],
              "average": None}
    if not detail["shown"]:
        return detail

    detail["comments"] = int(course_df["comment"].notna().sum())    # only the NUMBER of comments
    ratings = course_df["rating"].to_numpy()
    levels = RATING_MAX - RATING_MIN + 1
    counts = np.bincount(ratings - RATING_MIN, minlength=levels)    # how many 1s, 2s, 3s...
    percents = counts / counts.sum() * 100
    detail["average"] = round(float(np.mean(ratings)), 2)
    detail["distribution"] = [
        {"rating": RATING_MIN + i, "count": int(counts[i]), "percent": round(float(percents[i]), 1)}
        for i in range(levels)
    ]

    for (question_id, question_text), group in course_df.groupby(["question_id", "question_text"]):
        values = group["rating"].to_numpy()
        n = int(len(values))
        question_shown = n >= MIN_GROUP_SIZE
        detail["questions"].append({
            "question_text": question_text,
            "n": n,
            "shown": question_shown,
            "average": round(float(np.mean(values)), 2) if question_shown else None,
            "favorable": round(float(np.mean(values >= FAVORABLE_FROM) * 100), 1) if question_shown else None,
        })
    return detail


def course_distributions(df):
    """For the stacked chart: % of 1s, 2s, 3s, 4s, 5s for every course that is allowed to be shown."""
    rows = []
    levels = RATING_MAX - RATING_MIN + 1
    for (course_id, course_name), group in df.groupby(["course_id", "course_name"]):
        students = group["submission_id"].nunique()
        if students < MIN_GROUP_SIZE:
            continue                                   # privacy rule: skip small groups
        counts = np.bincount(group["rating"].to_numpy() - RATING_MIN, minlength=levels)
        rows.append({
            "course_name": course_name,
            "students": int(students),
            "percents": (counts / counts.sum() * 100).tolist(),
        })
    return rows


def question_summary(df):
    """One row per course and question: number of ratings, average, % favorable (small groups hidden)."""
    results = []
    keys = ["course_id", "course_name", "question_id", "question_text"]
    for (course_id, course_name, question_id, question_text), group in df.groupby(keys):
        values = group["rating"].to_numpy()
        n = int(len(values))
        shown = n >= MIN_GROUP_SIZE
        results.append({
            "course_name": course_name,
            "question_text": question_text,
            "ratings": n,
            "average": round(float(np.mean(values)), 2) if shown else None,
            "favorable": round(float(np.mean(values >= FAVORABLE_FROM) * 100), 1) if shown else None,
        })
    return results


def rating_distribution_table(df):
    """One row per course and rating value (1 to 5): how many ratings and what percent."""
    rows = []
    levels = RATING_MAX - RATING_MIN + 1
    for (course_id, course_name), group in df.groupby(["course_id", "course_name"]):
        if group["submission_id"].nunique() < MIN_GROUP_SIZE:
            continue                                   # privacy rule: skip small groups
        counts = np.bincount(group["rating"].to_numpy() - RATING_MIN, minlength=levels)
        for i in range(levels):
            rows.append({
                "course_name": course_name,
                "rating": RATING_MIN + i,
                "count": int(counts[i]),
                "percent": round(float(counts[i] / counts.sum() * 100), 1),
            })
    return rows