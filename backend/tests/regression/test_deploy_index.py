"""F13: production answered 500 because the corpus was never indexed there.

Three things must hold on a fresh deployment:
  - a missing collection is "index unavailable" (503), not a crash;
  - the server builds an empty index at startup, and only then;
  - the image ships the corpus the indexer reads.
No Qdrant, no network: fakes throughout.
"""

from __future__ import annotations

from pathlib import Path

import httpx
import pytest
from qdrant_client.http.exceptions import UnexpectedResponse

import app.main as main
from app.ingest import index_if_empty
from app.retrieve.qdrant_store import QdrantVectorStore
from app.retrieve.store import RetrievalUnavailable
from tests.fixtures.fake_model import FakeModel
from tests.fixtures.fake_store import FakeVectorStore

FIXTURE_CORPUS = Path(__file__).resolve().parents[1] / "fixtures" / "corpus"
BACKEND = Path(__file__).resolve().parents[2]


class _MissingCollectionClient:
    """What Qdrant returns when the collection has never been created."""

    def query_points(self, **_kwargs):
        raise UnexpectedResponse(
            status_code=404,
            reason_phrase="Not Found",
            content=b'{"status":{"error":"Collection not found"}}',
            headers=httpx.Headers(),
        )


def test_a_missing_collection_is_index_unavailable_not_a_crash():
    store = QdrantVectorStore.__new__(QdrantVectorStore)
    store.collection = "policy_passages_not_built"
    store._client = _MissingCollectionClient()  # noqa: SLF001 - a fake client, by design

    with pytest.raises(RetrievalUnavailable) as raised:
        store.search([0.0] * 1536, limit=5)

    assert "404" in str(raised.value)


def test_the_startup_builds_an_empty_index(model: FakeModel):
    store = FakeVectorStore()

    result = index_if_empty(store, model.embed, FIXTURE_CORPUS)

    assert result is not None
    assert result.passages > 0
    assert store.count() == result.passages


def test_the_startup_leaves_a_populated_index_alone(model: FakeModel):
    store = FakeVectorStore()
    index_if_empty(store, model.embed, FIXTURE_CORPUS)
    calls_before = len(model.embed_calls)

    result = index_if_empty(store, model.embed, FIXTURE_CORPUS)

    assert result is None
    assert len(model.embed_calls) == calls_before


def test_a_failed_startup_build_never_stops_the_server(monkeypatch):
    def broken(*_args, **_kwargs):
        raise RuntimeError("embedding provider unreachable")

    monkeypatch.setattr(main, "index_if_empty", broken)

    main._index_corpus_if_empty()  # must return, not raise  # noqa: SLF001


def test_an_empty_index_is_unavailable_not_a_refusal(monkeypatch):
    """Before the index is built, a question must not be refused as out of scope."""
    from fastapi.testclient import TestClient
    from sqlalchemy import create_engine, func, select
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool

    import app.core.records as records
    import app.features.ask as ask_module
    from app.core.database import Base, get_session
    from app.main import app as api

    engine = create_engine("sqlite://", connect_args={"check_same_thread": False},
                           poolclass=StaticPool)
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine, expire_on_commit=False)()

    monkeypatch.setattr(ask_module, "get_vector_store", lambda: FakeVectorStore())
    monkeypatch.setattr(ask_module, "embed", lambda texts: [[1.0, 0.0]] * len(texts))

    def override():
        yield db
        db.commit()

    api.dependency_overrides[get_session] = override
    try:
        response = TestClient(api).post("/ask", json={"question": "Any policy on crypto?"})
    finally:
        api.dependency_overrides.clear()

    assert response.status_code == 503
    assert "outcome" not in response.json()
    assert db.scalar(select(func.count()).select_from(records.Message)) == 0


def test_the_image_ships_the_corpus_the_indexer_reads():
    dockerfile = (BACKEND / "Dockerfile").read_text(encoding="utf-8")

    assert "COPY corpus/ ./corpus/" in dockerfile
    assert (BACKEND / "corpus" / "MANIFEST.yaml").exists()
