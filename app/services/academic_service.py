from sqlalchemy.orm import Session
from app.models import academic as models
from app.schemas import academic as schemas
import uuid

def get_faculty(db: Session, faculty_id: uuid.UUID):
    return db.query(models.Faculty).filter(models.Faculty.id == faculty_id).first()

def get_faculties(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Faculty).offset(skip).limit(limit).all()

def create_faculty(db: Session, faculty: schemas.FacultyCreate):
    db_faculty = models.Faculty(name=faculty.name)
    db.add(db_faculty)
    db.commit()
    db.refresh(db_faculty)
    return db_faculty

def get_department(db: Session, department_id: uuid.UUID):
    return db.query(models.Department).filter(models.Department.id == department_id).first()

def get_departments_by_faculty(db: Session, faculty_id: uuid.UUID, skip: int = 0, limit: int = 100):
    return db.query(models.Department).filter(models.Department.faculty_id == faculty_id).offset(skip).limit(limit).all()

def create_department(db: Session, department: schemas.DepartmentCreate):
    db_department = models.Department(**department.model_dump())
    db.add(db_department)
    db.commit()
    db.refresh(db_department)
    return db_department

def get_semester(db: Session, semester_id: uuid.UUID):
    return db.query(models.Semester).filter(models.Semester.id == semester_id).first()

def get_semesters_by_department(db: Session, department_id: uuid.UUID, skip: int = 0, limit: int = 100):
    return db.query(models.Semester).filter(models.Semester.department_id == department_id).offset(skip).limit(limit).all()

def create_semester(db: Session, semester: schemas.SemesterCreate):
    db_semester = models.Semester(**semester.model_dump())
    db.add(db_semester)
    db.commit()
    db.refresh(db_semester)
    return db_semester

def get_book(db: Session, book_id: uuid.UUID):
    return db.query(models.Book).filter(models.Book.id == book_id).first()

def get_books_by_semester(db: Session, semester_id: uuid.UUID, skip: int = 0, limit: int = 100):
    return db.query(models.Book).filter(models.Book.semester_id == semester_id).offset(skip).limit(limit).all()

def create_book(db: Session, book: schemas.BookCreate, qdrant_collection: str, book_id: uuid.UUID):
    db_book = models.Book(**book.model_dump(), id=book_id, qdrant_collection=qdrant_collection)
    db.add(db_book)
    db.commit()
    db.refresh(db_book)
    return db_book
