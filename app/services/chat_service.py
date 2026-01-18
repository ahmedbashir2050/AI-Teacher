from sqlalchemy.orm import Session
from app.repository import chat_repository
from app.rag.retriever import retrieve_relevant_chunks
from app.rag.prompt import create_teacher_prompt
from app.services.llm_service import llm_service
from app.models.user import User
from uuid import UUID
from app.repository import book_repository

def handle_chat_message(db: Session, user: User, session_id: UUID | None, user_message: str, book_id: int) -> tuple[str, UUID]:
    book = book_repository.get_book_by_id(db, book_id=book_id)
    if not book:
        return "Book not found.", None

    if session_id:
        chat_session = chat_repository.get_chat_session(db, session_id)
        if not chat_session:
            # Handle case where session_id is provided but not found, or doesn't belong to the user
            chat_session = chat_repository.create_chat_session(db, user)
    else:
        chat_session = chat_repository.create_chat_session(db, user)

    chat_repository.create_chat_message(db, chat_session.id, "user", user_message)

    chat_history = chat_repository.get_chat_messages(db, session_id=chat_session.id)

    relevant_chunks = retrieve_relevant_chunks(user_message, collection_name=book.qdrant_collection_name)

    if not relevant_chunks:
        assistant_message = "هذا السؤال خارج المقرر"
    else:
        prompt = create_teacher_prompt(relevant_chunks, user_message, chat_history)
        assistant_message = llm_service.get_chat_completion(prompt)

    chat_repository.create_chat_message(db, chat_session.id, "assistant", assistant_message)

    return assistant_message, chat_session.id
