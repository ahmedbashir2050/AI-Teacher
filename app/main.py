import asyncio
import time
import uuid

import sentry_sdk
from fastapi import FastAPI, Request, Response
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.api import admin, auth, chat, exam, flashcards, ingest, summarize
from app.config import settings
from app.core.cache import redis_client
from app.core.limiter import limiter
from app.core.logging import get_logger
from app.core.security import decode_token
from app.services.qdrant_service import qdrant_service

logger = get_logger(__name__)

if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        traces_sample_rate=1.0,
        profiles_sample_rate=1.0,
        environment=settings.ENVIRONMENT,
    )

app = FastAPI(
    title="AI Teacher API",
    description="A RAG-powered AI Teaching System",
    version="1.0.0",
)

# --- Tracing Setup ---
resource = Resource(attributes={"service.name": "ai-teacher-api"})
provider = TracerProvider(resource=resource)

if settings.ENVIRONMENT == "development":
    processor = BatchSpanProcessor(ConsoleSpanExporter())
    provider.add_span_processor(processor)
# Add other exporters for production here (e.g., Jaeger, Zipkin)
# else:
#     from opentelemetry.sdk.trace.export import OTLPSpanExporter
#     exporter = OTLPSpanExporter()
#     processor = BatchSpanProcessor(exporter)
#     provider.add_span_processor(processor)

FastAPIInstrumentor.instrument_app(app, tracer_provider=provider)


def get_username_from_request(request: Request) -> str | None:
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        token_data = decode_token(token)
        if token_data:
            return token_data.username
    return None


@app.middleware("http")
async def log_requests(request: Request, call_next):
    request_id = str(uuid.uuid4())
    start_time = time.time()
    username = get_username_from_request(request)

    logger.info(
        "start_request",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "client_host": request.client.host,
            "username": username,
        },
    )

    response = await call_next(request)

    process_time = (time.time() - start_time) * 1000

    logger.info(
        "end_request",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "process_time_ms": f"{process_time:.2f}",
        },
    )

    response.headers["X-Request-ID"] = request_id
    return response


app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# Include API routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])
app.include_router(ingest.router, prefix="/api", tags=["Ingestion"])
app.include_router(chat.router, prefix="/api", tags=["Chat"])
app.include_router(summarize.router, prefix="/api", tags=["Summarize"])
app.include_router(flashcards.router, prefix="/api", tags=["Flashcards"])
app.include_router(exam.router, prefix="/api", tags=["Exam"])


@app.on_event("shutdown")
async def shutdown_event():
    """
    Handle graceful shutdown.
    """
    logger.info("Application is shutting down.")
    # Give a small delay for in-flight requests to complete.
    await asyncio.sleep(2)
    logger.info("Shutdown complete.")


@app.get("/health", tags=["Health Check"])
@limiter.limit("100/minute")
def health_check(request: Request):
    """
    Liveness probe. Returns 200 OK if the service is running.
    """
    return {"status": "ok"}


@app.get("/ready", tags=["Health Check"])
@limiter.limit("10/minute")
def readiness_check(request: Request, response: Response):
    """
    Readiness probe. Checks if dependencies are available.
    """
    redis_ready = False
    if redis_client:
        try:
            redis_client.ping()
            redis_ready = True
        except Exception:
            pass

    qdrant_ready = False
    try:
        qdrant_service.client.get_collection(
            collection_name=qdrant_service.collection_name
        )
        qdrant_ready = True
    except Exception:
        try:
            # Fallback for when the collection doesn't exist yet but the service is up.
            qdrant_service.client.cluster_status()
            qdrant_ready = True
        except Exception:
            pass

    if redis_ready and qdrant_ready:
        return {"status": "ready"}
    else:
        response.status_code = 503
        return {
            "status": "not_ready",
            "dependencies": {
                "redis": "ready" if redis_ready else "not_ready",
                "qdrant": "ready" if qdrant_ready else "not_ready",
            },
        }


@app.get("/", tags=["Health Check"])
@limiter.limit("100/minute")
def read_root(request: Request):
    """
    Root endpoint for health checks.
    """
    return {"status": "ok", "message": "Welcome to the AI Teacher API!"}
