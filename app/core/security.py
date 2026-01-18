from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel
from enum import Enum
from app.config import settings
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.repository import user_repository

# --- User Roles ---
class UserRole(str, Enum):
    ADMIN = "admin"
    ACADEMIC = "academic"
    STUDENT = "student"

# --- JWT Token Handling ---
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")

class TokenData(BaseModel):
    username: str
    role: UserRole

class Token(BaseModel):
    access_token: str
    refresh_token: str | None = None
    token_type: str = "bearer"

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({
        "exp": expire,
        "iss": settings.JWT_ISSUER,
        "aud": settings.JWT_AUDIENCE,
    })
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode = data.copy()
    to_encode.update({
        "exp": expire,
        "iss": settings.JWT_ISSUER,
        "aud": settings.JWT_AUDIENCE,
    })
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

def decode_token(token: str) -> TokenData | None:
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            audience=settings.JWT_AUDIENCE,
            issuer=settings.JWT_ISSUER
        )
        username = payload.get("sub")
        role = payload.get("role")
        if username is None or role is None:
            return None
        return TokenData(username=username, role=UserRole(role))
    except JWTError:
        return None

# --- Dependency for getting current user ---
def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    token_data = decode_token(token)
    if token_data is None:
        raise credentials_exception

    user = user_repository.get_user_by_username(db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user

# --- Role-based Access Control Dependencies ---
def require_role(required_roles: list[UserRole]):
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="The user does not have adequate privileges"
            )
        return current_user
    return role_checker

ADMIN_ACCESS = require_role([UserRole.ADMIN])
ACADEMIC_ACCESS = require_role([UserRole.ADMIN, UserRole.ACADEMIC])
STUDENT_ACCESS = require_role([UserRole.ADMIN, UserRole.ACADEMIC, UserRole.STUDENT])
