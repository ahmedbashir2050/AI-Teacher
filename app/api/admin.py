from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from app.services import academic_service, book_processing_service
from app.schemas import academic as schemas
from app.api.dependencies import get_db
from app.core.security import get_current_user
from app.models.user import User
import uuid

router = APIRouter()

def get_current_admin_or_academic_user(current_user: User = Depends(get_current_user)):
    if current_user.role not in ["admin", "academic"]:
        raise HTTPException(status_code=403, detail="The user doesn't have enough privileges")
    return current_user

@router.post("/upload-book/", response_model=schemas.Book)
async def upload_book(
    title: str,
    language: str,
    semester_id: uuid.UUID,
    faculty_id: uuid.UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_or_academic_user)
):
    """
    Upload a book, process it, and store it. Admin or Academic access required.
    """
    # Generate a new UUID for the book
    book_id = uuid.uuid4()

    # Read the file content
    file_content = await file.read()

    # Process and store the book content in the vector database
    collection_name = book_processing_service.process_and_store_book(
        book_id=book_id,
        faculty_id=faculty_id,
        semester_id=semester_id,
        file_content=file_content
    )

    # Create the book record in the database
    book_create = schemas.BookCreate(title=title, language=language, semester_id=semester_id)
    db_book = academic_service.create_book(db=db, book=book_create, qdrant_collection=collection_name, book_id=book_id)

    return db_book
