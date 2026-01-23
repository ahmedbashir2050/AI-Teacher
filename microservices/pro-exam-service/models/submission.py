from sqlalchemy import Column, DateTime, JSON, Integer, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from db.base import BaseModel

class ProExamSubmission(BaseModel):
    __tablename__ = "pro_exam_submissions"

    exam_id = Column(UUID(as_uuid=True), ForeignKey("pro_exams.id"), index=True, nullable=False)
    student_id = Column(UUID(as_uuid=True), index=True, nullable=False)

    start_time = Column(DateTime, nullable=False)
    submission_time = Column(DateTime, nullable=True)

    status = Column(String(50), default="STARTED") # STARTED, SUBMITTED, EXPIRED

    # Store student answers only after submission
    answers = Column(JSON, nullable=True)

    # Results
    total_score = Column(Integer, nullable=True)
    section_scores = Column(JSON, nullable=True) # { "matching_1": 20, "matching_2": 20, "tf": 20, "mcq": 40 }

    request_id = Column(String(255), nullable=True)
