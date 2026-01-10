from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.services import chat_service
from app.schemas import chat as chat_schemas
from app.api.dependencies import get_db
from app.core.security import get_current_user
from app.models.user import User

router = APIRouter()

@router.post("/chat/", response_model=chat_schemas.ChatMessage)
def chat_with_book(
    request: chat_schemas.ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Handles a chat request from a user, providing a response based on the
    content of the specified book and the conversation history.
    """
    # 1. Save the user's question to the chat history
    user_message = chat_schemas.ChatMessageCreate(
        book_id=request.book_id,
        role="user",
        message=request.question
    )
    chat_service.save_chat_message(db=db, user_id=current_user.id, message=user_message)

    # 2. Load the recent chat history
    chat_history = chat_service.get_chat_history(db=db, user_id=current_user.id, book_id=request.book_id)

    # 3. Retrieve relevant book chunks
    retrieved_chunks = chat_service.search_book_chunks(book_id=request.book_id, query=request.question)

    # 4. Generate a response
    response_text = chat_service.generate_response(
        chat_history=chat_history,
        retrieved_chunks=retrieved_chunks,
        user_question=request.question
    )

    # 5. Save the assistant's response to the chat history
    assistant_message = chat_schemas.ChatMessageCreate(
        book_id=request.book_id,
        role="assistant",
        message=response_text
    )
    db_assistant_message = chat_service.save_chat_message(db=db, user_id=current_user.id, message=assistant_message)

    return db_assistant_message
