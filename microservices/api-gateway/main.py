import httpx
import uuid
from fastapi import FastAPI, Request, Response, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from jose import jwt, JWTError
from core.config import settings
import aioredis
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
from prometheus_fastapi_instrumentator import Instrumentator
from contextlib import asynccontextmanager
from starlette.background import BackgroundTask
from core.observability import setup_logging, setup_tracing, instrument_app

# Setup observability
logger = setup_logging("api-gateway")
setup_tracing("api-gateway")

# Global httpx client for connection pooling
http_client = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global http_client
    # Startup
    redis = await aioredis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)
    await FastAPILimiter.init(redis)
    http_client = httpx.AsyncClient(
        timeout=60.0,
        limits=httpx.Limits(max_connections=500, max_keepalive_connections=100)
    )
    # Initialize instrumentator
    Instrumentator().instrument(app).expose(app)

    yield
    # Shutdown
    await http_client.aclose()
    await redis.close()

app = FastAPI(title="API Gateway", version="1.0.0", lifespan=lifespan)
instrument_app(app, "api-gateway")

# CORS Hardening
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def reverse_proxy(request: Request, url: str, user_data: dict = None):
    # Correlation ID
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

    headers = dict(request.headers)
    headers.pop("host", None)
    headers["X-Request-ID"] = request_id

    if user_data:
        headers["X-User-Id"] = str(user_data.get("sub"))
        headers["X-User-Role"] = str(user_data.get("role"))

    try:
        rp_req = http_client.build_request(
            request.method,
            url,
            headers=headers,
            content=request.stream(),
            params=request.query_params
        )
        rp_resp = await http_client.send(rp_req, stream=True)

        return StreamingResponse(
            rp_resp.aiter_raw(),
            status_code=rp_resp.status_code,
            headers=dict(rp_resp.headers),
            background=BackgroundTask(rp_resp.aclose)
        )
    except httpx.RequestError as exc:
        logger.error(f"Service unavailable: {exc}", extra={"request_id": request_id})
        raise HTTPException(status_code=503, detail="Service unavailable")

def get_current_user(request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")

    token = auth_header.split(" ")[1]
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            audience=settings.JWT_AUDIENCE,
            issuer=settings.JWT_ISSUER
        )
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.api_route("/api/auth/{path:path}", methods=["GET", "POST", "PUT", "DELETE"], tags=["Auth"])
async def auth_route(request: Request, path: str):
    url = f"{settings.AUTH_SERVICE_URL}/auth/{path}"
    return await reverse_proxy(request, url)

@app.api_route("/api/users/{path:path}", methods=["GET", "POST", "PUT", "DELETE"], dependencies=[Depends(RateLimiter(times=100, minutes=1))])
async def user_route(request: Request, path: str, user_data: dict = Depends(get_current_user)):
    url = f"{settings.USER_SERVICE_URL}/{path}"
    return await reverse_proxy(request, url, user_data=user_data)

@app.api_route("/api/chat/{path:path}", methods=["GET", "POST", "PUT", "DELETE"], dependencies=[Depends(RateLimiter(times=50, minutes=1))])
async def chat_route(request: Request, path: str, user_data: dict = Depends(get_current_user)):
    url = f"{settings.CHAT_SERVICE_URL}/{path}"
    return await reverse_proxy(request, url, user_data=user_data)

@app.api_route("/api/rag/{path:path}", methods=["GET", "POST", "PUT", "DELETE"], dependencies=[Depends(RateLimiter(times=20, minutes=1))])
async def rag_route(request: Request, path: str, user_data: dict = Depends(get_current_user)):
    url = f"{settings.RAG_SERVICE_URL}/{path}"
    return await reverse_proxy(request, url, user_data=user_data)

@app.api_route("/api/exams/{path:path}", methods=["GET", "POST", "PUT", "DELETE"], dependencies=[Depends(RateLimiter(times=50, minutes=1))])
async def exam_route(request: Request, path: str, user_data: dict = Depends(get_current_user)):
    url = f"{settings.EXAM_SERVICE_URL}/{path}"
    return await reverse_proxy(request, url, user_data=user_data)

@app.get("/health")
def health():
    return {"status": "ok"}
