from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session
from repository.user_repository import user_repository
from models.user import User, RoleEnum
from fastapi import HTTPException

class UserService:
    @staticmethod
    def get_user_by_id(db: Session, user_id: UUID) -> User:
        user = user_repository.get_by_id(db, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user

    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        return user_repository.get_by_email(db, email)

    @staticmethod
    def create_user(db: Session, user_data: dict) -> User:
        existing_user = user_repository.get_by_email(db, user_data["email"])
        if existing_user:
            raise HTTPException(status_code=409, detail="Email already registered")
        return user_repository.create(db, user_data)

    @staticmethod
    def update_profile(db: Session, user_id: UUID, update_data: dict) -> User:
        user = UserService.get_user_by_id(db, user_id)
        return user_repository.update(db, user, update_data)

    @staticmethod
    def deactivate_user(db: Session, user_id: UUID) -> User:
        user = UserService.get_user_by_id(db, user_id)
        return user_repository.soft_delete(db, user)

user_service = UserService()
