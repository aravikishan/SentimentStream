"""Shared fixtures for SentimentStream tests."""

import os
import sys
import pytest

# Ensure the project root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Override settings before importing anything else
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["TESTING"] = "1"

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models.database import Base, get_db


@pytest.fixture(name="db_engine")
def fixture_db_engine():
    """Create an in-memory SQLite engine for testing."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(name="db_session")
def fixture_db_session(db_engine):
    """Create a database session for testing."""
    TestSession = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    session = TestSession()
    yield session
    session.close()


@pytest.fixture(name="client")
def fixture_client(db_engine):
    """Create a FastAPI TestClient with overridden database."""
    from app import create_app

    TestSession = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)

    def override_get_db():
        db = TestSession()
        try:
            yield db
        finally:
            db.close()

    app = create_app()
    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app, raise_server_exceptions=False) as c:
        yield c

    app.dependency_overrides.clear()
