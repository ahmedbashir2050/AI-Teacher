import uuid
import aioredis
from fastapi import FastAPI, Request
from fastapi_limiter import FastAPILimiter
from prometheus_fastapi_instrumentator import Instrumentator
from api.chat import router as chat_router
from db.base import Base
from db.session import engine
from core.config import settings
from core.observability import setup_logging, setup_tracing, instrument_app

# Setup observability
logger = setup_logging("chat-service")
setup_tracing("chat-service")

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Chat Service", version="1.0.0")
instrument_app(app, "chat-service")

@app.on_event("startup")
async def startup():
    try:
        redis = await aioredis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)
        await FastAPILimiter.init(redis)
        Instrumentator().instrument(app).expose(app)
    except Exception as e:
        logger.error(f"Failed to initialize Redis for rate limiting: {e}")

@app.middleware("http")
async def security_and_correlation_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    request.state.request_id = request_id

    if request.url.path not in ["/health", "/docs", "/openapi.json"]:
        if not request.headers.get("X-User-Id"):
            logger.warning("Untrusted request to chat-service: Missing X-User-Id", extra={"request_id": request_id})

    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response

app.include_router(chat_router, tags=["Chat"])

@app.get("/health")
def health():
    return {"status": "ok"}
