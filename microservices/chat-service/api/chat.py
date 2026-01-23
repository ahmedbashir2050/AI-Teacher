from typing import Optional, List
from uuid import UUID

from core.audit import log_audit
from core.cache import cache_result
from core.metrics import START_CHAT_TOTAL
from db.session import get_db, get_read_db
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


class AnswerReviewResponse(BaseModel):
    id: UUID
    user_id: UUID
    question_text: str
    ai_answer: str
    rag_confidence_score: Optional[float] = None
    verified_by_teacher: bool
    teacher_comment: Optional[str] = None
    custom_tags: Optional[List[str]] = None
    is_correct: Optional[bool] = None

    class Config:
        from_attributes = True


class TeacherVerifyRequest(BaseModel):
    verified: bool
    comment: Optional[str] = None
    custom_tags: Optional[List[str]] = None


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


@router.post("/student/{student_id}/start-chat")
async def start_chat(
    student_id: UUID,
    payload: dict, # { book_id }
    db: Session = Depends(get_db),
    x_user_id: str = Header(...),
    x_faculty_id: Optional[str] = Header(None),
    x_semester_id: Optional[str] = Header(None),
):
    if str(student_id) != x_user_id:
        raise HTTPException(status_code=403, detail="Unauthorized")

    book_id = UUID(payload.get("book_id"))

    # 1. Verify selection via internal call to library-service
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(
                f"{settings.LIBRARY_SERVICE_URL}/student/verify-selection/{student_id}/{book_id}"
            )
            if resp.status_code != 200 or not resp.json().get("is_selected"):
                raise HTTPException(status_code=400, detail="Book is not selected by student")
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail="Failed to verify book selection")
        except Exception as e:
             raise HTTPException(status_code=500, detail=f"Selection verification error: {e}")

    # 2. Create session scoped to this book
    from repository import chat_repository
    collection_name = payload.get("collection_name", "academic")

    session = chat_repository.create_chat_session(
        db,
        user_id=x_user_id,
        collection_name=collection_name,
        faculty_id=x_faculty_id,
        semester_id=x_semester_id,
        book_id=book_id
    )

    START_CHAT_TOTAL.inc()

    log_audit(x_user_id, "START_BOOK_CHAT", "chat_session", str(session.id), metadata={"book_id": str(book_id)})

    return {"session_id": session.id, "book_id": book_id}


@router.post("/internal/sessions/invalidate")
async def invalidate_sessions(
    payload: dict, # { user_id, book_id }
    db: Session = Depends(get_db)
):
    """
    Invalidates active chat sessions for a user tied to a specific book.
    Triggered when a book is removed or profile changes.
    """
    from repository import chat_repository
    user_id = payload.get("user_id")
    book_id = payload.get("book_id")

    if not user_id:
        raise HTTPException(status_code=400, detail="user_id is required")

    # If book_id is provided, invalidate sessions for that book
    # If not, invalidate ALL sessions for the user (profile change case)
    chat_repository.invalidate_user_sessions(db, UUID(user_id), UUID(book_id) if book_id else None)

    return {"status": "sessions invalidated"}


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


@router.get("/teacher/answers", response_model=List[AnswerReviewResponse])
async def get_teacher_answers(
    db: Session = Depends(get_read_db),
    x_user_role: str = Header(...),
    x_user_faculty_id: Optional[str] = Header(None),
):
    if x_user_role not in ["teacher", "admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Unauthorized")

    # Strict RBAC: Teachers MUST have a faculty_id
    if x_user_role == "teacher" and not x_user_faculty_id:
        raise HTTPException(status_code=403, detail="Teacher faculty context missing")

    from repository import chat_repository

    return chat_repository.get_answers_for_review(db, faculty_id=x_user_faculty_id)


@router.post("/teacher/answers/{answer_id}/verify")
async def teacher_verify(
    answer_id: UUID,
    request: TeacherVerifyRequest,
    fastapi_req: Request,
    db: Session = Depends(get_db),
    x_user_id: str = Header(...),
    x_user_role: str = Header(...),
):
    if x_user_role not in ["teacher", "admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Unauthorized")

    from repository import chat_repository

    success = chat_repository.verify_answer_by_teacher(
        db, answer_id, request.verified, request.comment, request.custom_tags
    )
    if not success:
        raise HTTPException(status_code=404, detail="Answer not found")

    log_audit(
        x_user_id,
        "teacher_verify",
        "answer_audit_log",
        resource_id=str(answer_id),
        metadata={"verified": request.verified, "comment": request.comment},
        request_id=getattr(fastapi_req.state, "request_id", None),
    )
    return {"status": "success"}


@router.post("/teacher/answers/{answer_id}/feedback")
async def teacher_feedback(
    answer_id: UUID,
    request: TeacherVerifyRequest,  # Reuse model for feedback
    fastapi_req: Request,
    db: Session = Depends(get_db),
    x_user_id: str = Header(...),
    x_user_role: str = Header(...),
):
    if x_user_role not in ["teacher", "admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Unauthorized")

    from repository import chat_repository

    # Feedback is essentially a verification with a comment
    success = chat_repository.verify_answer_by_teacher(
        db, answer_id, True, request.comment, request.custom_tags
    )
    if not success:
        raise HTTPException(status_code=404, detail="Answer not found")

    log_audit(
        x_user_id,
        "teacher_feedback",
        "answer_audit_log",
        resource_id=str(answer_id),
        metadata={"comment": request.comment},
        request_id=getattr(fastapi_req.state, "request_id", None),
    )
    return {"status": "success"}


@router.get("/teacher/students/{student_id}/ai-confidence")
@cache_result(ttl=600)
async def get_student_confidence(
    student_id: UUID,
    db: Session = Depends(get_read_db),
    x_user_role: str = Header(...),
):
    if x_user_role not in ["teacher", "admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Unauthorized")

    from repository import chat_repository

    confidence = chat_repository.get_student_ai_confidence(db, student_id)
    return {"student_id": student_id, "ai_confidence_score": confidence or 0.0}


@router.get("/teacher/courses/{course_id}/progress")
@cache_result(ttl=600)
async def get_course_chat_progress(
    course_id: str,
    db: Session = Depends(get_read_db),
    x_user_role: str = Header(...),
):
    if x_user_role not in ["teacher", "admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Unauthorized")

    from repository import chat_repository

    stats = chat_repository.get_course_progress(db, course_id)
    return {
        "course_id": course_id,
        "total_interactions": stats.total_interactions,
        "avg_confidence": float(stats.avg_confidence or 0),
        "unique_students": stats.unique_students,
    }


@router.get("/teacher/performance")
async def get_teacher_performance(
    db: Session = Depends(get_read_db),
    x_user_role: str = Header(...),
    x_user_faculty_id: Optional[str] = Header(None),
):
    if x_user_role not in ["teacher", "admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Unauthorized")

    # Strict RBAC: Teachers MUST have a faculty_id
    if x_user_role == "teacher" and not x_user_faculty_id:
        raise HTTPException(status_code=403, detail="Teacher faculty context missing")

    from repository import chat_repository

    return chat_repository.get_performance_stats(db, faculty_id=x_user_faculty_id)


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
