"""Stage 04 review fixes: F1, F2, F5, F6 and F7.

Each test pins a behaviour the five-pass review found missing, so it cannot
return silently. No Qdrant, no network and no Postgres: SQLite and fakes.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.core.records as records
import app.features.ask as ask_module
from app import main
from app.core.database import Base, get_session
from app.generate import ProviderError, compose
from app.main import app
from app.retrieve.qdrant_store import QdrantVectorStore
from app.retrieve.store import Hit, RetrievalUnavailable


def _hit() -> Hit:
    return Hit(
        passage_id="p1",
        text="Claims of 75 pounds or more require line-manager approval.",
        document_id="travel-expense-policy",
        document_title="Travel and Expense Policy",
        section="4.2 Approval thresholds",
        score=0.9,
        metadata={"status": "current", "version": "3.1"},
    )


class _StoreThatIsDown:
    def search(self, embedding, limit=5, min_score=0.0):
        raise RetrievalUnavailable("ResponseHandlingException")

    def ensure_ready(self):
        pass

    def count(self):
        return 0


class _WorkingStore:
    def search(self, embedding, limit=5, min_score=0.0):
        return [_hit()]

    def ensure_ready(self):
        pass

    def count(self):
        return 1


@pytest.fixture
def session():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine, expire_on_commit=False)()
    yield db
    db.close()


@pytest.fixture
def client(session, monkeypatch):
    monkeypatch.setattr(ask_module, "embed", lambda texts: [[1.0, 0.0]] * len(texts))
    monkeypatch.setattr(ask_module, "compose_answer", lambda q, p, e: "Claims of 75 need approval.")
    monkeypatch.setattr(ask_module, "get_vector_store", lambda: _WorkingStore())

    def override():
        yield session
        session.commit()

    app.dependency_overrides[get_session] = override
    yield TestClient(app)
    app.dependency_overrides.clear()


def _count(session, model) -> int:
    return session.scalar(select(func.count()).select_from(model))


# ------------------------------------------------ F1 -- retrieval failure is a 503


def test_a_store_that_is_down_returns_503_and_records_nothing(client, session, monkeypatch):
    monkeypatch.setattr(ask_module, "get_vector_store", lambda: _StoreThatIsDown())

    response = client.post("/ask", json={"question": "What is the threshold?"})

    assert response.status_code == 503
    assert "search is unavailable" in response.json()["detail"]
    assert _count(session, records.Conversation) == 0
    assert _count(session, records.Message) == 0


def test_an_embedding_failure_returns_503_and_records_nothing(client, session, monkeypatch):
    def unreachable(texts):
        raise ProviderError("embed failed (fake)", retryable=True)

    monkeypatch.setattr(ask_module, "embed", unreachable)

    response = client.post("/ask", json={"question": "What is the threshold?"})

    assert response.status_code == 503
    assert _count(session, records.Message) == 0


def test_the_qdrant_client_error_is_translated_at_the_store_boundary():
    store = QdrantVectorStore(url="http://127.0.0.1:1", collection="unused", dim=1536)

    with pytest.raises(RetrievalUnavailable):
        store.search([0.0] * 1536, limit=5)


# ------------------------------------------------------- F2 -- empty reply is not an answer


def test_an_empty_model_reply_is_degraded_not_answered(client, session, monkeypatch):
    monkeypatch.setattr(compose, "generate", lambda *a, **k: "")
    monkeypatch.setattr(ask_module, "compose_answer", compose.compose_answer)

    body = client.post("/ask", json={"question": "What is the threshold?"}).json()

    assert body["outcome"] == "degraded"
    assert body["answer"] is None
    assert body["citations"]


def test_compose_answer_refuses_to_return_an_empty_string(monkeypatch):
    monkeypatch.setattr(compose, "generate", lambda *a, **k: "")

    with pytest.raises(ProviderError):
        compose.compose_answer("q", [_hit()], [])


# ------------------------------------------------------- F5 -- startup uses logging


def test_startup_does_not_print_to_stdout():
    source = Path(main.__file__).read_text(encoding="utf-8")

    assert "print(" not in source


# ------------------------------------------------------- F7 -- CORS is narrowed


def test_cors_allows_post_from_the_frontend_origin():
    response = TestClient(app).options(
        "/ask",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )

    assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"
    assert response.headers.get("access-control-allow-credentials") is None


def test_cors_refuses_methods_the_api_does_not_use():
    response = TestClient(app).options(
        "/ask",
        headers={"Origin": "http://localhost:3000", "Access-Control-Request-Method": "DELETE"},
    )

    # Starlette answers a disallowed method with 400 and lists only the allowed
    # ones. A browser refuses the request because DELETE is not in that list.
    assert response.status_code == 400
    assert "DELETE" not in response.headers["access-control-allow-methods"]
