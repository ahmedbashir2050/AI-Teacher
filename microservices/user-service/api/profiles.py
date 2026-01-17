from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from ..db.session import get_db
from pydantic import BaseModel
from ..models.user import UserProfile

router = APIRouter()

class ProfileUpdate(BaseModel):
    full_name: str = None
    faculty_id: str = None
    department_id: str = None
    semester_id: str = None

@router.get("/me")
def get_my_profile(db: Session = Depends(get_db), x_user_id: str = Header(...)):
    profile = db.query(UserProfile).filter(UserProfile.user_id == x_user_id).first()
    if not profile:
        profile = UserProfile(user_id=x_user_id)
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile

@router.put("/me")
def update_my_profile(profile_in: ProfileUpdate, db: Session = Depends(get_db), x_user_id: str = Header(...)):
    profile = db.query(UserProfile).filter(UserProfile.user_id == x_user_id).first()
    if not profile:
        profile = UserProfile(user_id=x_user_id)
        db.add(profile)

    if profile_in.full_name is not None:
        profile.full_name = profile_in.full_name
    if profile_in.faculty_id is not None:
        profile.faculty_id = profile_in.faculty_id
    if profile_in.department_id is not None:
        profile.department_id = profile_in.department_id
    if profile_in.semester_id is not None:
        profile.semester_id = profile_in.semester_id

    db.commit()
    db.refresh(profile)
    return profile
