from __future__ import annotations

from collections.abc import Iterator
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_session
from app.core.models import Conversation, Message
from app.features.answer import Answered, Degraded
from app.main import app
from app.retrieve.query import Grounded, Insufficient
from app.retrieve.store import Hit


def as_hits(passages) -> list[Hit]:
    return [
        Hit(
            passage_id=passage.id,
            text=passage.text,
            document_id=passage.document_id,
            document_title=passage.document_title,
            section=passage.section,
            score=1.0,
            metadata=passage.metadata,
        )
        for passage in passages
    ]


@pytest.fixture
def api_client(monkeypatch: pytest.MonkeyPatch):
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    test_sessions = sessionmaker(bind=engine, expire_on_commit=False)

    def override_session() -> Iterator:
        with test_sessions() as session:
            try:
                yield session
                session.commit()
            except Exception:
                session.rollback()
                raise

    app.dependency_overrides[get_session] = override_session
    yield TestClient(app), test_sessions
    app.dependency_overrides.clear()
    engine.dispose()


def test_ask_endpoint_returns_a_contract_valid_answer_and_persists_turns(
    api_client, passages, monkeypatch: pytest.MonkeyPatch
) -> None:
    client, test_sessions = api_client
    hits = as_hits(passages)
    monkeypatch.setattr(
        "app.features.ask.retrieve",
        lambda question: Grounded(hits=hits),
    )
    monkeypatch.setattr(
        "app.features.ask.generate_answer",
        lambda question, hits, *, conversation_context="": Answered(
            answer="Claims of 75 pounds or more require approval.",
            citations=hits,
            model="test-model",
            prompt_version="v1",
            latency_ms=12,
        ),
    )

    response = client.post("/ask", json={"question": "What is the approval threshold?"})

    assert response.status_code == 200
    body = response.json()
    assert body["outcome"] == "answered"
    assert body["answer"] == "Claims of 75 pounds or more require approval."
    assert len(body["citations"]) == len(hits)
    assert UUID(body["conversation_id"])
    assert UUID(body["message_id"])
    assert body["latency_ms"] >= 0
    with test_sessions() as session:
        messages = session.scalars(select(Message).order_by(Message.created_at)).all()
        assert [message.role for message in messages] == ["user", "assistant"]
        assert messages[-1].outcome == "answered"
        assert messages[-1].model == "test-model"
        assert messages[-1].prompt_version == "v1"
        assert len(messages[-1].citations) == len(hits)
        assert session.get(Conversation, UUID(body["conversation_id"])) is not None


def test_refusal_is_explicit_and_skips_generation(
    api_client, monkeypatch: pytest.MonkeyPatch
) -> None:
    client, _ = api_client
    monkeypatch.setattr(
        "app.features.ask.retrieve",
        lambda question: Insufficient(best_score=0.01),
    )

    def unexpected_generation(*args, **kwargs):
        raise AssertionError("refusal must not call generation")

    monkeypatch.setattr("app.features.ask.generate_answer", unexpected_generation)
    response = client.post("/ask", json={"question": "Can I expense my partner's flight?"})

    assert response.status_code == 200
    assert response.json()["outcome"] == "refused"
    assert response.json()["citations"] == []
    assert "contact Compliance" in response.json()["answer"]


def test_degraded_response_has_no_composed_answer(api_client, passages, monkeypatch) -> None:
    client, _ = api_client
    hits = as_hits(passages)
    monkeypatch.setattr(
        "app.features.ask.retrieve",
        lambda question: Grounded(hits=hits),
    )
    monkeypatch.setattr(
        "app.features.ask.generate_answer",
        lambda question, hits, *, conversation_context="": Degraded(
            answer=None,
            citations=hits,
            model="test-model",
            prompt_version="v1",
            latency_ms=0,
        ),
    )
    response = client.post("/ask", json={"question": "What is the approval threshold?"})

    assert response.status_code == 200
    assert response.json()["outcome"] == "degraded"
    assert response.json()["answer"] is None
    assert response.json()["citations"]


def test_blank_question_is_rejected(api_client) -> None:
    client, _ = api_client
    response = client.post("/ask", json={"question": "  "})

    assert response.status_code == 422
