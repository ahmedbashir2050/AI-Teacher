import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from sqlalchemy.orm import sessionmaker
import os

# Set the database URL for testing BEFORE importing anything from the app
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'

# Patch the get_qdrant_client function BEFORE any app code is imported.
patcher = patch('app.core.qdrant_db.get_qdrant_client', return_value=MagicMock())
patcher.start()

# Explicitly import all models to ensure they are registered with Base.metadata
from app.models import academic, user, chat

from app.main import app
from app.api.dependencies import get_db
from app.core.database import engine, Base
from app.services import user_service, academic_service
from app.schemas import user as user_schemas, academic as academic_schemas

# Setup the test database session
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Override the get_db dependency for the app
def override_get_db():
    database = TestingSessionLocal()
    try:
        yield database
    finally:
        database.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="session")
def client():
    # Create the tables
    Base.metadata.create_all(bind=engine)

    # Populate the test database with initial data
    db = TestingSessionLocal()
    user_service.create_user(db, user_schemas.UserCreate(role="admin"), "admin_user_id")
    user_service.create_user(db, user_schemas.UserCreate(role="student"), "student_user_id")
    academic_service.create_college(db, academic_schemas.CollegeCreate(name="Test College"))
    academic_service.create_department(db, academic_schemas.DepartmentCreate(name="Test Department", college_id=1))
    academic_service.create_semester(db, academic_schemas.SemesterCreate(name="Test Semester", department_id=1))
    academic_service.create_course(db, academic_schemas.CourseCreate(name="Test Course", code="TC101", semester_id=1))
    academic_service.create_book(db, academic_schemas.BookCreate(title="Test Book", language="English", course_id=1), "admin_user_id")
    db.commit()
    db.close()

    with TestClient(app) as test_client:
        yield test_client

    # Drop the tables
    Base.metadata.drop_all(bind=engine)

def pytest_sessionfinish(session, exitstatus):
    # Clean up the patch after the test session ends
    patcher.stop()
