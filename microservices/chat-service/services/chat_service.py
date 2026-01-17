from sqlalchemy.orm import Session
from ..repository import chat_repository
from ..rag.prompt import create_teacher_prompt
from .llm_service import llm_service
from uuid import UUID
import httpx
from ..core.config import settings
import logging
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

@retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=1, max=2))
async def call_rag_search(user_message: str, collection_name: str, request_id: str):
    async with httpx.AsyncClient(timeout=5.0) as client:
        resp = await client.post(
            f"{settings.RAG_SERVICE_URL}/search",
            json={"query": user_message, "top_k": 5, "collection_name": collection_name},
            headers={"X-Request-ID": request_id}
        )
        resp.raise_for_status()
        return resp.json()

async def handle_chat_message(db: Session, user_id: str, session_id: UUID | None, user_message: str, collection_name: str, request_id: str = None) -> tuple[str, UUID]:
    if session_id:
        chat_session = chat_repository.get_chat_session(db, session_id)
        if not chat_session or str(chat_session.user_id) != user_id:
            chat_session = chat_repository.create_chat_session(db, user_id)
    else:
        chat_session = chat_repository.create_chat_session(db, user_id)

    chat_repository.create_chat_message(db, chat_session.id, "user", user_message)
    chat_history = chat_repository.get_chat_messages(db, session_id=chat_session.id)

    # Call RAG Service with retries and timeout
    relevant_chunks = []
    try:
        results = await call_rag_search(user_message, collection_name, request_id)
        relevant_chunks = [r["text"] for r in results]
    except Exception as e:
        logger.error(f"RAG service error or unavailable: {e}", extra={"request_id": request_id})
        # Graceful degradation: If RAG fails, we could use a generic fallback or history-only
        # For now, we'll proceed with empty chunks which leads to "outside curriculum" response
        pass

    if not relevant_chunks:
        assistant_message = "هذا السؤال خارج المقرر"
    else:
        history_formatted = [{"role": msg.role, "content": msg.content} for msg in chat_history]
        prompt = create_teacher_prompt(relevant_chunks, user_message, history_formatted)
        assistant_message = await llm_service.get_chat_completion(prompt)

    chat_repository.create_chat_message(db, chat_session.id, "assistant", assistant_message)

    return assistant_message, chat_session.id
