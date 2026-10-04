"""Shared pytest fixtures. Each test gets a fresh database with demo data."""
import os
import tempfile
import uuid
from pathlib import Path

# Point the app at a throwaway SQLite file BEFORE importing it.
_db_file = Path(tempfile.gettempdir()) / f"heraura_test_{uuid.uuid4().hex}.db"
os.environ["DATABASE_URL"] = f"sqlite:///{_db_file.as_posix()}"

import pytest
from fastapi.testclient import TestClient

from app.db import Base, SessionLocal, engine
from app.main import app
from app.seed import seed_demo_data


@pytest.fixture(autouse=True)
def fresh_db():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        seed_demo_data(db)
    yield


@pytest.fixture
def db():
    with SessionLocal() as session:
        yield session


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def new_user_payload():
    unique = uuid.uuid4().hex[:8]
    return {"email": f"user_{unique}@example.com", "full_name": "Test Patient", "password": "Str0ngPass!"}


@pytest.fixture
def logged_in_client(client, new_user_payload):
    response = client.post("/api/auth/register", json=new_user_payload)
    assert response.status_code == 201
    return client
