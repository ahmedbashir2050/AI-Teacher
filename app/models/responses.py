from pydantic import BaseModel, Field
from typing import List

class ChatResponse(BaseModel):
    answer: str

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
    exam_title: str
    questions: List[ExamQuestion]

class UserResponse(BaseModel):
    username: str
    role: str

class MessageResponse(BaseModel):
    message: str
