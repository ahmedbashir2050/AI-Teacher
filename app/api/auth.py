from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from app.core.security import create_access_token, create_refresh_token, verify_password, get_password_hash, Token
from app.models.requests import UserCreate
from app.models.responses import UserResponse
from app.config import settings

router = APIRouter()

def get_dummy_users_db():
    return {
        "admin": {
            "username": "admin",
            "hashed_password": get_password_hash(settings.ADMIN_DEFAULT_PASSWORD),
            "role": "admin",
            "disabled": False,
        },
        "student": {
            "username": "student",
            "hashed_password": get_password_hash(settings.STUDENT_DEFAULT_PASSWORD),
            "role": "student",
            "disabled": False,
        }
    }

@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    DUMMY_USERS_DB = get_dummy_users_db()
    user = DUMMY_USERS_DB.get(form_data.username)
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if user["disabled"]:
        raise HTTPException(status_code=400, detail="Inactive user")

    access_token = create_access_token(
        data={"sub": user["username"], "role": user["role"]}
    )
    refresh_token = create_refresh_token(
        data={"sub": user["username"], "role": user["role"]}
    )
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

@router.post("/register", response_model=UserResponse, status_code=201)
async def register_user(user: UserCreate):
    DUMMY_USERS_DB = get_dummy_users_db()
    if user.username in DUMMY_USERS_DB:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )

    hashed_password = get_password_hash(user.password)
    DUMMY_USERS_DB[user.username] = {
        "username": user.username,
        "hashed_password": hashed_password,
        "role": "student", # Default role
        "disabled": False
    }
    return UserResponse(username=user.username, role="student")
