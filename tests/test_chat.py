from unittest.mock import patch

@patch('app.services.chat_service.generate_response', return_value="This is a test response.")
def test_chat_with_book(mock_generate_response, client):
    response = client.post(
        "/api/chat/",
        json={"book_id": 1, "question": "What is the capital of France?"},
        headers={"Authorization": "Bearer student_token"}
    )
    assert response.status_code == 200
    assert response.json()["message"] == "This is a test response."
