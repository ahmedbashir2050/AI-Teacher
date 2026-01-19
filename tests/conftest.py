# tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.hashing import get_password_hash
from app.core.security import UserRole
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.user import Role, User

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def test_client():
    # Create a test user and role for authentication
    db = TestingSessionLocal()
    role = Role(name=UserRole.STUDENT.value, description="Student role")
    db.add(role)
    db.commit()
    db.refresh(role)

    user = User(
        email="testuser@example.com",
        hashed_password=get_password_hash("testpassword"),
        role_id=role.id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    yield TestClient(app)
