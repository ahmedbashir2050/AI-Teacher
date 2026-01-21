from db.base import BaseModel
from sqlalchemy import Column, ForeignKey, Integer, String, Boolean, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID

class Faculty(BaseModel):
    __tablename__ = "faculties"
    name = Column(String(255), unique=True, index=True, nullable=False)
    departments = relationship(
        "Department", back_populates="faculty", cascade="all, delete-orphan"
    )

class Department(BaseModel):
    __tablename__ = "departments"
    name = Column(String(255), index=True, nullable=False)
    faculty_id = Column(ForeignKey("faculties.id"), nullable=False, index=True)
    faculty = relationship("Faculty", back_populates="departments")
    books = relationship("Book", back_populates="department", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("name", "faculty_id", name="_department_faculty_uc"),
    )

class Book(BaseModel):
    __tablename__ = "books"
    title = Column(String(255), nullable=False, index=True)
    faculty_id = Column(ForeignKey("faculties.id"), nullable=False, index=True)
    department_id = Column(ForeignKey("departments.id"), nullable=False, index=True)
    semester = Column(Integer, nullable=False, index=True)
    language = Column(String(50), nullable=False, default="ar")
    file_key = Column(String(512), unique=True, nullable=False)
    file_hash = Column(String(64), unique=True, index=True, nullable=False) # For duplicate detection
    uploaded_by = Column(UUID(as_uuid=True), nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    is_approved = Column(Boolean, default=False, nullable=False, index=True)
    approved_by = Column(UUID(as_uuid=True), nullable=True)

    faculty = relationship("Faculty")
    department = relationship("Department", back_populates="books")
