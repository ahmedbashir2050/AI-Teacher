from fastapi import APIRouter, HTTPException
from app.models.requests import FlashcardsRequest
from app.models.responses import FlashcardsResponse, Flashcard
from app.rag.retriever import retrieve_relevant_chunks
from app.services.llm_service import llm_service
import json

router = APIRouter()

def create_flashcards_prompt(context: list[str], count: int) -> str:
    context_str = "\n\n".join(context)
    prompt = f"""
Based ONLY on the following text, generate {count} flashcards.
Each flashcard should be a distinct question and a concise answer.
Format the output as a JSON list of objects, where each object has a "question" and "answer" key.

Example:
[
  {{"question": "What is the capital of France?", "answer": "Paris."}},
  {{"question": "Who wrote 'Hamlet'?", "answer": "William Shakespeare."}}
]

Text:
{context_str}
"""
    return prompt.strip()

@router.post("/flashcards", response_model=FlashcardsResponse)
async def generate_flashcards(request: FlashcardsRequest):
    """
    Generates a list of flashcards for a given chapter.
    """
    try:
        relevant_chunks = retrieve_relevant_chunks(f"Flashcards for {request.chapter}", top_k=10)

        if not relevant_chunks:
            return FlashcardsResponse(flashcards=[])

        prompt = create_flashcards_prompt(relevant_chunks, request.count)
        response_text = llm_service.get_chat_completion(prompt)

        # Clean the response to ensure it's valid JSON
        # The model might sometimes add markdown backticks
        cleaned_response = response_text.strip().replace("```json", "").replace("```", "").strip()

        try:
            flashcards_data = json.loads(cleaned_response)
            flashcards = [Flashcard(**item) for item in flashcards_data]
        except (json.JSONDecodeError, TypeError):
            # Fallback if the model doesn't produce valid JSON
             raise HTTPException(status_code=500, detail="Failed to parse flashcards from the model's response.")


        return FlashcardsResponse(flashcards=flashcards)

    except Exception as e:
        print(f"Flashcards endpoint error: {e}")
        raise HTTPException(status_code=500, detail="An internal error occurred.")
