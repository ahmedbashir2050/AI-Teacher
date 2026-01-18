from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from db.session import get_db
from repository import academic_repository
from pydantic import BaseModel
from typing import List

router = APIRouter()

class FacultyResponse(BaseModel):
    id: str
    name: str
    class Config:
        from_attributes = True

@router.get("/faculties", response_model=List[FacultyResponse])
def list_faculties(db: Session = Depends(get_db)):
    return academic_repository.get_faculties(db)
