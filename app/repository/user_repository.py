from sqlalchemy.orm import Session
from app.models.user import User, Role as UserRole
from app.core.hashing import get_password_hash

def create_user(db: Session, username: str, password: str, role: UserRole) -> User:
    db_user = User(
        username=username,
        hashed_password=get_password_hash(password),
        role=role,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_user_by_email(db: Session, email: str) -> User:
    return db.query(User).filter(User.email == email).first()
