import os
import uuid

import pandas as pd
from dotenv import load_dotenv
from flask import Flask, Response, abort, render_template, request, redirect, url_for
import charts
from analysis import (MIN_GROUP_SIZE, course_detail, course_distributions, course_summary,
                      load_feedback, question_summary, rating_distribution_table)
from db import get_connection
from privacy import clean_comment

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "change-me")

RATING_MIN, RATING_MAX = 1, 5
MAX_COMMENT_LENGTH = 500


def get_courses_and_questions():
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT course_id, course_name FROM courses ORDER BY course_name")
    courses = cur.fetchall()
    cur.execute("SELECT question_id, question_text FROM feedback_questions ORDER BY question_id")
    questions = cur.fetchall()
    cur.close()
    conn.close()
    return courses, questions


def show_form(errors=None, old=None):
    courses, questions = get_courses_and_questions()
    return render_template(
        "form.html",
        courses=courses,
        questions=questions,
        ratings=range(RATING_MIN, RATING_MAX + 1),
        errors=errors or [],
        old=old or {},
        max_comment=MAX_COMMENT_LENGTH,
    )


@app.route("/")
def form():
    return show_form()


@app.route("/submit", methods=["POST"])
def submit():
    courses, questions = get_courses_and_questions()
    valid_course_ids = {c["course_id"] for c in courses}
    errors = []

    # 1. validate the course
    raw_course = request.form.get("course_id", "")
    course_id = int(raw_course) if raw_course.isdigit() else None
    if course_id not in valid_course_ids:
        errors.append("Please choose a course.")

    # 2. validate every rating (must be a whole number from 1 to 5)
    answers = []
    for q in questions:
        raw = request.form.get(f"rating_{q['question_id']}", "")
        if raw.isdigit() and RATING_MIN <= int(raw) <= RATING_MAX:
            answers.append((q["question_id"], int(raw)))
        else:
            errors.append(f"Please give a rating from {RATING_MIN} to {RATING_MAX} for: {q['question_text']}")

    # 3. validate the optional comment
    comment = request.form.get("comment", "").strip()
    if len(comment) > MAX_COMMENT_LENGTH:
        errors.append(f"Comment must be {MAX_COMMENT_LENGTH} characters or fewer.")

    if errors:
        return show_form(errors=errors, old=request.form)
    
    comment = clean_comment(comment)      # remove emails, phone numbers, links, student ids

    # 4. save: one random id per form, NOT linked to any student
    submission_id = str(uuid.uuid4())
    rows = []
    for i, (question_id, rating) in enumerate(answers):
        # the comment is stored once, on the first answer of the form
        rows.append((submission_id, course_id, question_id, rating, comment or None if i == 0 else None))

    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.executemany(
            "INSERT INTO feedback (submission_id, course_id, question_id, rating, comment_optional) "
            "VALUES (%s, %s, %s, %s, %s)",
            rows,
        )
        conn.commit()
    except Exception:
        conn.rollback()
        return show_form(errors=["Sorry, your feedback could not be saved. Please try again."], old=request.form)
    finally:
        conn.close()

    return redirect(url_for("thanks"))


@app.route("/thanks")
def thanks():
    return render_template("thanks.html")

@app.route("/results")
def results():
    df = load_feedback()
    return render_template("results.html", courses=course_summary(df), min_group=MIN_GROUP_SIZE)


@app.route("/results/<int:course_id>")
def course_page(course_id):
    detail = course_detail(load_feedback(), course_id)
    if detail is None:
        abort(404)
    return render_template("course.html", **detail)
@app.route("/charts")
def charts_page():
    return render_template("charts.html")


@app.route("/chart/course-comparison.png")
def chart_course_comparison():
    png = charts.course_comparison_png(course_summary(load_feedback()))
    return Response(png, mimetype="image/png")


@app.route("/chart/distribution.png")
def chart_distribution():
    png = charts.distribution_png(course_distributions(load_feedback()))
    return Response(png, mimetype="image/png")
def safe_cell(value):
    """Spreadsheets run text starting with = + - @ as a formula, so put a ' in front of it."""
    if isinstance(value, str) and value and value[0] in "=+-@":
        return "'" + value
    return value


def csv_download(rows, columns, filename):
    table = pd.DataFrame(rows, columns=columns).map(safe_cell)
    return Response(
        table.to_csv(index=False),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@app.route("/export/course-summary.csv")
def export_course_summary():
    columns = ["course_name", "students", "ratings", "average", "median", "std", "favorable"]
    return csv_download(course_summary(load_feedback()), columns, "course_summary.csv")


@app.route("/export/question-summary.csv")
def export_question_summary():
    columns = ["course_name", "question_text", "ratings", "average", "favorable"]
    return csv_download(question_summary(load_feedback()), columns, "question_summary.csv")


@app.route("/export/rating-distribution.csv")
def export_rating_distribution():
    columns = ["course_name", "rating", "count", "percent"]
    return csv_download(rating_distribution_table(load_feedback()), columns, "rating_distribution.csv")
if __name__ == "__main__":
    app.run(debug=True, port=5001)