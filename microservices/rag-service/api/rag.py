from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from services.qdrant_service import QdrantService
from rag.embeddings import generate_embedding
from tasks import ingest_document_task
from core.cache import cache_result
from qdrant_client import models
import uuid
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter()

class SearchRequest(BaseModel):
    query: str
    top_k: int = 5
    collection_name: str
    faculty_id: str
    semester_id: str

class SearchResult(BaseModel):
    text: str
    score: float

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
        query_filter = models.Filter(
            must=[
                models.FieldCondition(key="faculty_id", match=models.MatchValue(value=request.faculty_id)),
                models.FieldCondition(key="semester_id", match=models.MatchValue(value=request.semester_id)),
            ]
        )
        search_results = qs.search(vector=query_vector, limit=request.top_k, query_filter=query_filter)
        return [{"text": point.payload["text"], "score": point.score} for point in search_results]
    except Exception as e:
        return []

@router.post("/ingest")
async def ingest_document(collection_name: str, faculty_id: str, semester_id: str, file: UploadFile = File(...)):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    file_content = await file.read()

    # Trigger async task
    task = ingest_document_task.delay(
        collection_name,
        faculty_id,
        semester_id,
        file_content,
        file.filename
    )

    return {
        "message": "Ingestion started",
        "task_id": task.id,
        "filename": file.filename
    }
