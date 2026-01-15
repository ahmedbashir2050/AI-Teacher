# app/models/exam.py
from sqlalchemy import Column, Integer, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from app.db.base import BaseModel
from app.models.user import User
from app.models.academics import Course

class Exam(BaseModel):
    """
    Represents an exam generated for a specific course.
    - `course_id` links the exam to the course it was generated from.
    - `content` stores the exam questions and answers in a structured format (JSON).
    """
    __tablename__ = 'exams'

    course_id = Column(ForeignKey('courses.id'), nullable=False, index=True)
    # Storing the exam content as JSON allows for flexible and structured data,
    # including multiple-choice questions, theory questions, and answers.
    content = Column(JSON, nullable=False)

    # Many-to-one relationship to the Course.
    course = relationship("Course")

    # One-to-many relationship: An exam can have multiple attempts by different students.
    attempts = relationship("ExamAttempt", back_populates="exam", cascade="all, delete-orphan")

class ExamAttempt(BaseModel):
    """
    Represents a student's attempt at taking an exam.
    - `exam_id` links the attempt to the specific exam.
    - `user_id` links the attempt to the student who took it.
    - `answers` stores the student's submitted answers.
    - `score` stores the calculated result of the attempt.
    """
    __tablename__ = 'exam_attempts'

    exam_id = Column(ForeignKey('exams.id'), nullable=False, index=True)
    user_id = Column(ForeignKey('users.id'), nullable=False, index=True)

    # Storing answers in JSON allows for a flexible structure to match the exam's content.
    answers = Column(JSON, nullable=False)
    # The score can be calculated and stored here for later analysis.
    score = Column(Integer, nullable=True)

    # Many-to-one relationship to the Exam.
    exam = relationship("Exam", back_populates="attempts")

    # Many-to-one relationship to the User (student).
    user = relationship("User")
