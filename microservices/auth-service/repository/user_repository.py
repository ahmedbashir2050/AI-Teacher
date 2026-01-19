from datetime import datetime, timezone

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
        auth_provider="local",
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def create_google_user(
    db: Session,
    email: str,
    full_name: str = None,
    avatar_url: str = None,
    role: RoleEnum = RoleEnum.STUDENT,
):
    db_user = User(
        email=email,
        full_name=full_name,
        avatar_url=avatar_url,
        auth_provider="google",
        role=role,
        is_active=True,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def update_last_login(db: Session, user: User):
    user.last_login_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(user)
    return user
