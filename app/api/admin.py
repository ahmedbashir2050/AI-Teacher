from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from app.services import academic_service, book_processing_service
from app.schemas import academic as schemas
from app.api.dependencies import get_db
from app.core.security import get_current_admin_user
from app.models.user import User

router = APIRouter()

@router.post("/upload-book/", response_model=schemas.Book)
async def upload_book(
    title: str,
    language: str,
    course_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Upload a book, process it, and store it. Admin access required.
    """
    # Create the book record in the database
    book_create = schemas.BookCreate(title=title, language=language, course_id=course_id)
    db_book = academic_service.create_book(db=db, book=book_create, user_id=current_user.id)

    # Read the file content
    file_content = await file.read()

    # Process and store the book content in the vector database
    book_processing_service.process_and_store_book(book_id=db_book.id, file_content=file_content)

    return db_book
