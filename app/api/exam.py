from fastapi import APIRouter, HTTPException, Depends
from app.models.requests import ExamRequest, ExamSubmissionRequest
from app.models.responses import ExamResponse, ExamQuestion, ExamResultResponse
from app.services import exam_service
from app.core.security import STUDENT_ACCESS
from app.db.session import get_db
from sqlalchemy.orm import Session
from app.models.user import User
from app.repository import exam_repository

router = APIRouter()

@router.post("/exam", response_model=ExamResponse)
async def generate_exam(request: ExamRequest, db: Session = Depends(get_db), current_user: User = Depends(STUDENT_ACCESS)):
    """
    Generates a university-style exam from the curriculum content and stores it in the database.
    """
    db_exam = exam_service.generate_and_store_exam(db, request)

    if not db_exam:
        raise HTTPException(status_code=500, detail="Failed to generate or store the exam.")

    questions = [ExamQuestion(
        question_type=q.question_type.value,
        question=q.question_text,
        options=q.options,
        correct_answer=q.correct_answer,
    ) for q in db_exam.questions]

    return ExamResponse(
        exam_id=db_exam.id,
        exam_title=db_exam.title,
        questions=questions,
    )

@router.post("/exam/{exam_id}/submit", response_model=ExamResultResponse)
async def submit_exam(exam_id: int, submission: ExamSubmissionRequest, db: Session = Depends(get_db), current_user: User = Depends(STUDENT_ACCESS)):
    """
    Submits a student's answers for an exam and returns the score.
    """
    db_exam = exam_repository.get_exam(db, exam_id)
    if not db_exam:
        raise HTTPException(status_code=404, detail="Exam not found.")

    # In a real application, you'd have more sophisticated logic for scoring
    # and handling submissions.
    score = 0
    total_questions = len(db_exam.questions)

    db_attempt = exam_repository.create_exam_attempt(db, db_exam, current_user)

    for answer in submission.answers:
        question = next((q for q in db_exam.questions if q.id == answer.question_id), None)
        if question:
            is_correct = answer.answer_text == question.correct_answer
            if is_correct:
                score += 1
            exam_repository.create_exam_attempt_answer(
                db, db_attempt, question, answer.answer_text, is_correct
            )

    db_attempt.score = score
    db.commit()

    return ExamResultResponse(
        attempt_id=db_attempt.id,
        score=score,
        total_questions=total_questions,
    )
