from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.api import academic, admin, chat
from app.core.database import engine
from app.models import academic as academic_models, user as user_models

from app.core.qdrant_db import create_collection_if_not_exists

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    # Table creation is handled by the test setup (conftest.py) for testing
    # and should be handled by a migration tool (like Alembic) in production.
    yield
    # Shutdown

app = FastAPI(lifespan=lifespan)

app.include_router(academic.router, prefix="/api", tags=["academic"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])
app.include_router(chat.router, prefix="/api", tags=["chat"])

@app.get("/")
def read_root():
    return {"Hello": "World"}
