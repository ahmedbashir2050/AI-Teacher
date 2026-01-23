import logging
import httpx
from uuid import UUID
from typing import List, Tuple

from repository.book_repository import BookRepository
from models.library import Book, ActionEnum, StudentSelectedBook
from core.config import settings
from core.metrics import BOOK_SELECTION_OPERATIONS, AVAILABLE_BOOKS_REQUESTS
from core.audit import log_audit
from sqlalchemy.orm import Session
from fastapi import HTTPException

logger = logging.getLogger(__name__)

class StudentBookService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = BookRepository(db)

    async def get_available_books(self, student_id: UUID, profile: dict) -> List[dict]:
        AVAILABLE_BOOKS_REQUESTS.inc()
        current_semester = int(profile.get("semester", 1))

        # Get faculty/dept IDs
        faculty = self.repo.get_faculty_by_name(profile.get("faculty"))
        dept_id_str = profile.get("department_id")
        if not faculty or not dept_id_str:
            raise HTTPException(status_code=400, detail="Student academic context incomplete")

        dept_id = UUID(dept_id_str)

        books_with_status = self.repo.get_available_books_for_student(
            student_id=student_id,
            faculty_id=faculty.id,
            department_id=dept_id,
            current_semester=current_semester
        )

        results = []
        for book, is_selected in books_with_status:
            effective_selected = is_selected or (book.semester == current_semester)
            results.append({
                "id": book.id,
                "title": book.title,
                "semester": book.semester,
                "is_selected": effective_selected,
                "is_mandatory": book.semester == current_semester
            })
        return results

    async def add_book_selection(self, student_id: UUID, book_id: UUID, source_semester: int, profile: dict, request_id: str = None) -> dict:
        book = self.repo.get_book_by_id(book_id)
        if not book:
            raise HTTPException(status_code=404, detail="Book not found")

        faculty = self.repo.get_faculty_by_name(profile.get("faculty"))
        if not faculty or book.faculty_id != faculty.id:
             raise HTTPException(status_code=403, detail="Book is not from your college")

        current_semester = int(profile.get("semester", 1))
        if book.semester != current_semester:
            count = self.repo.get_selection_count(student_id, current_semester)
            if count >= settings.MAX_ADDITIONAL_BOOKS:
                raise HTTPException(
                    status_code=400,
                    detail=f"Maximum additional books ({settings.MAX_ADDITIONAL_BOOKS}) exceeded"
                )

        self.repo.add_selected_book(
            student_id=student_id,
            book_id=book_id,
            semester=current_semester,
            source_semester=source_semester
        )

        BOOK_SELECTION_OPERATIONS.labels(action="add").inc()

        # Update RAG retriever
        async with httpx.AsyncClient() as client:
            try:
                await client.post(
                    f"{settings.RAG_SERVICE_URL}/refresh",
                    params={"faculty_id": str(faculty.id), "semester_id": str(current_semester)}
                )
            except Exception as e:
                logger.warning(f"Failed to refresh RAG retriever: {e}")

        log_audit(
            user_id=str(student_id),
            action="ADD_BOOK_SELECTION",
            resource="book",
            resource_id=str(book_id),
            metadata={"semester": current_semester, "source_semester": source_semester},
            request_id=request_id
        )
        return {"status": "success", "message": "Book added to selection"}

    async def remove_book_selection(self, student_id: UUID, book_id: UUID, profile: dict, request_id: str = None) -> dict:
        book = self.repo.get_book_by_id(book_id)
        if not book:
            raise HTTPException(status_code=404, detail="Book not found")

        current_semester = int(profile.get("semester", 1))

        # Mandatory book check (Service Layer Enforcement)
        if book.semester == current_semester:
             raise HTTPException(status_code=400, detail="Cannot remove mandatory books of the current semester")

        latest_selection = self.repo.is_book_selected(student_id, book_id)
        if not latest_selection:
             raise HTTPException(status_code=400, detail="Book is not currently selected")

        # Semester lock check
        from models.library import StudentSelectedBook
        from sqlalchemy import desc
        latest_record = self.db.query(StudentSelectedBook).filter(
            StudentSelectedBook.student_id == student_id,
            StudentSelectedBook.book_id == book_id
        ).order_by(desc(StudentSelectedBook.created_at)).first()

        if latest_record and latest_record.semester != current_semester:
            raise HTTPException(status_code=400, detail="Cannot modify selections from previous semesters")

        self.repo.remove_selected_book(
            student_id=student_id,
            book_id=book_id,
            semester=current_semester,
            source_semester=book.semester
        )

        BOOK_SELECTION_OPERATIONS.labels(action="remove").inc()

        # Update RAG retriever
        async with httpx.AsyncClient() as client:
            try:
                await client.post(
                    f"{settings.RAG_SERVICE_URL}/refresh",
                    params={"faculty_id": str(book.faculty_id), "semester_id": str(current_semester)}
                )
                # Invalidate active chat sessions in chat-service for this book
                await client.post(
                    f"{settings.CHAT_SERVICE_URL}/internal/sessions/invalidate",
                    json={"user_id": str(student_id), "book_id": str(book_id)}
                )
            except Exception as e:
                logger.warning(f"Failed to refresh RAG or invalidate sessions: {e}")

        log_audit(
            user_id=str(student_id),
            action="REMOVE_BOOK_SELECTION",
            resource="book",
            resource_id=str(book_id),
            metadata={"semester": current_semester},
            request_id=request_id
        )
        return {"status": "success", "message": "Book removed from selection"}
