from unittest.mock import patch, MagicMock

@patch('google.cloud.firestore.Client', return_value=MagicMock())
@patch('app.services.chat_service.generate_response', return_value="This is a test response.")
def test_chat_with_book(mock_generate_response, mock_firestore_client, client):
    # Get a book from the test data
    faculty_id = client.get("/api/faculties/").json()[0]["id"]
    department_id = client.get(f"/api/departments/{faculty_id}").json()[0]["id"]
    semester_id = client.get(f"/api/semesters/{department_id}").json()[0]["id"]
    book_id = client.get(f"/api/books/{semester_id}").json()[0]["id"]

    response = client.post(
        "/api/chat/ask",
        json={"book_id": book_id, "question": "What is the capital of France?"},
        headers={"Authorization": "Bearer student_token"}
    )
    assert response.status_code == 200
    assert response.json()["answer"] == "This is a test response."
