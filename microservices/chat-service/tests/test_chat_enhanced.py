import pytest
from unittest.mock import patch, MagicMock
from uuid import uuid4
from fastapi.testclient import TestClient

# Mock DB and other global side effects before importing app
with patch("sqlalchemy.create_engine"), \
     patch("sqlalchemy.orm.sessionmaker"), \
     patch("db.base.Base.metadata.create_all"), \
     patch("redis.asyncio.from_url"), \
     patch("fastapi_limiter.FastAPILimiter.init"):
    from main import app

client = TestClient(app)

@pytest.fixture
def mock_rag_search():
    with patch("services.chat_service.call_rag_search") as mock:
        mock.return_value = [
            {
                "text": "Numerical Analysis is a branch of mathematics.",
                "score": 0.9,
                "source": "math_book.pdf",
                "page": 23,
                "book_id": "book123"
            }
        ]
        yield mock

@pytest.fixture
def mock_llm_service():
    with patch("services.chat_service.llm_service") as mock:
        mock.detect_intent_and_rewrite_query.return_value = {
            "intent": "DEFINITION",
            "mode": "UNDERSTANDING",
            "rewritten_query": "What is Numerical Analysis?"
        }
        mock.get_cached_rag_results.return_value = None
        mock.get_cached_response.return_value = None
        mock.get_chat_completion_with_validation.return_value = {
            "answer": "التعريف: التحليل العددي هو فرع من الرياضيات...\nالشرح: ...\nمثال: ...\nملخص: ...",
            "source": {"book": "math_book.pdf", "page": 23},
            "hallucination": False
        }
        yield mock

def test_chat_returns_source(mock_rag_search, mock_llm_service):
    headers = {
        "X-User-Id": str(uuid4()),
        "X-Faculty-Id": "engineering",
        "X-Semester-Id": "1"
    }
    # Mock JWT payload
    mock_user = {
        "sub": headers["X-User-Id"],
        "role": "student",
        "faculty": "engineering",
        "semester": "1"
    }
    payload = {
        "message": "What is Numerical Analysis?",
        "collection_name": "test_collection"
    }

    # We need to mock DB session too
    with patch("api.chat.get_db"), patch("api.chat.chat_repository"), patch("services.chat_service.chat_repository"):
        response = client.post("/chat", json=payload, headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "source" in data
    assert data["source"]["book"] == "math_book.pdf"
    assert data["source"]["page"] == 23
    assert "audit_log_id" in data

def test_hallucination_blocked(mock_rag_search, mock_llm_service):
    # Mock hallucination detected
    mock_llm_service.get_chat_completion_with_validation.return_value = {
        "answer": "Answer not found in official curriculum",
        "source": {"book": "System", "page": "N/A"},
        "hallucination": True
    }

    headers = {
        "X-User-Id": str(uuid4()),
        "X-Faculty-Id": "engineering",
        "X-Semester-Id": "1"
    }
    payload = {
        "message": "Something not in the book",
        "collection_name": "test_collection"
    }

    with patch("api.chat.get_db"), patch("api.chat.chat_repository"), patch("services.chat_service.log_audit"):
        response = client.post("/chat", json=payload, headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert "خارج نطاق المحتوى المقرر" in data["answer"]
