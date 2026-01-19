from uuid import UUID, uuid4

from models.exam import Exam, Question
from sqlalchemy.orm import Session


def create_exam(db: Session, title: str, course_id: str, creator_id: str):
    db_exam = Exam(id=uuid4(), title=title, course_id=course_id, creator_id=creator_id)
    db.add(db_exam)
    db.commit()
    db.refresh(db_exam)
    return db_exam


def create_exam_question(
    db: Session,
    exam_id: UUID,
    content: str,
    options: list = None,
    correct_answer: str = None,
):
    db_q = Question(
        id=uuid4(),
        exam_id=exam_id,
        content=content,
        options=options,
        correct_answer=correct_answer,
    )
    db.add(db_q)
    db.commit()
    db.refresh(db_q)
    return db_q


def get_exam(db: Session, exam_id: UUID):
    return db.query(Exam).filter(Exam.id == exam_id, Exam.is_deleted.is_(None)).first()


def get_exam_questions(db: Session, exam_id: UUID):
    return (
        db.query(Question)
        .filter(Question.exam_id == exam_id, Question.is_deleted.is_(None))
        .all()
    )
