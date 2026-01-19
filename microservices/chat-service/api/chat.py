from typing import Optional
from uuid import UUID

from core.audit import log_audit
from db.session import get_db
from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    Header,
    HTTPException,
    Request,
    status,
)
from fastapi_limiter.depends import RateLimiter
from pydantic import BaseModel
from services import chat_service
from sqlalchemy.orm import Session

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[UUID] = None
    collection_name: str
    faculty_id: Optional[str] = None
    semester_id: Optional[str] = None


class ChatResponse(BaseModel):
    answer: str
    source: dict
    session_id: UUID
    audit_log_id: Optional[UUID] = None


class FeedbackRequest(BaseModel):
    audit_log_id: UUID
    is_correct: bool


def get_user_id_key(request: Request):
    # Use X-User-Id for rate limiting
    return request.headers.get("X-User-Id", request.client.host)


@router.delete("/session/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    x_user_id: str = Header(...),
):
    from repository import chat_repository

    request_id = getattr(request.state, "request_id", None)
    success = chat_repository.soft_delete_session(db, session_id, x_user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found or unauthorized")

    log_audit(
        x_user_id,
        "delete",
        "chat_session",
        resource_id=str(session_id),
        request_id=request_id,
    )
    return None


@router.post(
    "/chat",
    response_model=ChatResponse,
    dependencies=[
        Depends(RateLimiter(times=20, minutes=1, identifier=get_user_id_key))
    ],
)
async def chat(
    request: ChatRequest,
    fastapi_req: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    x_user_id: str = Header(...),
    x_faculty_id: Optional[str] = Header(None),
    x_semester_id: Optional[str] = Header(None),
):
    request_id = getattr(fastapi_req.state, "request_id", None)

    # Enforce Faculty + Semester context (from request or headers)
    faculty_id = request.faculty_id or x_faculty_id
    semester_id = request.semester_id or x_semester_id

    if not faculty_id or not semester_id:
        raise HTTPException(
            status_code=400,
            detail="Academic context (Faculty and Semester) is required and non-bypassable.",
        )

    (
        assistant_message,
        session_id,
        learning_summary,
        history_delta,
        metadata,
        source_info,
        audit_log_id,
    ) = await chat_service.handle_chat_message(
        db,
        user_id=x_user_id,
        session_id=request.session_id,
        user_message=request.message,
        collection_name=request.collection_name,
        faculty_id=faculty_id,
        semester_id=semester_id,
        request_id=request_id,
    )

    # Offload summarization to background
    background_tasks.add_task(
        chat_service.update_learning_summary_task,
        db,
        session_id,
        learning_summary,
        history_delta,
    )

    log_audit(
        x_user_id,
        "message",
        "chat_session",
        resource_id=str(session_id),
        metadata=metadata,
        request_id=request_id,
    )
    return ChatResponse(
        answer=assistant_message,
        source=source_info,
        session_id=session_id,
        audit_log_id=audit_log_id,
    )


@router.post("/feedback")
async def student_feedback(
    request: FeedbackRequest,
    db: Session = Depends(get_db),
    x_user_id: str = Header(...),
):
    from core.metrics import STUDENT_FEEDBACK_TOTAL
    from repository import chat_repository

    success = chat_repository.update_answer_feedback(
        db, request.audit_log_id, request.is_correct
    )
    if success:
        STUDENT_FEEDBACK_TOTAL.labels(is_correct=str(request.is_correct)).inc()
    if not success:
        raise HTTPException(status_code=404, detail="Audit log not found")
    return {"status": "success"}


@router.post("/verify/{log_id}")
async def admin_verify(
    log_id: UUID,
    verified: bool = True,
    db: Session = Depends(get_db),
    x_user_role: str = Header(...),
):
    if x_user_role not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Unauthorized")

    from core.metrics import VERIFIED_ANSWERS_TOTAL
    from repository import chat_repository

    success = chat_repository.verify_answer(db, log_id, verified)
    if success:
        VERIFIED_ANSWERS_TOTAL.labels(is_verified=str(verified)).inc()
    if not success:
        raise HTTPException(status_code=404, detail="Audit log not found")
    return {"status": "success"}
