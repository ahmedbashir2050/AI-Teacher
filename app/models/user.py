from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, index=True) # Firebase UID
    role = Column(String, index=True) # "admin" or "student"
    college_id = Column(Integer, ForeignKey("colleges.id"), nullable=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)

    college = relationship("College", back_populates="users")
    department = relationship("Department", back_populates="users")
