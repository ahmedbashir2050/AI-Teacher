from app.core.celery_worker import celery_app
from app.rag.loader import load_pdf
from app.rag.chunker import chunk_text
from app.rag.embeddings import generate_embedding
from app.services.qdrant_service import qdrant_service
from qdrant_client import models
from app.core.logging import get_logger
import sentry_sdk
import uuid
import io

logger = get_logger(__name__)

@celery_app.task(name="tasks.process_document")
def process_document_task(file_content: bytes, filename: str):
    """
    Celery task to process and ingest a document in the background.
    """
    try:
        logger.info(f"Starting document processing for {filename}")
        text = load_pdf(io.BytesIO(file_content))
        chunks = chunk_text(text)

        if not chunks:
            logger.warning(f"Could not extract text from the PDF: {filename}")
            return

        points = []
        first_vector = generate_embedding(chunks[0])
        vector_size = len(first_vector)
        qdrant_service.create_collection_if_not_exists(vector_size=vector_size)

        points.append(models.PointStruct(
            id=str(uuid.uuid4()),
            vector=first_vector,
            payload={"text": chunks[0], "source": filename}
        ))

        for i in range(1, len(chunks)):
            chunk = chunks[i]
            vector = generate_embedding(chunk)
            point = models.PointStruct(
                id=str(uuid.uuid4()),
                vector=vector,
                payload={"text": chunk, "source": filename}
            )
            points.append(point)

        if points:
            qdrant_service.upsert_points(points)

        logger.info(f"Successfully ingested {len(chunks)} chunks from {filename}.")

    except Exception as e:
        logger.error(f"Error processing document {filename}: {e}", exc_info=True)
        sentry_sdk.capture_exception(e)
