# app/models/academics.py
from sqlalchemy import Column, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship

from app.db.base import BaseModel


class Faculty(BaseModel):
    """
    Represents a faculty (e.g., 'Faculty of Engineering').
    This is the top level of the academic hierarchy.
    """

    __tablename__ = "faculties"

    name = Column(String(255), unique=True, index=True, nullable=False)

    # One-to-many relationship: A faculty has many departments.
    # cascade="all, delete-orphan" ensures that when a faculty is deleted,
    # all its associated departments are also deleted.
    departments = relationship(
        "Department", back_populates="faculty", cascade="all, delete-orphan"
    )


class Department(BaseModel):
    """
    Represents a department within a faculty (e.g., 'Computer Science').
    """

    __tablename__ = "departments"

    name = Column(String(255), index=True, nullable=False)
    faculty_id = Column(ForeignKey("faculties.id"), nullable=False, index=True)

    # Many-to-one relationship: A department belongs to one faculty.
    faculty = relationship("Faculty", back_populates="departments")

    # One-to-many relationship: A department has many semesters.
    semesters = relationship(
        "Semester", back_populates="department", cascade="all, delete-orphan"
    )

    __table_args__ = (
        # Ensures that department names are unique within the same faculty.
        UniqueConstraint("name", "faculty_id", name="_department_faculty_uc"),
    )


class Semester(BaseModel):
    """
    Represents a semester within a department (e.g., 'Fall 2024').
    """

    __tablename__ = "semesters"

    # Using an integer for the semester number is efficient for sorting and querying.
    semester_number = Column(Integer, nullable=False)
    department_id = Column(ForeignKey("departments.id"), nullable=False, index=True)

    # Many-to-one relationship: A semester belongs to one department.
    department = relationship("Department", back_populates="semesters")

    # One-to-many relationship: A semester has many courses.
    courses = relationship(
        "Course", back_populates="semester", cascade="all, delete-orphan"
    )

    __table_args__ = (
        # Ensures that semester numbers are unique within the same department.
        UniqueConstraint(
            "semester_number", "department_id", name="_semester_department_uc"
        ),
    )


class Course(BaseModel):
    """
    Represents a course within a semester (e.g., 'Introduction to AI').
    """

    __tablename__ = "courses"

    name = Column(String(255), index=True, nullable=False)
    semester_id = Column(ForeignKey("semesters.id"), nullable=False, index=True)

    # Many-to-one relationship: A course belongs to one semester.
    semester = relationship("Semester", back_populates="courses")

    # One-to-many relationship: A course can have multiple books/materials.
    books = relationship("Book", back_populates="course", cascade="all, delete-orphan")

    __table_args__ = (
        # Ensures that course names are unique within the same semester.
        UniqueConstraint("name", "semester_id", name="_course_semester_uc"),
    )


class Book(BaseModel):
    """
    Represents a book or curriculum document for a specific course.
    This is the content that will be ingested into the RAG system.
    """

    __tablename__ = "books"

    title = Column(String(255), nullable=False)
    # The qdrant_collection_name will be dynamically generated and stored here
    # to ensure strict data isolation between different faculties and semesters.
    qdrant_collection_name = Column(
        String(255), unique=True, index=True, nullable=False
    )
    course_id = Column(ForeignKey("courses.id"), nullable=False, index=True)

    # Many-to-one relationship: A book belongs to one course.
    course = relationship("Course", back_populates="books")
