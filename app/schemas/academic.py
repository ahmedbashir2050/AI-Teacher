from pydantic import BaseModel, ConfigDict
from typing import Optional
import datetime

class CollegeBase(BaseModel):
    name: str

class CollegeCreate(CollegeBase):
    pass

class College(CollegeBase):
    id: int

    model_config = ConfigDict(from_attributes=True)

class DepartmentBase(BaseModel):
    name: str
    college_id: int

class DepartmentCreate(DepartmentBase):
    pass

class Department(DepartmentBase):
    id: int

    model_config = ConfigDict(from_attributes=True)

class SemesterBase(BaseModel):
    name: str
    department_id: int

class SemesterCreate(SemesterBase):
    pass

class Semester(SemesterBase):
    id: int

    model_config = ConfigDict(from_attributes=True)

class CourseBase(BaseModel):
    name: str
    code: str
    semester_id: int

class CourseCreate(CourseBase):
    pass

class Course(CourseBase):
    id: int

    model_config = ConfigDict(from_attributes=True)

class BookBase(BaseModel):
    title: str
    language: str
    course_id: int

class BookCreate(BookBase):
    pass

class Book(BookBase):
    id: int
    uploaded_by: str
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)
