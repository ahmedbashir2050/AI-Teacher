from fastapi import APIRouter, HTTPException

from app.core.cache import get_cache, set_cache
from app.core.security import STUDENT_ACCESS
from app.models.requests import SummarizeRequest
from app.models.responses import SummarizeResponse
from app.rag.retriever import retrieve_relevant_chunks
from app.services.llm_service import llm_service

router = APIRouter()


def create_summarize_prompt(context: list[str], style: str) -> str:
    context_str = "\n\n".join(context)
    if style == "exam":
        instruction = "Summarize the key points for an exam."
    elif style == "bullet":
        instruction = "Summarize the content in bullet points."
    else:
        instruction = "Summarize the content in a simple, easy-to-understand way."

    prompt = f"""
Based ONLY on the following text, provide a summary.
{instruction}

Text:
{context_str}
"""
    return prompt.strip()


@router.post("/summarize", response_model=SummarizeResponse)
async def summarize_chapter(
    request: SummarizeRequest, current_user: dict = STUDENT_ACCESS
):
    """
    Generates a summary for a given chapter based on retrieved content.
    Caches the result to improve performance on subsequent requests.
    """
    cache_key = f"summary:{request.chapter}:{request.style}"
    cached_summary = get_cache(cache_key)
    if cached_summary:
        return SummarizeResponse(summary=cached_summary)

    try:
        # Retrieve context for the entire chapter
        relevant_chunks = retrieve_relevant_chunks(
            f"Summary of {request.chapter}", top_k=10
        )

        if not relevant_chunks:
            return SummarizeResponse(
                summary="Could not find content for the specified chapter."
            )

        prompt = create_summarize_prompt(relevant_chunks, request.style)
        summary = llm_service.get_chat_completion(prompt)

        # Cache the new summary
        set_cache(cache_key, summary, ttl=3600)

        return SummarizeResponse(summary=summary)

    except Exception as e:
        print(f"Summarize endpoint error: {e}")
        raise HTTPException(status_code=500, detail="An internal error occurred.")
