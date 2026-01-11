import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from sqlalchemy.orm import sessionmaker
import os
import uuid

# Set the database URL for testing BEFORE importing anything from the app
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'

# Patch the get_qdrant_client function BEFORE any app code is imported.
patcher = patch('app.core.qdrant_db.get_qdrant_client', return_value=MagicMock())
patcher.start()

# Explicitly import all models to ensure they are registered with Base.metadata
from app.models import academic, user

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
    user_service.create_user(db, user_schemas.UserCreate(role="academic"), "academic_user_id")
    user_service.create_user(db, user_schemas.UserCreate(role="student"), "student_user_id")

    faculty = academic_service.create_faculty(db, academic_schemas.FacultyCreate(name="Test Faculty"))
    department = academic_service.create_department(db, academic_schemas.DepartmentCreate(name="Test Department", faculty_id=faculty.id))
    semester = academic_service.create_semester(db, academic_schemas.SemesterCreate(name="Test Semester", department_id=department.id))
    academic_service.create_book(db, academic_schemas.BookCreate(title="Test Book", language="English", semester_id=semester.id), "faculty_123_semester_456", uuid.uuid4())

    db.commit()
    db.close()

    with TestClient(app) as test_client:
        yield test_client

    # Drop the tables
    Base.metadata.drop_all(bind=engine)

def pytest_sessionfinish(session, exitstatus):
    # Clean up the patch after the test session ends
    patcher.stop()
