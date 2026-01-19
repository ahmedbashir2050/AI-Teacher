import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import sys
import os

# Mock environment variables before importing settings
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["JWT_SECRET_KEY"] = "test-secret"
os.environ["JWT_AUDIENCE"] = "test-audience"
os.environ["JWT_ISSUER"] = "test-issuer"
os.environ["GOOGLE_CLIENT_ID"] = "test-google-id"
os.environ["USER_SERVICE_URL"] = "http://localhost:8001"

# Add the service directory to sys.path
sys.path.append(os.path.join(os.getcwd(), "microservices/auth-service"))

from main import app
from db.session import get_db

client = TestClient(app)

@pytest.fixture
def mock_db():
    return MagicMock()

def test_google_login_success(mock_db):
    app.dependency_overrides[get_db] = lambda: mock_db

    mock_idinfo = {
        "email": "test@example.com",
        "name": "Test User",
        "picture": "http://example.com/photo.jpg",
        "iss": "https://accounts.google.com",
        "email_verified": True
    }

    mock_user = {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "email": "test@example.com",
        "role": "student",
        "is_active": True,
        "auth_provider": "google",
        "full_name": "Test User",
        "avatar_url": "http://example.com/photo.jpg"
    }

    with patch("api.auth.verify_google_token", return_value=mock_idinfo), \
         patch("api.auth.user_service_client.get_user_by_email", return_value=None), \
         patch("api.auth.user_service_client.create_user", return_value=mock_user):

        response = client.post("/auth/google", json={"id_token": "valid_token"})

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    app.dependency_overrides.clear()

from fastapi import HTTPException

def test_google_login_failure(mock_db):
    app.dependency_overrides[get_db] = lambda: mock_db

    with patch("api.auth.verify_google_token", side_effect=HTTPException(status_code=401, detail="Invalid Token")):
        response = client.post("/auth/google", json={"id_token": "invalid_token"})
        assert response.status_code == 401

    app.dependency_overrides.clear()

def test_google_login_suspended_user(mock_db):
    app.dependency_overrides[get_db] = lambda: mock_db

    mock_idinfo = {
        "email": "suspended@example.com",
        "name": "Suspended User",
        "iss": "https://accounts.google.com",
        "email_verified": True
    }

    mock_user = {
        "id": "550e8400-e29b-41d4-a716-446655440001",
        "email": "suspended@example.com",
        "role": "student",
        "is_active": False,
        "auth_provider": "google",
        "full_name": "Suspended User"
    }

    with patch("api.auth.verify_google_token", return_value=mock_idinfo), \
         patch("api.auth.user_service_client.get_user_by_email", return_value=mock_user):

        response = client.post("/auth/google", json={"id_token": "valid_token"})
        assert response.status_code == 403
        assert response.json()["detail"] == "Account suspended"

    app.dependency_overrides.clear()
