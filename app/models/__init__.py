# app/models/__init__.py
"""
This file makes the models package and allows for easy importing of all ORM models.
Importing all models here is also crucial for Alembic's autogenerate feature
to detect all the defined models and generate the correct migration scripts.
"""

from .user import User, Role, RoleEnum
from .academics import Faculty, Department, Semester, Course, Book
from .chat import ChatSession, ChatMessage
from .exam import Exam, ExamAttempt

__all__ = [
    "User",
    "Role",
    "RoleEnum",
    "Faculty",
    "Department",
    "Semester",
    "Course",
    "Book",
    "ChatSession",
    "ChatMessage",
    "Exam",
    "ExamAttempt",
]
