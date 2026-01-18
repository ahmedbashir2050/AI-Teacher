import uuid
import logging
from fastapi import FastAPI, Request, Response
from prometheus_fastapi_instrumentator import Instrumentator
from api.auth import router as auth_router
from db.base import Base
from db.session import engine

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Auth Service", version="1.0.0")
Instrumentator().instrument(app).expose(app)

@app.middleware("http")
async def add_correlation_id(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    # Set request_id in request state for access in routes
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response

app.include_router(auth_router, prefix="/auth", tags=["Authentication"])

@app.get("/health")
def health():
    return {"status": "ok"}
