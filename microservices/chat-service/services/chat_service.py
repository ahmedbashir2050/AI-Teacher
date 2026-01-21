import json
import logging
from uuid import UUID

import httpx
from core.audit import log_audit
from core.metrics import (
    ANSWERS_TOTAL,
    HALLUCINATIONS_BLOCKED_TOTAL,
    SIMILARITY_SCORE,
    ANSWER_LATENCY,
)
from core.config import settings
from rag.prompt import create_teacher_prompt
from repository import chat_repository
from services.llm_service import llm_service
from sqlalchemy.orm import Session
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

SIMILARITY_THRESHOLD = 0.7
MAX_QUERY_LENGTH = 500


@retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=1, max=2))
async def call_rag_search(
    user_message: str,
    collection_name: str,
    faculty_id: str,
    semester_id: str,
    request_id: str,
):
    async with httpx.AsyncClient(timeout=5.0) as client:
        resp = await client.post(
            f"{settings.RAG_SERVICE_URL}/search",
            json={
                "query": user_message,
                "top_k": 5,
                "collection_name": collection_name,
                "faculty_id": faculty_id,
                "semester_id": semester_id,
            },
            headers={"X-Request-ID": request_id},
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
    request_id: str = None,
) -> tuple:
    with ANSWER_LATENCY.time():
        return await _handle_chat_message_logic(
            db,
            user_id,
            session_id,
            user_message,
            collection_name,
            faculty_id,
            semester_id,
            request_id,
        )


async def _handle_chat_message_logic(
    db: Session,
    user_id: str,
    session_id: UUID | None,
    user_message: str,
    collection_name: str,
    faculty_id: str,
    semester_id: str,
    request_id: str = None,
) -> tuple:
    # 1. Get/Create Session
    if session_id:
        chat_session = chat_repository.get_chat_session(db, session_id)
        if not chat_session or str(chat_session.user_id) != user_id:
            chat_session = chat_repository.create_chat_session(
                db, user_id, collection_name, faculty_id, semester_id
            )
    else:
        chat_session = chat_repository.create_chat_session(
            db, user_id, collection_name, faculty_id, semester_id
        )

    # 2. Guardrails: Input Validation
    if not user_message or len(user_message.strip()) == 0:
        return "من فضلك أدخل سؤالاً صحيحاً.", chat_session.id, None, "", {}, {}, None

    if len(user_message) > MAX_QUERY_LENGTH:
        return (
            f"عذراً، السؤال طويل جداً. يرجى اختصاره إلى أقل من {MAX_QUERY_LENGTH} حرفاً.",
            chat_session.id,
            None,
            "",
            {},
            {},
            None
        )

    # Academic Safety: Detect cheating attempts
    cheating_keywords = ["حل الامتحان", "إجابة كاملة", "حل لي هذا", "أعطني الأجوبة"]
    if any(kw in user_message for kw in cheating_keywords):
        return (
            "أنا هنا لمساعدتك في فهم المادة وشرح المفاهيم بأسلوب تعليمي، وليس لحل الامتحانات أو الواجبات بشكل كامل. كيف يمكنني مساعدتك في شرح نقطة معينة؟",
            chat_session.id,
            None,
            "",
            {},
            {},
            None
        )

    # 3. Memory Optimization: Get history and summary
    chat_history = chat_repository.get_chat_messages(db, session_id=chat_session.id)
    # Only keep very recent messages for flow, rely on summary for long-term memory
    history_formatted = [
        {"role": msg.role, "content": msg.content} for msg in chat_history[-3:]
    ]
    history_str = "\n".join([f"{m['role']}: {m['content']}" for m in history_formatted])

    learning_summary = (
        chat_session.learning_summary
        or chat_repository.get_latest_learning_summary(db, user_id, collection_name)
    )

    # 4. Intent Detection & Query Rewriting
    analysis = await llm_service.detect_intent_and_rewrite_query(
        user_message, history_str
    )
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
            results = await llm_service.get_cached_rag_results(
                rewritten_query, collection_name, faculty_id, semester_id
            )
            if results:
                cache_used = True
            else:
                results = await call_rag_search(
                    rewritten_query,
                    collection_name,
                    faculty_id,
                    semester_id,
                    request_id,
                )
                await llm_service.cache_rag_results(
                    rewritten_query, collection_name, faculty_id, semester_id, results
                )

            # Enforce similarity score threshold
            filtered_results = [
                r for r in results if r.get("score", 0) >= SIMILARITY_THRESHOLD
            ]
            if filtered_results:
                max_score = max(r.get("score", 0) for r in filtered_results)
                SIMILARITY_SCORE.observe(max_score)
                # Keep full objects for source attribution
                relevant_chunks = filtered_results
        except Exception as e:
            logger.error(f"RAG service error: {e}", extra={"request_id": request_id})

    # 6. Generate Response with Structured Validation
    source_info = {"book": "N/A", "page": "N/A"}
    hallucination_detected = False

    if not relevant_chunks and intent not in ["GENERAL"]:
        assistant_message = "عذراً، هذا الموضوع غير مغطى في الكتاب المقرر المتاح لي حالياً. أنا مصمم للمساعدة في محتوى المنهج الدراسي فقط لضمان دقة المعلومات."
    else:
        prompt_messages = create_teacher_prompt(
            relevant_chunks,
            user_message,
            history_formatted,
            learning_summary,
            intent=intent,
            mode=mode,
        )

        # Intelligent Caching for Responses
        cached_resp = await llm_service.get_cached_response(
            faculty_id, semester_id, user_message
        )
        if cached_resp:
            cache_used = True
            try:
                resp_json = json.loads(cached_resp)
                assistant_message = resp_json.get("answer", "")
                source_info = resp_json.get("source", source_info)
            except:
                assistant_message = cached_resp
        else:
            context_text = "\n".join([c["text"] for c in relevant_chunks])
            resp_data = await llm_service.get_chat_completion_with_validation(
                prompt_messages, context=context_text
            )
            assistant_message = resp_data.get("answer", "")
            source_info = resp_data.get("source", source_info)
            hallucination_detected = resp_data.get("hallucination", False)

            if not hallucination_detected:
                await llm_service.cache_response(
                    faculty_id, semester_id, user_message, json.dumps(resp_data)
                )

    # 7. AI Quality Evaluation Logging
    quality_flag = "PASS"
    if hallucination_detected:
        quality_flag = "HALLUCINATION"
        HALLUCINATIONS_BLOCKED_TOTAL.inc()
    elif (not relevant_chunks and intent != "GENERAL") or len(assistant_message) < 20:
        quality_flag = "FAIL"

    ANSWERS_TOTAL.labels(faculty_id=faculty_id, status=quality_flag).inc()

    logger.info(
        f"AI_QUALITY_LOG: req={request_id} intent={intent} rag_score={max_score} cache={cache_used} "
        f"resp_len={len(assistant_message)} flag={quality_flag} source={source_info}"
    )

    if hallucination_detected:
        log_audit(
            user_id,
            "hallucination_blocked",
            "chat_message",
            metadata={
                "question": user_message,
                "answer": assistant_message,
                "rag_score": max_score,
            },
            request_id=request_id,
        )

    # 8. Save messages and Audit Log
    chat_repository.create_chat_message(db, chat_session.id, "user", user_message)
    chat_repository.create_chat_message(
        db, chat_session.id, "assistant", assistant_message
    )

    audit_log = chat_repository.create_answer_audit_log(
        db,
        user_id=user_id,
        session_id=chat_session.id,
        question_text=user_message,
        ai_answer=assistant_message,
        source_info=source_info,
        book_id=relevant_chunks[0].get("book_id") if relevant_chunks else None,
        rag_confidence_score=max_score,
    )

    # Prepare background task info (summarization)
    # We summarize if history is getting long
    history_delta = f"user: {user_message}\nassistant: {assistant_message}"

    metadata = {
        "intent": intent,
        "mode": mode,
        "rag_score": max_score,
        "cache_used": cache_used,
        "relevant_chunks_count": len(relevant_chunks),
        "quality_flag": quality_flag,
        "source": source_info,
    }

    return (
        assistant_message,
        chat_session.id,
        learning_summary,
        history_delta,
        metadata,
        source_info,
        audit_log.id,
    )


async def update_learning_summary_task(
    db: Session, session_id: UUID, current_summary: str, history_delta: str
):
    """
    Background task to update the learning summary without blocking the user response.
    """
    try:
        updated_summary = await llm_service.summarize_learning_state(
            current_summary or "", history_delta
        )
        chat_repository.update_session_summary(db, session_id, updated_summary)
    except Exception as e:
        logger.error(f"Failed to update learning summary: {e}")
