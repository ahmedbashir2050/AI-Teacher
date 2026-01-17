import uuid
import logging
from fastapi import FastAPI, Request, Response
from .api.exam import router as exam_router
from .db.base import Base
from .db.session import engine

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Exam Service", version="1.0.0")

@app.middleware("http")
async def security_and_correlation_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    request.state.request_id = request_id

    if request.url.path not in ["/health", "/docs", "/openapi.json"]:
        if not request.headers.get("X-User-Id"):
            logger.warning(f"Untrusted request to exam-service: Missing X-User-Id", extra={"request_id": request_id})

    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response

app.include_router(exam_router, tags=["Exam"])

@app.get("/health")
def health():
    return {"status": "ok"}
