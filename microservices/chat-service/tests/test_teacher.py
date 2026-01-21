import pytest
from unittest.mock import patch, MagicMock, ANY
from uuid import uuid4
from fastapi.testclient import TestClient

# Mock DB and other global side effects
with patch("sqlalchemy.create_engine"), \
     patch("sqlalchemy.orm.sessionmaker"), \
     patch("db.base.Base.metadata.create_all"), \
     patch("redis.asyncio.from_url"), \
     patch("fastapi_limiter.FastAPILimiter.init"):
    from main import app

client = TestClient(app)

def test_get_teacher_answers_success():
    teacher_id = str(uuid4())
    faculty_id = "engineering"
    headers = {
        "X-User-Id": teacher_id,
        "X-User-Role": "teacher",
        "X-User-Faculty-Id": faculty_id
    }

    mock_answers = [
        {
            "id": uuid4(),
            "user_id": uuid4(),
            "question_text": "What is math?",
            "ai_answer": "Math is fun.",
            "rag_confidence_score": 0.95,
            "verified_by_teacher": False,
            "teacher_comment": None,
            "is_correct": True
        }
    ]

    with patch("api.chat.get_db"), \
         patch("repository.chat_repository.get_answers_for_review") as mock_get:
        mock_get.return_value = mock_answers
        response = client.get("/teacher/answers", headers=headers)

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["question_text"] == "What is math?"
    mock_get.assert_called_once_with(ANY, faculty_id=faculty_id)

def test_get_teacher_answers_unauthorized():
    headers = {
        "X-User-Id": str(uuid4()),
        "X-User-Role": "student",
        "X-User-Faculty-Id": "engineering"
    }

    response = client.get("/teacher/answers", headers=headers)
    assert response.status_code == 403

def test_teacher_verify_success():
    teacher_id = str(uuid4())
    log_id = uuid4()
    headers = {
        "X-User-Id": teacher_id,
        "X-User-Role": "teacher",
        "X-User-Faculty-Id": "engineering"
    }
    payload = {
        "verified": True,
        "comment": "Well explained.",
        "custom_tags": ["helpful", "accurate"]
    }

    with patch("api.chat.get_db"), \
         patch("repository.chat_repository.verify_answer_by_teacher") as mock_verify, \
         patch("api.chat.log_audit"):
        mock_verify.return_value = True
        response = client.post(f"/teacher/verify/{log_id}", json=payload, headers=headers)

    assert response.status_code == 200
    assert response.json() == {"status": "success"}
    mock_verify.assert_called_once_with(ANY, log_id, True, "Well explained.", ["helpful", "accurate"])

def test_get_teacher_performance_success():
    teacher_id = str(uuid4())
    faculty_id = "engineering"
    headers = {
        "X-User-Id": teacher_id,
        "X-User-Role": "teacher",
        "X-User-Faculty-Id": faculty_id
    }

    mock_stats = {
        "avg_confidence": 0.88,
        "total_answers": 100,
        "positive_feedback_rate": 0.92
    }

    with patch("api.chat.get_db"), \
         patch("repository.chat_repository.get_performance_stats") as mock_stats_repo:
        mock_stats_repo.return_value = mock_stats
        response = client.get("/teacher/performance", headers=headers)

    assert response.status_code == 200
    assert response.json()["total_answers"] == 100
    mock_stats_repo.assert_called_once_with(ANY, faculty_id=faculty_id)
