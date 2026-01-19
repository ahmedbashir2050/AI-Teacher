# app/db/base.py
import uuid

from sqlalchemy import Column, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, declared_attr

# Central declarative base for all ORM models.
# This Base object will collect metadata for all tables.
Base = declarative_base()


class BaseModel(Base):
    """
    Base ORM model for all other models to inherit from.
    It provides:
    1. A UUID primary key (`id`).
    2. Automatic `created_at` and `updated_at` timestamp fields.
    3. An automatic table name generation scheme (e.g., 'User' -> 'users').
    """

    __abstract__ = True  # This ensures SQLAlchemy doesn't create a table for BaseModel.

    # Using UUID for primary keys is a good practice for distributed systems
    # and to avoid exposing sequential IDs in APIs.
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Timestamps to track record creation and last update.
    # `server_default` executes the function on the database side.
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    @declared_attr
    def __tablename__(cls) -> str:
        # A simple pluralization rule: add 's' to the lowercase class name.
        # This is a common convention and keeps table names consistent.
        return f"{cls.__name__.lower()}s"
