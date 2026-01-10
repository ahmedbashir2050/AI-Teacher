from fastapi import APIRouter, UploadFile, File, HTTPException
from app.rag.loader import load_pdf
from app.rag.chunker import chunk_text
from app.rag.embeddings import generate_embedding
from app.services.qdrant_service import qdrant_service
from qdrant_client import models
import uuid
import io

router = APIRouter()

@router.post("/ingest", status_code=201)
async def ingest_document(file: UploadFile = File(...)):
    """
    Processes and ingests a new curriculum document.
    """
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    try:
        # 1. Load and Chunk
        file_content = await file.read()
        text = load_pdf(io.BytesIO(file_content))
        chunks = chunk_text(text)

        if not chunks:
            raise HTTPException(status_code=400, detail="Could not extract text from the PDF.")

        # 2. Generate Embeddings and prepare for Qdrant
        points = []
        # Get the embedding size from the first chunk
        first_vector = generate_embedding(chunks[0])
        vector_size = len(first_vector)
        qdrant_service.create_collection_if_not_exists(vector_size=vector_size)

        # Add the first point
        points.append(models.PointStruct(
            id=str(uuid.uuid4()),
            vector=first_vector,
            payload={"text": chunks[0], "source": file.filename}
        ))

        # Process the rest of the chunks
        for i in range(1, len(chunks)):
            chunk = chunks[i]
            vector = generate_embedding(chunk)
            point = models.PointStruct(
                id=str(uuid.uuid4()),
                vector=vector,
                payload={"text": chunk, "source": file.filename}
            )
            points.append(point)

        # 3. Upsert to Qdrant
        if points:
            qdrant_service.upsert_points(points)

        return {"message": f"Successfully ingested {len(chunks)} chunks from {file.filename}."}

    except Exception as e:
        # Log the error for debugging
        print(f"Ingestion error: {e}")
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
