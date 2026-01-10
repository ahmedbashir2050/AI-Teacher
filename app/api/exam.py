from fastapi import APIRouter, HTTPException
from app.models.requests import ExamRequest
from app.models.responses import ExamResponse, ExamQuestion
from app.rag.retriever import retrieve_relevant_chunks
from app.services.llm_service import llm_service
from openai import APIError
import json

router = APIRouter()

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

@router.post("/exam", response_model=ExamResponse)
async def generate_exam(request: ExamRequest):
    """
    Generates a university-style exam from the curriculum content.
    """
    try:
        relevant_chunks = retrieve_relevant_chunks(f"Exam material for {request.chapter}", top_k=15)

        if not relevant_chunks:
             raise HTTPException(status_code=404, detail="Could not find sufficient content for the specified chapter.")

        prompt = create_exam_prompt(relevant_chunks, request.mcq, request.theory)
        response_text = llm_service.get_chat_completion(prompt)

        cleaned_response = response_text.strip().replace("```json", "").replace("```", "").strip()

        try:
            exam_data = json.loads(cleaned_response)
            questions = [ExamQuestion(**q) for q in exam_data.get("questions", [])]
        except (json.JSONDecodeError, TypeError):
             raise HTTPException(status_code=500, detail="Failed to parse the exam from the model's response.")


        return ExamResponse(
            exam_title=f"Final Exam: {request.chapter}",
            questions=questions
        )

    except APIError as e:
        print(f"Exam endpoint LLM error: {e}")
        raise HTTPException(status_code=502, detail="The external LLM service failed.")

    except Exception as e:
        print(f"Exam endpoint error: {e}")
        raise HTTPException(status_code=500, detail="An internal error occurred.")
