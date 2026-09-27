"""F5 -- POST /ask. REQ-A1, REQ-A2, REQ-A5, REQ-C1, REQ-C2, D7.

The real route, with the fake store and model and an in-memory database
standing in for Qdrant, OpenRouter and Postgres.
"""

from __future__ import annotations

import uuid
from dataclasses import replace

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api import ask as ask_api
from app.core import database
from app.core.config import settings
from app.core.models import Conversation, Message, MessageCitation
from app.main import app
from app.retrieve.store import Passage

THRESHOLD_QUESTION = "What is the approval threshold for claims?"
OUT_OF_SCOPE = "How many days of parental leave do I get?"


@pytest.fixture
def db():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False},
                           poolclass=StaticPool)
    database.Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


@pytest.fixture
def config(monkeypatch):
    monkeypatch.setattr(ask_api, "settings", replace(
        settings, _min_score="0.2", _retrieve_top_k="3", generation_enabled=True,
        llm_model="openai/test-model",
    ))


def _client(db, store, model) -> TestClient:
    def session():
        with db.begin() as s:
            yield s

    app.dependency_overrides = {
        ask_api.get_db: session,
        ask_api.get_store: lambda: store,
        ask_api.get_embed: lambda: model.embed,
        ask_api.get_generate: lambda: model.generate,
    }
    return TestClient(app)


@pytest.fixture
def client(db, loaded_store, model, config):
    yield _client(db, loaded_store, model)
    app.dependency_overrides = {}


def _ask(client, question=THRESHOLD_QUESTION, conversation_id=None):
    return client.post("/ask", json={"question": question, "conversation_id": conversation_id})


# --- the three outcomes: REQ-A1, REQ-A2 --------------------------------------


def test_an_answerable_question_is_answered_with_citations(client, model):
    body = _ask(client).json()

    assert body["outcome"] == "answered"
    assert body["answer"] == model.answer
    assert body["citations"][0] == {
        "document_id": "travel-expense-policy",
        "document_title": "Travel and Expense Policy",
        "section": "4.2 Approval thresholds",
        "version": "1.0",
        "status": "current",
        "score": pytest.approx(body["citations"][0]["score"]),
    }
    assert uuid.UUID(body["conversation_id"]) and uuid.UUID(body["message_id"])
    assert isinstance(body["latency_ms"], int)


def test_an_out_of_scope_question_is_refused_with_no_citations_and_no_model_call(client, model):
    body = _ask(client, OUT_OF_SCOPE).json()

    assert body["outcome"] == "refused"
    assert "does not cover" in body["answer"]
    assert "Compliance" in body["answer"]
    assert body["citations"] == []
    assert not model.was_called


def test_generation_off_is_degraded_with_passages_and_no_answer(db, loaded_store, model,
                                                               monkeypatch):
    monkeypatch.setattr(ask_api, "settings", replace(
        settings, _min_score="0.2", _retrieve_top_k="3", generation_enabled=False,
    ))
    client = _client(db, loaded_store, model)
    body = _ask(client).json()
    app.dependency_overrides = {}

    assert body["outcome"] == "degraded"
    assert body["answer"] is None
    assert body["citations"]
    assert not model.was_called


def test_an_unreachable_model_is_degraded(db, loaded_store, failing_model, config):
    # Embedding still works here; only generation fails.
    failing_model.fail = False
    original = failing_model.generate

    def unreachable(*args, **kwargs):
        failing_model.fail = True
        return original(*args, **kwargs)

    failing_model.generate = unreachable
    client = _client(db, loaded_store, failing_model)
    body = _ask(client).json()
    app.dependency_overrides = {}

    assert body["outcome"] == "degraded"
    assert body["answer"] is None
    assert body["citations"]


def test_an_empty_question_is_rejected(client):
    assert _ask(client, "   ").status_code == 422


def test_an_unknown_conversation_is_404(client):
    assert _ask(client, conversation_id=str(uuid.uuid4())).status_code == 404


def test_retrieval_failing_is_an_error_not_a_refusal(db, loaded_store, failing_model, config):
    client = _client(db, loaded_store, failing_model)
    response = _ask(client)
    app.dependency_overrides = {}

    assert response.status_code == 503
    assert "outcome" not in response.json()


# --- citations: D7 -----------------------------------------------------------


def test_two_passages_from_one_section_are_one_citation_with_the_higher_score(
    db, store, model, passages, config
):
    first = passages[0]
    second = replace(first, id="p0b", text=first.text + " Approval is recorded in the system.")
    store.upsert([first, second, *passages[1:]])
    client = _client(db, store, model)
    citations = _ask(client).json()["citations"]
    app.dependency_overrides = {}

    sections = [(c["document_id"], c["version"], c["section"]) for c in citations]
    assert sections.count(("travel-expense-policy", "1.0", "4.2 Approval thresholds")) == 1
    scores = [c["score"] for c in citations]
    assert scores == sorted(scores, reverse=True)


def test_the_same_section_in_two_versions_is_two_citations(db, store, model, passages, config):
    old = replace(passages[0], id="old", metadata={"version": "0.9", "status": "superseded"})
    store.upsert([*passages, old])
    client = _client(db, store, model)
    citations = _ask(client).json()["citations"]
    app.dependency_overrides = {}

    statuses = {(c["version"], c["status"]) for c in citations
                if c["section"] == "4.2 Approval thresholds"}
    assert statuses == {("1.0", "current"), ("0.9", "superseded")}


# --- the record: REQ-C1, REQ-C2, REQ-G5 --------------------------------------


def test_the_first_question_creates_a_conversation_and_stores_both_turns(client, db):
    body = _ask(client).json()

    with db() as s:
        conversation = s.get(Conversation, uuid.UUID(body["conversation_id"]))
        messages = s.scalars(select(Message).order_by(Message.created_at, Message.role.desc()))
        user, assistant = sorted(messages, key=lambda m: m.role != "user")
        assert conversation is not None
        assert (user.role, user.content, user.outcome) == ("user", THRESHOLD_QUESTION, None)
        assert assistant.id == uuid.UUID(body["message_id"])
        assert (assistant.outcome, assistant.content) == ("answered", body["answer"])
        assert assistant.model == "openai/test-model"
        assert assistant.prompt_version == "answer_v1"
        assert assistant.latency_ms == body["latency_ms"]


def test_the_answers_citations_are_stored_against_it(client, db):
    body = _ask(client).json()

    with db() as s:
        stored = s.scalars(select(MessageCitation).where(
            MessageCitation.message_id == uuid.UUID(body["message_id"])
        )).all()
        assert {(c.document_id, c.section, c.version, c.status) for c in stored} == {
            (c["document_id"], c["section"], c["version"], c["status"])
            for c in body["citations"]
        }


def test_a_refusal_is_recorded_too_with_no_model_or_prompt(client, db):
    body = _ask(client, OUT_OF_SCOPE).json()

    with db() as s:
        assistant = s.get(Message, uuid.UUID(body["message_id"]))
        assert assistant.outcome == "refused"
        assert assistant.model is None and assistant.prompt_version is None


def test_a_second_question_joins_the_same_conversation(client, db):
    first = _ask(client).json()
    second = _ask(client, OUT_OF_SCOPE, first["conversation_id"]).json()

    assert second["conversation_id"] == first["conversation_id"]
    with db() as s:
        assert s.query(Message).count() == 4
        assert s.query(Conversation).count() == 1


# --- /healthz: REQ-A5, NFR-5 -------------------------------------------------


def test_healthz_answers_when_postgres_and_qdrant_are_down(monkeypatch):
    from app.api import health
    from app.retrieve.qdrant_store import QdrantVectorStore

    unreachable_db = create_engine("postgresql+pg8000://u:p@127.0.0.1:9/none")
    monkeypatch.setattr(database, "_engine", unreachable_db)
    monkeypatch.setattr(health, "get_vector_store",
                        lambda: QdrantVectorStore(url="http://127.0.0.1:9"))

    response = TestClient(app).get("/healthz")

    assert response.status_code == 200
    dependencies = response.json()["dependencies"]
    assert dependencies["database"].startswith("down")
    assert dependencies["vector_store"].startswith("down")


def test_passage_fixture_is_what_these_tests_assume(passages: list[Passage]):
    assert passages[0].section == "4.2 Approval thresholds"
