from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session
from models.user import User, RoleEnum
from datetime import datetime

class UserRepository:
    def get_by_id(self, db: Session, user_id: UUID) -> Optional[User]:
        return db.query(User).filter(User.id == user_id, User.is_deleted.is_(None)).first()

    def get_by_email(self, db: Session, email: str) -> Optional[User]:
        return db.query(User).filter(User.email == email, User.is_deleted.is_(None)).first()

    def create(self, db: Session, user_in: dict) -> User:
        user = User(**user_in)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    def update(self, db: Session, user: User, update_data: dict) -> User:
        for field, value in update_data.items():
            setattr(user, field, value)
        db.commit()
        db.refresh(user)
        return user

    def soft_delete(self, db: Session, user: User) -> User:
        user.is_deleted = datetime.now()
        db.commit()
        db.refresh(user)
        return user

user_repository = UserRepository()
