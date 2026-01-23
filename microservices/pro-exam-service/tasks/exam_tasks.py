import asyncio
import logging
from core.celery_app import celery_app
from db.session import SessionLocal
from services.exam_service import exam_service

logger = logging.getLogger(__name__)

@celery_app.task(name="tasks.generate_pro_exam_task", bind=True, max_retries=3)
def generate_pro_exam_task(
    self,
    book_id: str,
    faculty_id: str,
    department_id: str,
    semester_id: str,
    title: str,
    request_id: str = None
):
    db = SessionLocal()
    try:
        loop = asyncio.get_event_loop()
        exam = loop.run_until_complete(
            exam_service.generate_exam(
                db, book_id, faculty_id, department_id, semester_id, title, request_id
            )
        )
        return {"exam_id": str(exam.id)}
    except Exception as exc:
        logger.error(f"Error in generate_pro_exam_task: {exc}")
        self.retry(exc=exc, countdown=60)
    finally:
        db.close()
