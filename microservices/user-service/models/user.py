from db.base import BaseModel
from sqlalchemy import Column, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID


class UserProfile(BaseModel):
    __tablename__ = "user_profiles"

    user_id = Column(UUID(as_uuid=True), unique=True, index=True, nullable=False)
    full_name = Column(String(255))
    faculty_id = Column(ForeignKey("faculties.id"), index=True, nullable=True)
    department_id = Column(ForeignKey("departments.id"), index=True, nullable=True)
    semester_id = Column(ForeignKey("semesters.id"), index=True, nullable=True)
