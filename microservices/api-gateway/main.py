import httpx
import uuid
from fastapi import FastAPI, Request, Response, HTTPException, Depends
from jose import jwt, JWTError
from core.config import settings
import aioredis
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
from prometheus_fastapi_instrumentator import Instrumentator
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="API Gateway", version="1.0.0")

@app.on_event("startup")
async def startup():
    redis = await aioredis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)
    await FastAPILimiter.init(redis)
    Instrumentator().instrument(app).expose(app)

async def reverse_proxy(request: Request, url: str, user_data: dict = None):
    # Correlation ID
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

    async with httpx.AsyncClient(timeout=10.0) as client:
        headers = dict(request.headers)
        headers.pop("host", None)
        headers["X-Request-ID"] = request_id

        if user_data:
            headers["X-User-Id"] = str(user_data.get("sub"))
            headers["X-User-Role"] = str(user_data.get("role"))

        try:
            rp_req = client.build_request(
                request.method,
                url,
                headers=headers,
                content=await request.body(),
                params=request.query_params
            )
            rp_resp = await client.send(rp_req)

            response = Response(
                content=rp_resp.content,
                status_code=rp_resp.status_code,
                headers=dict(rp_resp.headers)
            )
            response.headers["X-Request-ID"] = request_id
            return response
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
