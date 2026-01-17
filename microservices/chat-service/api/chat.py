from fastapi import APIRouter, Depends, HTTPException, Header, Request, BackgroundTasks
from sqlalchemy.orm import Session
from ..db.session import get_db
from ..services import chat_service
from pydantic import BaseModel
from uuid import UUID
from typing import Optional
from fastapi_limiter.depends import RateLimiter

router = APIRouter()

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[UUID] = None
    collection_name: str
    faculty_id: Optional[str] = None
    semester_id: Optional[str] = None

class ChatResponse(BaseModel):
    message: str
    session_id: UUID

def get_user_id_key(request: Request):
    # Use X-User-Id for rate limiting
    return request.headers.get("X-User-Id", request.client.host)

@router.post("/chat", response_model=ChatResponse, dependencies=[Depends(RateLimiter(times=20, minutes=1, identifier=get_user_id_key))])
async def chat(
    request: ChatRequest,
    fastapi_req: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    x_user_id: str = Header(...),
    x_faculty_id: Optional[str] = Header(None),
    x_semester_id: Optional[str] = Header(None)
):
    request_id = getattr(fastapi_req.state, "request_id", None)

    # Enforce Faculty + Semester context (from request or headers)
    faculty_id = request.faculty_id or x_faculty_id
    semester_id = request.semester_id or x_semester_id

    if not faculty_id or not semester_id:
        raise HTTPException(status_code=400, detail="Academic context (Faculty and Semester) is required and non-bypassable.")

    assistant_message, session_id, learning_summary, history_delta = await chat_service.handle_chat_message(
        db,
        user_id=x_user_id,
        session_id=request.session_id,
        user_message=request.message,
        collection_name=request.collection_name,
        faculty_id=faculty_id,
        semester_id=semester_id,
        request_id=request_id
    )

    # Offload summarization to background
    background_tasks.add_task(
        chat_service.update_learning_summary_task,
        db,
        session_id,
        learning_summary,
        history_delta
    )

    return ChatResponse(message=assistant_message, session_id=session_id)
