from fastapi import APIRouter
from api.v1.endpoints import exam, submission

router = APIRouter()

router.include_router(exam.router, prefix="/exams", tags=["Exams"])
router.include_router(submission.router, prefix="/submissions", tags=["Submissions"])
