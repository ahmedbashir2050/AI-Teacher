import pytest
from uuid import uuid4
from fastapi.testclient import TestClient
from main import app
from db.session import get_db
from models.library import Book, Faculty, Department, StudentSelectedBook, ActionEnum
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.base import Base

# Setup test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_api_v_final.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

def test_available_books(mocker):
    # Mock user profile
    student_id = uuid4()
    faculty_id = uuid4()
    dept_id = uuid4()

    mocker.patch("api.books.get_user_profile", return_value={
        "faculty": "Engineering",
        "department_id": str(dept_id),
        "semester": "3"
    })

    db = TestingSessionLocal()
    faculty = Faculty(id=faculty_id, name="Engineering")
    dept = Department(id=dept_id, name="CS", faculty_id=faculty_id)
    book = Book(
        id=uuid4(),
        title="Software Engineering",
        faculty_id=faculty_id,
        department_id=dept_id,
        semester=3,
        language="ar",
        file_key="se.pdf",
        file_hash="hash1",
        uploaded_by=uuid4(),
        is_active=True
    )
    db.add(faculty)
    db.add(dept)
    db.add(book)
    db.commit()

    headers = {"X-User-Id": str(student_id)}
    response = client.get(f"/student/{student_id}/available-books", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Software Engineering"
    assert data[0]["is_selected"] is True # Mandatory
    assert data[0]["is_mandatory"] is True

def test_add_remove_book(mocker):
    student_id = uuid4()
    faculty_id = uuid4()
    dept_id = uuid4()
    book_id = uuid4()

    mocker.patch("api.books.get_user_profile", return_value={
        "faculty": "Engineering",
        "department_id": str(dept_id),
        "semester": "3"
    })

    db = TestingSessionLocal()
    faculty = Faculty(id=faculty_id, name="Engineering")
    dept = Department(id=dept_id, name="CS", faculty_id=faculty_id)
    book = Book(
        id=book_id,
        title="Advanced Math",
        faculty_id=faculty_id,
        department_id=dept_id,
        semester=1, # Different semester
        language="ar",
        file_key="math.pdf",
        file_hash="hash2",
        uploaded_by=uuid4(),
        is_active=True
    )
    db.add(faculty)
    db.add(dept)
    db.add(book)
    db.commit()

    headers = {"X-User-Id": str(student_id)}

    # Add book
    response = client.post(
        f"/student/{student_id}/add-book",
        json={"book_id": str(book_id), "source_semester": 1},
        headers=headers
    )
    assert response.status_code == 200

    # Check selection status
    response = client.get(f"/student/{student_id}/available-books", headers=headers)
    data = response.json()
    assert any(b["id"] == str(book_id) and b["is_selected"] is True for b in data)

    # Remove book
    response = client.post(
        f"/student/{student_id}/remove-book",
        json={"book_id": str(book_id)},
        headers=headers
    )
    assert response.status_code == 200

def test_semester_lock(mocker):
    student_id = uuid4()
    faculty_id = uuid4()
    dept_id = uuid4()
    book_id = uuid4()

    db = TestingSessionLocal()
    faculty = Faculty(id=faculty_id, name="Engineering")
    dept = Department(id=dept_id, name="CS", faculty_id=faculty_id)
    book = Book(
        id=book_id,
        title="Old Book",
        faculty_id=faculty_id,
        department_id=dept_id,
        semester=1,
        language="ar",
        file_key="old.pdf",
        file_hash="hash_old",
        uploaded_by=uuid4(),
        is_active=True
    )
    db.add(faculty)
    db.add(dept)
    db.add(book)

    # Add selection in Semester 2
    selection = StudentSelectedBook(
        student_id=student_id,
        book_id=book_id,
        semester=2,
        source_semester=1,
        action=ActionEnum.ADD
    )
    db.add(selection)
    db.commit()

    # Now student is in Semester 3
    mocker.patch("api.books.get_user_profile", return_value={
        "faculty": "Engineering",
        "department_id": str(dept_id),
        "semester": "3"
    })

    headers = {"X-User-Id": str(student_id)}

    # Try to remove selection made in Semester 2
    response = client.post(
        f"/student/{student_id}/remove-book",
        json={"book_id": str(book_id)},
        headers=headers
    )
    assert response.status_code == 400
    assert "Cannot modify selections from previous semesters" in response.json()["detail"]

def test_cannot_remove_mandatory(mocker):
    student_id = uuid4()
    faculty_id = uuid4()
    dept_id = uuid4()
    book_id = uuid4()

    db = TestingSessionLocal()
    faculty = Faculty(id=faculty_id, name="Engineering")
    dept = Department(id=dept_id, name="CS", faculty_id=faculty_id)
    book = Book(
        id=book_id,
        title="Current Mandatory Book",
        faculty_id=faculty_id,
        department_id=dept_id,
        semester=3, # Matches student semester
        language="ar",
        file_key="man.pdf",
        file_hash="hash_man",
        uploaded_by=uuid4(),
        is_active=True
    )
    db.add(faculty)
    db.add(dept)
    db.add(book)
    db.commit()

    mocker.patch("api.books.get_user_profile", return_value={
        "faculty": "Engineering",
        "department_id": str(dept_id),
        "semester": "3"
    })

    headers = {"X-User-Id": str(student_id)}

    response = client.post(
        f"/student/{student_id}/remove-book",
        json={"book_id": str(book_id)},
        headers=headers
    )
    assert response.status_code == 400
    assert "Cannot remove mandatory books" in response.json()["detail"]
