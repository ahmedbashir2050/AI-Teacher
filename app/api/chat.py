from fastapi import APIRouter, HTTPException, Depends, Request
from app.models.requests import ChatRequest
from app.models.responses import ChatResponse
from app.services import chat_service
from app.core.security import STUDENT_ACCESS
from app.core.limiter import limiter
from app.db.session import get_db
from sqlalchemy.orm import Session
from app.models.user import User
from uuid import UUID

router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
@limiter.limit("5/minute")
async def chat_with_teacher(request: Request, chat_request: ChatRequest, db: Session = Depends(get_db), current_user: User = Depends(STUDENT_ACCESS)):
    """
    Handles a student's question by retrieving relevant context
    from the curriculum, generating a grounded answer, and saving the conversation.
    """
    try:
        assistant_message, session_id = chat_service.handle_chat_message(db, current_user, chat_request.session_id, chat_request.question, chat_request.book_id)
        if not session_id:
            raise HTTPException(status_code=404, detail=assistant_message)
        return ChatResponse(answer=assistant_message, session_id=session_id)
    except Exception as e:
        # Log the error for debugging
        print(f"Chat endpoint error: {e}")
        raise HTTPException(status_code=500, detail="An internal error occurred.")
