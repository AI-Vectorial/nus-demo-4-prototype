"""M04 Policy Assistant — backend API.

Ask (F5), the corpus (F7) and history (F8), over an index the service keeps
in step with the corpus itself. docs/PRD.md says what must be true;
tickets/T1-plan.md says how table 3 built it.
"""

from __future__ import annotations

import logging
import os
import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import DBAPIError

from app.api import ask, conversations, corpus, health
from app.core import database
from app.core.config import settings
from app.generate import embed
from app.ingest.ingest import ensure_index
from app.retrieve import get_vector_store

log = logging.getLogger("app.main")

# The application's own troubleshooting lines -- ids, outcomes, latency, never
# a question's text (NFR-6, C22) -- at INFO; everything else at WARNING.
logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s %(message)s")
logging.getLogger("app").setLevel(logging.INFO)

BUILD_SHA = os.getenv("RAILWAY_GIT_COMMIT_SHA", "local")[:7]
ENVIRONMENT = os.getenv("RAILWAY_ENVIRONMENT_NAME", "development")

# The Next.js frontend is a separate Railway service, so it is cross-origin.
ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
    if origin.strip()
]

@asynccontextmanager
async def lifespan(_: FastAPI):
    """Make this table's own database exist before serving.

    Five services share one Postgres instance and each owns one database.
    Creating it here rather than by hand means a reset is self-healing: drop
    the database, restart, and it comes back empty.

    A failure is logged and reported by /healthz, never fatal -- a health
    endpoint that cannot start because its dependency is down reports nothing
    at all, which is the opposite of useful.
    """
    ok, detail = database.ensure_database()
    print(f"database: {detail}")
    if ok:
        _, detail = database.ensure_tables()
        print(f"tables: {detail}")
    # In the background, so /healthz answers while the index is built.
    threading.Thread(target=_ensure_index, name="ensure-index", daemon=True).start()
    yield


def _ensure_index() -> None:
    """Build the index if it is missing or stale. Never raises: a failure is
    logged, /healthz shows the passage count, and the next start tries again."""
    try:
        status = ensure_index(
            get_vector_store(), embed,
            corpus_dir=settings.corpus_dir,
            max_tokens=settings.chunk_max_tokens,
            overlap_tokens=settings.chunk_overlap_tokens,
            batch_size=settings.embedding_batch_size,
            dimensions=settings.embedding_dimensions,
        )
        log.info(status)
    except Exception as exc:  # noqa: BLE001 - reported, not handled
        log.error("index not ensured: %s", type(exc).__name__)


app = FastAPI(
    title="M04 Policy Assistant API",
    description="Ask questions about internal policy. Answers cite their sources.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(DBAPIError)
def _database_unavailable(_: Request, exc: DBAPIError) -> JSONResponse:
    """Postgres down is an outage to report, not a crash to leak (NFR-5)."""
    log.error("database error: %s", type(exc.orig).__name__)
    return JSONResponse(status_code=503, content={"detail": "conversation store is unavailable"})


app.include_router(health.router)
app.include_router(ask.router)
app.include_router(corpus.router)
app.include_router(conversations.router)


@app.get("/")
async def root() -> dict[str, str]:
    """Service identity. The user-facing interface is the frontend service."""
    return {
        "service": "m04-policy-assistant-api",
        "version": "0.1.0",
        "build": BUILD_SHA,
        "environment": ENVIRONMENT,
        "docs": "/docs",
    }
