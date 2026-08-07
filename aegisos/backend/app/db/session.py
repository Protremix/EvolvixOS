import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.base import Base

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://aegis:aegis@localhost:5432/evolvixos",
)

# SQLite support for testing
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
