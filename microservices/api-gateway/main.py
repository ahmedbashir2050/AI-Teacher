import uuid
from contextlib import asynccontextmanager

import redis.asyncio as aioredis
import httpx
from core.config import settings
from core.observability import instrument_app, setup_logging, setup_tracing
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
from jose import JWTError, jwt
from prometheus_fastapi_instrumentator import Instrumentator
from starlette.background import BackgroundTask

# Setup observability
logger = setup_logging("api-gateway")
setup_tracing("api-gateway")

# Global httpx client for connection pooling
http_client = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global http_client
    # Startup
    redis = await aioredis.from_url(
        settings.REDIS_URL, encoding="utf-8", decode_responses=True
    )
    await FastAPILimiter.init(redis)
    http_client = httpx.AsyncClient(
        timeout=60.0,
        limits=httpx.Limits(max_connections=500, max_keepalive_connections=100),
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
    allow_origins=["*"],  # In production, replace with specific origins
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
        if user_data.get("faculty"):
            headers["X-User-Faculty"] = str(user_data.get("faculty"))
        if user_data.get("faculty_id"):
            headers["X-User-Faculty-Id"] = str(user_data.get("faculty_id"))

    # Reuse body if it was already read by a dependency
    content = getattr(request.state, "body", None)
    if content is None:
        content = request.stream()

    try:
        rp_req = http_client.build_request(
            request.method,
            url,
            headers=headers,
            content=content,
            params=request.query_params,
        )
        rp_resp = await http_client.send(rp_req, stream=True)

        return StreamingResponse(
            rp_resp.aiter_raw(),
            status_code=rp_resp.status_code,
            headers=dict(rp_resp.headers),
            background=BackgroundTask(rp_resp.aclose),
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
            issuer=settings.JWT_ISSUER,
            options={"leeway": 60},  # 60 seconds clock skew tolerance
        )
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

def enforce_role(allowed_roles: list[str]):
    def role_checker(user_data: dict = Depends(get_current_user)):
        role = user_data.get("role")
        if role not in allowed_roles:
            raise HTTPException(status_code=403, detail="Forbidden: Insufficient permissions")
        return user_data
    return role_checker

async def verify_enrollment(request: Request, user_data: dict = Depends(get_current_user)):
    # Admins bypass enrollment checks
    if user_data.get("role") in ["admin", "super_admin"]:
        return user_data

    # For chat and exam routes, we expect faculty_id and semester_id
    # They can be in the body (JSON) or query params
    target_faculty = None
    target_semester = None

    if request.method in ["POST", "PUT", "PATCH"]:
        try:
            # We must be careful not to consume the stream if we use it later.
            # However, reverse_proxy uses request.stream().
            # If we call request.json(), it consumes the stream.
            # We can store the body in request.state to reuse it.
            body_bytes = await request.body()
            request.state.body = body_bytes
            import json
            body = json.loads(body_bytes)
            target_faculty = body.get("faculty_id")
            target_semester = body.get("semester_id")
        except:
            pass

    if not target_faculty:
        target_faculty = request.query_params.get("faculty_id")
    if not target_semester:
        target_semester = request.query_params.get("semester_id")

    # If the request specifically targets a faculty/semester, it must match the user's
    user_faculty = user_data.get("faculty")
    user_semester = str(user_data.get("semester"))

    if target_faculty and target_faculty != user_faculty:
        raise HTTPException(status_code=403, detail=f"Unauthorized faculty access: {target_faculty}")

    # Teachers don't have a semester restriction, only faculty
    if user_data.get("role") == "teacher":
        return user_data

    if target_semester and str(target_semester) != user_semester:
        raise HTTPException(status_code=403, detail=f"Not enrolled in semester: {target_semester}")

    return user_data


@app.api_route(
    "/api/auth/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE"],
    tags=["Auth"],
    dependencies=[Depends(RateLimiter(times=20, minutes=1))],
)
@app.api_route(
    "/api/v1/auth/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE"],
    tags=["Auth"],
    dependencies=[Depends(RateLimiter(times=20, minutes=1))],
)
async def auth_route(request: Request, path: str):
    url = f"{settings.AUTH_SERVICE_URL}/auth/{path}"
    return await reverse_proxy(request, url)


@app.api_route(
    "/api/v1/admin/books{path:path}",
    methods=["GET", "POST", "PUT", "DELETE"],
    dependencies=[Depends(RateLimiter(times=50, minutes=1))],
)
async def admin_books_route(
    request: Request,
    path: str,
    user_data: dict = Depends(enforce_role(["admin", "super_admin", "teacher"])),
):
    url = f"{settings.LIBRARY_SERVICE_URL}/admin/books{path}"
    return await reverse_proxy(request, url, user_data=user_data)


@app.api_route(
    "/api/v1/teacher/chat/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE"],
    dependencies=[Depends(RateLimiter(times=50, minutes=1))],
)
async def teacher_chat_route(
    request: Request,
    path: str,
    user_data: dict = Depends(enforce_role(["teacher", "admin", "super_admin"])),
):
    url = f"{settings.CHAT_SERVICE_URL}/teacher/{path}"
    return await reverse_proxy(request, url, user_data=user_data)


@app.api_route(
    "/api/v1/teacher/exams/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE"],
    dependencies=[Depends(RateLimiter(times=50, minutes=1))],
)
async def teacher_exam_route(
    request: Request,
    path: str,
    user_data: dict = Depends(enforce_role(["teacher", "admin", "super_admin"])),
):
    url = f"{settings.EXAM_SERVICE_URL}/teacher/{path}"
    return await reverse_proxy(request, url, user_data=user_data)


@app.api_route(
    "/api/v1/books{path:path}",
    methods=["GET", "POST", "PUT", "DELETE"],
    dependencies=[Depends(RateLimiter(times=50, minutes=1))],
)
async def library_books_route(
    request: Request, path: str, user_data: dict = Depends(get_current_user)
):
    url = f"{settings.LIBRARY_SERVICE_URL}/books{path}"
    return await reverse_proxy(request, url, user_data=user_data)


@app.api_route(
    "/api/v1/admin/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE"],
    dependencies=[Depends(RateLimiter(times=50, minutes=1))],
)
async def admin_route(
    request: Request, path: str, user_data: dict = Depends(enforce_role(["admin", "super_admin"]))
):
    url = f"{settings.USER_SERVICE_URL}/admin/{path}"
    return await reverse_proxy(request, url, user_data=user_data)


@app.api_route(
    "/api/users/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE"],
    dependencies=[Depends(RateLimiter(times=100, minutes=1))],
)
@app.api_route(
    "/api/v1/users/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE"],
    dependencies=[Depends(RateLimiter(times=100, minutes=1))],
)
async def user_route(
    request: Request, path: str, user_data: dict = Depends(get_current_user)
):
    url = f"{settings.USER_SERVICE_URL}/{path}"
    return await reverse_proxy(request, url, user_data=user_data)


@app.api_route(
    "/api/chat/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE"],
    dependencies=[Depends(RateLimiter(times=50, minutes=1))],
)
@app.api_route(
    "/api/v1/chat/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE"],
    dependencies=[Depends(RateLimiter(times=50, minutes=1))],
)
async def chat_route(
    request: Request, path: str, user_data: dict = Depends(verify_enrollment)
):
    url = f"{settings.CHAT_SERVICE_URL}/{path}"
    return await reverse_proxy(request, url, user_data=user_data)


@app.api_route(
    "/api/rag/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE"],
    dependencies=[Depends(RateLimiter(times=20, minutes=1))],
)
@app.api_route(
    "/api/v1/rag/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE"],
    dependencies=[Depends(RateLimiter(times=20, minutes=1))],
)
async def rag_route(
    request: Request, path: str, user_data: dict = Depends(get_current_user)
):
    url = f"{settings.RAG_SERVICE_URL}/{path}"
    return await reverse_proxy(request, url, user_data=user_data)


@app.api_route(
    "/api/exams/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE"],
    dependencies=[Depends(RateLimiter(times=50, minutes=1))],
)
@app.api_route(
    "/api/v1/exams/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE"],
    dependencies=[Depends(RateLimiter(times=50, minutes=1))],
)
async def exam_route(
    request: Request, path: str, user_data: dict = Depends(verify_enrollment)
):
    # verify_enrollment also ensures the user is logged in.
    # We might still want to enforce role student/teacher if it's not student-only.
    url = f"{settings.EXAM_SERVICE_URL}/{path}"
    return await reverse_proxy(request, url, user_data=user_data)


@app.api_route(
    "/api/v1/pro-exams/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE"],
    dependencies=[Depends(RateLimiter(times=50, minutes=1))],
)
async def pro_exam_route(
    request: Request, path: str, user_data: dict = Depends(verify_enrollment)
):
    url = f"{settings.PRO_EXAM_SERVICE_URL}/api/v1/exams/{path}"
    return await reverse_proxy(request, url, user_data=user_data)


@app.api_route(
    "/api/v1/pro-submissions/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE"],
    dependencies=[Depends(RateLimiter(times=50, minutes=1))],
)
async def pro_submission_route(
    request: Request, path: str, user_data: dict = Depends(verify_enrollment)
):
    url = f"{settings.PRO_EXAM_SERVICE_URL}/api/v1/submissions/{path}"
    return await reverse_proxy(request, url, user_data=user_data)


@app.get("/health")
def health():
    return {"status": "ok"}
