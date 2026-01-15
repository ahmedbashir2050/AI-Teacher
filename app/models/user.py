# app/models/user.py
import enum
from sqlalchemy import Column, String, Boolean, ForeignKey, Enum
from sqlalchemy.orm import relationship
from app.db.base import BaseModel

class RoleEnum(enum.Enum):
    """
    Defines the roles available in the system.
    Using an Enum provides type safety and clarity.
    """
    ADMIN = "admin"
    ACADEMIC = "academic"
    STUDENT = "student"

class Role(BaseModel):
    """
    Role model to manage user permissions.
    - A `name` to identify the role (e.g., ADMIN, STUDENT).
    - A `description` for clarity in admin interfaces.
    """
    __tablename__ = 'roles' # Overriding the default pluralization

    name = Column(String(50), unique=True, index=True, nullable=False)
    description = Column(String(255), nullable=True)

    users = relationship("User", back_populates="role")

class User(BaseModel):
    """
    User model for authentication and identification.
    - `email` is the primary identifier and must be unique.
    - `hashed_password` stores the securely hashed password.
    - `is_active` can be used to disable accounts without deleting them.
    - `role_id` links the user to a specific role.
    """
    __tablename__ = 'users'

    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    role_id = Column(ForeignKey('roles.id'), nullable=False)
    role = relationship("Role", back_populates="users")

    # Relationships to other models will be added here later,
    # e.g., chat_sessions, exam_attempts
