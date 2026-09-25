"""M04 Policy Assistant — backend API.

THE SCAFFOLD. Everything needed to serve, test and deploy -- and nothing that
answers a question. Ingestion, retrieval, refusal, generation and the /ask
endpoint are yours to build.

Start with docs/PRD.md for what must be true, and docs/features.md for what to
build first. START-HERE.md is your first two minutes.
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import ask, corpus, health
from app.core import database, models  # noqa: F401 - models registers the tables

BUILD_SHA = os.getenv("RAILWAY_GIT_COMMIT_SHA", "local")[:7]
ENVIRONMENT = os.getenv("RAILWAY_ENVIRONMENT_NAME", "development")

# The Next.js frontend is a separate Railway service, so it is cross-origin.
ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
    if origin.strip()
]

def _index_if_empty() -> None:
    """Index the corpus on first boot, if nothing is indexed yet.

    A deployment whose collection is empty cannot answer anything, and the
    Qdrant instance is only reachable from inside Railway's private network --
    so there is no way to index it from a laptop after the fact.

    This does NOT do the work for anybody. It calls ingest(), which is the
    function being built; before that exists, or if it raises, the collection
    simply stays empty and /healthz says so. It runs only when the count is
    zero, so it costs one call on every later restart and never re-embeds.

    Deliberately synchronous. It takes a few seconds on a corpus this size, and
    serving requests against an empty index would only produce refusals that
    look like a broken product.
    """
    try:
        from app.retrieve import get_vector_store

        store = get_vector_store()
        store.ensure_ready()
        if store.count() > 0:
            print(f"corpus: {store.count()} passages already indexed")
            return
    except Exception as error:  # noqa: BLE001 - reported, never fatal
        print(f"corpus: vector store unavailable ({type(error).__name__})")
        return

    try:
        from app.ingest import ingest

        result = ingest()
        print(f"corpus: indexed {result}")
    except ImportError:
        print("corpus: empty, and ingestion is not built yet")
    except Exception as error:  # noqa: BLE001 - reported, never fatal
        print(f"corpus: indexing failed ({type(error).__name__}: {error})")


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
        # Only once the database exists. Create_all is additive and idempotent,
        # so a restart costs nothing and a fresh database comes up ready.
        try:
            with database.session_scope() as session:
                database.Base.metadata.create_all(session.get_bind())
            print("database: tables ready")
        except Exception as error:  # noqa: BLE001 - reported, never fatal
            print(f"database: tables unavailable ({type(error).__name__})")

    _index_if_empty()
    yield


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
app.include_router(ask.router)  # F5/F6 -- ask, and the conversation behind it
app.include_router(corpus.router)  # F7 -- browse the corpus, read from disk


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
