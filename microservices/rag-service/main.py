import uuid

from api.rag import router as rag_router
from core.observability import instrument_app, setup_logging, setup_tracing
from db.base import Base
from db.session import engine
from fastapi import FastAPI, Request
from prometheus_fastapi_instrumentator import Instrumentator

# Setup observability
logger = setup_logging("rag-service")
setup_tracing("rag-service")

Base.metadata.create_all(bind=engine)

app = FastAPI(title="RAG Service", version="1.0.0")
Instrumentator().instrument(app).expose(app)
instrument_app(app, "rag-service")


@app.middleware("http")
async def security_and_correlation_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    request.state.request_id = request_id

    if request.url.path not in ["/health", "/docs", "/openapi.json"]:
        if not request.headers.get("X-User-Id"):
            logger.warning(
                "Untrusted request to rag-service: Missing X-User-Id",
                extra={"request_id": request_id},
            )

    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


app.include_router(rag_router, tags=["RAG"])


@app.get("/health")
def health():
    return {"status": "ok"}
