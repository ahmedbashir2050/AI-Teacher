from db.base import BaseModel
from sqlalchemy import JSON, Boolean, Column, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID


class ChatSession(BaseModel):
    __tablename__ = "chat_sessions"
    user_id = Column(UUID(as_uuid=True), index=True, nullable=False)
    collection_name = Column(String(255), index=True)
    faculty_id = Column(String(255), index=True)
    semester_id = Column(String(255), index=True)
    book_id = Column(UUID(as_uuid=True), index=True) # Scoped to a specific book
    learning_summary = Column(Text)  # Summarized user learning state
    title = Column(String(255))


class ChatMessage(BaseModel):
    __tablename__ = "chat_messages"
    session_id = Column(
        UUID(as_uuid=True), ForeignKey("chat_sessions.id"), index=True, nullable=False
    )
    role = Column(String(50), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)


class AnswerAuditLog(BaseModel):
    __tablename__ = "answer_audit_logs"
    user_id = Column(UUID(as_uuid=True), index=True, nullable=False)
    session_id = Column(UUID(as_uuid=True), index=True)
    book_id = Column(String(255), index=True)
    question_text = Column(Text, nullable=False)
    ai_answer = Column(Text, nullable=False)
    source_reference = Column(Text)  # JSON string of source info
    verified = Column(Boolean, default=False)
    verified_by_teacher = Column(Boolean, default=False)
    teacher_comment = Column(Text)
    rag_confidence_score = Column(Float)
    custom_tags = Column(JSON)
    is_correct = Column(Boolean, nullable=True)  # student feedback
