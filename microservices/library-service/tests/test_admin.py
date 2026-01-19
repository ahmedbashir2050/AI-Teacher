import pytest
from fastapi.testclient import TestClient
import uuid
from unittest.mock import patch, MagicMock
import sys
import os

# Ensure the app can be imported
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from main import app

client = TestClient(app)

@pytest.fixture
def admin_headers():
    return {
        "X-User-Id": str(uuid.uuid4()),
        "X-User-Role": "admin",
        "X-Request-ID": "test-request-id",
    }

@pytest.fixture
def student_headers():
    return {
        "X-User-Id": str(uuid.uuid4()),
        "X-User-Role": "student",
        "X-Request-ID": "test-request-id",
    }

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

@patch("repository.book_repository.BookRepository.create_faculty")
def test_create_faculty(mock_create, admin_headers):
    # Use a dict or a serializable object
    mock_create.return_value = {"id": str(uuid.uuid4()), "name": "Engineering"}
    response = client.post(
        "/admin/faculties", json={"name": "Engineering"}, headers=admin_headers
    )
    assert response.status_code == 200, response.text
    assert response.json()["name"] == "Engineering"

def test_upload_book_validation(admin_headers):
    # Test invalid file type
    response = client.post(
        "/admin/books",
        data={
            "title": "Test Book",
            "faculty_id": str(uuid.uuid4()),
            "department_id": str(uuid.uuid4()),
            "semester": 1,
        },
        files={"file": ("test.txt", b"content", "text/plain")},
        headers=admin_headers,
    )
    assert response.status_code == 400
    assert "Only PDF files are allowed" in response.json()["detail"]

@patch("repository.book_repository.BookRepository.get_book_by_id")
@patch("api.books.get_user_profile")
@patch("services.storage_service.storage_service.generate_presigned_url")
def test_download_book_eligibility(mock_url, mock_profile, mock_book, student_headers):
    # Mock book
    book_id = uuid.uuid4()
    faculty_id = uuid.uuid4()
    dept_id = uuid.uuid4()

    book_mock = MagicMock()
    book_mock.id = book_id
    book_mock.faculty_id = faculty_id
    book_mock.department_id = dept_id
    book_mock.semester = 1
    book_mock.file_key = "path/to/book.pdf"
    book_mock.title = "Test Book"
    mock_book.return_value = book_mock

    # Mock user profile (mismatching)
    mock_profile.return_value = {
        "faculty": "Science",
        "major": "Biology",
        "semester": 1
    }

    # Mock repository for names
    with patch("repository.book_repository.BookRepository.get_faculty_by_id") as mock_fac, \
         patch("repository.book_repository.BookRepository.get_department_by_id") as mock_dept:

        fac_mock = MagicMock()
        fac_mock.name = "Engineering"
        mock_fac.return_value = fac_mock

        dept_mock = MagicMock()
        dept_mock.name = "CS"
        mock_dept.return_value = dept_mock

        response = client.get(f"/books/{book_id}/download", headers=student_headers)
        assert response.status_code == 403, response.text
        assert "not eligible" in response.json()["detail"]

        # Mock user profile (matching)
        mock_profile.return_value = {
            "faculty": "Engineering",
            "major": "CS",
            "semester": 1
        }
        mock_url.return_value = "https://s3.com/signed-url"

        response = client.get(f"/books/{book_id}/download", headers=student_headers)
        assert response.status_code == 200, response.text
        assert response.json()["download_url"] == "https://s3.com/signed-url"

@patch("repository.book_repository.BookRepository.get_book_by_hash")
@patch("repository.book_repository.BookRepository.get_faculty_by_id")
@patch("repository.book_repository.BookRepository.get_department_by_id")
@patch("services.storage_service.storage_service.upload_file")
@patch("repository.book_repository.BookRepository.create_book")
@patch("core.celery_app.celery_app.send_task")
def test_upload_book_success(mock_send_task, mock_create_book, mock_upload, mock_dept, mock_fac, mock_hash, admin_headers):
    mock_hash.return_value = None

    fac_id = uuid.uuid4()
    dept_id = uuid.uuid4()
    user_id = admin_headers["X-User-Id"]

    fac_mock = MagicMock()
    fac_mock.name = "Engineering"
    mock_fac.return_value = fac_mock

    dept_mock = MagicMock()
    dept_mock.name = "CS"
    dept_mock.faculty_id = fac_id
    mock_dept.return_value = dept_mock

    mock_upload.return_value = True

    book_id = uuid.uuid4()

    # Create a dict that matches BookResponse Pydantic model
    created_book_data = {
        "id": book_id,
        "title": "Test PDF",
        "faculty_id": fac_id,
        "department_id": dept_id,
        "semester": 1,
        "language": "ar",
        "file_key": "books/Engineering/CS/1/uuid.pdf",
        "uploaded_by": uuid.UUID(user_id),
        "is_active": True
    }

    # Use a MagicMock that behaves like the object with attributes
    mock_book_obj = MagicMock()
    for k, v in created_book_data.items():
        setattr(mock_book_obj, k, v)

    mock_create_book.return_value = mock_book_obj

    response = client.post(
        "/admin/books",
        data={
            "title": "Test PDF",
            "faculty_id": str(fac_id),
            "department_id": str(dept_id),
            "semester": 1,
        },
        files={"file": ("test.pdf", b"%PDF-1.4 content", "application/pdf")},
        headers=admin_headers,
    )

    assert response.status_code == 200, response.text
    assert mock_upload.called
    assert mock_create_book.called
    assert mock_send_task.called

    # Verify RAG task arguments
    c_args, c_kwargs = mock_send_task.call_args
    assert c_args[0] == "tasks.ingest_document_task"
    assert c_kwargs["args"] == ["library_books", str(fac_id), str(dept_id), 1, str(book_id)]
    assert c_kwargs["kwargs"]["file_key"].startswith("books/Engineering/CS/1/")
