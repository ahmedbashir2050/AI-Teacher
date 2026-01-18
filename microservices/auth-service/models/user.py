import enum
from sqlalchemy import Column, String, Boolean, Enum
from db.base import BaseModel

class RoleEnum(str, enum.Enum):
    ADMIN = "admin"
    ACADEMIC = "academic"
    STUDENT = "student"

class User(BaseModel):
    __tablename__ = 'users'

    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    role = Column(Enum(RoleEnum), default=RoleEnum.STUDENT, nullable=False)
