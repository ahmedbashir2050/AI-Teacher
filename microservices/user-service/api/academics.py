from typing import List

from db.session import get_db, get_read_db
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from repository import academic_repository
from sqlalchemy.orm import Session

router = APIRouter()


class FacultyResponse(BaseModel):
    id: str
    name: str

    class Config:
        from_attributes = True


@router.get("/faculties", response_model=List[FacultyResponse])
def list_faculties(db: Session = Depends(get_read_db)):
    return academic_repository.get_faculties(db)
