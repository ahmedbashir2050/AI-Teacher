import pytest
from unittest.mock import patch, MagicMock, ANY
from uuid import uuid4
from fastapi.testclient import TestClient

# Mock DB and other global side effects
with patch("sqlalchemy.create_engine"), \
     patch("sqlalchemy.orm.sessionmaker"), \
     patch("db.base.Base.metadata.create_all"), \
     patch("redis.asyncio.from_url"):
    from main import app

client = TestClient(app)

def test_get_teacher_exam_performance_success():
    teacher_id = str(uuid4())
    faculty_id = str(uuid4())
    headers = {
        "X-User-Id": teacher_id,
        "X-User-Role": "teacher",
        "X-User-Faculty-Id": faculty_id
    }

    mock_stats = {
        "average_score": 75.5,
        "total_attempts": 50
    }

    with patch("api.exam.get_db"), \
         patch("repository.exam_repository.get_performance_stats") as mock_stats_repo:
        mock_stats_repo.return_value = mock_stats
        response = client.get("/teacher/performance", headers=headers)

    assert response.status_code == 200
    assert response.json()["average_score"] == 75.5
    mock_stats_repo.assert_called_once_with(ANY, course_id=None, faculty_id=faculty_id)

def test_get_teacher_exam_performance_unauthorized():
    headers = {
        "X-User-Id": str(uuid4()),
        "X-User-Role": "student",
        "X-User-Faculty-Id": str(uuid4())
    }

    response = client.get("/teacher/performance", headers=headers)
    assert response.status_code == 403
