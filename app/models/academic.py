from sqlalchemy import Column, String, ForeignKey, DateTime, UUID
from sqlalchemy.orm import relationship
from app.core.database import Base
import datetime
import uuid

class Faculty(Base):
    __tablename__ = "faculties"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    departments = relationship("Department", back_populates="faculty")
    users = relationship("User", back_populates="faculty")


class Department(Base):
    __tablename__ = "departments"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, index=True)
    faculty_id = Column(UUID(as_uuid=True), ForeignKey("faculties.id"))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    faculty = relationship("Faculty", back_populates="departments")
    semesters = relationship("Semester", back_populates="department")
    users = relationship("User", back_populates="department")

class Semester(Base):
    __tablename__ = "semesters"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, index=True)
    department_id = Column(UUID(as_uuid=True), ForeignKey("departments.id"))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    department = relationship("Department", back_populates="semesters")
    books = relationship("Book", back_populates="semester")

class Book(Base):
    __tablename__ = "books"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, index=True)
    language = Column(String)
    semester_id = Column(UUID(as_uuid=True), ForeignKey("semesters.id"))
    qdrant_collection = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    semester = relationship("Semester", back_populates="books")
