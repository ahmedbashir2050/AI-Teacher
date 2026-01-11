from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.services import chat_service, academic_service
from app.schemas import chat as chat_schemas
from app.api.dependencies import get_db
from app.core.security import get_current_user
from app.models.user import User
import uuid

router = APIRouter()

def get_current_student_user(current_user: User = Depends(get_current_user)):
    if current_user.role != "student":
        raise HTTPException(status_code=403, detail="The user doesn't have enough privileges")
    return current_user

@router.post("/chat/ask", response_model=dict)
def ask_question(
    request: chat_schemas.ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_student_user)
):
    """
    Handles a chat request from a user, providing a response based on the
    content of the specified book and the conversation history.
    """
    # 1. Get the book from the database
    book = academic_service.get_book(db, book_id=request.book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    # 2. Save the user's question to the chat history
    chat_service.save_chat_message(db, user_id=current_user.id, book_id=request.book_id, role="user", message=request.question)

    # 3. Load the recent chat history
    chat_history = chat_service.get_chat_history(db, user_id=current_user.id, book_id=request.book_id)

    # 4. Retrieve relevant book chunks
    retrieved_chunks = chat_service.search_book_chunks(
        collection_name=book.qdrant_collection,
        book_id=request.book_id,
        query=request.question
    )

    # 5. Generate a response
    response_text = chat_service.generate_response(
        chat_history=chat_history,
        retrieved_chunks=retrieved_chunks,
        user_question=request.question
    )

    # 6. Save the assistant's response to the chat history
    chat_service.save_chat_message(db, user_id=current_user.id, book_id=request.book_id, role="ai", message=response_text)

    return {"answer": response_text}
