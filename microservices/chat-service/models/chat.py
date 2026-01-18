from sqlalchemy import Column, String, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from db.base import BaseModel

class ChatSession(BaseModel):
    __tablename__ = 'chat_sessions'
    user_id = Column(UUID(as_uuid=True), index=True, nullable=False)
    collection_name = Column(String(255), index=True)
    faculty_id = Column(String(255), index=True)
    semester_id = Column(String(255), index=True)
    learning_summary = Column(Text) # Summarized user learning state
    title = Column(String(255))

class ChatMessage(BaseModel):
    __tablename__ = 'chat_messages'
    session_id = Column(UUID(as_uuid=True), ForeignKey('chat_sessions.id'), index=True, nullable=False)
    role = Column(String(50), nullable=False) # 'user' or 'assistant'
    content = Column(Text, nullable=False)
