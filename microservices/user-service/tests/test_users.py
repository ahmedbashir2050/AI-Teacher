from fastapi.testclient import TestClient
from main import app
import pytest
from uuid import uuid4

client = TestClient(app)

def test_get_me_no_header():
    response = client.get("/me")
    assert response.status_code == 422 # Missing Header

def test_get_me_with_header(monkeypatch):
    # Mocking user_service.get_user_by_id
    user_id = str(uuid4())
    from core.services import user_service

    class MockUser:
        def __init__(self):
            self.id = user_id
            self.email = "test@example.com"
            self.full_name = "Test User"
            self.role = "student"
            self.auth_provider = "password"
            self.avatar_url = None
            self.university_id = None
            self.faculty = None
            self.major = None
            self.semester = None
            self.is_active = True

    def mock_get_user_by_id(db, uid):
        return MockUser()

    monkeypatch.setattr(user_service, "get_user_by_id", mock_get_user_by_id)

    response = client.get("/me", headers={"X-User-Id": user_id})
    assert response.status_code == 200
    assert response.json()["email"] == "test@example.com"
