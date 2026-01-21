from uuid import UUID, uuid4

from models.exam import Exam, ExamAttempt, Question
from sqlalchemy.orm import Session


def create_exam(
    db: Session,
    title: str,
    course_id: str,
    creator_id: str,
    faculty_id: str = None,
    semester_id: str = None,
):
    db_exam = Exam(
        id=uuid4(),
        title=title,
        course_id=course_id,
        creator_id=creator_id,
        faculty_id=faculty_id,
        semester_id=semester_id,
    )
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


from sqlalchemy import func


def get_performance_stats(db: Session, course_id: str = None, faculty_id: str = None):
    query = db.query(
        func.avg(ExamAttempt.score).label("average_score"),
        func.count(ExamAttempt.id).label("total_attempts"),
    ).join(Exam)

    if course_id:
        query = query.filter(Exam.course_id == course_id)
    if faculty_id:
        query = query.filter(Exam.faculty_id == faculty_id)

    stats = query.one()
    return {
        "average_score": float(stats.average_score or 0),
        "total_attempts": int(stats.total_attempts or 0),
    }
