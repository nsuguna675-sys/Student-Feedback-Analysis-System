# Student Feedback Analysis System

A Flask website that collects anonymous course feedback and summarises rating patterns
(averages, response counts, distributions) with charts and CSV exports.

**Data policy:** only synthetic (made-up) feedback is used. No real student data.

## Technologies
Python, Flask, MySQL, Pandas, NumPy, Matplotlib.

## Features
- Anonymous feedback form (course, 1-5 rating per question, optional comment)
- Rating validation in the browser, in Flask and in MySQL (CHECK constraint)
- Average rating, median, spread and % favorable by course and by question
- Response counts and rating distributions
- Charts: course comparison and rating distribution
- CSV export of aggregated summaries
- Privacy: courses/questions with fewer than 5 responses are hidden; comments are cleaned
  of emails, phone numbers, links and ids, and are never displayed

## Setup
1. Install Python 3 and MySQL 8.
2. In the project folder:
   ```
   python3 -m venv .venv
   source .venv/bin/activate
   pip install flask mysql-connector-python pandas numpy matplotlib python-dotenv
   ```
3. Create a `.env` file (never share it):
   ```
   DB_HOST=127.0.0.1
   DB_USER=root
   DB_PASSWORD=your_mysql_password
   DB_NAME=student_feedback
   SECRET_KEY=any-random-text
   ```
4. Create the database and tables by running the SQL in `schema.sql` (MySQL Workbench).
5. Add synthetic data: `python seed_data.py` (type `yes`).
6. Run the website: `python app.py` and open http://127.0.0.1:5001

## Pages
| Address | What it shows |
|---|---|
| `/` | Feedback form |
| `/results` | Course-wise averages and response counts |
| `/results/<id>` | Rating distribution and question averages for one course |
| `/charts` | Course comparison and rating distribution charts |
| `/export/course-summary.csv` | Download course summary (also question-summary, rating-distribution) |

## Database
Tables: `courses`, `feedback_questions`, `feedback` (primary keys, foreign keys and a
CHECK constraint on the rating).

## Limitations
- One student could submit twice because no identities are stored.
- Comment cleaning is pattern based and cannot detect names.