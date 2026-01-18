import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from app.main import app
from app.core.security import create_access_token, UserRole

client = TestClient(app)

# ===================================
# Mocks for External Services
# ===================================

@pytest.fixture(scope="module")
def mock_llm_service():
    """Mocks the LLM service."""
    with patch('app.services.llm_service.llm_service') as mock:
        mock.get_chat_completion.return_value = "Mocked LLM response."
        yield mock

@pytest.fixture(scope="module")
def mock_retriever():
    """Mocks the retriever."""
    with patch('app.rag.retriever.retrieve_relevant_chunks') as mock:
        mock.return_value = ["Mocked chunk"]
        yield mock

# ===================================
# Test Tokens
# ===================================

@pytest.fixture(scope="module")
def admin_token() -> str:
    return create_access_token({"sub": "admin", "role": UserRole.ADMIN})

@pytest.fixture(scope="module")
def student_token() -> str:
    return create_access_token({"sub": "student", "role": UserRole.STUDENT})

# ===================================
# Tests for Authentication
# ===================================

def test_login_for_access_token():
    response = client.post("/api/auth/token", data={"username": "student", "password": "studentpassword"})
    assert response.status_code == 200
    json_response = response.json()
    assert "access_token" in json_response
    assert json_response["token_type"] == "bearer"

def test_login_invalid_credentials():
    response = client.post("/api/auth/token", data={"username": "student", "password": "wrongpassword"})
    assert response.status_code == 401
    assert response.json() == {"detail": "Incorrect username or password"}

def test_register_user():
    response = client.post("/api/auth/register", json={"username": "newuser", "password": "newpassword"})
    assert response.status_code == 201
    assert response.json() == {"username": "newuser", "role": "student"}

    # Verify the user can login
    response = client.post("/api/auth/token", data={"username": "newuser", "password": "newpassword"})
    assert response.status_code == 200

# ===================================
# Tests for Rate Limiting
# ===================================

def test_rate_limiting_chat(student_token):
    headers = {"Authorization": f"Bearer {student_token}"}
    # The limit is 5/minute, so 6 requests should trigger it.
    for i in range(5):
        response = client.post("/api/chat", json={"question": "test"}, headers=headers)
        assert response.status_code == 200

    response = client.post("/api/chat", json={"question": "test"}, headers=headers)
    assert response.status_code == 429

# ===================================
# Tests for Role Enforcement
# ===================================

def test_ingest_admin_access(admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    # This is a simplified test; we are not actually uploading a file.
    # We expect a 422 for a missing file, which shows we passed the auth check.
    response = client.post("/api/ingest", headers=headers)
    assert response.status_code == 422

def test_ingest_student_no_access(student_token):
    headers = {"Authorization": f"Bearer {student_token}"}
    response = client.post("/api/ingest", headers=headers)
    assert response.status_code == 403
    assert response.json() == {"detail": "The user does not have adequate privileges"}

def test_chat_student_access(student_token):
    headers = {"Authorization": f"Bearer {student_token}"}
    response = client.post("/api/chat", json={"question": "What is economics?"}, headers=headers)
    assert response.status_code == 200

# ===================================
# Tests for Health Checks
# ===================================

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_readiness_check():
    # This test assumes dependencies are available.
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ready"}
