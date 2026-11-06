-- Student Feedback Analysis System: database setup
-- Run this file in MySQL Workbench to create everything from scratch.

CREATE DATABASE IF NOT EXISTS student_feedback;
USE student_feedback;

-- Courses that can receive feedback
CREATE TABLE IF NOT EXISTS courses (
    course_id INT AUTO_INCREMENT PRIMARY KEY,
    course_name VARCHAR(120) NOT NULL UNIQUE
);

-- The questions students rate
CREATE TABLE IF NOT EXISTS feedback_questions (
    question_id INT AUTO_INCREMENT PRIMARY KEY,
    question_text VARCHAR(255) NOT NULL UNIQUE
);

-- One row per rating. submission_id is a random code shared by the answers of one form.
-- It is not linked to any student, so feedback stays anonymous.
CREATE TABLE IF NOT EXISTS feedback (
    feedback_id INT AUTO_INCREMENT PRIMARY KEY,
    submission_id CHAR(36) NOT NULL,
    course_id INT NOT NULL,
    question_id INT NOT NULL,
    rating TINYINT NOT NULL,
    comment_optional VARCHAR(500),
    submitted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (course_id) REFERENCES courses(course_id),
    FOREIGN KEY (question_id) REFERENCES feedback_questions(question_id),
    CONSTRAINT chk_rating CHECK (rating BETWEEN 1 AND 5)
);

-- Starting data
INSERT IGNORE INTO courses (course_name) VALUES
 ('Data Structures'), ('Database Systems'), ('Operating Systems');

INSERT IGNORE INTO feedback_questions (question_text) VALUES
 ('The course content was clear.'),
 ('The instructor explained concepts well.'),
 ('The workload was manageable.');