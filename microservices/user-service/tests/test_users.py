from fastapi.testclient import TestClient
from main import app
import pytest
from uuid import uuid4
from unittest.mock import patch, MagicMock

client = TestClient(app)

def test_get_me_no_header():
    response = client.get("/me")
    assert response.status_code == 422 # Missing Header

def test_get_me_with_header():
    user_id = str(uuid4())

    mock_user = MagicMock()
    mock_user.id = user_id
    mock_user.email = "test@example.com"
    mock_user.full_name = "Test User"
    mock_user.role = "student"
    mock_user.auth_provider = "password"
    mock_user.avatar_url = None
    mock_user.university_id = None
    mock_user.faculty = None
    mock_user.faculty_id = None
    mock_user.major = None
    mock_user.department_id = None
    mock_user.semester = None
    mock_user.semester_id = None
    mock_user.is_active = True

    with patch("core.services.user_service.get_user_by_id", return_value=mock_user), \
         patch("api.users.get_read_db"):
        response = client.get("/me", headers={"X-User-Id": user_id})

    assert response.status_code == 200
    assert response.json()["email"] == "test@example.com"

def test_assign_teacher_success():
    admin_id = str(uuid4())
    teacher_id = uuid4()

    mock_teacher = MagicMock()
    mock_teacher.id = teacher_id
    mock_teacher.role = "teacher"
    mock_teacher.email = "teacher@test.com"
    mock_teacher.full_name = "Teacher Name"
    mock_teacher.auth_provider = "password"
    mock_teacher.is_active = True

    payload = {
        "faculty_id": str(uuid4()),
        "department_id": str(uuid4())
    }

    with patch("core.services.user_service.get_user_by_id", return_value=mock_teacher), \
         patch("core.services.user_service.update_profile") as mock_update, \
         patch("api.admin.get_db"), \
         patch("api.admin.log_audit"):

        mock_update.return_value = mock_teacher

        response = client.post(
            f"/admin/teachers/{teacher_id}/assign",
            json=payload,
            headers={
                "X-User-Id": admin_id,
                "X-User-Role": "admin"
            }
        )

    assert response.status_code == 200
    mock_update.assert_called_once()

def test_assign_teacher_forbidden_for_student():
    response = client.post(
        f"/admin/teachers/{uuid4()}/assign",
        json={},
        headers={
            "X-User-Id": str(uuid4()),
            "X-User-Role": "student"
        }
    )
    assert response.status_code == 403
