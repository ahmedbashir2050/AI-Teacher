import enum

from db.base import BaseModel
from sqlalchemy import Boolean, Column, DateTime, Enum, String


class RoleEnum(str, enum.Enum):
    ADMIN = "admin"
    ACADEMIC = "academic"
    STUDENT = "student"


class User(BaseModel):
    __tablename__ = "users"

    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=True)
    full_name = Column(String, nullable=True)
    avatar_url = Column(String, nullable=True)
    hashed_password = Column(String, nullable=True)
    auth_provider = Column(String, default="local", nullable=False)
    last_login_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    role = Column(Enum(RoleEnum), default=RoleEnum.STUDENT, nullable=False)
