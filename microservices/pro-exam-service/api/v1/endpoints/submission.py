from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from db.session import get_db
from models.exam import ProExam
from models.submission import ProExamSubmission
from services.scoring_service import scoring_service
from core.audit import log_audit
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import Optional

router = APIRouter()

class SubmissionRequest(BaseModel):
    answers: dict # { "matching_1": [...], "tf": [...], ... }

@router.post("/{submission_id}/submit")
async def submit_exam(
    submission_id: str,
    request: SubmissionRequest,
    db: Session = Depends(get_db),
    x_user_id: str = Header(...)
):
    submission = db.query(ProExamSubmission).filter(
        ProExamSubmission.id == submission_id,
        ProExamSubmission.student_id == x_user_id
    ).first()

    if not submission:
        raise HTTPException(status_code=404, detail="Submission session not found")

    if submission.status != "STARTED":
        raise HTTPException(status_code=400, detail="Exam already submitted or expired")

    exam = db.query(ProExam).filter(ProExam.id == submission.exam_id).first()

    # Check timing
    now = datetime.utcnow()
    # Allowing 2 minutes grace period for network latency
    limit = submission.start_time + timedelta(minutes=exam.time_limit_minutes + 2)

    if now > limit:
        submission.status = "EXPIRED"
        db.commit()
        raise HTTPException(status_code=403, detail="Submission rejected: Time limit exceeded")

    # Scoring
    total_score, section_scores = scoring_service.calculate_score(exam.content, request.answers)

    # Persistence
    submission.answers = request.answers
    submission.submission_time = now
    submission.status = "SUBMITTED"
    submission.total_score = total_score
    submission.section_scores = section_scores

    db.commit()

    log_audit(
        user_id=x_user_id,
        action="exam_submit",
        resource="pro_exam",
        resource_id=str(exam.id),
        metadata={"submission_id": submission_id, "score": total_score}
    )

    return {
        "final_score": total_score,
        "section_breakdown": section_scores,
        "correct_answers": exam.content,
        "submission_time": submission.submission_time
    }

@router.get("/results/{submission_id}")
async def get_results(
    submission_id: str,
    db: Session = Depends(get_db),
    x_user_id: str = Header(...)
):
    submission = db.query(ProExamSubmission).filter(
        ProExamSubmission.id == submission_id,
        ProExamSubmission.student_id == x_user_id
    ).first()

    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    if submission.status != "SUBMITTED":
        raise HTTPException(status_code=400, detail="Results not available yet")

    exam = db.query(ProExam).filter(ProExam.id == submission.exam_id).first()

    return {
        "final_score": submission.total_score,
        "section_breakdown": submission.section_scores,
        "answers": submission.answers,
        "correct_answers": exam.content,
        "submission_time": submission.submission_time
    }
