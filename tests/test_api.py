import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

# Correctly import the app from the 'src' directory
from app.main import app

client = TestClient(app)

# ===================================
# Mocks for External Services
# ===================================

@pytest.fixture
def mock_llm_service():
    """Mocks the LLM service where it is imported in the API modules."""
    llm_mock = MagicMock()
    with patch('app.api.chat.llm_service', llm_mock), \
         patch('app.api.summarize.llm_service', llm_mock), \
         patch('app.api.flashcards.llm_service', llm_mock), \
         patch('app.api.exam.llm_service', llm_mock):
        yield llm_mock

@pytest.fixture
def mock_retriever():
    """Mocks the retrieve_relevant_chunks function used in various API modules."""
    # We need to patch the retriever where it's looked up, which is in the API modules.
    # To be safe, we'll patch it in all modules that use it.
    with patch('app.api.chat.retrieve_relevant_chunks') as mock_chat, \
         patch('app.api.summarize.retrieve_relevant_chunks') as mock_summarize, \
         patch('app.api.flashcards.retrieve_relevant_chunks') as mock_flashcards, \
         patch('app.api.exam.retrieve_relevant_chunks') as mock_exam:
        # Yield a single mock that can be configured for all
        mock_chat.return_value = ["Mocked chunk"]
        mock_summarize.return_value = ["Mocked chunk"]
        mock_flashcards.return_value = ["Mocked chunk"]
        mock_exam.return_value = ["Mocked chunk"]
        yield {
            "chat": mock_chat,
            "summarize": mock_summarize,
            "flashcards": mock_flashcards,
            "exam": mock_exam
        }


# ===================================
# Test for Root Endpoint (Health Check)
# ===================================
def test_read_root():
    """Tests the root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "message": "Welcome to the AI Teacher API!"}

# ===================================
# Tests for /api/chat
# ===================================

def test_chat_successful_response(mock_retriever, mock_llm_service):
    """Tests a successful chat interaction."""
    mock_llm_service.get_chat_completion.return_value = "The answer is about economics."

    response = client.post("/api/chat", json={"question": "What is economics?"})

    assert response.status_code == 200
    assert response.json() == {"answer": "The answer is about economics."}
    mock_retriever["chat"].assert_called_once_with("What is economics?")

def test_chat_no_context_found(mock_retriever):
    """Tests the case where no relevant chunks are found."""
    mock_retriever["chat"].return_value = []
    response = client.post("/api/chat", json={"question": "An obscure question."})
    assert response.status_code == 200
    assert response.json() == {"answer": "هذا السؤال خارج المقرر"}

# ===================================
# Tests for /api/summarize
# ===================================

def test_summarize_successful_response(mock_retriever, mock_llm_service):
    """Tests a successful summary generation."""
    mock_llm_service.get_chat_completion.return_value = "This is a summary."
    response = client.post("/api/summarize", json={"chapter": "Chapter 1", "style": "simple"})
    assert response.status_code == 200
    assert response.json() == {"summary": "This is a summary."}

# ===================================
# Tests for /api/flashcards
# ===================================

def test_flashcards_successful_generation(mock_retriever, mock_llm_service):
    """Tests successful flashcard generation."""
    mock_llm_service.get_chat_completion.return_value = '[{"question": "Q1", "answer": "A1"}]'
    response = client.post("/api/flashcards", json={"chapter": "History", "count": 1})
    assert response.status_code == 200
    assert response.json()["flashcards"][0]["question"] == "Q1"

def test_flashcards_malformed_json_response(mock_retriever, mock_llm_service):
    """Tests handling of malformed JSON from the LLM."""
    mock_llm_service.get_chat_completion.return_value = "Not JSON"
    response = client.post("/api/flashcards", json={"chapter": "History", "count": 2})
    assert response.status_code == 500

# ===================================
# Tests for /api/exam
# ===================================

def test_exam_successful_generation(mock_retriever, mock_llm_service):
    """Tests successful exam generation."""
    mock_llm_service.get_chat_completion.return_value = '''
    {"questions": [{"question_type": "mcq", "question": "Q1", "options": ["1", "2"], "correct_answer": "2"}]}
    '''
    response = client.post("/api/exam", json={"chapter": "Math", "mcq": 1, "theory": 0})
    assert response.status_code == 200
    assert response.json()["exam_title"] == "Final Exam: Math"
    assert len(response.json()["questions"]) == 1

def test_exam_llm_api_error(mock_retriever, mock_llm_service):
    """Tests handling of an LLM API error."""
    from openai import APIError
    mock_llm_service.get_chat_completion.side_effect = APIError(message="API Error", request=MagicMock(), body=None)
    response = client.post("/api/exam", json={"chapter": "Math", "mcq": 1, "theory": 0})
    assert response.status_code == 502
