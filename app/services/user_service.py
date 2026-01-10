from sqlalchemy.orm import Session
from app.models import user as models
from app.schemas import user as schemas

def get_user(db: Session, user_id: str):
    return db.query(models.User).filter(models.User.id == user_id).first()

def create_user(db: Session, user: schemas.UserCreate, user_id: str):
    db_user = models.User(**user.model_dump(), id=user_id)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user
