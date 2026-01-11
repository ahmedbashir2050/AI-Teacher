from pydantic import BaseModel
import uuid

class ChatRequest(BaseModel):
    book_id: uuid.UUID
    question: str
