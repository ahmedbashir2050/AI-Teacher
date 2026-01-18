from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import jwt
import redis.asyncio as redis
from pydantic import BaseModel, EmailStr
from db.session import get_db
from repository import user_repository
from core.config import settings
from core.security import create_access_token, create_refresh_token, verify_password
from models.user import RoleEnum
from core.audit import log_audit

router = APIRouter()

class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    username: str
    role: str

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(request: Request, user_in: UserCreate, db: Session = Depends(get_db)):
    request_id = getattr(request.state, "request_id", None)
    if user_repository.get_user_by_email(db, email=user_in.email):
        log_audit("anonymous", "register", "user", status="failure", details={"reason": "email_exists"}, request_id=request_id)
        raise HTTPException(status_code=400, detail="Email already registered")
    if user_repository.get_user_by_username(db, username=user_in.username):
        raise HTTPException(status_code=400, detail="Username already registered")

    user = user_repository.create_user(
        db,
        email=user_in.email,
        username=user_in.username,
        password=user_in.password
    )
    log_audit(str(user.id), "register", "user", status="success", request_id=request_id)
    return user

@router.post("/login", response_model=Token)
def login(request: Request, db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()):
    request_id = getattr(request.state, "request_id", None)
    user = user_repository.get_user_by_username(db, username=form_data.username)
    if not user:
        user = user_repository.get_user_by_email(db, email=form_data.username)

    if not user or not verify_password(form_data.password, user.hashed_password):
        log_audit(form_data.username, "login", "user", status="failure", details={"reason": "invalid_credentials"}, request_id=request_id)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": str(user.id), "role": user.role.value})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})

    log_audit(str(user.id), "login", "user", status="success", request_id=request_id)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

async def get_redis():
    r = await redis.from_url(settings.REDIS_URL, decode_responses=True)
    try:
        yield r
    finally:
        await r.close()

@router.post("/logout")
async def logout(request: Request, token: str = Depends(oauth2_scheme), r: redis.Redis = Depends(get_redis)):
    request_id = getattr(request.state, "request_id", None)
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            audience=settings.JWT_AUDIENCE,
            issuer=settings.JWT_ISSUER
        )
        exp = payload.get("exp")
        import time
        ttl = int(exp - time.time()) if exp else 3600
        if ttl > 0:
            await r.setex(f"blacklist:{token}", ttl, "true")

        log_audit(payload.get("sub"), "logout", "token", status="success", request_id=request_id)
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
            issuer=settings.JWT_ISSUER
        )
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        user = db.query(user_repository.User).filter(user_repository.User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")

        access_token = create_access_token(data={"sub": str(user.id), "role": user.role.value})
        new_refresh_token = create_refresh_token(data={"sub": str(user.id)})

        log_audit(str(user.id), "refresh", "token", status="success", request_id=request_id)

        return {
            "access_token": access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer"
        }
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
