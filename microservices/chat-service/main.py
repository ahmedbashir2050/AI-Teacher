import uuid
import logging
import aioredis
from fastapi import FastAPI, Request, Response
from fastapi_limiter import FastAPILimiter
from .api.chat import router as chat_router
from .db.base import Base
from .db.session import engine
from .core.config import settings

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Chat Service", version="1.0.0")

@app.on_event("startup")
async def startup():
    try:
        redis = await aioredis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)
        await FastAPILimiter.init(redis)
    except Exception as e:
        logger.error(f"Failed to initialize Redis for rate limiting: {e}")
        # Graceful degradation: Limiter will be disabled if init fails

@app.middleware("http")
async def security_and_correlation_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    request.state.request_id = request_id

    if request.url.path not in ["/health", "/docs", "/openapi.json"]:
        if not request.headers.get("X-User-Id"):
            logger.warning(f"Untrusted request to chat-service: Missing X-User-Id", extra={"request_id": request_id})

    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response

app.include_router(chat_router, tags=["Chat"])

@app.get("/health")
def health():
    return {"status": "ok"}
