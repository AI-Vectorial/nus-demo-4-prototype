"""Shared by the API feature tests: SQLite in memory for the section 6 tables,
the real corpus indexed into the fake store, and /ask wired to fakes.

FAKE_SCALE_MIN_SCORE is a threshold on the fake model's bag-of-words scale. It
exercises the refusal logic; it is NOT table 3's D2 value, which is measured on
the real embedding model and signed off by the team.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.ask import AskDeps, get_deps
from app.core.database import Base, get_session
from app.ingest import corpus
from app.ingest.ingest import ingest
from app.main import app

CORPUS = Path(__file__).resolve().parents[2] / "corpus"
FAKE_SCALE_MIN_SCORE = 0.3


@pytest.fixture
def db():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False},
                           poolclass=StaticPool)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


@pytest.fixture
def indexed(store, model):
    ingest(store, model.embed, corpus_dir=CORPUS, max_tokens=400, overlap_tokens=0,
           batch_size=96)
    return store


@pytest.fixture(autouse=True)
def _clear_overrides():
    yield
    app.dependency_overrides.clear()


def api(db, store, *, embed, generate, enabled=True) -> TestClient:
    def session():
        s = db()
        try:
            yield s
            s.commit()
        finally:
            s.close()

    app.dependency_overrides[get_session] = session
    app.dependency_overrides[get_deps] = lambda: AskDeps(
        store=store, embed=embed, generate=generate, documents=corpus.load(CORPUS),
        top_k=5, min_score=FAKE_SCALE_MIN_SCORE, context_messages=5,
        generation_enabled=enabled, model_name="fake-model",
    )
    return TestClient(app)
