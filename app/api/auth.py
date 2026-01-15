from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from app.core.security import create_access_token, create_refresh_token, verify_password, Token
from app.core.hashing import get_password_hash
from app.models.requests import UserCreate
from app.models.responses import UserResponse
from app.config import settings
from app.db.session import get_db
from sqlalchemy.orm import Session
from app.repository import user_repository
from app.core.security import UserRole

router = APIRouter()

@router.post("/token", response_model=Token)
async def login_for_access_token(db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()):
    user = user_repository.get_user_by_username(db, username=form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        data={"sub": user.username, "role": user.role.value}
    )
    refresh_token = create_refresh_token(
        data={"sub": user.username, "role": user.role.value}
    )
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

@router.post("/register", response_model=UserResponse, status_code=201)
async def register_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = user_repository.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )

    db_user = user_repository.create_user(db, username=user.username, password=user.password, role=UserRole.STUDENT)
    return UserResponse(username=db_user.username, role=db_user.role.value)
