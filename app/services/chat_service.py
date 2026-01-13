from sqlalchemy.orm import Session
from app.repository import chat_repository
from app.rag.retriever import retrieve_relevant_chunks
from app.rag.prompt import create_teacher_prompt
from app.services.llm_service import llm_service
from app.models.db import User
from uuid import UUID

def handle_chat_message(db: Session, user: User, session_id: UUID | None, user_message: str) -> tuple[str, UUID]:
    if session_id:
        chat_session = chat_repository.get_chat_session(db, session_id)
        if not chat_session:
            # Handle case where session_id is provided but not found, or doesn't belong to the user
            chat_session = chat_repository.create_chat_session(db, user)
    else:
        chat_session = chat_repository.create_chat_session(db, user)

    chat_repository.create_chat_message(db, chat_session.id, "user", user_message)

    # For now, we'll keep the RAG logic the same. We can enhance this later to use chat history.
    relevant_chunks = retrieve_relevant_chunks(user_message)

    if not relevant_chunks:
        assistant_message = "هذا السؤال خارج المقرر"
    else:
        prompt = create_teacher_prompt(relevant_chunks, user_message)
        assistant_message = llm_service.get_chat_completion(prompt)

    chat_repository.create_chat_message(db, chat_session.id, "assistant", assistant_message)

    return assistant_message, chat_session.id
