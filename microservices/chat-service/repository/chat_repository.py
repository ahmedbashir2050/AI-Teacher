from sqlalchemy.orm import Session
from models.chat import ChatSession, ChatMessage
from uuid import UUID, uuid4
from datetime import datetime

def get_chat_session(db: Session, session_id: UUID):
    return db.query(ChatSession).filter(ChatSession.id == session_id, ChatSession.is_deleted.is_(None)).first()

def create_chat_session(db: Session, user_id: str, collection_name: str = None, faculty_id: str = None, semester_id: str = None):
    session = ChatSession(
        id=uuid4(),
        user_id=user_id,
        collection_name=collection_name,
        faculty_id=faculty_id,
        semester_id=semester_id
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session

def get_latest_learning_summary(db: Session, user_id: str, collection_name: str):
    latest_session = db.query(ChatSession).filter(
        ChatSession.user_id == user_id,
        ChatSession.collection_name == collection_name,
        ChatSession.learning_summary.is_not(None)
    ).order_by(ChatSession.created_at.desc()).first()
    return latest_session.learning_summary if latest_session else None

def update_session_summary(db: Session, session_id: UUID, summary: str):
    session = get_chat_session(db, session_id)
    if session:
        session.learning_summary = summary
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

def soft_delete_session(db: Session, session_id: UUID, user_id: str):
    session = db.query(ChatSession).filter(ChatSession.id == session_id, ChatSession.user_id == user_id).first()
    if session:
        session.is_deleted = datetime.utcnow()
        db.commit()
        return True
    return False
