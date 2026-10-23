"""F5 -- ask. REQ-A1, REQ-A2, REQ-C1, REQ-C2.

Uses the fakes and an in-memory SQLite database. No Qdrant, Postgres or network.
"""

from __future__ import annotations

import uuid
from dataclasses import replace

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.retrieve.search as search_module
from app.api.ask import (
    get_db,
    get_embed,
    get_generate,
    get_store,
)
from app.core.config import settings
from app.core.database import Base
from app.generate.client import ProviderError
from app.main import app
from app.models.record import Conversation, Message, MessageCitation
from app.retrieve.search import Grounded  # noqa: F401  (imported to show the type exists)

QUESTION = "What is the approval threshold for a travel expense claim?"
UNRELATED = "something entirely unrelated to banking policy"
OUTCOMES = {"answered", "refused", "degraded"}


@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    session = session_factory()
    yield session
    session.close()
    engine.dispose()


@pytest.fixture
def api(loaded_store, model, db_session, monkeypatch):
    """The real app, with its dependencies pointed at the fakes."""
    monkeypatch.setattr(search_module, "settings", replace(settings, min_score=0.1))
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_store] = lambda: loaded_store
    app.dependency_overrides[get_embed] = lambda: model.embed
    app.dependency_overrides[get_generate] = lambda: model.generate
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


def _ask(client, question=QUESTION, conversation_id=None):
    return client.post("/ask", json={"question": question, "conversation_id": conversation_id})


def test_an_answered_question_returns_the_contract(api, model):
    """REQ-A1, REQ-A2: outcome is explicit, and every field of PRD §5 is present."""
    body = _ask(api).json()

    assert body["outcome"] == "answered"
    assert body["answer"]
    assert body["conversation_id"]
    assert body["message_id"]
    assert isinstance(body["latency_ms"], int)
    assert model.was_called


def test_citations_carry_document_section_version_status_and_score(api):
    body = _ask(api).json()

    assert body["citations"]
    for citation in body["citations"]:
        assert {"document_id", "document_title", "section", "version", "status", "score"} <= citation.keys()
        assert citation["status"] in {"current", "superseded"}


def test_citations_are_one_per_document_and_section(api):
    """D7: the same section retrieved twice is one citation, with its highest score."""
    body = _ask(api).json()

    keys = [(c["document_id"], c["section"]) for c in body["citations"]]
    assert len(keys) == len(set(keys))


def test_a_question_the_corpus_cannot_support_is_refused_without_a_model_call(api, model, monkeypatch):
    """REQ-R3: outcome refused, answer is the reason, no citations, no model call."""
    monkeypatch.setattr(search_module, "settings", replace(settings, min_score=0.99))

    body = _ask(api, question=UNRELATED).json()

    assert body["outcome"] == "refused"
    assert body["answer"]
    assert body["citations"] == []
    assert not model.was_called


def test_a_provider_failure_degrades_with_passages_and_no_answer(loaded_store, model, failing_model, db_session, monkeypatch):
    """REQ-G6, REQ-U6: passages come back, answer is null, outcome is degraded."""
    monkeypatch.setattr(search_module, "settings", replace(settings, min_score=0.1))
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_store] = lambda: loaded_store
    app.dependency_overrides[get_embed] = lambda: model.embed
    app.dependency_overrides[get_generate] = lambda: failing_model.generate
    try:
        body = TestClient(app).post("/ask", json={"question": QUESTION}).json()
    finally:
        app.dependency_overrides.clear()

    assert body["outcome"] == "degraded"
    assert body["answer"] is None
    assert body["citations"]


def test_a_provider_failure_before_search_is_an_error_not_a_refusal(loaded_store, model, db_session, monkeypatch):
    """The question cannot be searched, so it is neither answered nor refused. REQ-U5."""
    def unreachable(texts):
        raise ProviderError("embedding service unreachable")

    monkeypatch.setattr(search_module, "settings", replace(settings, min_score=0.1))
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_store] = lambda: loaded_store
    app.dependency_overrides[get_embed] = lambda: unreachable
    app.dependency_overrides[get_generate] = lambda: model.generate
    try:
        response = TestClient(app).post("/ask", json={"question": QUESTION})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 503


def test_every_response_is_exactly_one_of_three_outcomes(api):
    assert _ask(api).json()["outcome"] in OUTCOMES


def test_the_question_is_required(api):
    response = api.post("/ask", json={"conversation_id": None})

    assert response.status_code == 422


def test_the_first_question_creates_a_conversation(api, db_session):
    """REQ-C1."""
    body = _ask(api).json()

    conversation = db_session.get(Conversation, uuid.UUID(body["conversation_id"]))
    assert conversation is not None


def test_question_and_answer_are_both_stored_against_the_conversation(api, db_session):
    """REQ-C2: one user turn and one assistant turn, both on the conversation."""
    body = _ask(api).json()

    rows = db_session.scalars(
        select(Message).where(Message.conversation_id == uuid.UUID(body["conversation_id"]))
    ).all()
    assert sorted(m.role for m in rows) == ["assistant", "user"]
    assistant = next(m for m in rows if m.role == "assistant")
    assert assistant.outcome == "answered"
    assert assistant.prompt_version
    assert assistant.latency_ms is not None


def test_a_follow_up_joins_the_same_conversation(api, db_session):
    first = _ask(api).json()
    second = _ask(api, question="and what about above 500?", conversation_id=first["conversation_id"]).json()

    assert second["conversation_id"] == first["conversation_id"]
    count = db_session.scalar(
        select(func.count()).select_from(Message).where(
            Message.conversation_id == uuid.UUID(first["conversation_id"])
        )
    )
    assert count == 4


def test_an_unknown_conversation_is_a_404(api):
    response = _ask(api, conversation_id="00000000-0000-0000-0000-000000000000")

    assert response.status_code == 404


def test_citations_are_stored(api, db_session):
    body = _ask(api).json()

    stored = db_session.scalar(
        select(func.count()).select_from(MessageCitation).join(Message).where(
            Message.conversation_id == uuid.UUID(body["conversation_id"])
        )
    )
    assert stored == len(body["citations"])
