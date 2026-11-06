import uuid
from datetime import datetime, timedelta

import numpy as np

from db import get_connection

rng = np.random.default_rng(42)  # same seed = same fake data every time

# (course name, typical rating, number of students who respond)
COURSES = [
    ("Data Structures", 3.7, 41),
    ("Database Systems", 3.9, 36),
    ("Operating Systems", 3.2, 29),
    ("Computer Networks", 4.0, 22),
    ("Research Methods", 3.4, 3),   # deliberately tiny: tests the small-group privacy rule
]

COMMENTS = [
    "Clear explanations and good examples.",
    "More practice problems would help.",
    "The pace was a little fast.",
    "Labs were useful and well structured.",
    "Please share the slides earlier.",
    "Great course overall.",
]

INSERT_SQL = (
    "INSERT INTO feedback "
    "(submission_id, course_id, question_id, rating, comment_optional, submitted_at) "
    "VALUES (%s, %s, %s, %s, %s, %s)"
)


def main():
    answer = input("This DELETES all existing feedback and adds fake data. Type yes to continue: ")
    if answer.strip().lower() != "yes":
        print("Cancelled. Nothing was changed.")
        return

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("DELETE FROM feedback")

    for name, _, _ in COURSES:
        cur.execute("INSERT IGNORE INTO courses (course_name) VALUES (%s)", (name,))

    cur.execute("SELECT course_id, course_name FROM courses")
    course_ids = {name: cid for cid, name in cur.fetchall()}

    cur.execute("SELECT question_id FROM feedback_questions ORDER BY question_id")
    question_ids = [row[0] for row in cur.fetchall()]

    now = datetime.now().replace(microsecond=0)
    rows = []
    for name, typical, students in COURSES:
        for _ in range(students):
            submission_id = str(uuid.uuid4())          # one random id per fake student
            mood = rng.normal(0, 0.6)                   # a student rates all questions similarly
            when = now - timedelta(days=int(rng.integers(0, 90)))
            comment_used = False
            for question_id in question_ids:
                raw = typical + mood + rng.normal(0, 0.7)
                rating = int(np.clip(np.rint(raw), 1, 5))   # keep it between 1 and 5
                comment = None
                if not comment_used and rng.random() < 0.15:
                    comment = COMMENTS[int(rng.integers(len(COMMENTS)))]
                    comment_used = True
                rows.append((submission_id, course_ids[name], question_id, rating, comment, when))

    cur.executemany(INSERT_SQL, rows)
    conn.commit()
    cur.close()
    conn.close()
    print(f"Done. Added {len(rows)} ratings from {sum(c[2] for c in COURSES)} fake students.")


if __name__ == "__main__":
    main()