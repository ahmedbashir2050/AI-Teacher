import logging

from core.celery_app import celery_app
from db.session import SessionLocal
from services.exam_service import generate_and_store_exam

logger = logging.getLogger(__name__)


@celery_app.task(name="tasks.generate_exam_task", bind=True, max_retries=3)
def generate_exam_task(
    self,
    user_id: str,
    course_id: str,
    collection_name: str,
    faculty_id: str,
    semester_id: str,
    mcq_count: int,
    theory_count: int,
    request_id: str,
):
    db = SessionLocal()
    try:
        # Note: We need to adapt generate_and_store_exam to be synchronous if called from Celery,
        # OR run it in an event loop. Since it's already async, we'll use async_to_sync or similar,
        # but for simplicity, let's just run it in a new loop.
        import asyncio

        loop = asyncio.get_event_loop()
        exam = loop.run_until_complete(
            generate_and_store_exam(
                db,
                user_id,
                course_id,
                collection_name,
                faculty_id,
                semester_id,
                mcq_count,
                theory_count,
                request_id,
            )
        )
        return (
            {"exam_id": str(exam.id)} if exam else {"error": "Failed to generate exam"}
        )
    except Exception as exc:
        logger.error(f"Error in generate_exam_task: {exc}")
        self.retry(exc=exc, countdown=60)
    finally:
        db.close()
