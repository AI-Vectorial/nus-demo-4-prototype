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
import runpy
import sys
import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import ask, corpus, health
from app.core import database

log = logging.getLogger(__name__)

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

    A Codespace gets indexed because somebody types `python -m app.ingest`.
    A deployment has nobody to type it. Without this, every table's live URL
    answers 500 on the first question it is ever asked -- the collection does
    not exist, retrieval 404s, and the only clue is a stack trace in a log
    nobody is looking at during a demo.

    It runs the table's own ingestion, through REQ-I1's command, rather than
    calling into their modules: `python -m app.ingest` is a fixed requirement,
    so it is the one entry point every table is guaranteed to have.

    In a thread, because indexing takes a minute or two and the health check
    has to keep answering -- Railway stops routing to a container whose health
    check never passes, so blocking here would mean never deploying at all.

    Silent before F1 exists, and silent once there are passages: the cost of a
    needless re-embed is real money and a weekly budget.
    """
    try:
        from app.retrieve import get_vector_store

        if get_vector_store().count() > 0:
            print("index: already indexed")
            return
    except Exception:
        pass  # no collection yet, or not reachable -- try to build it

    argv = sys.argv
    sys.argv = ["app.ingest"]
    try:
        runpy.run_module("app.ingest", run_name="__main__")
    except Exception as exc:
        print(f"index: not indexed -- {type(exc).__name__}: {exc}")
    finally:
        sys.argv = argv


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
        try:
            database.create_schema()
        except Exception as exc:
            log.error("database schema initialization failed (%s)", type(exc).__name__)

    # The deployment indexes itself. See _index_if_empty.
    threading.Thread(target=_index_if_empty, name="index", daemon=True).start()
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
app.include_router(ask.router)
app.include_router(corpus.router)

# Your routers are mounted here.
#
#   app.include_router(ask.router)    F5 -- the endpoint that makes it a product
#
# See docs/features.md for what to build and in what order.


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
