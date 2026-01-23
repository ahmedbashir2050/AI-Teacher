import logging
from uuid import UUID
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Header, Request
from sqlalchemy.orm import Session

from db.session import get_db
from repository.book_repository import BookRepository
from models.library import Book, ActionEnum
from core.config import settings
from core.audit import log_audit
from services.student_book_service import StudentBookService

router = APIRouter()
logger = logging.getLogger(__name__)

async def get_student_context(user_id: str):
    """Fetch student context from user-service"""
    from api.books import get_user_profile
    profile = await get_user_profile(user_id)
    if not profile:
        raise HTTPException(status_code=500, detail="Could not verify student academic context")
    return profile

@router.get("/{student_id}/available-books")
async def get_available_books(
    request: Request,
    student_id: UUID,
    db: Session = Depends(get_db),
    x_user_id: str = Header(...),
):
    if str(student_id) != x_user_id:
        raise HTTPException(status_code=403, detail="Unauthorized")

    profile = await get_student_context(x_user_id)
    service = StudentBookService(db)

    books = await service.get_available_books(student_id, profile)

    log_audit(
        user_id=x_user_id,
        action="AVAILABLE_BOOKS_FETCHED",
        resource="student_books",
        metadata={"student_id": str(student_id), "semester": profile.get("semester")},
        request_id=getattr(request.state, "request_id", None)
    )

    return books

@router.post("/{student_id}/add-book")
async def add_book(
    request: Request,
    student_id: UUID,
    payload: dict, # { book_id, source_semester }
    db: Session = Depends(get_db),
    x_user_id: str = Header(...)
):
    if str(student_id) != x_user_id:
        raise HTTPException(status_code=403, detail="Unauthorized")

    book_id = UUID(payload.get("book_id"))
    source_semester = payload.get("source_semester")

    profile = await get_student_context(x_user_id)
    service = StudentBookService(db)

    return await service.add_book_selection(
        student_id,
        book_id,
        source_semester,
        profile,
        request_id=getattr(request.state, "request_id", None)
    )

@router.post("/{student_id}/remove-book")
async def remove_book(
    request: Request,
    student_id: UUID,
    payload: dict, # { book_id }
    db: Session = Depends(get_db),
    x_user_id: str = Header(...)
):
    if str(student_id) != x_user_id:
        raise HTTPException(status_code=403, detail="Unauthorized")

    book_id = UUID(payload.get("book_id"))

    profile = await get_student_context(x_user_id)
    service = StudentBookService(db)

    return await service.remove_book_selection(
        student_id,
        book_id,
        profile,
        request_id=getattr(request.state, "request_id", None)
    )

@router.post("/internal/student/{student_id}/reset")
async def reset_student_selections(
    student_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Hard reset of student selections. Triggered on profile change.
    """
    from models.library import StudentSelectedBook
    db.query(StudentSelectedBook).filter(StudentSelectedBook.student_id == student_id).delete()
    db.commit()
    return {"status": "reset complete"}

@router.get("/verify-selection/{student_id}/{book_id}")
async def verify_selection(
    student_id: UUID,
    book_id: UUID,
    db: Session = Depends(get_db)
):
    """Internal endpoint for chat-service to verify selection"""
    repo = BookRepository(db)
    is_selected = repo.is_book_selected(student_id, book_id)

    if not is_selected:
        # Check if mandatory
        from api.books import get_user_profile
        profile = await get_user_profile(str(student_id))
        if profile:
            current_semester = int(profile.get("semester", 0))
            book = repo.get_book_by_id(book_id)
            if book and book.semester == current_semester:
                return {"is_selected": True, "reason": "mandatory"}

    return {"is_selected": is_selected}
