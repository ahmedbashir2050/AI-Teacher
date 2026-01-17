from sqlalchemy.orm import Session
from ..models.academics import Faculty, Department, Semester, Course, Book

def get_faculties(db: Session):
    return db.query(Faculty).all()

def get_faculty(db: Session, faculty_id: str):
    return db.query(Faculty).filter(Faculty.id == faculty_id).first()
