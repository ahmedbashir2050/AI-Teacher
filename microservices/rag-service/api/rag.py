from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from ..services.qdrant_service import QdrantService
from ..rag.loader import load_pdf
from ..rag.chunker import chunk_text
from ..rag.embeddings import generate_embedding
from qdrant_client import models
import uuid
import io
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
async def search(request: SearchRequest):
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
    text = load_pdf(io.BytesIO(file_content))
    chunks = chunk_text(text)

    if not chunks:
        return {"message": "No text extracted from PDF"}

    qs = QdrantService(collection_name=collection_name)
    points = []

    # Process chunks in series for simplicity, but await each embedding
    for chunk in chunks:
        vector = await generate_embedding(chunk)
        points.append(models.PointStruct(
            id=str(uuid.uuid4()),
            vector=vector,
            payload={
                "text": chunk,
                "source": file.filename,
                "faculty_id": faculty_id,
                "semester_id": semester_id
            }
        ))

    # Create collection using the first vector size
    if points:
        qs.create_collection_if_not_exists(vector_size=len(points[0].vector))
        qs.upsert_points(points)

    return {"message": f"Successfully ingested {len(chunks)} chunks into {collection_name}"}
