from pydantic import BaseModel, ConfigDict
from typing import Optional

import uuid

class UserBase(BaseModel):
    role: str
    faculty_id: Optional[uuid.UUID] = None
    department_id: Optional[uuid.UUID] = None

class UserCreate(UserBase):
    pass

class User(UserBase):
    id: str # This will be the user_id from Firebase

    model_config = ConfigDict(from_attributes=True)
