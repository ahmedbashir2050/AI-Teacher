from pydantic import BaseModel, ConfigDict
from typing import Optional
import datetime
import uuid

class FacultyBase(BaseModel):
    name: str

class FacultyCreate(FacultyBase):
    pass

class Faculty(FacultyBase):
    id: uuid.UUID
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)

class DepartmentBase(BaseModel):
    name: str
    faculty_id: uuid.UUID

class DepartmentCreate(DepartmentBase):
    pass

class Department(DepartmentBase):
    id: uuid.UUID
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)

class SemesterBase(BaseModel):
    name: str
    department_id: uuid.UUID

class SemesterCreate(SemesterBase):
    pass

class Semester(SemesterBase):
    id: uuid.UUID
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)

class BookBase(BaseModel):
    title: str
    language: str
    semester_id: uuid.UUID

class BookCreate(BookBase):
    pass

class Book(BookBase):
    id: uuid.UUID
    qdrant_collection: str
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)
