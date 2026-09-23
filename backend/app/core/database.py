"""Postgres: corpus metadata and the record of every exchange.

Sessions are synchronous on purpose. Endpoints that touch the database are
declared with `def` rather than `async def`, so FastAPI runs them in a thread
pool and nothing blocks the event loop -- one fewer concept for a table to
learn, and no async-driver footguns during a two-hour lab.
"""

from __future__ import annotations

import logging
from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings

log = logging.getLogger(__name__)


class Base(DeclarativeBase):
    """Base for every ORM model."""


def _normalise(url: str) -> str:
    # Railway hands out postgres:// ; SQLAlchemy 2 wants postgresql+pg8000://
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+pg8000://", 1)
    return url


_engine = (
    create_engine(
        _normalise(settings.database_url),
        pool_pre_ping=True,  # Railway recycles connections; check before using
        pool_size=5,
        max_overflow=5,
    )
    if settings.database_configured
    else None
)

SessionLocal = (
    sessionmaker(bind=_engine, autoflush=False, expire_on_commit=False) if _engine else None
)


@contextmanager
def session_scope() -> Iterator[Session]:
    """A transaction. Commits on success, rolls back on anything else."""
    if SessionLocal is None:
        raise RuntimeError("DATABASE_URL is not set")
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_session() -> Iterator[Session]:
    """FastAPI dependency."""
    with session_scope() as db:
        yield db


def health() -> tuple[bool, str]:
    """Never raises: /healthz must answer even when Postgres is down."""
    if _engine is None:
        return False, "DATABASE_URL not set"
    try:
        with _engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True, "reachable"
    except Exception as exc:  # noqa: BLE001 - reported, not handled
        return False, f"unreachable: {type(exc).__name__}"
