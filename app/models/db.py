from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    DateTime,
    Text,
    Enum,
    ARRAY,
    JSON,
    Boolean,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.db.base import Base


class UserRole(enum.Enum):
    STUDENT = "student"
    ACADEMIC = "academic"
    ADMIN = "admin"


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    chat_sessions = relationship("ChatSession", back_populates="user")
    exam_attempts = relationship("ExamAttempt", back_populates="user")

class Faculty(Base):
    __tablename__ = "faculties"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)

    # Relationships
    departments = relationship("Department", back_populates="faculty")

class Department(Base):
    __tablename__ = "departments"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    faculty_id = Column(Integer, ForeignKey("faculties.id"), nullable=False)

    # Relationships
    faculty = relationship("Faculty", back_populates="departments")
    semesters = relationship("Semester", back_populates="department")

class Semester(Base):
    __tablename__ = "semesters"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False) # e.g., "Fall 2024"
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)

    # Relationships
    department = relationship("Department", back_populates="semesters")
    courses = relationship("Course", back_populates="semester")

class Course(Base):
    __tablename__ = "courses"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    semester_id = Column(Integer, ForeignKey("semesters.id"), nullable=False)

    # Relationships
    semester = relationship("Semester", back_populates="courses")
    books = relationship("Book", back_populates="course")

class Book(Base):
    __tablename__ = "books"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    qdrant_collection_name = Column(String, unique=True, nullable=False)

    # Relationships
    course = relationship("Course", back_populates="books")
    exams = relationship("Exam", back_populates="book")

class ChatSession(Base):
    __tablename__ = "chat_sessions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session")

class ChatMessageRole(enum.Enum):
    USER = "user"
    ASSISTANT = "assistant"

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"), nullable=False)
    role = Column(Enum(ChatMessageRole), nullable=False)
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    qdrant_vector_ids = Column(ARRAY(String))

    # Relationships
    session = relationship("ChatSession", back_populates="messages")

class Exam(Base):
    __tablename__ = "exams"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    book = relationship("Book", back_populates="exams")
    questions = relationship("ExamQuestion", back_populates="exam")
    attempts = relationship("ExamAttempt", back_populates="exam")

class ExamQuestionType(enum.Enum):
    MCQ = "mcq"
    THEORY = "theory"

class ExamQuestion(Base):
    __tablename__ = "exam_questions"
    id = Column(Integer, primary_key=True, index=True)
    exam_id = Column(Integer, ForeignKey("exams.id"), nullable=False)
    question_type = Column(Enum(ExamQuestionType), nullable=False)
    question_text = Column(Text, nullable=False)
    options = Column(JSON) # For MCQ
    correct_answer = Column(Text, nullable=False)

    # Relationships
    exam = relationship("Exam", back_populates="questions")

class ExamAttempt(Base):
    __tablename__ = "exam_attempts"
    id = Column(Integer, primary_key=True, index=True)
    exam_id = Column(Integer, ForeignKey("exams.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    score = Column(Integer)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))

    # Relationships
    exam = relationship("Exam", back_populates="attempts")
    user = relationship("User", back_populates="exam_attempts")
    answers = relationship("ExamAttemptAnswer", back_populates="attempt")

class ExamAttemptAnswer(Base):
    __tablename__ = "exam_attempt_answers"
    id = Column(Integer, primary_key=True, index=True)
    attempt_id = Column(Integer, ForeignKey("exam_attempts.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("exam_questions.id"), nullable=False)
    answer_text = Column(Text)
    is_correct = Column(Boolean)

    # Relationships
    attempt = relationship("ExamAttempt", back_populates="answers")
    question = relationship("ExamQuestion")
