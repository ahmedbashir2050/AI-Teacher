from pydantic import BaseModel
from typing import List
from uuid import UUID

class ChatResponse(BaseModel):
    answer: str
    session_id: UUID

class SummarizeResponse(BaseModel):
    summary: str

class Flashcard(BaseModel):
    question: str
    answer: str

class FlashcardsResponse(BaseModel):
    flashcards: List[Flashcard]

class ExamQuestion(BaseModel):
    question_type: str
    question: str
    options: List[str] | None = None
    correct_answer: str

class ExamResponse(BaseModel):
    exam_id: int
    exam_title: str
    questions: List[ExamQuestion]

class ExamResultResponse(BaseModel):
    attempt_id: int
    score: int
    total_questions: int

class UserResponse(BaseModel):
    username: str
    role: str

class MessageResponse(BaseModel):
    message: str
