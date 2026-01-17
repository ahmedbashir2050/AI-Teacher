import uuid
import logging
from fastapi import FastAPI, Request, Response, HTTPException
from .api.academics import router as academics_router
from .api.profiles import router as profiles_router
from .db.base import Base
from .db.session import engine

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="User Service", version="1.0.0")

@app.middleware("http")
async def security_and_correlation_middleware(request: Request, call_next):
    # Correlation ID
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    request.state.request_id = request_id

    # Trust Boundary: Identity headers MUST be present (except for health/docs)
    if request.url.path not in ["/health", "/docs", "/openapi.json"]:
        if not request.headers.get("X-User-Id"):
            logger.warning(f"Missing X-User-Id header in request {request.url.path}", extra={"request_id": request_id})
            # In a real Zero Trust env, we would strictly reject this.
            # For now, we allow but log, or could enforce:
            # raise HTTPException(status_code=403, detail="Untrusted request")
            pass

    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response

app.include_router(academics_router, tags=["Academics"])
app.include_router(profiles_router, prefix="/profiles", tags=["Profiles"])

@app.get("/health")
def health():
    return {"status": "ok"}
