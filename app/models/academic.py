from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.core.database import Base
import datetime

class College(Base):
    __tablename__ = "colleges"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    departments = relationship("Department", back_populates="college")
    users = relationship("User", back_populates="college")


class Department(Base):
    __tablename__ = "departments"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    college_id = Column(Integer, ForeignKey("colleges.id"))
    college = relationship("College", back_populates="departments")
    semesters = relationship("Semester", back_populates="department")
    users = relationship("User", back_populates="department")

class Semester(Base):
    __tablename__ = "semesters"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    department_id = Column(Integer, ForeignKey("departments.id"))
    department = relationship("Department", back_populates="semesters")
    courses = relationship("Course", back_populates="semester")

class Course(Base):
    __tablename__ = "courses"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    code = Column(String, unique=True, index=True)
    semester_id = Column(Integer, ForeignKey("semesters.id"))
    semester = relationship("Semester", back_populates="courses")
    books = relationship("Book", back_populates="course")

class Book(Base):
    __tablename__ = "books"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    language = Column(String)
    course_id = Column(Integer, ForeignKey("courses.id"))
    course = relationship("Course", back_populates="books")
    uploaded_by = Column(String) # Assuming admin_id is a string
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
