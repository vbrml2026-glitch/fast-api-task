from __future__ import annotations

import os
from pathlib import Path
import uuid
import sys

import pytest


# Configure test environment before importing the app (app reads env on import).
_TEST_DB_FILE = Path(__file__).with_name("test.sqlite")
if _TEST_DB_FILE.exists():
    _TEST_DB_FILE.unlink()

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

os.environ["DATABASE_URL"] = f"sqlite+pysqlite:///{_TEST_DB_FILE}"
os.environ["JWT_SECRET"] = "test-secret"
os.environ["JWT_ALGORITHM"] = "HS256"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "60"


from fastapi.testclient import TestClient  # noqa: E402

from app.db import get_session_local, init_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Post, PostVote, User  # noqa: E402

init_db()

@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(autouse=True)
def clean_db():
    SessionLocal = get_session_local()
    db = SessionLocal()
    try:
        # Delete in dependency order to satisfy FK constraints.
        db.execute(PostVote.__table__.delete())
        db.execute(Post.__table__.delete())
        db.execute(User.__table__.delete())
        db.commit()
    finally:
        db.close()


@pytest.fixture()
def make_user_credentials():
    def _make_user_credentials():
        suffix = uuid.uuid4().hex[:8]
        username = f"user_{suffix}"
        email = f"{username}@example.com"
        password = "password123"
        return {"username": username, "email": email, "password": password}

    return _make_user_credentials

