from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from models.library import Book, Faculty, Department
from datetime import datetime

class BookRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_book_by_id(self, book_id: UUID) -> Optional[Book]:
        return self.db.query(Book).filter(Book.id == book_id, Book.is_deleted.is_(None)).first()

    def get_book_by_hash(self, file_hash: str) -> Optional[Book]:
        return self.db.query(Book).filter(Book.file_hash == file_hash, Book.is_deleted.is_(None)).first()

    def create_book(self, book_data: dict) -> Book:
        book = Book(**book_data)
        self.db.add(book)
        self.db.commit()
        self.db.refresh(book)
        return book

    def update_book(self, book_id: UUID, update_data: dict) -> Optional[Book]:
        book = self.get_book_by_id(book_id)
        if book:
            for key, value in update_data.items():
                setattr(book, key, value)
            self.db.commit()
            self.db.refresh(book)
        return book

    def soft_delete_book(self, book_id: UUID) -> bool:
        book = self.get_book_by_id(book_id)
        if book:
            book.is_deleted = datetime.utcnow()
            self.db.commit()
            return True
        return False

    def list_books(
        self,
        faculty_id: Optional[UUID] = None,
        department_id: Optional[UUID] = None,
        semester: Optional[int] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Book]:
        query = self.db.query(Book).filter(Book.is_deleted.is_(None))
        if faculty_id:
            query = query.filter(Book.faculty_id == faculty_id)
        if department_id:
            query = query.filter(Book.department_id == department_id)
        if semester:
            query = query.filter(Book.semester == semester)
        return query.offset(skip).limit(limit).all()

    def get_faculty_by_id(self, faculty_id: UUID) -> Optional[Faculty]:
        return self.db.query(Faculty).filter(Faculty.id == faculty_id, Faculty.is_deleted.is_(None)).first()

    def get_department_by_id(self, department_id: UUID) -> Optional[Department]:
        return self.db.query(Department).filter(Department.id == department_id, Department.is_deleted.is_(None)).first()

    def create_faculty(self, name: str) -> Faculty:
        faculty = Faculty(name=name)
        self.db.add(faculty)
        self.db.commit()
        self.db.refresh(faculty)
        return faculty

    def create_department(self, name: str, faculty_id: UUID) -> Department:
        department = Department(name=name, faculty_id=faculty_id)
        self.db.add(department)
        self.db.commit()
        self.db.refresh(department)
        return department
