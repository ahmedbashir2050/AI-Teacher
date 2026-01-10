from pydantic import BaseModel, ConfigDict
from typing import Optional

class UserBase(BaseModel):
    role: str
    college_id: Optional[int] = None
    department_id: Optional[int] = None

class UserCreate(UserBase):
    pass

class User(UserBase):
    id: str # This will be the user_id from Firebase

    model_config = ConfigDict(from_attributes=True)
