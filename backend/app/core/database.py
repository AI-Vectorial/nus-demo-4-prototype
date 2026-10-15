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
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings

log = logging.getLogger(__name__)


class Base(DeclarativeBase):
    """Base for every ORM model."""


def _normalise(url: str, database: str | None = "") -> str:
    """Railway's URL, pointed at this table's own database.

    database="" uses settings.database_name; database=None leaves the server's
    default database in place, which is what ensure_database() needs.
    """
    # Railway hands out postgres:// ; SQLAlchemy 2 wants postgresql+pg8000://
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+pg8000://", 1)

    # One Postgres instance, one database per table. Swapping the path here --
    # rather than trusting every session to set search_path -- means isolation
    # holds no matter how the connection is later used.
    target = settings.database_name if database == "" else database
    if target:
        base, _, _ = url.rpartition("/")
        url = f"{base}/{target}"
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


def ensure_database() -> tuple[bool, str]:
    """Create this table's database if it does not exist yet.

    One Postgres instance holds five databases, one per table. Rather than
    creating them by hand before the lab -- which is a step that can be
    forgotten, and which needs a public proxy the instance does not have -- each
    service creates its own on startup, from inside Railway's private network.

    That also makes a reset self-healing: drop the database, restart, and it
    comes back empty. Never raises; a failure here is reported by /healthz.
    """
    if not settings.database_url or not settings.database_name:
        return False, "DATABASE_URL or DATABASE_NAME not set"

    # CREATE DATABASE cannot run inside a transaction, and it cannot run from a
    # connection to the database being created -- so connect to the server's
    # default database instead.
    admin_url = _normalise(settings.database_url, database=None)

    try:
        admin = create_engine(admin_url, isolation_level="AUTOCOMMIT")
        with admin.connect() as conn:
            exists = conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :name"),
                {"name": settings.database_name},
            ).scalar()
            if exists:
                return True, f"{settings.database_name} already present"

            # Identifiers cannot be bound as parameters. The value comes from
            # our own deployment configuration, never from a request, and is
            # checked here so a typo cannot become a statement.
            name = settings.database_name
            if not name.replace("_", "").isalnum():
                return False, f"refusing to create a database named {name!r}"

            conn.execute(text(f'CREATE DATABASE "{name}"'))  # noqa: S608
            log.info("created database %s", name)
            return True, f"{name} created"
    except ProgrammingError as error:
        # Another service created it between the check and the create.
        if "already exists" in str(error):
            return True, f"{settings.database_name} already present"
        return False, f"could not create: {type(error).__name__}"
    except Exception as error:  # noqa: BLE001 - reported, not handled
        return False, f"could not create: {type(error).__name__}"
    finally:
        try:
            admin.dispose()
        except Exception:  # noqa: BLE001, S110 - nothing useful to do
            pass


def create_tables() -> tuple[bool, str]:
    """Create the record tables if they are not there. Never raises.

    Runs on boot, like ensure_database(). A failure is reported by /healthz and
    by the endpoints that need the tables, not by refusing to start.
    """
    if _engine is None:
        return False, "DATABASE_URL not set"
    try:
        import app.core.records  # noqa: F401 - registers the models on Base

        Base.metadata.create_all(_engine)
        return True, "tables ready"
    except Exception as exc:  # noqa: BLE001 - reported, not handled
        return False, f"could not create tables: {type(exc).__name__}"


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
