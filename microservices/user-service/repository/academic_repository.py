from models.academics import Faculty
from sqlalchemy.orm import Session


def get_faculties(db: Session):
    return db.query(Faculty).filter(Faculty.is_deleted.is_(None)).all()


def get_faculty(db: Session, faculty_id: str):
    return (
        db.query(Faculty)
        .filter(Faculty.id == faculty_id, Faculty.is_deleted.is_(None))
        .first()
    )
