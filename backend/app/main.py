"""M04 Policy Assistant — backend API.

THE SCAFFOLD. Everything needed to serve, test and deploy -- and nothing that
answers a question. Ingestion, retrieval, refusal, generation and the /ask
endpoint are yours to build.

Start with docs/PRD.md for what must be true, and docs/features.md for what to
build first. START-HERE.md is your first two minutes.
"""

from __future__ import annotations

import logging
import os
import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import ask, conversations, corpus, health
from app.core import database
from app.generate import embed
from app.ingest import index_if_empty
from app.retrieve import get_vector_store

BUILD_SHA = os.getenv("RAILWAY_GIT_COMMIT_SHA", "local")[:7]
ENVIRONMENT = os.getenv("RAILWAY_ENVIRONMENT_NAME", "development")

# Startup and per-exchange lines (F5, F6) need to reach stderr, not vanish.
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# The Next.js frontend is a separate Railway service, so it is cross-origin.
ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
    if origin.strip()
]

def _index_corpus_if_empty() -> None:
    """Build the index on a fresh deployment, in the background (F13).

    Runs off the startup path, so the server answers /healthz during the build.
    Only an empty store is indexed here. A failure is logged by type and shows in
    /healthz as zero passages. It never stops the server (NFR-5).
    """
    try:
        result = index_if_empty(get_vector_store(), embed)
    except Exception as error:  # noqa: BLE001 - logged by type, visible in /healthz
        log.warning("index: not built at startup (%s); run python -m app.ingest",
                    type(error).__name__)
        return
    if result is None:
        log.info("index: already populated, nothing to build")
    else:
        log.info("index: built %d documents, %d passages", result.documents, result.passages)


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
    (log.info if ok else log.warning)("database: %s", detail)
    ok, detail = database.create_tables()
    (log.info if ok else log.warning)("tables: %s", detail)
    threading.Thread(target=_index_corpus_if_empty, name="index-corpus", daemon=True).start()
    yield


app = FastAPI(
    title="M04 Policy Assistant API",
    description="Ask questions about internal policy. Answers cite their sources.",
    version="0.1.0",
    lifespan=lifespan,
)

# Only the methods and headers the API uses (review F7). The browser never calls
# the API directly, so credentials are not needed.
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

app.include_router(health.router)
app.include_router(ask.router)           # F5
app.include_router(conversations.router) # F8
app.include_router(corpus.router)        # F7


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
