from typing import Optional
from core.audit import log_audit
from core.cache import cache_result
from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel
from qdrant_client import models
from rag.embeddings import generate_embedding
from services.qdrant_service import QdrantService
from tasks import ingest_document_task
import time
from core.metrics import RETRIEVER_REFRESH_LATENCY, RETRIEVER_REFRESH_TOTAL

router = APIRouter()


class SearchRequest(BaseModel):
    query: str
    top_k: int = 5
    collection_name: str
    faculty_id: str
    semester_id: str
    department_id: Optional[str] = None
    book_id: Optional[str] = None


class SearchResult(BaseModel):
    text: str
    score: float
    source: str
    page: int
    book_id: str


@router.post("/search")
@cache_result(ttl=600)
async def search(request: SearchRequest):
    # We need to convert request to something JSON serializable for cache key
    # But cache_result handles args/kwargs. Since request is a Pydantic model,
    # it might need conversion.
    return await _do_search(request)


async def _do_search(request: SearchRequest):
    qs = QdrantService(collection_name=request.collection_name)
    query_vector = await generate_embedding(request.query)
    try:
        # Enforce Faculty + Semester isolation
        must_conditions = [
            models.FieldCondition(
                key="faculty_id", match=models.MatchValue(value=request.faculty_id)
            ),
            models.FieldCondition(
                key="semester_id",
                match=models.MatchValue(value=request.semester_id),
            ),
        ]
        if request.department_id:
            must_conditions.append(
                models.FieldCondition(
                    key="department_id",
                    match=models.MatchValue(value=request.department_id),
                )
            )
        if request.book_id:
            must_conditions.append(
                models.FieldCondition(
                    key="book_id",
                    match=models.MatchValue(value=request.book_id),
                )
            )

        query_filter = models.Filter(must=must_conditions)
        search_results = qs.search(
            vector=query_vector, limit=request.top_k, query_filter=query_filter
        )
        return [
            {
                "text": point.payload["text"],
                "score": point.score,
                "source": point.payload.get("source", "Unknown"),
                "page": point.payload.get("page", 0),
                "book_id": point.payload.get("book_id", "Unknown"),
            }
            for point in search_results
        ]
    except Exception:
        return []


@router.post("/refresh")
async def refresh_retriever(
    faculty_id: str,
    semester_id: str,
):
    """
    Incrementally refreshes the retriever state or clears caches.
    Ensures that newly added/selected books are prioritized or indexed.
    """
    start_time = time.time()
    # In a real implementation, we might clear Redis caches for this context
    # Or trigger a re-indexing of a vector store if it's stateful.
    # For now, we clear the RAG cache to ensure fresh results.
    from core.cache import get_redis
    redis = await get_redis()

    # We use a pattern to clear context-specific keys
    # rag_cache:{faculty}:{semester}:*
    pattern = f"rag_cache:{faculty_id}:{semester_id}:*"
    keys = await redis.keys(pattern)
    if keys:
        await redis.delete(*keys)

    RETRIEVER_REFRESH_LATENCY.observe(time.time() - start_time)
    RETRIEVER_REFRESH_TOTAL.inc()

    log_audit(
        user_id="system",
        action="refresh_retriever",
        resource="rag",
        metadata={"faculty_id": faculty_id, "semester_id": semester_id}
    )
    return {"status": "refreshed"}


@router.post("/ingest")
async def ingest_document(
    collection_name: str,
    faculty_id: str,
    semester_id: str,
    file: UploadFile = File(...),
):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    file_content = await file.read()

    # Trigger async task
    task = ingest_document_task.delay(
        collection_name, faculty_id, semester_id, file_content, file.filename
    )

    log_audit(
        user_id="system",  # Ingestion might be done by an admin or system process
        action="ingest_request",
        resource="document",
        metadata={
            "collection_name": collection_name,
            "faculty_id": faculty_id,
            "semester_id": semester_id,
            "filename": file.filename,
            "task_id": task.id,
        },
    )

    return {
        "message": "Ingestion started",
        "task_id": task.id,
        "filename": file.filename,
    }
