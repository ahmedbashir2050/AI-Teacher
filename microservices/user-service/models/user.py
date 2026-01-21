import enum

from db.base import BaseModel
from sqlalchemy import Boolean, Column, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID


class RoleEnum(str, enum.Enum):
    STUDENT = "student"
    TEACHER = "teacher"
    ADMIN = "admin"


class AuthProviderEnum(str, enum.Enum):
    GOOGLE = "google"
    PASSWORD = "password"


class User(BaseModel):
    __tablename__ = "users"

    email = Column(String(255), unique=True, index=True, nullable=False)
    full_name = Column(String(255))
    role = Column(
        Enum(RoleEnum, name="role_enum"), default=RoleEnum.STUDENT, nullable=False, index=True
    )
    auth_provider = Column(
        Enum(AuthProviderEnum, name="auth_provider_enum"), nullable=False
    )
    avatar_url = Column(String(512))
    university_id = Column(String(100), index=True)
    faculty = Column(String(255))
    faculty_id = Column(UUID(as_uuid=True), ForeignKey("faculties.id"), index=True)
    major = Column(String(255))
    department_id = Column(UUID(as_uuid=True), ForeignKey("departments.id"), index=True)
    semester = Column(String(100))
    semester_id = Column(UUID(as_uuid=True), ForeignKey("semesters.id"), index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    hashed_password = Column(String(255), nullable=True)
