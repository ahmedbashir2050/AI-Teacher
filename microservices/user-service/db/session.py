from core.config import settings
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

read_engine = create_engine(settings.READ_DATABASE_URL or settings.DATABASE_URL, pool_pre_ping=True)
ReadSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=read_engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_read_db():
    db = ReadSessionLocal()
    try:
        yield db
    finally:
        db.close()
