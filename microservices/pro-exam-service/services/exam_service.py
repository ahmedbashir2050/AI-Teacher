import logging
import httpx
from sqlalchemy.orm import Session
from models.exam import ProExam
from services.llm_service import llm_service
from core.config import settings
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

class ExamService:
    @retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=1, max=2))
    async def _fetch_book_context(self, book_id: str, faculty_id: str, semester_id: str, department_id: str = None, request_id: str = None) -> list[dict]:
        async with httpx.AsyncClient(timeout=30.0) as client:
            payload = {
                "query": "Generate comprehensive exam questions covering all key concepts.",
                "top_k": 40, # High enough to cover 4 sections
                "collection_name": "books",
                "faculty_id": str(faculty_id),
                "semester_id": str(semester_id),
            }
            if department_id:
                payload["department_id"] = str(department_id)
            # We assume rag-service supports book_id or we will update it.
            payload["book_id"] = str(book_id)

            resp = await client.post(
                f"{settings.RAG_SERVICE_URL}/search",
                json=payload,
                headers={"X-Request-ID": request_id} if request_id else {}
            )
            resp.raise_for_status()
            return resp.json()

    async def generate_exam(self, db: Session, book_id: str, faculty_id: str, department_id: str, semester_id: str, title: str, request_id: str = None) -> ProExam:
        logger.info(f"Generating professional exam for book {book_id}")

        context = await self._fetch_book_context(book_id, faculty_id, semester_id, department_id, request_id)
        if not context:
            logger.error(f"No context found for book {book_id}")
            raise ValueError("No context found for the specified book.")

        exam_content = await llm_service.generate_pro_exam(context)

        db_exam = ProExam(
            title=title,
            book_id=book_id,
            faculty_id=faculty_id,
            department_id=department_id,
            semester_id=semester_id,
            content=exam_content
        )
        db.add(db_exam)
        db.commit()
        db.refresh(db_exam)

        return db_exam

exam_service = ExamService()
