import redis.asyncio as redis
from core.audit import log_audit
from core.config import settings
from core.google_auth import verify_google_token
from core.security import create_access_token, create_refresh_token, verify_password
from db.session import get_db
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import jwt
from models.user import RoleEnum
from pydantic import BaseModel, EmailStr
from repository import user_repository
from sqlalchemy.orm import Session

router = APIRouter()


class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str


class UserResponse(BaseModel):
    id: str
    email: str
    username: str | None = None
    full_name: str | None = None
    avatar_url: str | None = None
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
def register(request: Request, user_in: UserCreate, db: Session = Depends(get_db)):
    request_id = getattr(request.state, "request_id", None)
    if user_repository.get_user_by_email(db, email=user_in.email):
        log_audit(
            "anonymous",
            "register",
            "user",
            status="failure",
            metadata={"reason": "email_exists"},
            request_id=request_id,
        )
        raise HTTPException(status_code=400, detail="Email already registered")
    if user_repository.get_user_by_username(db, username=user_in.username):
        raise HTTPException(status_code=400, detail="Username already registered")

    user = user_repository.create_user(
        db, email=user_in.email, username=user_in.username, password=user_in.password
    )
    log_audit(str(user.id), "register", "user", status="success", request_id=request_id)
    return user


@router.post("/google", response_model=Token)
async def google_login(
    request: Request, login_data: GoogleLogin, db: Session = Depends(get_db)
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
    full_name = idinfo.get("name")
    avatar_url = idinfo.get("picture")

    # 2. Fetch or Create User
    user = user_repository.get_user_by_email(db, email=email)

    if not user:
        user = user_repository.create_google_user(
            db, email=email, full_name=full_name, avatar_url=avatar_url
        )
        log_audit(
            user_id=str(user.id),
            action="USER_CREATED_FROM_GOOGLE",
            resource="user",
            status="success",
            metadata={"email": email},
            request_id=request_id,
        )
    else:
        # Check if user is active
        if not user.is_active:
            log_audit(
                user_id=str(user.id),
                action="GOOGLE_LOGIN_FAILURE",
                resource="user",
                status="failure",
                metadata={"reason": "account_suspended", "email": email},
                request_id=request_id,
            )
            raise HTTPException(status_code=403, detail="Account suspended")

        # Ensure auth provider is updated if linking is allowed
        if user.auth_provider != "google":
            user.auth_provider = "google"
            db.commit()

    # 3. Update last login
    user_repository.update_last_login(db, user)

    # 4. Issue Tokens
    access_token = create_access_token(
        data={
            "sub": str(user.id),
            "role": user.role.value,
            "email": user.email,
            "auth_provider": user.auth_provider,
        }
    )
    refresh_token = create_refresh_token(
        data={
            "sub": str(user.id),
            "email": user.email,
            "auth_provider": user.auth_provider,
        }
    )

    log_audit(
        user_id=str(user.id),
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
def login(
    request: Request,
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends(),
):
    request_id = getattr(request.state, "request_id", None)
    user = user_repository.get_user_by_username(db, username=form_data.username)
    if not user:
        user = user_repository.get_user_by_email(db, email=form_data.username)

    if not user or not verify_password(form_data.password, user.hashed_password):
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
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        data={
            "sub": str(user.id),
            "role": user.role.value,
            "email": user.email,
            "auth_provider": user.auth_provider,
        }
    )
    refresh_token = create_refresh_token(
        data={
            "sub": str(user.id),
            "email": user.email,
            "auth_provider": user.auth_provider,
        }
    )

    log_audit(str(user.id), "login", "user", status="success", request_id=request_id)

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
def refresh_token(request: Request, refresh_token: str, db: Session = Depends(get_db)):
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

        user = (
            db.query(user_repository.User)
            .filter(user_repository.User.id == user_id)
            .first()
        )
        if not user:
            raise HTTPException(status_code=401, detail="User not found")

        access_token = create_access_token(
            data={
                "sub": str(user.id),
                "role": user.role.value,
                "email": user.email,
                "auth_provider": user.auth_provider,
            }
        )
        new_refresh_token = create_refresh_token(
            data={
                "sub": str(user.id),
                "email": user.email,
                "auth_provider": user.auth_provider,
            }
        )

        log_audit(
            str(user.id), "refresh", "token", status="success", request_id=request_id
        )

        return {
            "access_token": access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
        }
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")


class RoleUpdate(BaseModel):
    user_id: str
    new_role: RoleEnum


@router.put("/roles", status_code=status.HTTP_200_OK)
async def update_user_role(
    request: Request, update: RoleUpdate, db: Session = Depends(get_db)
):
    # In a real app, this would be protected by ADMIN role
    request_id = getattr(request.state, "request_id", None)
    user = (
        db.query(user_repository.User)
        .filter(user_repository.User.id == update.user_id)
        .first()
    )
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    old_role = user.role.value
    user.role = update.new_role
    db.commit()

    log_audit(
        user_id="admin",  # Assume admin caller
        action="update_role",
        resource="user",
        resource_id=update.user_id,
        metadata={"old_role": old_role, "new_role": update.new_role.value},
        request_id=request_id,
    )
    return {"message": "Role updated successfully"}
