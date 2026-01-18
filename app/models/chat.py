# app/models/chat.py
from sqlalchemy import Column, String, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.db.base import BaseModel

class ChatSession(BaseModel):
    """
    Represents a single conversation session between a user and the AI
    for a specific book.
    - `user_id` links the session to the user who initiated it.
    - `book_id` links the session to the curriculum material being discussed.
    """
    __tablename__ = 'chat_sessions'

    user_id = Column(ForeignKey('users.id'), nullable=False, index=True)
    book_id = Column(ForeignKey('books.id'), nullable=False, index=True)

    # Many-to-one relationship: A session belongs to a user.
    user = relationship("User") # No back-populates needed if user doesn't need to see all sessions directly.

    # Many-to-one relationship: A session is about a specific book.
    book = relationship("Book") # Similarly, no back-populates needed here.

    # One-to-many relationship: A session contains many messages.
    # The 'order_by' ensures that when we load messages, they are in chronological order.
    # The 'cascade' option ensures that deleting a session also deletes its messages.
    messages = relationship(
        "ChatMessage",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="ChatMessage.created_at"
    )

class ChatMessage(BaseModel):
    """
    Represents a single message within a chat session.
    - `session_id` links the message to its parent session.
    - `role` indicates whether the message is from the 'user' or the 'assistant'.
    - `content` stores the actual text of the message.
    """
    __tablename__ = 'chat_messages'

    session_id = Column(ForeignKey('chat_sessions.id'), nullable=False, index=True)
    # Using a simple String for the role is sufficient here. An Enum could also be used.
    role = Column(String(50), nullable=False) # 'user' or 'assistant'
    content = Column(Text, nullable=False)

    # Many-to-one relationship: A message belongs to one session.
    session = relationship("ChatSession", back_populates="messages")
