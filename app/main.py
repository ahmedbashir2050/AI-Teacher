from fastapi import FastAPI
from app.api import chat, summarize, exam, flashcards, ingest

app = FastAPI(
    title="AI Teacher API",
    description="A RAG-powered AI Teaching System",
    version="1.0.0"
)

# Include API routers
app.include_router(ingest.router, prefix="/api", tags=["Ingestion"])
app.include_router(chat.router, prefix="/api", tags=["Chat"])
app.include_router(summarize.router, prefix="/api", tags=["Summarize"])
app.include_router(flashcards.router, prefix="/api", tags=["Flashcards"])
app.include_router(exam.router, prefix="/api", tags=["Exam"])

@app.get("/", tags=["Health Check"])
def read_root():
    """
    Root endpoint for health checks.
    """
    return {"status": "ok", "message": "Welcome to the AI Teacher API!"}
