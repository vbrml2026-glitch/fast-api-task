from __future__ import annotations

import os
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import get_database_url

Base = declarative_base()

_ENGINE: Engine | None = None
_SessionLocal: sessionmaker | None = None


def get_engine() -> Engine:
    global _ENGINE
    if _ENGINE is not None:
        return _ENGINE

    url = get_database_url()
    if url.startswith("sqlite") and ":memory:" in url:
        _ENGINE = create_engine(
            url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
    else:
        _ENGINE = create_engine(url)
    return _ENGINE


def get_session_local() -> sessionmaker:
    global _SessionLocal
    if _SessionLocal is not None:
        return _SessionLocal

    engine = get_engine()
    _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return _SessionLocal


def get_db() -> Generator:
    SessionLocal = get_session_local()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    # Create tables for development/testing. For the required "verification" flow,
    # we still provide a PostgreSQL SQL script separately.
    from app.models import User, Post, PostVote  # noqa: F401

    engine = get_engine()
    Base.metadata.create_all(bind=engine)

