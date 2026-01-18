from sqlalchemy import Column, String, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from db.base import BaseModel

class Faculty(BaseModel):
    __tablename__ = 'faculties'
    name = Column(String(255), unique=True, index=True, nullable=False)
    departments = relationship("Department", back_populates="faculty", cascade="all, delete-orphan")

class Department(BaseModel):
    __tablename__ = 'departments'
    name = Column(String(255), index=True, nullable=False)
    faculty_id = Column(ForeignKey('faculties.id'), nullable=False, index=True)
    faculty = relationship("Faculty", back_populates="departments")
    semesters = relationship("Semester", back_populates="department", cascade="all, delete-orphan")
    __table_args__ = (UniqueConstraint('name', 'faculty_id', name='_department_faculty_uc'),)

class Semester(BaseModel):
    __tablename__ = 'semesters'
    semester_number = Column(Integer, nullable=False)
    department_id = Column(ForeignKey('departments.id'), nullable=False, index=True)
    department = relationship("Department", back_populates="semesters")
    courses = relationship("Course", back_populates="semester", cascade="all, delete-orphan")
    __table_args__ = (UniqueConstraint('semester_number', 'department_id', name='_semester_department_uc'),)

class Course(BaseModel):
    __tablename__ = 'courses'
    name = Column(String(255), index=True, nullable=False)
    semester_id = Column(ForeignKey('semesters.id'), nullable=False, index=True)
    semester = relationship("Semester", back_populates="courses")
    books = relationship("Book", back_populates="course", cascade="all, delete-orphan")
    __table_args__ = (UniqueConstraint('name', 'semester_id', name='_course_semester_uc'),)

class Book(BaseModel):
    __tablename__ = 'books'
    title = Column(String(255), nullable=False)
    qdrant_collection_name = Column(String(255), unique=True, index=True, nullable=False)
    course_id = Column(ForeignKey('courses.id'), nullable=False, index=True)
    course = relationship("Course", back_populates="books")
