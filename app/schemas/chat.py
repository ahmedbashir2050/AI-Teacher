from pydantic import BaseModel, ConfigDict
import datetime

class ChatMessageBase(BaseModel):
    book_id: int
    role: str # "user" or "assistant"
    message: str

class ChatMessageCreate(ChatMessageBase):
    pass

class ChatMessage(ChatMessageBase):
    id: int
    user_id: str
    timestamp: datetime.datetime

    model_config = ConfigDict(from_attributes=True)

class ChatRequest(BaseModel):
    book_id: int
    question: str
