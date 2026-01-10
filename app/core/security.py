from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.services import user_service
from app.api.dependencies import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Placeholder for Firebase token validation
def verify_firebase_token(token: str):
    # In a real application, you would use firebase_admin to verify the token
    # For now, we'll just return a dummy user_id
    if token == "admin_token":
        return "admin_user_id"
    return "student_user_id"


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    user_id = verify_firebase_token(token)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = user_service.get_user(db, user_id=user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user

def get_current_admin_user(current_user: dict = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="The user doesn't have enough privileges")
    return current_user
