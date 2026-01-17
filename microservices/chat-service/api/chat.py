from fastapi import APIRouter, Depends, HTTPException, Header, Request
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
    db: Session = Depends(get_db),
    x_user_id: str = Header(...)
):
    request_id = getattr(fastapi_req.state, "request_id", None)

    assistant_message, session_id = await chat_service.handle_chat_message(
        db,
        user_id=x_user_id,
        session_id=request.session_id,
        user_message=request.message,
        collection_name=request.collection_name,
        request_id=request_id
    )
    return ChatResponse(message=assistant_message, session_id=session_id)
