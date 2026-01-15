from sqlalchemy.orm import Session
from app.repository import exam_repository
from app.rag.retriever import retrieve_relevant_chunks
from app.services.llm_service import llm_service
from app.models.academics import Book
from app.models.user import User
from app.models.requests import ExamRequest
import json
from openai import APIError
from app.repository import book_repository

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

def generate_and_store_exam(db: Session, exam_request: ExamRequest):
    book = book_repository.get_book_by_id(db, book_id=exam_request.book_id)
    if not book:
        return None

    relevant_chunks = retrieve_relevant_chunks(f"Exam material for {exam_request.chapter}", top_k=15, collection_name=book.qdrant_collection_name)

    if not relevant_chunks:
        return None

    prompt = create_exam_prompt(relevant_chunks, exam_request.mcq, exam_request.theory)

    try:
        response_text = llm_service.get_chat_completion(prompt)
        cleaned_response = response_text.strip().replace("```json", "").replace("```", "").strip()
        exam_data = json.loads(cleaned_response)
    except (APIError, json.JSONDecodeError):
        return None

    db_exam = exam_repository.create_exam(db, f"Final Exam: {exam_request.chapter}", book)

    for q in exam_data.get("questions", []):
        exam_repository.create_exam_question(
            db,
            db_exam,
            q["question_type"],
            q["question"],
            q.get("options"),
            q["correct_answer"],
        )

    return db_exam
