from fastapi import APIRouter, Depends, Header, Request, HTTPException
from sqlalchemy.orm import Session
from db.session import get_db
from core.services import user_service
from core.audit import log_audit
from pydantic import BaseModel, EmailStr
from typing import Optional
from uuid import UUID

router = APIRouter()

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    university_id: Optional[str] = None
    faculty: Optional[str] = None
    faculty_id: Optional[UUID] = None
    major: Optional[str] = None
    department_id: Optional[UUID] = None
    semester: Optional[str] = None
    semester_id: Optional[UUID] = None

class UserCreateInternal(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    role: str
    auth_provider: str
    avatar_url: Optional[str] = None
    hashed_password: Optional[str] = None

class UserResponse(BaseModel):
    id: UUID
    email: str
    full_name: Optional[str] = None
    role: str
    auth_provider: str
    avatar_url: Optional[str] = None
    university_id: Optional[str] = None
    faculty: Optional[str] = None
    faculty_id: Optional[UUID] = None
    major: Optional[str] = None
    department_id: Optional[UUID] = None
    semester: Optional[str] = None
    semester_id: Optional[UUID] = None
    is_active: bool

    class Config:
        from_attributes = True

@router.get("/me", response_model=UserResponse)
def get_me(
    request: Request,
    db: Session = Depends(get_db),
    x_user_id: str = Header(...)
):
    request_id = getattr(request.state, "request_id", None)
    user = user_service.get_user_by_id(db, UUID(x_user_id))

    log_audit(
        user_id=x_user_id,
        action="USER_PROFILE_FETCHED",
        resource="user",
        status="success",
        request_id=request_id
    )
    return user

@router.patch("/me", response_model=UserResponse)
def update_me(
    request: Request,
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    x_user_id: str = Header(...)
):
    request_id = getattr(request.state, "request_id", None)
    update_data = user_update.model_dump(exclude_unset=True)
    user = user_service.update_profile(db, UUID(x_user_id), update_data)

    log_audit(
        user_id=x_user_id,
        action="USER_PROFILE_UPDATED",
        resource="user",
        status="success",
        metadata=update_data,
        request_id=request_id
    )
    return user

@router.get("/internal/users/email/{email}", response_model=UserResponse)
def get_user_by_email_internal(
    email: str,
    db: Session = Depends(get_db)
):
    user = user_service.get_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.get("/internal/users/{user_id}", response_model=UserResponse)
def get_user_by_id_internal(
    user_id: UUID,
    db: Session = Depends(get_db)
):
    user = user_service.get_user_by_id(db, user_id)
    return user

@router.post("/internal/users", response_model=UserResponse)
def create_user_internal(
    request: Request,
    user_in: UserCreateInternal,
    db: Session = Depends(get_db)
):
    request_id = getattr(request.state, "request_id", None)
    user = user_service.create_user(db, user_in.model_dump())

    log_audit(
        user_id=str(user.id),
        action="USER_CREATED",
        resource="user",
        status="success",
        metadata={"email": user.email, "role": user.role},
        request_id=request_id
    )
    return user

@router.delete("/internal/users/{user_id}", response_model=UserResponse)
def deactivate_user_internal(
    request: Request,
    user_id: UUID,
    db: Session = Depends(get_db)
):
    request_id = getattr(request.state, "request_id", None)
    user = user_service.deactivate_user(db, user_id)

    log_audit(
        user_id=str(user_id),
        action="USER_DEACTIVATED",
        resource="user",
        status="success",
        request_id=request_id
    )
    return user
