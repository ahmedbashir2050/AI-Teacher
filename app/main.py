from fastapi import FastAPI
<<<<<<< Updated upstream
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
=======
from contextlib import asynccontextmanager
from app.api import academic, admin, chat
from app.core.database import engine
from app.models import academic as academic_models, user as user_models, chat as chat_models

from app.core.qdrant_db import create_collection_if_not_exists

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    # Table creation is handled by the test setup (conftest.py) for testing
    # and should be handled by a migration tool (like Alembic) in production.
    create_collection_if_not_exists()
    yield
    # Shutdown

app = FastAPI(lifespan=lifespan)

app.include_router(academic.router, prefix="/api", tags=["academic"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])
app.include_router(chat.router, prefix="/api", tags=["chat"])

@app.get("/")
def read_root():
    return {"Hello": "World"}
>>>>>>> Stashed changes
