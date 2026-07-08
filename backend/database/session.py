"""
Database - Session Management
==============================
Provides the SQLAlchemy engine, session factory, and FastAPI dependency
``get_db()`` for request-scoped sessions.
"""

from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from backend.config import settings
from backend.database.base import Base

logger = logging.getLogger(__name__)

# ── Engine Configuration ──────────────────────────────────────────────
_connect_args: dict = {}
if settings.DATABASE_URL.startswith("sqlite"):
    _connect_args = {"check_same_thread": False}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=_connect_args,
    pool_pre_ping=True,
    echo=settings.DEBUG,
)

# Enable WAL mode for SQLite to improve concurrent read performance
if settings.DATABASE_URL.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_conn, _connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL;")
        cursor.execute("PRAGMA foreign_keys=ON;")
        cursor.close()

# ── Session Factory ───────────────────────────────────────────────────
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


# ── Flask Dependency Helper ───────────────────────────────────────────
def get_db() -> Session:
    """Return the request-scoped database session from Flask's application context.
    
    This replaces the old FastAPI dependency generator. The session is opened
    in `before_request` and closed in `teardown_appcontext`.
    """
    from flask import g
    return getattr(g, "db", None)


# ── Context Manager (for non-FastAPI usage) ───────────────────────────
@contextmanager
def db_session() -> Generator[Session, None, None]:
    """Context-manager wrapper around ``SessionLocal`` for scripts / services."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# ── Table Creation Utility ────────────────────────────────────────────
def init_db() -> None:
    """Create all tables that don't yet exist.

    Call this once at application startup.
    """
    # Import models so they are registered on ``Base.metadata``
    import backend.database.models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialised (engine=%s)", engine.url)
