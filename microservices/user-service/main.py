import uuid

from api.academics import router as academics_router
from api.profiles import router as profiles_router
from core.observability import instrument_app, setup_logging, setup_tracing
from db.base import Base
from db.session import engine
from fastapi import FastAPI, Request
from prometheus_fastapi_instrumentator import Instrumentator

# Setup observability
logger = setup_logging("user-service")
setup_tracing("user-service")

Base.metadata.create_all(bind=engine)

app = FastAPI(title="User Service", version="1.0.0")
Instrumentator().instrument(app).expose(app)
instrument_app(app, "user-service")


@app.middleware("http")
async def security_and_correlation_middleware(request: Request, call_next):
    # Correlation ID
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    request.state.request_id = request_id

    # Trust Boundary: Identity headers MUST be present (except for health/docs)
    if request.url.path not in ["/health", "/docs", "/openapi.json"]:
        if not request.headers.get("X-User-Id"):
            logger.warning(
                f"Missing X-User-Id header in request {request.url.path}",
                extra={"request_id": request_id},
            )

    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


app.include_router(academics_router, tags=["Academics"])
app.include_router(profiles_router, prefix="/profiles", tags=["Profiles"])


@app.get("/health")
def health():
    return {"status": "ok"}
