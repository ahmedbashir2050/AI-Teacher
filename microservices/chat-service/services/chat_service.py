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
    # 1. Get/Create Session
    if session_id:
        chat_session = chat_repository.get_chat_session(db, session_id)
        if not chat_session or str(chat_session.user_id) != user_id:
            chat_session = chat_repository.create_chat_session(db, user_id, collection_name)
    else:
        chat_session = chat_repository.create_chat_session(db, user_id, collection_name)

    # 2. Get history and learning state
    chat_history = chat_repository.get_chat_messages(db, session_id=chat_session.id)
    history_formatted = [{"role": msg.role, "content": msg.content} for msg in chat_history]
    history_str = "\n".join([f"{m['role']}: {m['content']}" for m in history_formatted[-5:]])

    learning_summary = chat_session.learning_summary or chat_repository.get_latest_learning_summary(db, user_id, collection_name)

    # 3. Intent Detection & Query Rewriting
    analysis = await llm_service.detect_intent_and_rewrite_query(user_message, history_str)
    intent = analysis.get("intent", "GENERAL")
    mode = analysis.get("mode", "UNDERSTANDING")
    rewritten_query = analysis.get("rewritten_query", user_message)

    # 4. Multi-stage Retrieval
    relevant_chunks = []
    if intent != "OUTSIDE_SYLLABUS":
        try:
            results = await call_rag_search(rewritten_query, collection_name, request_id)
            initial_chunks = [r["text"] for r in results]
            # Re-ranking
            relevant_chunks = await llm_service.rerank_results(rewritten_query, initial_chunks)
        except Exception as e:
            logger.error(f"RAG service error: {e}", extra={"request_id": request_id})

    # 5. Generate Response
    if not relevant_chunks and intent != "GENERAL":
         assistant_message = "عذراً، هذا الموضوع غير مغطى في الكتاب المقرر. أنا هنا لمساعدتك في محتوى المنهج فقط."
    else:
        prompt_messages = create_teacher_prompt(
            relevant_chunks,
            user_message,
            history_formatted,
            learning_summary,
            intent=intent,
            mode=mode
        )
        assistant_message = await llm_service.get_chat_completion(prompt_messages)

    # 6. Save messages
    chat_repository.create_chat_message(db, chat_session.id, "user", user_message)
    chat_repository.create_chat_message(db, chat_session.id, "assistant", assistant_message)

    # Prepare background task info
    new_history_str = history_str + f"\nuser: {user_message}\nassistant: {assistant_message}"

    return assistant_message, chat_session.id, learning_summary, new_history_str

async def update_learning_summary_task(db: Session, session_id: UUID, current_summary: str, history_delta: str):
    """
    Background task to update the learning summary without blocking the user response.
    """
    try:
        updated_summary = await llm_service.summarize_learning_state(current_summary or "", history_delta)
        chat_repository.update_session_summary(db, session_id, updated_summary)
    except Exception as e:
        logger.error(f"Failed to update learning summary: {e}")
