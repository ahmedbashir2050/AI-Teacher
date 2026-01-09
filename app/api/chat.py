from fastapi import APIRouter, HTTPException
from app.models.requests import ChatRequest
from app.models.responses import ChatResponse
from app.rag.retriever import retrieve_relevant_chunks
from app.rag.prompt import create_teacher_prompt
from app.services.llm_service import llm_service

router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
async def chat_with_teacher(request: ChatRequest):
    """
    Handles a student's question by retrieving relevant context
    from the curriculum and generating a grounded answer.
    """
    try:
        # 1. Retrieve relevant context
        relevant_chunks = retrieve_relevant_chunks(request.question)

        if not relevant_chunks:
            # If no context is found, respond according to the strict rule
            return ChatResponse(answer="هذا السؤال خارج المقرر")

        # 2. Create the prompt with the retrieved context
        prompt = create_teacher_prompt(relevant_chunks, request.question)

        # 3. Get the answer from the LLM
        answer = llm_service.get_chat_completion(prompt)

        return ChatResponse(answer=answer)

    except Exception as e:
        # Log the error for debugging
        print(f"Chat endpoint error: {e}")
        raise HTTPException(status_code=500, detail="An internal error occurred.")
