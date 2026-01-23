from sqlalchemy import Column, String, JSON, Integer
from sqlalchemy.dialects.postgresql import UUID
from db.base import BaseModel

class ProExam(BaseModel):
    __tablename__ = "pro_exams"

    title = Column(String(255), nullable=False)
    book_id = Column(UUID(as_uuid=True), index=True, nullable=False)
    faculty_id = Column(UUID(as_uuid=True), index=True)
    department_id = Column(UUID(as_uuid=True), index=True)
    semester_id = Column(UUID(as_uuid=True), index=True)

    # Store the full exam structure: sections, questions, correct answers, and source page info
    # format: { "sections": [ { "type": "matching", "questions": [...] }, ... ] }
    content = Column(JSON, nullable=False)

    time_limit_minutes = Column(Integer, default=60)
