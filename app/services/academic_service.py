from sqlalchemy.orm import Session
from app.models import academic as models
from app.schemas import academic as schemas

def get_college(db: Session, college_id: int):
    return db.query(models.College).filter(models.College.id == college_id).first()

def get_colleges(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.College).offset(skip).limit(limit).all()

def create_college(db: Session, college: schemas.CollegeCreate):
    db_college = models.College(name=college.name)
    db.add(db_college)
    db.commit()
    db.refresh(db_college)
    return db_college

def get_department(db: Session, department_id: int):
    return db.query(models.Department).filter(models.Department.id == department_id).first()

def get_departments_by_college(db: Session, college_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.Department).filter(models.Department.college_id == college_id).offset(skip).limit(limit).all()

def create_department(db: Session, department: schemas.DepartmentCreate):
    db_department = models.Department(**department.model_dump())
    db.add(db_department)
    db.commit()
    db.refresh(db_department)
    return db_department

def get_semester(db: Session, semester_id: int):
    return db.query(models.Semester).filter(models.Semester.id == semester_id).first()

def get_semesters_by_department(db: Session, department_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.Semester).filter(models.Semester.department_id == department_id).offset(skip).limit(limit).all()

def create_semester(db: Session, semester: schemas.SemesterCreate):
    db_semester = models.Semester(**semester.model_dump())
    db.add(db_semester)
    db.commit()
    db.refresh(db_semester)
    return db_semester

def get_course(db: Session, course_id: int):
    return db.query(models.Course).filter(models.Course.id == course_id).first()

def get_courses_by_semester(db: Session, semester_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.Course).filter(models.Course.semester_id == semester_id).offset(skip).limit(limit).all()

def create_course(db: Session, course: schemas.CourseCreate):
    db_course = models.Course(**course.model_dump())
    db.add(db_course)
    db.commit()
    db.refresh(db_course)
    return db_course

def get_book(db: Session, book_id: int):
    return db.query(models.Book).filter(models.Book.id == book_id).first()

def get_books_by_course(db: Session, course_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.Book).filter(models.Book.course_id == course_id).offset(skip).limit(limit).all()

def create_book(db: Session, book: schemas.BookCreate, user_id: str):
    db_book = models.Book(**book.model_dump(), uploaded_by=user_id)
    db.add(db_book)
    db.commit()
    db.refresh(db_book)
    return db_book
