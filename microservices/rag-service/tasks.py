import asyncio
import io
import logging
import uuid
import boto3

from core.audit import log_audit
from core.celery_app import celery_app
from core.config import settings
from qdrant_client import models
from rag.chunker import chunk_text
from rag.embeddings import generate_embedding
from rag.loader import load_pdf
from services.qdrant_service import QdrantService
from prometheus_client import Summary

logger = logging.getLogger(__name__)

RAG_INGESTION_TIME = Summary("rag_ingestion_seconds", "Time spent on RAG ingestion")


def get_s3_client():
    return boto3.client(
        "s3",
        endpoint_url=settings.S3_ENDPOINT_URL,
        aws_access_key_id=settings.S3_ACCESS_KEY,
        aws_secret_access_key=settings.S3_SECRET_KEY,
        region_name=settings.S3_REGION,
    )


@celery_app.task(name="tasks.ingest_document_task", bind=True, max_retries=3)
@RAG_INGESTION_TIME.time()
def ingest_document_task(
    self,
    collection_name: str,
    faculty_id: str,
    department_id: str,
    semester: int,
    book_id: str,
    file_key: str = None,
    file_content: bytes = None,
    filename: str = None,
    request_id: str = None,
):
    try:
        if file_key:
            s3 = get_s3_client()
            response = s3.get_object(Bucket=settings.S3_BUCKET_NAME, Key=file_key)
            file_content = response["Body"].read()
            if not filename:
                filename = file_key.split("/")[-1]

        if not file_content:
            return {"error": "No file content or file_key provided"}

        pages = load_pdf(io.BytesIO(file_content))

        if not pages:
            return {"message": "No text extracted from PDF"}

        qs = QdrantService(collection_name=collection_name)

        async def process_chunks():
            points = []
            for page in pages:
                chunks = chunk_text(page["text"])
                for chunk in chunks:
                    vector = await generate_embedding(chunk)
                    points.append(
                        models.PointStruct(
                            id=str(uuid.uuid4()),
                            vector=vector,
                            payload={
                                "text": chunk,
                                "source": filename,
                                "page": page["page"],
                                "book_id": book_id,
                                "faculty_id": faculty_id,
                                "department_id": department_id,
                                "semester": semester,
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
                "book_id": book_id,
                "chunks": num_chunks,
            },
            request_id=request_id,
        )

        return {
            "message": f"Successfully ingested {num_chunks} chunks",
            "filename": filename,
            "book_id": book_id,
        }
    except Exception as exc:
        logger.error(f"Error in ingest_document_task: {exc}")
        self.retry(exc=exc, countdown=60)
