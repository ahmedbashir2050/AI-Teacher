from pydantic import BaseModel, Field
from typing import Literal

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8, max_length=100)

class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=1000, description="The question to ask the AI Teacher.")

class SummarizeRequest(BaseModel):
    chapter: str = Field(..., min_length=1, description="The chapter to summarize.")
    style: Literal["exam", "simple", "bullet"] = Field("simple", description="The desired summarization style.")

class FlashcardsRequest(BaseModel):
    chapter: str = Field(..., min_length=1, description="The chapter to generate flashcards from.")
    count: int = Field(10, gt=0, le=50, description="The number of flashcards to generate.")

class ExamRequest(BaseModel):
    chapter: str = Field(..., min_length=1, description="The chapter to generate an exam from.")
    mcq: int = Field(10, ge=0, le=50, description="The number of multiple-choice questions.")
    theory: int = Field(5, ge=0, le=20, description="The number of theory-based questions.")
