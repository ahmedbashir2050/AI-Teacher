from sqlalchemy import Column, String, ForeignKey, Text, Integer, JSON
from sqlalchemy.dialects.postgresql import UUID
from db.base import BaseModel

class Exam(BaseModel):
    __tablename__ = 'exams'
    title = Column(String(255), nullable=False)
    course_id = Column(UUID(as_uuid=True), nullable=False)
    creator_id = Column(UUID(as_uuid=True), nullable=False)

class Question(BaseModel):
    __tablename__ = 'questions'
    exam_id = Column(UUID(as_uuid=True), ForeignKey('exams.id'), nullable=False)
    content = Column(Text, nullable=False)
    options = Column(JSON) # For multiple choice
    correct_answer = Column(Text)

class ExamAttempt(BaseModel):
    __tablename__ = 'exam_attempts'
    exam_id = Column(UUID(as_uuid=True), ForeignKey('exams.id'), nullable=False)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    score = Column(Integer)
    answers = Column(JSON)
