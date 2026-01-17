from fastapi import APIRouter, Depends, HTTPException, Header, Request
from sqlalchemy.orm import Session
from ..db.session import get_db
from ..services import exam_service
from ..repository import exam_repository
from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID

router = APIRouter()

class ExamCreateRequest(BaseModel):
    course_id: str
    collection_name: str
    mcq_count: int = 5
    theory_count: int = 2

class ExamResponse(BaseModel):
    id: UUID
    title: str
    course_id: str

@router.post("/generate", response_model=ExamResponse)
async def generate_exam(
    request: ExamCreateRequest,
    fastapi_req: Request,
    db: Session = Depends(get_db),
    x_user_id: str = Header(...)
):
    request_id = getattr(fastapi_req.state, "request_id", None)

    exam = await exam_service.generate_and_store_exam(
        db,
        user_id=x_user_id,
        course_id=request.course_id,
        collection_name=request.collection_name,
        mcq_count=request.mcq_count,
        theory_count=request.theory_count,
        request_id=request_id
    )
    if not exam:
        raise HTTPException(status_code=500, detail="Failed to generate exam")
    return exam

@router.get("/{exam_id}", response_model=ExamResponse)
def get_exam(exam_id: UUID, db: Session = Depends(get_db)):
    exam = exam_repository.get_exam(db, exam_id)
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    return exam
