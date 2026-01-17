from sqlalchemy.orm import Session
from ..repository import exam_repository
from .llm_service import llm_service
import json
import httpx
from ..core.config import settings
import logging
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

@retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=1, max=2))
async def call_rag_search(collection_name: str, request_id: str):
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(
            f"{settings.RAG_SERVICE_URL}/search",
            json={"query": "Exam material", "top_k": 15, "collection_name": collection_name},
            headers={"X-Request-ID": request_id}
        )
        resp.raise_for_status()
        return resp.json()

def create_exam_prompt(context: list[str], mcq_count: int, theory_count: int) -> str:
    context_str = "\n\n".join(context)
    prompt = f"""
Based ONLY on the provided academic text, generate a university-level exam.
The exam must contain exactly {mcq_count} multiple-choice questions and {theory_count} theory-based essay questions.
Provide a model answer for every question.

Format the output as a single JSON object with a key "questions", which is a list.
Each question in the list must be an object with the following keys:
- "question_type": either "mcq" or "theory".
- "question": The full text of the question.
- "options" (for mcq only): A list of 4 strings representing the choices.
- "correct_answer": The model answer. For mcqs, this should be one of the options.

Academic Text:
{context_str}
"""
    return prompt.strip()

async def generate_and_store_exam(db: Session, user_id: str, course_id: str, collection_name: str, mcq_count: int, theory_count: int, request_id: str = None):
    relevant_chunks = []
    try:
        results = await call_rag_search(collection_name, request_id)
        relevant_chunks = [r["text"] for r in results]
    except Exception as e:
        logger.error(f"Error calling RAG service for exam: {e}", extra={"request_id": request_id})

    if not relevant_chunks:
        return None

    prompt = create_exam_prompt(relevant_chunks, mcq_count, theory_count)

    try:
        response_text = await llm_service.get_chat_completion(prompt)
        cleaned_response = response_text.strip().replace("```json", "").replace("```", "").strip()
        exam_data = json.loads(cleaned_response)
    except Exception as e:
        logger.error(f"Error generating exam with LLM: {e}", extra={"request_id": request_id})
        return None

    db_exam = exam_repository.create_exam(db, f"Exam for {course_id}", course_id, user_id)

    for q in exam_data.get("questions", []):
        exam_repository.create_exam_question(
            db,
            db_exam.id,
            q["question"],
            q.get("options"),
            q["correct_answer"],
        )

    return db_exam
