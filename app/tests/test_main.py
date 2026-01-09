import sys
import os
from fastapi.testclient import TestClient

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from app.main import app

client = TestClient(app)

def test_read_root():
    """
    Tests the root endpoint to ensure the application is running.
    """
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "message": "Welcome to the AI Teacher API!"}

def test_chat_endpoint_no_content():
    """
    Tests the chat endpoint's behavior when no relevant content is found.
    It should return the mandatory Arabic phrase.
    """
    # This test assumes an empty database or a query that finds no matches.
    # We mock the retriever to simulate this scenario.
    from unittest.mock import patch
    with patch('app.api.chat.retrieve_relevant_chunks', return_value=[]):
        response = client.post("/api/chat", json={"question": "some obscure question"})
        assert response.status_code == 200
        assert response.json() == {"answer": "هذا السؤال خارج المقرر"}
