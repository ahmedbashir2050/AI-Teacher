import redis.asyncio as redis
from core.audit import log_audit
from core.config import settings
from core.google_auth import verify_google_token
from core.security import create_access_token, create_refresh_token, verify_password, get_password_hash
from core.user_client import user_service_client
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import jwt
from pydantic import BaseModel, EmailStr
from typing import Optional

router = APIRouter()

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None

class UserResponse(BaseModel):
    id: str
    email: str
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    auth_provider: str
    role: str

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class GoogleLogin(BaseModel):
    id_token: str

@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
async def register(request: Request, user_in: UserCreate):
    request_id = getattr(request.state, "request_id", None)

    existing_user = await user_service_client.get_user_by_email(user_in.email)
    if existing_user:
        log_audit(
            "anonymous",
            "register",
            "user",
            status="failure",
            metadata={"reason": "email_exists"},
            request_id=request_id,
        )
        raise HTTPException(status_code=400, detail="Email already registered")

    user_data = {
        "email": user_in.email,
        "full_name": user_in.full_name,
        "role": "student",
        "auth_provider": "password",
        "hashed_password": get_password_hash(user_in.password)
    }

    user = await user_service_client.create_user(user_data)
    log_audit(str(user["id"]), "register", "user", status="success", request_id=request_id)
    return user

@router.post("/google", response_model=Token)
async def google_login(
    request: Request, login_data: GoogleLogin
):
    request_id = getattr(request.state, "request_id", None)

    # 1. Verify Google Token
    try:
        idinfo = verify_google_token(login_data.id_token)
    except HTTPException as e:
        log_audit(
            user_id="anonymous",
            action="GOOGLE_LOGIN_FAILURE",
            resource="user",
            status="failure",
            metadata={"reason": e.detail},
            request_id=request_id,
        )
        raise e

    email = idinfo.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="Email missing from Google token")

    full_name = idinfo.get("name") or idinfo.get("given_name", "Google User")
    avatar_url = idinfo.get("picture")

    # 2. Fetch or Create User
    user = await user_service_client.get_user_by_email(email)

    if not user:
        user_data = {
            "email": email,
            "full_name": full_name,
            "avatar_url": avatar_url,
            "role": "student",
            "auth_provider": "google"
        }
        user = await user_service_client.create_user(user_data)
        log_audit(
            user_id=str(user["id"]),
            action="USER_CREATED_FROM_GOOGLE",
            resource="user",
            status="success",
            metadata={"email": email},
            request_id=request_id,
        )
    else:
        # Secure Account Linking: If user exists, we trust Google's verified email
        update_data = {}
        if not user.get("full_name") and full_name:
            update_data["full_name"] = full_name
        if not user.get("avatar_url") and avatar_url:
            update_data["avatar_url"] = avatar_url

        if update_data:
            await user_service_client.update_user(user["id"], update_data)
            user.update(update_data)

        # Check if user is active
        if not user.get("is_active"):
            log_audit(
                user_id=str(user["id"]),
                action="GOOGLE_LOGIN_FAILURE",
                resource="user",
                status="failure",
                metadata={"reason": "account_suspended", "email": email},
                request_id=request_id,
            )
            raise HTTPException(status_code=403, detail="Account suspended")

    # 3. Issue Tokens
    access_token = create_access_token(
        data={
            "sub": str(user["id"]),
            "role": user["role"],
            "email": user["email"],
            "auth_provider": user["auth_provider"],
            "faculty": user.get("faculty"),
            "semester": user.get("semester"),
        }
    )
    refresh_token = create_refresh_token(
        data={
            "sub": str(user["id"]),
            "email": user["email"],
            "auth_provider": user["auth_provider"],
        }
    )

    log_audit(
        user_id=str(user["id"]),
        action="GOOGLE_LOGIN_SUCCESS",
        resource="user",
        status="success",
        metadata={"email": email},
        request_id=request_id,
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }

@router.post("/login", response_model=Token)
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
):
    request_id = getattr(request.state, "request_id", None)
    user = await user_service_client.get_user_by_email(form_data.username)

    if not user or not user.get("hashed_password") or not verify_password(form_data.password, user["hashed_password"]):
        log_audit(
            form_data.username,
            "login",
            "user",
            status="failure",
            metadata={"reason": "invalid_credentials"},
            request_id=request_id,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.get("is_active"):
        raise HTTPException(status_code=403, detail="Account suspended")

    access_token = create_access_token(
        data={
            "sub": str(user["id"]),
            "role": user["role"],
            "email": user["email"],
            "auth_provider": user["auth_provider"],
            "faculty": user.get("faculty"),
            "semester": user.get("semester"),
        }
    )
    refresh_token = create_refresh_token(
        data={
            "sub": str(user["id"]),
            "email": user["email"],
            "auth_provider": user["auth_provider"],
        }
    )

    log_audit(str(user["id"]), "login", "user", status="success", request_id=request_id)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

async def get_redis():
    r = await redis.from_url(settings.REDIS_URL, decode_responses=True)
    try:
        yield r
    finally:
        await r.close()

@router.post("/logout")
async def logout(
    request: Request,
    token: str = Depends(oauth2_scheme),
    r: redis.Redis = Depends(get_redis),
):
    request_id = getattr(request.state, "request_id", None)
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            audience=settings.JWT_AUDIENCE,
            issuer=settings.JWT_ISSUER,
        )
        exp = payload.get("exp")
        import time

        ttl = int(exp - time.time()) if exp else 3600
        if ttl > 0:
            await r.setex(f"blacklist:{token}", ttl, "true")

        log_audit(
            payload.get("sub"),
            "logout",
            "token",
            status="success",
            request_id=request_id,
        )
        return {"message": "Successfully logged out"}
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

@router.post("/refresh", response_model=Token)
async def refresh_token(request: Request, refresh_token: str):
    request_id = getattr(request.state, "request_id", None)
    try:
        payload = jwt.decode(
            refresh_token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            audience=settings.JWT_AUDIENCE,
            issuer=settings.JWT_ISSUER,
        )
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        user = await user_service_client.get_user_by_id(user_id)
        if not user or not user.get("is_active"):
            raise HTTPException(status_code=401, detail="User not found or inactive")

        access_token = create_access_token(
            data={
                "sub": str(user["id"]),
                "role": user["role"],
                "email": user["email"],
                "auth_provider": user["auth_provider"],
                "faculty": user.get("faculty"),
                "semester": user.get("semester"),
            }
        )
        new_refresh_token = create_refresh_token(
            data={
                "sub": str(user["id"]),
                "email": user["email"],
                "auth_provider": user["auth_provider"],
            }
        )

        log_audit(
            str(user["id"]), "refresh", "token", status="success", request_id=request_id
        )

        return {
            "access_token": access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
        }
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
