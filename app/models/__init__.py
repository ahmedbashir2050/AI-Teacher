# app/models/__init__.py
"""
This file makes the models package and allows for easy importing of all ORM models.
Importing all models here is also crucial for Alembic's autogenerate feature
to detect all the defined models and generate the correct migration scripts.
"""

from .academics import Book, Course, Department, Faculty, Semester
from .chat import ChatMessage, ChatSession
from .exam import Exam, ExamAttempt
from .user import Role, RoleEnum, User

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
