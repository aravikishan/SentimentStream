"""SQLite database setup for SentimentStream using SQLAlchemy."""

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from config import settings

# Ensure instance directory exists for SQLite file
_base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.makedirs(os.path.join(_base_dir, "instance"), exist_ok=True)

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {},
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def create_tables() -> None:
    """Create all tables defined in the ORM models."""
    from models.schemas import Tweet, Topic, SentimentRecord  # noqa: F401
    Base.metadata.create_all(bind=engine)


def get_db():
    """Yield a database session, ensuring it is closed after use."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db_session():
    """Return a database session directly (for non-generator contexts)."""
    return SessionLocal()
