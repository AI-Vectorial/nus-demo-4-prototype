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

from app.api import ask, health
from app.core import database, models
from app.generate import embed
from app.ingest import ingest
from app.retrieve import get_vector_store

log = logging.getLogger(__name__)

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
    print(f"tables: {models.ensure_tables()}")
    threading.Thread(target=_index_if_empty, name="index-if-empty", daemon=True).start()
    yield


def _index_if_empty() -> None:
    """Index the corpus on first boot, in the background (build decision B).

    A deployment starts with an empty collection and there is no route from a
    workspace to it, so the service fills its own. Only when empty: later
    starts find the passages and do nothing. In the background, so /healthz
    answers at once. A failure -- the model provider down, say -- is logged
    and the service keeps serving; the next start tries again.
    """
    try:
        store = get_vector_store()
        if store.count():
            return
        print(f"vector store empty: indexed {ingest(store, embed)} passages")
    except Exception:  # noqa: BLE001 - reported; the service must keep serving
        log.exception("indexing on startup failed; will retry on next start")


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

app.include_router(health.router)
app.include_router(ask.router)


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
