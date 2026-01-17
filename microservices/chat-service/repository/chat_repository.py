from sqlalchemy.orm import Session
from ..models.chat import ChatSession, ChatMessage
from uuid import UUID, uuid4

def get_chat_session(db: Session, session_id: UUID):
    return db.query(ChatSession).filter(ChatSession.id == session_id).first()

def create_chat_session(db: Session, user_id: str):
    session = ChatSession(id=uuid4(), user_id=user_id)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session

def get_chat_messages(db: Session, session_id: UUID):
    return db.query(ChatMessage).filter(ChatMessage.session_id == session_id).order_by(ChatMessage.created_at.asc()).all()

def create_chat_message(db: Session, session_id: UUID, role: str, content: str):
    message = ChatMessage(session_id=session_id, role=role, content=content)
    db.add(message)
    db.commit()
    db.refresh(message)
    return message
