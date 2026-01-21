import hashlib
import time
import uuid
from typing import List, Optional
from uuid import UUID

from core.audit import log_audit
from core.cache import cache_result
from core.celery_app import celery_app
from core.metrics import BOOK_UPLOAD_LATENCY, RAG_INGESTION_TRIGGER_COUNT
from db.session import get_db, get_read_db
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, Request
from pydantic import BaseModel
from repository.book_repository import BookRepository
from services.storage_service import storage_service
from sqlalchemy.orm import Session

router = APIRouter()


class BookResponse(BaseModel):
    id: UUID
    title: str
    faculty_id: UUID
    department_id: UUID
    semester: int
    language: str
    file_key: str
    uploaded_by: UUID
    is_active: bool
    is_approved: bool
    approved_by: Optional[UUID]

    class Config:
        from_attributes = True


def get_current_staff(request: Request):
    user_id = request.headers.get("X-User-Id")
    role = request.headers.get("X-User-Role")
    faculty_id = request.headers.get("X-User-Faculty-Id")
    if not user_id or role not in ["admin", "super_admin", "teacher"]:
        raise HTTPException(status_code=403, detail="Forbidden: Staff access required")
    return {"user_id": user_id, "role": role, "faculty_id": faculty_id}


@router.post("/books", response_model=BookResponse)
async def upload_book(
    request: Request,
    title: str = Form(...),
    faculty_id: UUID = Form(...),
    department_id: UUID = Form(...),
    semester: int = Form(...),
    language: str = Form("ar"),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    staff: dict = Depends(get_current_staff),
):
    user_id = staff["user_id"]
    repo = BookRepository(db)

    # Teacher Restriction: Can only upload to their faculty
    if staff["role"] == "teacher":
        if not staff["faculty_id"] or str(staff["faculty_id"]) != str(faculty_id):
            raise HTTPException(
                status_code=403, detail="Teachers can only upload to their own faculty"
            )

    start_time = time.time()
    # Validation: File type
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    # Read file content for hash and upload
    content = await file.read()

    # Validation: File size (50MB limit)
    if len(content) > 50 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large (max 50MB)")

    file_hash = hashlib.sha256(content).hexdigest()

    # Check for duplicates
    existing_book = repo.get_book_by_hash(file_hash)
    if existing_book:
        raise HTTPException(status_code=409, detail="Book already exists")

    # Verify Faculty and Department exist
    faculty = repo.get_faculty_by_id(faculty_id)
    if not faculty:
        raise HTTPException(status_code=404, detail="Faculty not found")

    dept = repo.get_department_by_id(department_id)
    if not dept or dept.faculty_id != faculty_id:
        raise HTTPException(
            status_code=404, detail="Department not found in this faculty"
        )

    book_id = uuid.uuid4()
    # Path: books/{faculty}/{department}/{semester}/{book_id}.pdf
    file_key = f"books/{faculty.name}/{dept.name}/{semester}/{book_id}.pdf"

    # Upload to S3
    success = await storage_service.upload_file(content, file_key)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to upload file to storage")

    book_data = {
        "id": book_id,
        "title": title,
        "faculty_id": faculty_id,
        "department_id": department_id,
        "semester": semester,
        "language": language,
        "file_key": file_key,
        "file_hash": file_hash,
        "uploaded_by": user_id,
    }

    new_book = repo.create_book(book_data)

    BOOK_UPLOAD_LATENCY.observe(time.time() - start_time)

    log_audit(
        user_id=user_id,
        action="BOOK_UPLOADED",
        resource="book",
        resource_id=str(new_book.id),
        metadata={"title": title, "file_key": file_key},
        request_id=getattr(request.state, "request_id", None),
    )

    # Trigger RAG ingestion
    RAG_INGESTION_TRIGGER_COUNT.inc()
    celery_app.send_task(
        "tasks.ingest_document_task",
        args=[
            "library_books",  # collection_name
            str(new_book.faculty_id),
            str(new_book.department_id),
            new_book.semester,
            str(new_book.id),
        ],
        kwargs={"file_key": file_key, "filename": file.filename},
    )

    return new_book


@router.put("/books/{book_id}", response_model=BookResponse)
async def update_book(
    request: Request,
    book_id: UUID,
    title: Optional[str] = None,
    semester: Optional[int] = None,
    language: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    staff: dict = Depends(get_current_staff),
):
    user_id = staff["user_id"]
    repo = BookRepository(db)

    # Teacher Restriction
    if staff["role"] == "teacher":
        book = repo.get_book_by_id(book_id)
        if (
            not book
            or not staff["faculty_id"]
            or str(book.faculty_id) != str(staff["faculty_id"])
        ):
            raise HTTPException(
                status_code=403, detail="Teachers can only update their own faculty books"
            )

    update_data = {}
    if title is not None:
        update_data["title"] = title
    if semester is not None:
        update_data["semester"] = semester
    if language is not None:
        update_data["language"] = language
    if is_active is not None:
        update_data["is_active"] = is_active

    updated_book = repo.update_book(book_id, update_data)
    if not updated_book:
        raise HTTPException(status_code=404, detail="Book not found")

    log_audit(
        user_id=user_id,
        action="BOOK_UPDATED",
        resource="book",
        resource_id=str(book_id),
        metadata=update_data,
        request_id=getattr(request.state, "request_id", None),
    )

    return updated_book


@router.delete("/books/{book_id}")
async def delete_book(
    request: Request,
    book_id: UUID,
    db: Session = Depends(get_db),
    staff: dict = Depends(get_current_staff),
):
    user_id = staff["user_id"]
    repo = BookRepository(db)

    # Teacher Restriction
    if staff["role"] == "teacher":
        book = repo.get_book_by_id(book_id)
        if (
            not book
            or not staff["faculty_id"]
            or str(book.faculty_id) != str(staff["faculty_id"])
        ):
            raise HTTPException(
                status_code=403, detail="Teachers can only delete their own faculty books"
            )

    success = repo.soft_delete_book(book_id)
    if not success:
        raise HTTPException(status_code=404, detail="Book not found")

    log_audit(
        user_id=user_id,
        action="BOOK_DELETED",
        resource="book",
        resource_id=str(book_id),
        request_id=getattr(request.state, "request_id", None),
    )

    return {"message": "Book deleted successfully"}


@router.get("/books", response_model=List[BookResponse])
@cache_result(ttl=300)
async def list_books(
    faculty_id: Optional[UUID] = Query(None),
    department_id: Optional[UUID] = Query(None),
    semester: Optional[int] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_read_db),
    staff: dict = Depends(get_current_staff),
):
    repo = BookRepository(db)

    # Teacher Restriction
    if staff["role"] == "teacher":
        if not staff["faculty_id"]:
            return []
        faculty_id = UUID(staff["faculty_id"])

    return repo.list_books(
        faculty_id=faculty_id,
        department_id=department_id,
        semester=semester,
        skip=skip,
        limit=limit,
    )


class FacultyCreate(BaseModel):
    name: str


@router.post("/faculties")
async def create_faculty(
    request: Request,
    data: FacultyCreate,
    db: Session = Depends(get_db),
    staff: dict = Depends(get_current_staff),
):
    if staff["role"] == "teacher":
        raise HTTPException(status_code=403, detail="Teachers cannot create faculties")
    repo = BookRepository(db)
    new_faculty = repo.create_faculty(name=data.name)

    log_audit(
        user_id=staff["user_id"],
        action="FACULTY_CREATED",
        resource="faculty",
        resource_id=str(new_faculty.id),
        metadata={"name": data.name},
        request_id=getattr(request.state, "request_id", None),
    )
    return new_faculty


class DepartmentCreate(BaseModel):
    name: str
    faculty_id: UUID


@router.post("/departments")
async def create_department(
    request: Request,
    data: DepartmentCreate,
    db: Session = Depends(get_db),
    staff: dict = Depends(get_current_staff),
):
    if staff["role"] == "teacher":
        raise HTTPException(
            status_code=403, detail="Teachers cannot create departments"
        )
    repo = BookRepository(db)
    new_dept = repo.create_department(name=data.name, faculty_id=data.faculty_id)

    log_audit(
        user_id=staff["user_id"],
        action="DEPARTMENT_CREATED",
        resource="department",
        resource_id=str(new_dept.id),
        metadata={"name": data.name, "faculty_id": str(data.faculty_id)},
        request_id=getattr(request.state, "request_id", None),
    )
    return new_dept


class ApprovalRequest(BaseModel):
    approved: bool


@router.post("/curriculum/{curriculum_id}/approve", response_model=BookResponse)
async def approve_curriculum(
    request: Request,
    curriculum_id: UUID,
    approval: ApprovalRequest,
    db: Session = Depends(get_db),
    staff: dict = Depends(get_current_staff),
):
    user_id = staff["user_id"]
    repo = BookRepository(db)

    book = repo.get_book_by_id(curriculum_id)
    if not book:
        raise HTTPException(status_code=404, detail="Curriculum not found")

    # Teacher Restriction: Can only approve their faculty's curriculum
    if staff["role"] == "teacher":
        if (
            not staff["faculty_id"]
            or str(book.faculty_id) != str(staff["faculty_id"])
        ):
            raise HTTPException(
                status_code=403, detail="Teachers can only approve their own faculty curriculum"
            )

    update_data = {
        "is_approved": approval.approved,
        "approved_by": user_id if approval.approved else None
    }

    updated_book = repo.update_book(curriculum_id, update_data)

    log_audit(
        user_id=user_id,
        action="CURRICULUM_APPROVED" if approval.approved else "CURRICULUM_REJECTED",
        resource="book",
        resource_id=str(curriculum_id),
        metadata={"approved": approval.approved},
        request_id=getattr(request.state, "request_id", None),
    )

    return updated_book
