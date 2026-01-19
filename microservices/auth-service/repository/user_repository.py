from core.security import get_password_hash
from models.user import RoleEnum, User
from sqlalchemy.orm import Session


def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email, User.is_deleted.is_(None)).first()


def get_user_by_username(db: Session, username: str):
    return (
        db.query(User)
        .filter(User.username == username, User.is_deleted.is_(None))
        .first()
    )


def create_user(
    db: Session,
    email: str,
    username: str,
    password: str,
    role: RoleEnum = RoleEnum.STUDENT,
):
    db_user = User(
        email=email,
        username=username,
        hashed_password=get_password_hash(password),
        role=role,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user
