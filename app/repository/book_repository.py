from sqlalchemy.orm import Session
from app.models.db import Book

def get_book_by_id(db: Session, book_id: int) -> Book:
    return db.query(Book).filter(Book.id == book_id).first()
