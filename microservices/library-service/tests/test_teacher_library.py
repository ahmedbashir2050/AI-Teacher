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
def teacher_headers():
    return {
        "X-User-Id": str(uuid.uuid4()),
        "X-User-Role": "teacher",
        "X-User-Faculty-Id": str(uuid.uuid4()),
        "X-Request-ID": "test-request-id",
    }

@patch("repository.book_repository.BookRepository.get_book_by_hash")
@patch("repository.book_repository.BookRepository.get_faculty_by_id")
@patch("repository.book_repository.BookRepository.get_department_by_id")
@patch("services.storage_service.storage_service.upload_file")
@patch("repository.book_repository.BookRepository.create_book")
@patch("core.celery_app.celery_app.send_task")
def test_teacher_upload_book_success(mock_send_task, mock_create_book, mock_upload, mock_dept, mock_fac, mock_hash, teacher_headers):
    mock_hash.return_value = None
    fac_id = uuid.UUID(teacher_headers["X-User-Faculty-Id"])
    dept_id = uuid.uuid4()

    fac_mock = MagicMock()
    fac_mock.id = fac_id
    fac_mock.name = "Engineering"
    mock_fac.return_value = fac_mock

    dept_mock = MagicMock()
    dept_mock.id = dept_id
    dept_mock.name = "CS"
    dept_mock.faculty_id = fac_id
    mock_dept.return_value = dept_mock

    mock_upload.return_value = True

    mock_book_obj = MagicMock()
    mock_book_obj.id = uuid.uuid4()
    mock_book_obj.title = "Test PDF"
    mock_book_obj.faculty_id = fac_id
    mock_book_obj.department_id = dept_id
    mock_book_obj.semester = 1
    mock_book_obj.language = "ar"
    mock_book_obj.file_key = "books/Engineering/CS/1/uuid.pdf"
    mock_book_obj.uploaded_by = uuid.UUID(teacher_headers["X-User-Id"])
    mock_book_obj.is_active = True
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
        headers=teacher_headers,
    )

    assert response.status_code == 200
    assert mock_upload.called

def test_teacher_upload_book_wrong_faculty(teacher_headers):
    other_fac_id = str(uuid.uuid4())
    response = client.post(
        "/admin/books",
        data={
            "title": "Test PDF",
            "faculty_id": other_fac_id,
            "department_id": str(uuid.uuid4()),
            "semester": 1,
        },
        files={"file": ("test.pdf", b"%PDF-1.4 content", "application/pdf")},
        headers=teacher_headers,
    )
    assert response.status_code == 403
    assert "Teachers can only upload to their own faculty" in response.json()["detail"]

@patch("repository.book_repository.BookRepository.list_books")
def test_teacher_list_books_restricted(mock_list, teacher_headers):
    mock_list.return_value = []
    fac_id = uuid.UUID(teacher_headers["X-User-Faculty-Id"])

    response = client.get("/admin/books", headers=teacher_headers)

    assert response.status_code == 200
    mock_list.assert_called_once()
    # Check that faculty_id was passed correctly to the repo
    args, kwargs = mock_list.call_args
    assert kwargs["faculty_id"] == fac_id
