import json
from datetime import datetime
from uuid import UUID, uuid4

from models.chat import AnswerAuditLog, ChatMessage, ChatSession
from sqlalchemy.orm import Session


def get_chat_session(db: Session, session_id: UUID):
    return (
        db.query(ChatSession)
        .filter(ChatSession.id == session_id, ChatSession.is_deleted.is_(None))
        .first()
    )


def create_chat_session(
    db: Session,
    user_id: str,
    collection_name: str = None,
    faculty_id: str = None,
    semester_id: str = None,
):
    session = ChatSession(
        id=uuid4(),
        user_id=user_id,
        collection_name=collection_name,
        faculty_id=faculty_id,
        semester_id=semester_id,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def get_latest_learning_summary(db: Session, user_id: str, collection_name: str):
    latest_session = (
        db.query(ChatSession)
        .filter(
            ChatSession.user_id == user_id,
            ChatSession.collection_name == collection_name,
            ChatSession.learning_summary.is_not(None),
        )
        .order_by(ChatSession.created_at.desc())
        .first()
    )
    return latest_session.learning_summary if latest_session else None


def update_session_summary(db: Session, session_id: UUID, summary: str):
    session = get_chat_session(db, session_id)
    if session:
        session.learning_summary = summary
        db.commit()
        db.refresh(session)
    return session


def get_chat_messages(db: Session, session_id: UUID):
    return (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
        .all()
    )


def create_chat_message(db: Session, session_id: UUID, role: str, content: str):
    message = ChatMessage(session_id=session_id, role=role, content=content)
    db.add(message)
    db.commit()
    db.refresh(message)
    return message


def soft_delete_session(db: Session, session_id: UUID, user_id: str):
    session = (
        db.query(ChatSession)
        .filter(ChatSession.id == session_id, ChatSession.user_id == user_id)
        .first()
    )
    if session:
        session.is_deleted = datetime.utcnow()
        db.commit()
        return True
    return False


def create_answer_audit_log(
    db: Session,
    user_id: str,
    session_id: UUID,
    question_text: str,
    ai_answer: str,
    source_info: dict,
    book_id: str = None,
    rag_confidence_score: float = None,
):
    log_entry = AnswerAuditLog(
        id=uuid4(),
        user_id=user_id,
        session_id=session_id,
        book_id=book_id,
        question_text=question_text,
        ai_answer=ai_answer,
        source_reference=json.dumps(source_info),
        verified=False,
        rag_confidence_score=rag_confidence_score,
    )
    db.add(log_entry)
    db.commit()
    db.refresh(log_entry)
    return log_entry


def update_answer_feedback(db: Session, log_id: UUID, is_correct: bool):
    log_entry = db.query(AnswerAuditLog).filter(AnswerAuditLog.id == log_id).first()
    if log_entry:
        log_entry.is_correct = is_correct
        db.commit()
        db.refresh(log_entry)
        return True
    return False


def verify_answer_by_teacher(
    db: Session, log_id: UUID, verified: bool, comment: str = None, custom_tags: list = None
):
    log_entry = db.query(AnswerAuditLog).filter(AnswerAuditLog.id == log_id).first()
    if log_entry:
        log_entry.verified_by_teacher = verified
        log_entry.teacher_comment = comment
        if custom_tags is not None:
            log_entry.custom_tags = custom_tags
        db.commit()
        db.refresh(log_entry)
        return True
    return False


def get_answers_for_review(
    db: Session, faculty_id: str = None, skip: int = 0, limit: int = 50
):
    query = db.query(AnswerAuditLog).join(
        ChatSession, AnswerAuditLog.session_id == ChatSession.id
    )
    if faculty_id:
        query = query.filter(ChatSession.faculty_id == faculty_id)

    return (
        query.order_by(AnswerAuditLog.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


from sqlalchemy import func, case


def get_performance_stats(db: Session, faculty_id: str = None):
    query = db.query(
        func.avg(AnswerAuditLog.rag_confidence_score).label("avg_confidence"),
        func.count(AnswerAuditLog.id).label("total_answers"),
        func.avg(case((AnswerAuditLog.is_correct == True, 1), else_=0)).label(
            "positive_feedback_rate"
        ),
    ).join(ChatSession, AnswerAuditLog.session_id == ChatSession.id)

    if faculty_id:
        query = query.filter(ChatSession.faculty_id == faculty_id)

    stats = query.one()
    return {
        "avg_confidence": float(stats.avg_confidence or 0),
        "total_answers": int(stats.total_answers or 0),
        "positive_feedback_rate": float(stats.positive_feedback_rate or 0),
    }


def verify_answer(db: Session, log_id: UUID, verified: bool = True):
    log_entry = db.query(AnswerAuditLog).filter(AnswerAuditLog.id == log_id).first()
    if log_entry:
        log_entry.verified = verified
        db.commit()
        db.refresh(log_entry)
        return True
    return False
