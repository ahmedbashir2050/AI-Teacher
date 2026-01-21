from typing import Optional, List
from uuid import UUID

from core.audit import log_audit
from core.cache import cache_result
from db.session import get_db, get_read_db
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel
from repository import exam_repository
from sqlalchemy.orm import Session
from tasks import generate_exam_task

router = APIRouter()


class ExamCreateRequest(BaseModel):
    course_id: str
    collection_name: str
    faculty_id: str
    semester_id: str
    mcq_count: int = 5
    theory_count: int = 2


class ExamResponse(BaseModel):
    id: Optional[UUID] = None
    title: Optional[str] = None
    course_id: str
    status: str = "pending"
    task_id: Optional[str] = None


@router.post("/generate", response_model=ExamResponse)
async def generate_exam(
    request: ExamCreateRequest,
    fastapi_req: Request,
    db: Session = Depends(get_db),
    x_user_id: str = Header(...),
):
    request_id = getattr(fastapi_req.state, "request_id", None)

    # Trigger async task
    task = generate_exam_task.delay(
        x_user_id,
        request.course_id,
        request.collection_name,
        request.faculty_id,
        request.semester_id,
        request.mcq_count,
        request.theory_count,
        request_id,
    )

    log_audit(
        user_id=x_user_id,
        action="generate_request",
        resource="exam",
        metadata={
            "course_id": request.course_id,
            "collection_name": request.collection_name,
            "task_id": task.id,
        },
        request_id=request_id,
    )

    return ExamResponse(course_id=request.course_id, status="accepted", task_id=task.id)


@router.get("/{exam_id}", response_model=ExamResponse)
def get_exam(exam_id: UUID, db: Session = Depends(get_read_db)):
    exam = exam_repository.get_exam(db, exam_id)
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    return exam


@router.get("/teacher/performance")
async def get_teacher_performance(
    course_id: Optional[str] = None,
    db: Session = Depends(get_read_db),
    x_user_role: str = Header(...),
    x_user_faculty_id: Optional[str] = Header(None),
):
    if x_user_role not in ["teacher", "admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Unauthorized")

    # Strict RBAC: Teachers MUST have a faculty_id
    if x_user_role == "teacher" and not x_user_faculty_id:
        raise HTTPException(status_code=403, detail="Teacher faculty context missing")

    return exam_repository.get_performance_stats(
        db, course_id=course_id, faculty_id=x_user_faculty_id
    )


@router.get("/teacher/courses/{course_id}/progress")
@cache_result(ttl=600)
async def get_course_exam_progress(
    course_id: str,
    db: Session = Depends(get_read_db),
    x_user_role: str = Header(...),
    x_user_faculty_id: Optional[str] = Header(None),
):
    if x_user_role not in ["teacher", "admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Unauthorized")

    # Strict RBAC: Teachers MUST have a faculty_id
    if x_user_role == "teacher" and not x_user_faculty_id:
        raise HTTPException(status_code=403, detail="Teacher faculty context missing")

    results = exam_repository.get_course_progress(db, course_id)
    return [
        {
            "student_id": str(r.user_id),
            "avg_score": float(r.avg_score or 0),
            "exams_taken": r.exams_taken,
        }
        for r in results
    ]
