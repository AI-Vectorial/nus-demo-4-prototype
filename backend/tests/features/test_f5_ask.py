"""F5 -- POST /ask and the record it writes. Epic criteria 11, 16, 21 to 24.

The database is SQLite in memory, through the same models and the same
session factory the API uses -- CI has no Postgres, and these tests are about
what gets written, not about the engine.
"""

from __future__ import annotations

import time
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, func, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api import ask as ask_api
from app.core.database import Base
from app.core.models import Conversation, Message, MessageCitation
from app.generate.prompt import load_prompt
from app.main import app

ANSWERABLE = "What is the approval threshold for expenses?"
OFF_TOPIC = "something entirely unrelated to banking policy"


@pytest.fixture
def db():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False},
                           poolclass=StaticPool)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)


@pytest.fixture
def api(db, loaded_store, model):
    app.dependency_overrides[ask_api.get_sessions] = lambda: db
    app.dependency_overrides[ask_api.get_store] = lambda: loaded_store
    app.dependency_overrides[ask_api.get_model] = lambda: model
    app.dependency_overrides[ask_api.get_min_score] = lambda: 0.1
    yield TestClient(app)
    app.dependency_overrides.clear()


def _ask(api, question=ANSWERABLE, conversation_id=None):
    response = api.post("/ask", json={"question": question,
                                      "conversation_id": conversation_id})
    assert response.status_code == 200, response.text
    return response.json()


def _count(db, model) -> int:
    with db() as session:
        return session.scalar(select(func.count()).select_from(model))


# --------------------------------------------------------------- criterion 21


def test_an_answered_response_matches_the_contract(api):
    """REQ-A1, REQ-A2 -- PRD section 5."""
    body = _ask(api)

    assert body["outcome"] == "answered"
    assert body["answer"]
    assert body["citations"]
    assert set(body["citations"][0]) >= {"document_id", "document_title", "section",
                                         "version", "status", "score"}
    uuid.UUID(body["conversation_id"])
    uuid.UUID(body["message_id"])
    assert isinstance(body["latency_ms"], int)


def test_a_refused_response_matches_the_contract(api):
    body = _ask(api, OFF_TOPIC)

    assert body["outcome"] == "refused"
    assert body["answer"]
    assert body["citations"] == []


def test_a_degraded_response_matches_the_contract(api, model):
    model.fail_after = len(model.embed_calls) + 1  # embedding works, generation fails

    body = _ask(api)

    assert body["outcome"] == "degraded"
    assert body["answer"] is None
    assert body["citations"]


def test_an_empty_question_is_rejected(api):
    assert api.post("/ask", json={"question": "   "}).status_code == 422


def test_an_unknown_conversation_is_a_404(api):
    response = api.post("/ask", json={"question": ANSWERABLE,
                                      "conversation_id": str(uuid.uuid4())})
    assert response.status_code == 404


def test_a_search_outage_is_a_503_and_writes_nothing(api, db, failing_model):
    """Nothing retrieved and nothing to degrade to -- an error, not a refusal."""
    app.dependency_overrides[ask_api.get_model] = lambda: failing_model

    response = api.post("/ask", json={"question": ANSWERABLE})

    assert response.status_code == 503
    assert _count(db, Message) == 0


class _UnreachableStore:
    def search(self, embedding, limit=5, min_score=0.0):
        from app.retrieve.store import StoreUnavailable
        raise StoreUnavailable("vector store unreachable (fake)")


def test_a_vector_store_outage_is_a_503_and_writes_nothing(api, db, model):
    """Review F26 -- the same clear 503 as a model outage, not a bare 500."""
    app.dependency_overrides[ask_api.get_store] = lambda: _UnreachableStore()

    response = api.post("/ask", json={"question": ANSWERABLE})

    assert response.status_code == 503
    assert "unavailable" in response.json()["detail"]
    assert not model.was_called
    assert _count(db, Message) == 0


def test_a_database_outage_is_a_503_before_any_model_call(api, model):
    """Review F27 -- no record possible, so no paid model call either."""
    unreachable = create_engine("sqlite:////nonexistent-dir/for-this-test/x.db")
    app.dependency_overrides[ask_api.get_sessions] = lambda: sessionmaker(bind=unreachable)
    before = len(model.embed_calls)

    response = api.post("/ask", json={"question": ANSWERABLE})

    assert response.status_code == 503
    assert "record" in response.json()["detail"]
    assert not model.was_called
    assert len(model.embed_calls) == before


def test_no_database_connection_is_held_while_the_model_writes(api, db, model):
    """Review F27 -- follow-ups must not pin a pooled connection for the model call."""
    first = _ask(api)
    open_connections = [0]
    event.listen(db.kw["bind"], "checkout", lambda *a: open_connections.__setitem__(
        0, open_connections[0] + 1))
    event.listen(db.kw["bind"], "checkin", lambda *a: open_connections.__setitem__(
        0, open_connections[0] - 1))
    held = []
    original = model.generate

    def generate(*args, **kwargs):
        held.append(open_connections[0])
        return original(*args, **kwargs)

    model.generate = generate
    _ask(api, conversation_id=first["conversation_id"])

    assert held == [0]


# --------------------------------------------------------------- criterion 16


def test_the_stored_answer_records_model_prompt_version_and_latency(api, db):
    """REQ-G5."""
    body = _ask(api)

    with db() as session:
        message = session.get(Message, uuid.UUID(body["message_id"]))
    assert message.model
    assert message.prompt_version == load_prompt().version
    assert message.latency_ms == body["latency_ms"]


# --------------------------------------------------------------- criterion 23


def test_a_first_question_writes_one_conversation_two_messages_and_its_citations(api, db):
    """REQ-C1, REQ-C2."""
    body = _ask(api)

    assert _count(db, Conversation) == 1
    with db() as session:
        messages = session.scalars(select(Message).order_by(Message.created_at)).all()
        citations = session.scalars(select(MessageCitation)).all()
    assert [m.role for m in messages] == ["user", "assistant"]
    assert messages[0].content == ANSWERABLE
    assert messages[1].outcome == "answered"
    assert {str(m.conversation_id) for m in messages} == {body["conversation_id"]}
    assert sorted((c.document_id, c.section, c.version, c.status, c.score)
                  for c in citations) == sorted(
        (c["document_id"], c["section"], c["version"], c["status"], c["score"])
        for c in body["citations"])


def test_a_refusal_is_recorded_too(api, db):
    """P1 -- refused is an outcome, not an error."""
    _ask(api, OFF_TOPIC)

    with db() as session:
        outcomes = session.scalars(select(Message.outcome).where(
            Message.role == "assistant")).all()
    assert outcomes == ["refused"]
    assert _count(db, MessageCitation) == 0


# --------------------------------------------------------------- criterion 24


def test_a_second_question_joins_the_same_conversation(api, db):
    """REQ-C1, REQ-C2."""
    first = _ask(api)

    second = _ask(api, OFF_TOPIC, conversation_id=first["conversation_id"])

    assert second["conversation_id"] == first["conversation_id"]
    assert _count(db, Conversation) == 1
    assert _count(db, Message) == 4


# --------------------------------------------------------------- criterion 11


def test_a_refusal_is_fast(api):
    """NFR-2 -- no model call, so well under 1.5 s. Live timing in the ticket."""
    started = time.monotonic()
    body = _ask(api, OFF_TOPIC)
    assert body["outcome"] == "refused"
    assert time.monotonic() - started < 1.5


# --------------------------------------------------------------- criterion 22


class _DownStore:
    def health(self):
        return False, "unreachable: ConnectError"


def test_healthz_answers_and_names_a_vector_store_that_is_down(monkeypatch):
    """REQ-A5, NFR-5."""
    from app.api import health as health_api
    monkeypatch.setattr(health_api, "get_vector_store", lambda: _DownStore())
    monkeypatch.setattr(health_api.database, "health",
                        lambda: (False, "unreachable: OperationalError"))

    response = TestClient(app).get("/healthz")

    assert response.status_code == 200
    deps = response.json()["dependencies"]
    assert deps["vector_store"].startswith("down")
    assert deps["database"].startswith("down")
    assert "model" in deps


# --------------------------------------------- build decision B: index if empty


def test_an_empty_store_is_indexed_on_startup(store, model, monkeypatch):
    from app import main
    monkeypatch.setattr(main, "get_vector_store", lambda: store)
    monkeypatch.setattr(main, "embed", model.embed)

    main._index_if_empty()

    assert store.count() > 0


def test_a_complete_store_is_left_alone_on_startup(store, model, monkeypatch):
    from app import main
    from app.ingest import ingest
    ingest(store, model.embed)
    monkeypatch.setattr(main, "get_vector_store", lambda: store)
    monkeypatch.setattr(main, "embed", model.embed)
    before = len(model.embed_calls)

    main._index_if_empty()

    assert len(model.embed_calls) == before


def test_a_half_built_index_is_completed_on_startup(store, model, monkeypatch):
    """Review F2 -- a first boot that stopped part-way is finished by the next one."""
    from app import main
    from app.ingest import ingest, planned_passages
    ingest(store, model.embed)
    full = store.count()
    for passage_id in list(store._passages)[: full // 2]:
        del store._passages[passage_id]
    monkeypatch.setattr(main, "get_vector_store", lambda: store)
    monkeypatch.setattr(main, "embed", model.embed)

    main._index_if_empty()

    assert store.count() == full == planned_passages()


def test_a_failed_startup_index_does_not_stop_the_service(store, failing_model, monkeypatch):
    from app import main
    monkeypatch.setattr(main, "get_vector_store", lambda: store)
    monkeypatch.setattr(main, "embed", failing_model.embed)

    main._index_if_empty()  # logs, does not raise

    assert store.count() == 0
