from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.services import academic_service
from app.schemas import academic as schemas
from app.api.dependencies import get_db
from typing import List

router = APIRouter()

@router.post("/colleges/", response_model=schemas.College)
def create_college(college: schemas.CollegeCreate, db: Session = Depends(get_db)):
    return academic_service.create_college(db=db, college=college)

@router.get("/colleges/", response_model=List[schemas.College])
def read_colleges(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    colleges = academic_service.get_colleges(db, skip=skip, limit=limit)
    return colleges

@router.get("/colleges/{college_id}", response_model=schemas.College)
def read_college(college_id: int, db: Session = Depends(get_db)):
    db_college = academic_service.get_college(db, college_id=college_id)
    if db_college is None:
        raise HTTPException(status_code=404, detail="College not found")
    return db_college

@router.post("/departments/", response_model=schemas.Department)
def create_department(department: schemas.DepartmentCreate, db: Session = Depends(get_db)):
    return academic_service.create_department(db=db, department=department)

@router.get("/departments/{college_id}", response_model=List[schemas.Department])
def read_departments(college_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    departments = academic_service.get_departments_by_college(db, college_id=college_id, skip=skip, limit=limit)
    return departments

@router.post("/semesters/", response_model=schemas.Semester)
def create_semester(semester: schemas.SemesterCreate, db: Session = Depends(get_db)):
    return academic_service.create_semester(db=db, semester=semester)

@router.get("/semesters/{department_id}", response_model=List[schemas.Semester])
def read_semesters(department_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    semesters = academic_service.get_semesters_by_department(db, department_id=department_id, skip=skip, limit=limit)
    return semesters

@router.post("/courses/", response_model=schemas.Course)
def create_course(course: schemas.CourseCreate, db: Session = Depends(get_db)):
    return academic_service.create_course(db=db, course=course)

@router.get("/courses/{semester_id}", response_model=List[schemas.Course])
def read_courses(semester_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    courses = academic_service.get_courses_by_semester(db, semester_id=semester_id, skip=skip, limit=limit)
    return courses

@router.get("/books/{course_id}", response_model=List[schemas.Book])
def read_books(course_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    books = academic_service.get_books_by_course(db, course_id=course_id, skip=skip, limit=limit)
    return books
