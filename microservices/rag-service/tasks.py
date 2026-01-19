import asyncio
import io
import logging
import uuid

from core.audit import log_audit
from core.celery_app import celery_app
from qdrant_client import models
from rag.chunker import chunk_text
from rag.embeddings import generate_embedding
from rag.loader import load_pdf
from services.qdrant_service import QdrantService

logger = logging.getLogger(__name__)


@celery_app.task(name="tasks.ingest_document_task", bind=True, max_retries=3)
def ingest_document_task(
    self,
    collection_name: str,
    faculty_id: str,
    semester_id: str,
    file_content: bytes,
    filename: str,
):
    try:
        text = load_pdf(io.BytesIO(file_content))
        chunks = chunk_text(text)

        if not chunks:
            return {"message": "No text extracted from PDF"}

        qs = QdrantService(collection_name=collection_name)

        async def process_chunks():
            points = []
            for chunk in chunks:
                vector = await generate_embedding(chunk)
                points.append(
                    models.PointStruct(
                        id=str(uuid.uuid4()),
                        vector=vector,
                        payload={
                            "text": chunk,
                            "source": filename,
                            "faculty_id": faculty_id,
                            "semester_id": semester_id,
                        },
                    )
                )
            if points:
                qs.create_collection_if_not_exists(vector_size=len(points[0].vector))
                qs.upsert_points(points)
            return len(chunks)

        num_chunks = asyncio.run(process_chunks())

        log_audit(
            user_id="system",
            action="ingest_complete",
            resource="document",
            metadata={
                "collection_name": collection_name,
                "filename": filename,
                "chunks": num_chunks,
            },
        )

        return {
            "message": f"Successfully ingested {num_chunks} chunks",
            "filename": filename,
        }
    except Exception as exc:
        logger.error(f"Error in ingest_document_task: {exc}")
        self.retry(exc=exc, countdown=60)
