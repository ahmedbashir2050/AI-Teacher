from typing import Optional
from core.audit import log_audit
from core.cache import cache_result
from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel
from qdrant_client import models
from rag.embeddings import generate_embedding
from services.qdrant_service import QdrantService
from tasks import ingest_document_task

router = APIRouter()


class SearchRequest(BaseModel):
    query: str
    top_k: int = 5
    collection_name: str
    faculty_id: str
    semester_id: str
    department_id: Optional[str] = None


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
