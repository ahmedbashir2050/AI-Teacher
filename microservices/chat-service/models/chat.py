from sqlalchemy import Column, String, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from ..db.base import BaseModel

class ChatSession(BaseModel):
    __tablename__ = 'chat_sessions'
    user_id = Column(UUID(as_uuid=True), index=True, nullable=False)
    title = Column(String(255))

class ChatMessage(BaseModel):
    __tablename__ = 'chat_messages'
    session_id = Column(UUID(as_uuid=True), ForeignKey('chat_sessions.id'), nullable=False)
    role = Column(String(50), nullable=False) # 'user' or 'assistant'
    content = Column(Text, nullable=False)
