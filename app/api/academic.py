from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.services import academic_service
from app.schemas import academic as schemas
from app.api.dependencies import get_db
from typing import List
import uuid

router = APIRouter()

@router.post("/faculties/", response_model=schemas.Faculty)
def create_faculty(faculty: schemas.FacultyCreate, db: Session = Depends(get_db)):
    return academic_service.create_faculty(db=db, faculty=faculty)

@router.get("/faculties/", response_model=List[schemas.Faculty])
def read_faculties(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    faculties = academic_service.get_faculties(db, skip=skip, limit=limit)
    return faculties

@router.get("/faculties/{faculty_id}", response_model=schemas.Faculty)
def read_faculty(faculty_id: uuid.UUID, db: Session = Depends(get_db)):
    db_faculty = academic_service.get_faculty(db, faculty_id=faculty_id)
    if db_faculty is None:
        raise HTTPException(status_code=404, detail="Faculty not found")
    return db_faculty

@router.post("/departments/", response_model=schemas.Department)
def create_department(department: schemas.DepartmentCreate, db: Session = Depends(get_db)):
    return academic_service.create_department(db=db, department=department)

@router.get("/departments/{faculty_id}", response_model=List[schemas.Department])
def read_departments(faculty_id: uuid.UUID, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    departments = academic_service.get_departments_by_faculty(db, faculty_id=faculty_id, skip=skip, limit=limit)
    return departments

@router.post("/semesters/", response_model=schemas.Semester)
def create_semester(semester: schemas.SemesterCreate, db: Session = Depends(get_db)):
    return academic_service.create_semester(db=db, semester=semester)

@router.get("/semesters/{department_id}", response_model=List[schemas.Semester])
def read_semesters(department_id: uuid.UUID, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    semesters = academic_service.get_semesters_by_department(db, department_id=department_id, skip=skip, limit=limit)
    return semesters

@router.get("/books/{semester_id}", response_model=List[schemas.Book])
def read_books(semester_id: uuid.UUID, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    books = academic_service.get_books_by_semester(db, semester_id=semester_id, skip=skip, limit=limit)
    return books
