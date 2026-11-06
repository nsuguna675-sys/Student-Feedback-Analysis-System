# Student Feedback Analysis System

A Flask-based website that collects anonymous course feedback and summarizes rating patterns using charts and reports.

## Data Policy
Only synthetic (made-up) feedback is used. No real student data is included.

## Technologies Used
- Python
- Flask
- MySQL
- Pandas
- NumPy
- Matplotlib

## Features
- Anonymous student feedback form
- Rating validation
- Average rating and median calculation
- Response counts and rating distributions
- Charts for course comparison
- CSV export of summaries
- Privacy protection for feedback data

## Setup Instructions

1. Install Python 3 and MySQL 8.
2. Create a virtual environment.
3. Install the required packages:

```bash
pip install -r requirements.txt
```

4. Create a `.env` file with your database credentials.
5. Execute `schema.sql` in MySQL Workbench.
6. Add sample data using:

```bash
python seed_data.py
```

7. Run the application:

```bash
python app.py
```

8. Open `http://127.0.0.1:5001` in your browser.

## Project Pages
- `/` – Feedback form
- `/results` – Feedback results
- `/charts` – Charts and visualizations
- `/export/course-summary.csv` – Download course summary

## Contributors
Group Project

Original project repository: https://github.com/PrudhvinathTanneeru/Student_feedback_system

## Limitations
- Duplicate submissions may occur.
- Comment cleaning is pattern-based.
