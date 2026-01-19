import logging
from uuid import UUID

import httpx
from core.audit import log_audit
from core.config import settings
from core.metrics import BOOK_DOWNLOAD_COUNT
from db.session import get_db
from fastapi import APIRouter, Depends, HTTPException, Request
from repository.book_repository import BookRepository
from services.storage_service import storage_service
from sqlalchemy.orm import Session

router = APIRouter()
logger = logging.getLogger(__name__)


async def get_user_profile(user_id: str):
    async with httpx.AsyncClient() as client:
        try:
            # Call user-service /me endpoint
            resp = await client.get(
                f"{settings.USER_SERVICE_URL}/me", headers={"X-User-Id": user_id}
            )
            if resp.status_code == 200:
                return resp.json()
            else:
                logger.error(
                    f"Failed to fetch user profile: {resp.status_code} {resp.text}"
                )
        except Exception as e:
            logger.error(f"Failed to fetch user profile: {e}")
    return None


@router.get("/books/{book_id}/download")
async def download_book(book_id: UUID, request: Request, db: Session = Depends(get_db)):
    user_id = request.headers.get("X-User-Id")
    role = request.headers.get("X-User-Role")

    if not user_id:
        raise HTTPException(status_code=401, detail="User identity missing")

    repo = BookRepository(db)
    book = repo.get_book_by_id(book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    # If user is admin, allow download
    if role in ["admin", "super_admin"]:
        pass
    else:
        # Check student eligibility
        profile = await get_user_profile(user_id)
        if not profile:
            raise HTTPException(
                status_code=500, detail="Could not verify user eligibility"
            )

        # In this implementation, we assume we match by names or IDs.
        # Given user-service uses names in its User model, we look up our Faculty/Dept by name.
        faculty = repo.get_faculty_by_id(book.faculty_id)
        dept = repo.get_department_by_id(book.department_id)

        if not faculty or not dept:
            raise HTTPException(status_code=500, detail="Book academic context missing")

        # Eligibility check
        if (
            profile.get("faculty") != faculty.name
            or profile.get("major") != dept.name
            or str(profile.get("semester")) != str(book.semester)
        ):
            raise HTTPException(
                status_code=403, detail="You are not eligible to download this book"
            )

    # Generate signed URL (15 mins = 900s)
    url = await storage_service.generate_presigned_url(book.file_key, expiration=900)
    if not url:
        raise HTTPException(status_code=500, detail="Failed to generate download link")

    BOOK_DOWNLOAD_COUNT.labels(
        faculty_id=str(book.faculty_id), department_id=str(book.department_id)
    ).inc()

    log_audit(
        user_id=user_id,
        action="BOOK_DOWNLOADED",
        resource="book",
        resource_id=str(book_id),
        metadata={"title": book.title},
        request_id=getattr(request.state, "request_id", None),
    )

    return {"download_url": url}
