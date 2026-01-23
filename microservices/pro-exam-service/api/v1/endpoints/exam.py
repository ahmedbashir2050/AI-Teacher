from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from db.session import get_db
from models.exam import ProExam
from models.submission import ProExamSubmission
from tasks.exam_tasks import generate_pro_exam_task
from pydantic import BaseModel, UUID4
from datetime import datetime
from typing import Optional
import copy
import random

router = APIRouter()

class ExamGenerateRequest(BaseModel):
    book_id: UUID4
    faculty_id: UUID4
    department_id: UUID4
    semester_id: UUID4
    title: str

class SessionStartRequest(BaseModel):
    exam_id: UUID4

@router.post("/generate")
async def generate_exam(request: ExamGenerateRequest, x_request_id: Optional[str] = Header(None)):
    task = generate_pro_exam_task.delay(
        str(request.book_id),
        str(request.faculty_id),
        str(request.department_id),
        str(request.semester_id),
        request.title,
        x_request_id
    )
    return {"task_id": task.id, "message": "Exam generation started"}

@router.get("/{exam_id}")
async def get_exam(exam_id: UUID4, db: Session = Depends(get_db)):
    exam = db.query(ProExam).filter(ProExam.id == exam_id, ProExam.is_deleted == None).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")

    # Remove correct answers before sending to student
    content = copy.deepcopy(exam.content)
    for section in content.get("sections", []):
        if section["type"] == "matching":
            # Provide shuffled options for matching to prevent direct leakage
            all_b = [q["item_b"] for q in section["questions"]]
            random.shuffle(all_b)
            section["shuffled_options_b"] = all_b
            for q in section.get("questions", []):
                q.pop("item_b", None)
                q.pop("correct_answer", None)
        else:
            for q in section.get("questions", []):
                q.pop("correct_answer", None)

    return {
        "id": exam.id,
        "title": exam.title,
        "book_id": exam.book_id,
        "time_limit_minutes": exam.time_limit_minutes,
        "content": content
    }

@router.post("/start")
async def start_exam(request: SessionStartRequest, db: Session = Depends(get_db), x_user_id: str = Header(...)):
    # Check if active session already exists
    existing = db.query(ProExamSubmission).filter(
        ProExamSubmission.exam_id == request.exam_id,
        ProExamSubmission.student_id == x_user_id,
        ProExamSubmission.status == "STARTED"
    ).first()

    if existing:
        return {"submission_id": existing.id, "start_time": existing.start_time}

    new_session = ProExamSubmission(
        exam_id=request.exam_id,
        student_id=x_user_id,
        start_time=datetime.utcnow(),
        status="STARTED"
    )
    db.add(new_session)
    db.commit()
    db.refresh(new_session)

    return {"submission_id": new_session.id, "start_time": new_session.start_time}
