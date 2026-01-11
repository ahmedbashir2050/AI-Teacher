from sqlalchemy import Column, String, ForeignKey, UUID
from sqlalchemy.orm import relationship
from app.core.database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, index=True) # Firebase UID
    role = Column(String, index=True) # "admin", "academic", or "student"
    faculty_id = Column(UUID(as_uuid=True), ForeignKey("faculties.id"), nullable=True)
    department_id = Column(UUID(as_uuid=True), ForeignKey("departments.id"), nullable=True)

    faculty = relationship("Faculty", back_populates="users")
    department = relationship("Department", back_populates="users")
