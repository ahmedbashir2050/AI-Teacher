from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Request
from app.models.responses import MessageResponse
from app.core.security import ADMIN_ACCESS
from app.core.limiter import limiter
from app.tasks import process_document_task

router = APIRouter()

@router.post("/ingest", response_model=MessageResponse, status_code=202)
@limiter.limit("5/hour")
async def ingest_document(request: Request, file: UploadFile = File(...), current_user: dict = ADMIN_ACCESS):
    """
    Accepts a PDF document and offloads its processing and ingestion to a background worker.
    Requires ADMIN access.
    """
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    try:
        file_content = await file.read()
        process_document_task.delay(file_content, file.filename)
        return {"message": f"Document '{file.filename}' received and is being processed in the background."}

    except Exception as e:
        print(f"Ingestion submission error: {e}")
        raise HTTPException(status_code=500, detail="Failed to queue the document for processing.")
