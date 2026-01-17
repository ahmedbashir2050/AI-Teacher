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

SIMILARITY_THRESHOLD = 0.7
MAX_QUERY_LENGTH = 500

@retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=1, max=2))
async def call_rag_search(user_message: str, collection_name: str, faculty_id: str, semester_id: str, request_id: str):
    async with httpx.AsyncClient(timeout=5.0) as client:
        resp = await client.post(
            f"{settings.RAG_SERVICE_URL}/search",
            json={
                "query": user_message,
                "top_k": 5,
                "collection_name": collection_name,
                "faculty_id": faculty_id,
                "semester_id": semester_id
            },
            headers={"X-Request-ID": request_id}
        )
        resp.raise_for_status()
        return resp.json()

async def handle_chat_message(
    db: Session,
    user_id: str,
    session_id: UUID | None,
    user_message: str,
    collection_name: str,
    faculty_id: str,
    semester_id: str,
    request_id: str = None
) -> tuple:
    # 1. Guardrails: Input Validation
    if not user_message or len(user_message.strip()) == 0:
        return "من فضلك أدخل سؤالاً صحيحاً.", session_id, None, ""

    if len(user_message) > MAX_QUERY_LENGTH:
        return f"عذراً، السؤال طويل جداً. يرجى اختصاره إلى أقل من {MAX_QUERY_LENGTH} حرفاً.", session_id, None, ""

    # Academic Safety: Detect cheating attempts
    cheating_keywords = ["حل الامتحان", "إجابة كاملة", "حل لي هذا", "أعطني الأجوبة"]
    if any(kw in user_message for kw in cheating_keywords):
        return "أنا هنا لمساعدتك في فهم المادة وشرح المفاهيم بأسلوب تعليمي، وليس لحل الامتحانات أو الواجبات بشكل كامل. كيف يمكنني مساعدتك في شرح نقطة معينة؟", session_id, None, ""

    # 2. Get/Create Session
    if session_id:
        chat_session = chat_repository.get_chat_session(db, session_id)
        if not chat_session or str(chat_session.user_id) != user_id:
            chat_session = chat_repository.create_chat_session(db, user_id, collection_name, faculty_id, semester_id)
    else:
        chat_session = chat_repository.create_chat_session(db, user_id, collection_name, faculty_id, semester_id)

    # 3. Memory Optimization: Get history and summary
    chat_history = chat_repository.get_chat_messages(db, session_id=chat_session.id)
    # Only keep very recent messages for flow, rely on summary for long-term memory
    history_formatted = [{"role": msg.role, "content": msg.content} for msg in chat_history[-3:]]
    history_str = "\n".join([f"{m['role']}: {m['content']}" for m in history_formatted])

    learning_summary = chat_session.learning_summary or chat_repository.get_latest_learning_summary(db, user_id, collection_name)

    # 4. Intent Detection & Query Rewriting
    analysis = await llm_service.detect_intent_and_rewrite_query(user_message, history_str)
    intent = analysis.get("intent", "GENERAL")
    mode = analysis.get("mode", "UNDERSTANDING")
    rewritten_query = analysis.get("rewritten_query", user_message)

    # 5. RAG Hardening: Multi-stage Retrieval with Threshold
    relevant_chunks = []
    max_score = 0.0
    cache_used = False

    if intent not in ["OUTSIDE_SYLLABUS", "GENERAL"]:
        try:
            # Intelligent Caching for RAG results
            results = await llm_service.get_cached_rag_results(rewritten_query, collection_name, faculty_id, semester_id)
            if results:
                cache_used = True
            else:
                results = await call_rag_search(rewritten_query, collection_name, faculty_id, semester_id, request_id)
                await llm_service.cache_rag_results(rewritten_query, collection_name, faculty_id, semester_id, results)

            # Enforce similarity score threshold
            filtered_results = [r for r in results if r.get("score", 0) >= SIMILARITY_THRESHOLD]
            if filtered_results:
                max_score = max(r.get("score", 0) for r in filtered_results)
                initial_chunks = [r["text"] for r in filtered_results]
                # Re-ranking
                relevant_chunks = await llm_service.rerank_results(rewritten_query, initial_chunks)
        except Exception as e:
            logger.error(f"RAG service error: {e}", extra={"request_id": request_id})

    # 6. Generate Response with Structured Validation
    if not relevant_chunks and intent not in ["GENERAL"]:
         assistant_message = "عذراً، هذا الموضوع غير مغطى في الكتاب المقرر المتاح لي حالياً. أنا مصمم للمساعدة في محتوى المنهج الدراسي فقط لضمان دقة المعلومات."
    else:
        prompt_messages = create_teacher_prompt(
            relevant_chunks,
            user_message,
            history_formatted,
            learning_summary,
            intent=intent,
            mode=mode
        )

        # Intelligent Caching for Responses
        assistant_message = await llm_service.get_cached_response(faculty_id, semester_id, user_message)
        if assistant_message:
            cache_used = True
        else:
            assistant_message = await llm_service.get_chat_completion_with_validation(prompt_messages)
            await llm_service.cache_response(faculty_id, semester_id, user_message, assistant_message)

    # 7. AI Quality Evaluation Logging
    quality_flag = "PASS" if (relevant_chunks or intent == "GENERAL") and len(assistant_message) > 20 else "FAIL"
    logger.info(f"AI_QUALITY_LOG: req={request_id} intent={intent} rag_score={max_score} cache={cache_used} resp_len={len(assistant_message)} flag={quality_flag}")

    # 8. Save messages
    chat_repository.create_chat_message(db, chat_session.id, "user", user_message)
    chat_repository.create_chat_message(db, chat_session.id, "assistant", assistant_message)

    # Prepare background task info (summarization)
    # We summarize if history is getting long
    history_delta = f"user: {user_message}\nassistant: {assistant_message}"

    return assistant_message, chat_session.id, learning_summary, history_delta

async def update_learning_summary_task(db: Session, session_id: UUID, current_summary: str, history_delta: str):
    """
    Background task to update the learning summary without blocking the user response.
    """
    try:
        updated_summary = await llm_service.summarize_learning_state(current_summary or "", history_delta)
        chat_repository.update_session_summary(db, session_id, updated_summary)
    except Exception as e:
        logger.error(f"Failed to update learning summary: {e}")
